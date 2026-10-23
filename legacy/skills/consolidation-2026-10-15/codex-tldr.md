---
name: tldr
description: Create a tweet-size, outcome-first summary of the previous substantive assistant response or supplied text, then offer concrete next actions when useful. Use when the user invokes $tldr, writes /tldr or /tl in Codex, asks for a TLDR, or asks to shorten or summarize the last response.
---

# TLDR

Start every run with exactly:

`$tldr — tweet-size summary of the last assistant output, with next-action choices.`

## Summarize

1. Use explicit arguments as the target text. Treat a file path or a phrase such as "the test output above" as a pointer and resolve it.
2. Otherwise, summarize the previous substantive assistant response. Skip trivial acknowledgments.
3. If no target exists, say so in one line and stop.
4. Write one plain-language summary of at most 280 characters. Do not count the banner or action choices toward the limit.
5. Lead with the outcome or verdict. Preserve failures, uncertainty, blockers, and `UNVERIFIED` status without softening them.
6. Do not use a heading, table, bullet, or code block inside the summary.

## Offer next actions

Decide whether the target contains an issue to fix, an improvement to make, a concrete decision, or unfinished work.

- If it is not actionable, return only the banner and summary.
- If it is actionable and an interactive choice tool is callable in the current mode, use the summary as the question and provide two or three mutually exclusive choices. Put the best content-derived action first and mark it recommended; always include `Leave as is`. Keep labels concrete and at most five words.
- If no interactive choice tool is callable, put the summary after the banner, then offer the same two or three choices as a compact numbered list and ask the user to reply with a choice.
- Never invent filler actions merely to show choices.

When the user chooses an action, execute it immediately without reconfirmation. Follow all normal repository, safety, editing, and verification rules for that work. The summary itself is read-only and does not authorize changes.
