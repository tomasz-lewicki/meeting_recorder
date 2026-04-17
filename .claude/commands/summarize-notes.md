Your job is to process all raw meeting transcript files in `~/.meetings/todo/` and produce two artifacts per meeting:

1. **Cleaned Transcript** — a readable, speaker-attributed version of the raw transcript
2. **Executive Summary** — a concise summary of the meeting

Both should be saved to a per-meeting folder under: `~/projects/wiki/meeting notes/`

## Input

Scan `~/.meetings/todo/` for all `.md` files. Read each one in full before processing. If the folder is empty or doesn't exist, tell the user there are no transcripts to process.

Process each transcript file through Steps 1–4 below, then move it to `~/.meetings/done/` (create the directory if needed).

## Step 1: Identify Speakers and Title

- Examine the transcript for speaker names, contextual clues (e.g., "I'm Brandon"), and conversational patterns (who asks vs. who explains, topic ownership, etc.)
- If the transcript has stereo channel markers or other speaker indicators, use those directly.
- If speaker identity is ambiguous, make your best inference from context and flag any uncertain attributions when presenting the result.
- Use short speaker labels like first-name initial + colon (e.g., `B:`, `T:`). List the full mapping at the top (e.g., **Participants:** Brandon (B), Tomasz (T)).
- Derive a short descriptive meeting title from the transcript content (e.g., "Sprint Planning", "Auth Migration Design Review"). This title will be used in folder names and document headings.

## Step 2: Clean Transcript

Create a file called `transcript_clean.md` with:
- A title line: `# <Meeting Title> — YYYY-MM-DD (Cleaned Transcript)`
- A **Participants** line mapping initials to full names
- The conversation split into speaker turns with `INITIAL:` prefixes
- Timestamps preserved as `## HH:MM` section headers where present in the original
- Filler words, false starts, and repetitions cleaned up for readability
- Meaning and intent preserved faithfully — do not paraphrase or editorialize
- Natural sentence structure and punctuation restored

## Step 3: Executive Summary

Create a file called `executive_summary.md` with:
- `# Executive Summary — <Meeting Title> — YYYY-MM-DD`
- **Participants** and **Topic** fields
- **Overview**: 1-2 sentence description of what the meeting was about
- **Key Discussion Points**: bulleted list of the substantive topics covered, with enough detail to be useful without reading the full transcript
- **Action Items**: any commitments, next steps, or follow-ups mentioned (attribute to a person where possible). If none were discussed, omit this section.

## Step 4: Save to Wiki and Move Source

- Create a per-meeting folder at:
  `~/projects/wiki/meeting notes/YYYY-MM-DD <Meeting Title> (<Participant Names>)/`
- Place both `executive_summary.md` and `transcript_clean.md` in that folder.
- Move the original raw transcript file from `~/.meetings/todo/` to `~/.meetings/done/` (create `~/.meetings/done/` if it doesn't exist).

## Notes

- Prefer accuracy over polish. If something is unclear in the raw transcript, keep it close to the original rather than guessing.
- Do not invent dialogue or add information not present in the transcript.
- After processing all files, show the user a summary: how many transcripts were processed, the folder structure created for each, and any speaker attributions you're uncertain about.
