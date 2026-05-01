# Screenshot capture guide

You need 5 screenshots. Here's the exact recipe for each one.

Save all to: `docs/images/` in your repo, with these EXACT filenames:

1. `hero-dashboard.png`
2. `screenshot-overview.png`
3. `screenshot-analysis.png`
4. `screenshot-tailored-cv.png`
5. `screenshot-mobile.png`

You can also add later: `architecture.png` (the diagram).

---

## How to take screenshots on Windows

**Windows 10/11 built-in tool:**
1. Press **Win + Shift + S**
2. Click "Rectangular Snip"
3. Drag to select area
4. Click the notification at bottom-right to open in Snip & Sketch
5. Click Save (disk icon) → save as PNG

**For mobile-view screenshots** (without an actual phone):
1. Open Chrome at `http://localhost:3000` (or `http://51.24.16.185:3000`)
2. Press **F12** to open DevTools
3. Press **Ctrl+Shift+M** to toggle device toolbar
4. From the dropdown at top, pick **iPhone 14 Pro Max**
5. The page now displays at iPhone resolution
6. Take a screenshot of just the phone-shaped area

---

## Screenshot 1: hero-dashboard.png

**The most important one — this is the first thing visitors see.**

Configuration:
- Browser window: maximized to your full screen
- URL: `http://localhost:3000` (the new Overview page)
- Logged in
- At least 8-10 jobs in the system, with 4-6 of them analysed (have AI scores)

Capture area: **The entire visible page**, top to bottom. Header included. Aim for ~1600x1000 or similar.

Composition checklist:
- [ ] Pipeline funnel showing 3-4 different statuses with bars
- [ ] Stats cards visible at top
- [ ] Top opportunities section showing 2-3 jobs
- [ ] Either "Recent activity" or "Needs follow-up" visible
- [ ] No real personally identifiable companies on screen — if your real apps show "Goldman Sachs" and you don't want that public, censor or seed fake data first

If your data is sparse or shows real companies you'd rather hide, do this first:
1. Add 5-6 fake jobs (Acme Corp, Globex, Initech, Stark Industries, Wayne Enterprises, Wonka Industries)
2. Run AI Re-analyze on each to populate scores
3. Cycle some through different statuses (New, Applied, Interviewing)
4. Take the screenshot

---

## Screenshot 2: screenshot-overview.png

Same view as hero, but **closer crop** showing just the funnel + conversion rates.

Capture area: Just the "Pipeline" section card. Should look like a rectangle ~800x500.

This emphasizes the visual nature of the funnel.

---

## Screenshot 3: screenshot-analysis.png

A job's AI analysis tab.

Configuration:
- Click any job that has been AI-analyzed
- Click the **"Analysis"** tab
- Make sure the right pane shows the analysis (not generating)

Capture area: The job detail pane (right side). Aim for ~1000x800.

Composition checklist:
- [ ] Suitability score visible (the big number)
- [ ] Matched skills section
- [ ] Skill gaps section
- [ ] Reasoning paragraph

---

## Screenshot 4: screenshot-tailored-cv.png

The Tailored CV tab.

Configuration:
- Pick a job where you've clicked "Generate" on the Tailored CV tab
- Click the **"Tailored CV"** tab

Capture area: The job detail pane. ~1000x800.

Composition checklist:
- [ ] ATS Match percentage visible
- [ ] Keywords matched / missing visible
- [ ] First few lines of the tailored CV markdown content

---

## Screenshot 5: screenshot-mobile.png

The mobile view, ideally with the sidebar drawer open.

Configuration:
1. F12 → Ctrl+Shift+M → iPhone 14 Pro Max preset
2. Click the hamburger ☰ button → sidebar slides in
3. Make sure the AI score histogram is visible in the open sidebar

Capture area: ONLY the phone-shaped area, NOT the surrounding gray. ~430x900.

Composition checklist:
- [ ] Sidebar drawer visible from left
- [ ] Score histogram colored bars visible
- [ ] At least 2-3 jobs in the list
- [ ] Status filter pills visible

---

## Optional: architecture diagram (architecture.png)

If you have time, draw this in **excalidraw.com** (no signup):

```
                    [Internet]
                        ↓
            (port 3000 or HTTPS)
                        ↓
            ┌───────────────────┐
            │  AWS EC2 t4g.small│
            │  (ARM, eu-west-2) │
            │                   │
            │  ┌─────────────┐  │
            │  │  Frontend   │  │
            │  │  Next.js 14 │  │
            │  │  (port 3000)│  │
            │  └──────┬──────┘  │
            │         │ /api/*  │
            │  ┌──────▼──────┐  │
            │  │  Backend    │  │
            │  │  FastAPI    │  │
            │  │  (port 8000)│  │
            │  └──┬───────┬──┘  │
            │     │       │     │
            │  ┌──▼──┐ ┌─▼────┐ │
            │  │  DB │ │OpenAI│ │
            │  │ Pg16│ │  API │ │
            │  └─────┘ └──────┘ │
            └───────────────────┘
```

Or skip this — the README will still look fine without it.

---

## After capturing

Save all 5 PNGs to `docs/images/` in your repo:

```powershell
cd E:\stn_working\AI\trajectory
mkdir docs\images -Force

# Move screenshots from Downloads folder
move C:\Users\PC\Downloads\hero-dashboard.png docs\images\
move C:\Users\PC\Downloads\screenshot-overview.png docs\images\
move C:\Users\PC\Downloads\screenshot-analysis.png docs\images\
move C:\Users\PC\Downloads\screenshot-tailored-cv.png docs\images\
move C:\Users\PC\Downloads\screenshot-mobile.png docs\images\
```

Then verify:
```powershell
Get-ChildItem docs\images\
```

Should show all 5 files.

---

## Sizing tips

- **Hero screenshot:** Wider is better. ~1600 px wide ideal.
- **Other screenshots:** ~800-1000 px wide. Don't go larger — they'll be displayed in a 2-col grid.
- **Mobile:** Tall and narrow. ~430x900 ideal.

If a screenshot is too big (over 500 KB), it slows page load. Resize/compress at https://tinypng.com (free, no signup).

---

## What NOT to capture

- Login page (boring)
- Empty state with no jobs
- Loading spinner
- Error state

These don't sell the product.

---

Once all 5 screenshots are in `docs/images/`, the README will render with proper visuals. You can preview by opening the README on GitHub after pushing.
