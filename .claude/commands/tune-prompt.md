---
description: Safely iterate on one of the Claude system prompts in ai.py
argument-hint: <analysis|prep|research|tailor|extract> [goal]
---

Improve the `$ARGUMENTS` prompt in `backend/app/ai.py`
(`ANALYSIS_SYSTEM`, `PREP_SYSTEM`, `RESEARCH_SYSTEM`, `TAILOR_SYSTEM`, `EXTRACT_SYSTEM`).

1. Read the prompt, its function, and how the frontend renders the result (`frontend/src/components/tabs/`).
2. Write down the current output JSON contract. **It must not change** unless the user asks;
   if it does change, update the TS types and the tab in the same change.
3. Propose the edit as a diff with the reasoning. Keep the privacy rules (private profile notes never in tailored docs).
4. If `docs/specs/` has eval cases for this prompt, walk through them against the new version.
5. Record the change and its rationale in `docs/ai.md` under "Prompt changelog".
