---
name: tldr
description: Use to write or shorten a TLDR, including the required closing summary of substantive answers.
---

# TLDR

**Updated:** `03-nov-2026`

End every substantive user-facing final answer with this visible format:

**TL;DR**

- The main result or answer.
- Another important fact, limitation or uncertainty.
- A third useful point or the concrete next action, when relevant.

Use exactly three short Markdown bullets. Adapt their content to the actual task; the examples above are not fixed labels or mandatory categories. Preserve failures and untested behavior. Do not invent facts, work or decisions to fill the summary. Keep it concise and do not label bullets Outcome/Status/Next.

The literal **TL;DR** heading is required. A concluding paragraph without that heading and three bullets does not satisfy this format. Choice buttons or a question do not replace the visible closing summary; use them separately only for a real decision.

When explicitly invoked, summarize the user's supplied text or the previous substantive answer in the same format. Resolve a file pointer before summarizing it. If no source exists, state that briefly rather than inventing a summary.

An explicit user-requested output format takes precedence. Summarizing is read-only; a proposed next action is not permission to execute it. Continue already-authorized work without another approval prompt.
