#!/usr/bin/env python3
"""Records audio from a USB mic, transcribes with Whisper, and writes markdown notes."""

from __future__ import annotations

import argparse
import queue
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pyaudio
import whisper

SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1
FORMAT = pyaudio.paInt16
FRAMES_PER_BUFFER = 1024


def list_devices():
    """Print available audio input devices and exit."""
    pa = pyaudio.PyAudio()
    print("Available input devices:")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"  [{i}] {info['name']} ({int(info['defaultSampleRate'])}Hz, {info['maxInputChannels']}ch)")
    pa.terminate()


def find_dji_device(pa: pyaudio.PyAudio) -> int | None:
    """Auto-detect DJI mic by name."""
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0 and "wireless mic" in info["name"].lower():
            return i
    return None


def audio_capture_thread(pa: pyaudio.PyAudio, device_index: int, audio_queue: queue.Queue, stop_event: threading.Event):
    """Capture audio in a background thread, pushing frames to a queue."""
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=FRAMES_PER_BUFFER,
    )
    while not stop_event.is_set():
        try:
            data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
            audio_queue.put(data)
        except OSError:
            break
    stream.stop_stream()
    stream.close()


def transcribe_chunk(model, audio_data: np.ndarray) -> str:
    """Transcribe a numpy audio array with Whisper."""
    result = model.transcribe(audio_data, language="en", fp16=False)
    return result["text"].strip()


def write_segment(filepath: Path, timestamp: str, text: str):
    """Append a timestamped segment to the markdown file."""
    with open(filepath, "a") as f:
        f.write(f"\n## {timestamp}\n{text}\n")


def main():
    parser = argparse.ArgumentParser(description="Record and transcribe with Whisper")
    parser.add_argument("--device", type=int, default=None, help="Audio input device index")
    parser.add_argument("--chunk", type=int, default=30, help="Chunk duration in seconds (default: 30)")
    parser.add_argument("--model", type=str, default="large-v3", help="Whisper model name (default: large-v3)")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    parser.add_argument("--language", type=str, default="en", help="Language code (default: en)")
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    # Load Whisper model
    print(f"Loading Whisper {args.model} model (this may download ~3GB on first run)...")
    model = whisper.load_model(args.model)
    print("Model loaded.")

    # Set up audio
    pa = pyaudio.PyAudio()
    device_index = args.device
    if device_index is None:
        device_index = find_dji_device(pa)
        if device_index is not None:
            info = pa.get_device_info_by_index(device_index)
            print(f"Auto-detected: [{device_index}] {info['name']}")
        else:
            device_index = pa.get_default_input_device_info()["index"]
            info = pa.get_device_info_by_index(device_index)
            print(f"Using default input: [{device_index}] {info['name']}")

    # Create output file
    now = datetime.now()
    output_dir = Path.home() / ".meetings" / "todo"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"notes_{now.strftime('%Y-%m-%d_%H%M%S')}.md"
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        f.write(f"# Meeting Notes — {now.strftime('%Y-%m-%d')}\n")
    print(f"Writing to: {filepath}")

    # Start recording
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    capture = threading.Thread(
        target=audio_capture_thread,
        args=(pa, device_index, audio_queue, stop_event),
        daemon=True,
    )
    capture.start()

    frames_per_chunk = int(SAMPLE_RATE / FRAMES_PER_BUFFER * args.chunk)
    print(f"Recording ({args.chunk}s chunks). Press Ctrl+C to stop.\n")

    # Handle Ctrl+C
    shutdown = threading.Event()

    def on_signal(sig, frame):
        print("\nStopping...")
        shutdown.set()

    signal.signal(signal.SIGINT, on_signal)

    try:
        while not shutdown.is_set():
            chunk_start = datetime.now()
            frames = []
            for _ in range(frames_per_chunk):
                if shutdown.is_set():
                    break
                try:
                    data = audio_queue.get(timeout=1.0)
                    frames.append(data)
                except queue.Empty:
                    if shutdown.is_set():
                        break

            if not frames:
                continue

            # Convert to numpy float32 array for Whisper
            raw = b"".join(frames)
            audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            timestamp = chunk_start.strftime("%H:%M")
            print(f"[{timestamp}] Transcribing {len(audio_np) / SAMPLE_RATE:.1f}s of audio...", end=" ", flush=True)

            text = transcribe_chunk(model, audio_np)

            if text and text not in ("", "you", "Thank you.", "Thanks for watching!"):
                write_segment(filepath, timestamp, text)
                # Show preview (truncated)
                preview = text[:120] + "..." if len(text) > 120 else text
                print(f"✓ {preview}")
            else:
                print("(silence)")

    finally:
        stop_event.set()
        capture.join(timeout=2)
        pa.terminate()
        print(f"\nDone. Notes saved to: {filepath}")


if __name__ == "__main__":
    main()
