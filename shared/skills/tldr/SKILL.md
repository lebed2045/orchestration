---
name: tldr
description: Use when the user asks for a TLDR, invokes tldr or tl, or asks to shorten the previous answer.
---

# TLDR

**Updated:** `16-oct-2026`

Summarize the user's supplied text or the previous substantive assistant answer. Resolve a file pointer before summarizing it. If neither exists, state that briefly.

1. **Tweet.** One line, at most 280 characters, plain language, outcome first. No labels, headers, bullets or code. Failed, unverified or incomplete work says so; never soften it.
2. Then exactly one of:
   - **Choices** — the work leaves a real decision or a concrete unfinished step: offer up to three concrete options (labels of at most five words, one-line descriptions). Where the interface has a choice tool (Claude: `AskUserQuestion`), use the tweet as the question text instead of printing it separately, and add "Leave as is". Elsewhere, print the options as a numbered list under the tweet.
   - **Key points** — nothing to decide: up to three short bullets, each a distinct fact the tweet did not already say (a number, a path, a caveat). Fewer facts, fewer bullets.

Never use fixed labels such as Outcome/Status/Next, and never write filler ("none", "no blockers", "nothing to do"). Never invent options just to show choices. An explicit user request for another format takes precedence.

The summary is read-only. A proposed choice is not permission; a chosen option is, and runs without another confirmation. Continue already-authorized work without an approval prompt. No mandatory banner.
