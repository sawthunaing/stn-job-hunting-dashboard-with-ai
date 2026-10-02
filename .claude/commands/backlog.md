---
description: View, add to, or triage BACKLOG.md
argument-hint: [add "<idea>" | triage | next]
---

Work with `BACKLOG.md` at the repo root. Arguments: `$ARGUMENTS`

- **No arguments**: summarise the Now / Next sections as a short table (ID, priority, size, title).
- **`add "<idea>"`**: append a new item to **Inbox** using the next free `B-###` ID.
  Briefly inspect the codebase so the item names the real files involved. Give it a priority and size guess.
- **`triage`**: for each Inbox item, verify it against the code, assign priority and size, and move it
  into Now / Next / Later. Flag duplicates. Show the proposed moves before writing.
- **`next`**: recommend the single best item to do next (highest priority, smallest size, no blockers)
  and explain why in 2–3 sentences.

Keep the existing format exactly. Do not delete items; move finished ones to **Done**.
