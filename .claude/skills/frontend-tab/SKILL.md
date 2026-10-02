---
name: frontend-tab
description: Use when adding or modifying a per-job tab (Analysis, Description, Interview Prep, Tailored CV, or a new one) in frontend/src/components/tabs and the job detail view.
---

# Add or modify a job-detail tab

1. Look at an existing tab in `frontend/src/components/tabs/` (e.g. `InterviewPrepTab.tsx`) and copy its structure:
   props `{ job: JobDetail, onUpdate: (j: JobDetail) => void }` style, loading/error state, Generate/Regenerate button.
2. Reuse primitives from `frontend/src/components/ui.tsx` and `lucide-react` icons; style with Tailwind only.
3. Register the tab where the other tabs are listed (search for `InterviewPrepTab` in `frontend/src/app/applications/`).
4. Mobile: tab strips scroll horizontally; keep tap targets ≥44px and test at 375px width.
5. Demo mode: write actions return 403. Show the API error message rather than failing silently.
6. Verify: `cd frontend && npm run lint && npx tsc --noEmit`.
