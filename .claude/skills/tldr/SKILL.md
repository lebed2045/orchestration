---
name: tldr
description: Summarize the previous assistant output in a tweet-size message and offer clickable next-action buttons. Use when the user runs /tl or asks for a TLDR of the last response.
---

# tldr — tweet-size summary of the last output, with action buttons

**Updated:** `19-jun-2026`

**Charter:** The user shouldn't have to read a wall of text to decide what happens next. Compress the last output to one tweet, then hand them buttons for the real choices — or no buttons if there's genuinely nothing to choose.

## Steps

0. **Help banner.** Unless the invoking command already printed one (the `/tl` wrapper prints its own), print exactly this line first:

   `/tldr — tweet-size summary of the last assistant output, with clickable next-action buttons (/tl for short).`

1. **Pick the target text.**
   - If `$ARGUMENTS` is non-empty, treat it as the text to summarize (or a pointer to it — a file path, "the test output above", etc.).
   - Otherwise the target is the assistant's previous substantive output in this conversation — the long message the user is reacting to. Skip trivial acknowledgments to find the last message with real content.
   - If there is no prior assistant output and no arguments, say so in one line and stop.

2. **Tweet-size summary.** One message, **≤ 280 characters**, plain language. No headers, tables, bullets, or code blocks. Lead with the outcome/verdict, not the process. Anti-sycophancy applies: if the underlying output says failed / unverified / needs work, the summary says so — never soften it.

3. **Actionability triage** — exactly one of:
   - **Actionable** — the output contains an issue to fix, an improvement to make, a decision between concrete paths, or an unfinished step: call `AskUserQuestion`, using the ≤280-char summary as the question text (no separate prose message), with **2–4 options total derived from the content** (e.g. "Fix the failing import", "Apply the suggested refactor"). One of those options is always "Leave as is" — so at most 3 content actions. Labels concrete and ≤ 5 words; descriptions one line each. Never invent generic filler options just to show buttons.
   - **Not actionable** — pure acknowledgment, FYI, or something nothing can be done about: print the summary only, **no buttons**. This case should be rare; before choosing it, genuinely check whether anything could be fixed, improved, or verified.

4. **On button press: execute immediately.** No re-confirmation step. Normal repo and global rules still apply to the resulting work (Codex review, commit gates, EXECUTION_BLOCK on completion claims; `/wf` only if the user explicitly invokes it).

5. **Output discipline.** The summary itself is a read-only digest and exempt from EXECUTION_BLOCK. Any action taken after a button press follows the global rules in full.
