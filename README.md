<div align="center">

# Job Hunting AI

### AI-powered job application platform that scores fit, tailors your CV, and preps you for interviews — automatically.

[![Tech](https://img.shields.io/badge/Stack-Next.js_·_FastAPI_·_Postgres_·_Claude-2ea44f?style=for-the-badge)](#tech-stack)
[![Cloud](https://img.shields.io/badge/Cloud-AWS_EC2_(ARM)-orange?style=for-the-badge)](#architecture)

![Dashboard hero](docs/images/hero-dashboard.png)

</div>

---

## The problem

Every job application takes 2–3 hours: research the company, tailor your CV, prep for interviews, write a cover letter. Repeat 30 times during a job hunt and that's 90 hours of work — most of it lost the moment you submit.

**Job Hunting AI compresses each application from hours to minutes.**

---

## What it does

- **Paste a job URL** — the AI extracts company, role, location, salary range, requirements
- **Get instant fit analysis** — 0–100 suitability score with reasoning, matched/missing skills, red flags
- **Auto-generate tailored CV** — emphasizes the experience relevant to *this specific job*, not a generic resume blast
- **Pre-built interview prep** — likely questions, suggested answers, talking points, salary negotiation tips
- **Track your pipeline** — visual funnel from New → Applied → Interviewing → Offer with conversion rates
- **Score-based prioritization** — filter your pipeline by AI fit score so you focus on the highest-probability roles

---

## Screenshots

<table>
<tr>
<td width="50%">

**Pipeline overview**
![Overview](docs/images/screenshot-overview.png)
Funnel chart, top opportunities, recent activity, follow-up reminders.

</td>
<td width="50%">

**AI fit analysis**
![AI Analysis](docs/images/screenshot-analysis.png)
Live 0–100 scoring with matched skills, gaps, and reasoning.

</td>
</tr>
<tr>
<td width="50%">

**Tailored CV per job**
![Tailored CV](docs/images/screenshot-tailored-cv.png)
AI rewrites your CV emphasizing the most relevant experience for the target role.

</td>
<td width="50%">

**Mobile-first design**
![Mobile View](docs/images/screenshot-mobile.png)
Full-featured dashboard on iPhone with drawer navigation and full-screen modals.

</td>
</tr>
</table>

---

## Tech stack

<table>
<tr>
<td><b>Frontend</b></td>
<td>Next.js 14 (App Router) · TypeScript · Tailwind CSS · Lucide icons</td>
</tr>
<tr>
<td><b>Backend</b></td>
<td>FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Python 3.12</td>
</tr>
<tr>
<td><b>Database</b></td>
<td>PostgreSQL 16 (containerised, self-hosted)</td>
</tr>
<tr>
<td><b>AI</b></td>
<td>Anthropic Claude (Sonnet 4.6 by default; Haiku 4.5 / Opus configurable) via the official <code>anthropic</code> Python SDK</td>
</tr>
<tr>
<td><b>Auth</b></td>
<td>JWT (HS256) — custom implementation, no external auth provider</td>
</tr>
<tr>
<td><b>Infrastructure</b></td>
<td>Docker · Docker Compose · AWS EC2 (ARM Graviton t4g.small) · Terraform</td>
</tr>
<tr>
<td><b>CI/CD</b></td>
<td>Manual <code>git push</code> + <code>docker compose up --build</code> on EC2 (intentional simplicity for solo project)</td>
</tr>
</table>

---

## Architecture

![Architecture diagram](docs/images/architecture.png)

### Why this design

**Single ARM EC2 instance, all services in Docker on the same host.**

| Decision | Rationale |
|---|---|
| ARM Graviton (`t4g.small`) | ~40% cheaper than x86 equivalent, plenty of headroom for personal use |
| Postgres in Docker (not RDS) | RDS adds £15/month; Docker Postgres + automated backups gives 90% of the value at 5% of the cost |
| No load balancer / no auto-scaling | Single user, single region. Adding LBs is premature optimisation |
| Manual deploys via `git pull` | One developer, one server. CI/CD pipeline complexity not justified |
| Custom JWT auth (not Cognito/Auth0) | One user, one password. External auth providers are overkill |
| Cost target: ~$15/month | Personal project economics; would scale to ~$50/month for 50 users |

### AI integration deep-dive

All AI calls live in a single module (`backend/app/ai.py`) and go through one helper, `_call_json`, which sends a task-specific system prompt to Claude and parses a JSON object back. Each feature (extraction, fit analysis, interview prep, company research, CV / cover letter / email tailoring) is just a prompt plus a token budget:

```python
def _call_json(system: str, user: str, max_output_tokens: int = 4096) -> dict:
    resp = client().messages.create(
        model=settings.anthropic_model,
        max_tokens=max_output_tokens,
        system=system + "\n\nRespond with ONLY a single valid JSON object.",
        messages=[{"role": "user", "content": user}],
    )
    return json.loads(_strip_fences("".join(b.text for b in resp.content)))
```

The model is a single config value (`anthropic_model`), so swapping models for cost or quality is a one-line change with no code modifications:

| Model | Good for |
|---|---|
| `claude-haiku-4-5-20251001` | Cheapest and fastest; sufficient for URL extraction |
| `claude-sonnet-4-6` | Default; best balance of quality and cost for analysis and tailoring |
| `claude-opus-4-7` | Highest quality; most expensive |

Check [Anthropic's pricing page](https://www.anthropic.com/pricing) for current per-token rates. Since each analysis is a single short request, personal-use cost is typically small; the production table below suggests per-user spend caps for a multi-tenant deployment.

---

## Key features

### 🎯 AI-powered URL extraction

Paste a job listing URL from LinkedIn, Indeed, Otta, Workday, or any company careers page. The backend fetches the page (public hosts only, SSRF-guarded), sanitises the HTML, and feeds it to Claude for structured extraction. Indeed links are imported by job id with duplicate detection; if Indeed blocks the server, paste the posting text from your browser instead:

- Company name, role title, location, work type (remote/hybrid/onsite)
- Salary range with currency normalisation
- Required vs preferred skills
- Application URL
- Platform identification

### ✨ Suitability scoring

For each job, the AI compares the JD against your saved profile (CV, skills, salary expectations, deal-breakers) and outputs:

- **0–100 score** with category-band visualisation
- **Matched skills** — what the JD asks for that you have
- **Skill gaps** — what's required that you lack
- **Reasoning** — paragraph explanation of the fit
- **Salary alignment** — flag if the offered range conflicts with your target

### 📊 Pipeline overview with conversion rates

Visual funnel showing your application flow:

```
New           ████████ 8
Applied       ██████ 7      → 88% conversion
Interviewing  ████ 3        → 43% conversion
Offer         █ 1           → 33% conversion
```

Click any stage to filter the application list. Identify where you're losing applications.

### 🔍 Score-based filtering with histogram

Score histogram in the sidebar showing distribution of all applications by AI fit score. Slider to filter by minimum score (e.g., "show me only 75+ matches"). Tap any colored band to jump-filter.

### 📱 Mobile-first responsive design

Full feature parity on mobile:
- Hamburger drawer sidebar (slides in from left, backdrop overlay)
- Full-screen modal sheets for job entry on mobile
- Horizontally-scrollable tab strips
- Sticky bottom action zones thumb-friendly tap targets (44px+ per Apple HIG)
- iOS-aware viewport handling (`dvh` units to handle Safari URL bar showing/hiding)

---

## What I'd change for production

This was built for personal use. To productise it for multi-tenancy, the changes I'd make:

| Layer | Current | Production |
|---|---|---|
| **Auth** | Single hardcoded user | OAuth 2.0 (Google/LinkedIn sign-in), per-user data isolation |
| **DB** | Single Postgres in Docker | Managed Postgres (Aurora Serverless v2) with point-in-time restore |
| **AI rate limiting** | None | Per-user token budgets + Redis-based sliding-window rate limit |
| **Cost protection** | Anthropic spend limit | Per-user spend caps + cached responses for identical inputs |
| **Compute** | Single EC2 | ECS Fargate with auto-scaling on a load balancer |
| **CDN** | None | CloudFront in front of frontend, static asset caching |
| **Observability** | `docker logs` | Sentry for errors, CloudWatch for metrics, structured logging |
| **CI/CD** | Manual SSH | GitHub Actions → ECR → ECS deploy automation |
| **Backups** | Manual SQL dumps | Automated nightly to S3 with 30-day retention |

The current cost (~$15/month) would scale roughly linearly with users until ~500, where the architecture would need to shift to ECS for proper isolation.

---

## How to run it locally

### Prerequisites
- Docker Desktop
- An Anthropic API key (https://console.anthropic.com)

### Setup

```bash
git clone https://github.com/sawthunaing/stn-job-hunting-dashboard-with-ai.git
cd stn-job-hunting-dashboard-with-ai

# Configure
cp backend/config.example.json backend/config.json
# Edit backend/config.json - add your Anthropic key, set admin_username and admin_password

# Run
docker compose up -d --build
```

Open http://localhost:3000. Log in with the credentials you set in `config.json`.

### Run with HTTPS (local Docker Desktop)

A Caddy reverse proxy terminates TLS in front of the app, so the login password and JWT never travel over plain HTTP:

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d --build
```

Open **https://localhost**. Caddy signs the certificate with its own local CA, so the browser warns on first visit. Either accept the warning, or trust the CA:

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml cp caddy:/data/caddy/pki/authorities/local/root.crt ./caddy-local-root.crt
```

In this mode the frontend is served at `/` and the API at `/api` on the same origin, and the app containers no longer publish ports 3000/8000. For a real domain on EC2, set `SITE_ADDRESS` and `PUBLIC_API_URL` and layer it on `docker-compose.prod.yml` (see the comments in `docker-compose.https.yml`); Caddy then fetches a Let's Encrypt certificate automatically. Also open ports 80/443 and close 3000/8000 in the security group.

**Login rate limiting:** after 5 failed logins from one IP within 15 minutes the API returns `429` with a `Retry-After` header (a global cap also throttles guessing spread across many IPs). Tune with `login_max_attempts` and `login_window_seconds` in `config.json`. Limits are kept in memory, so they reset when the API container restarts.

### First-time setup

1. Visit `/profile` and fill in your CV details (this is what the AI uses for tailoring)
2. Click **+ Add** in the sidebar
3. Paste any job URL — the AI extracts everything
4. Click **AI Re-analyze** on the job to compute fit score

### Running the tests

No Postgres, API key or network needed: the backend tests use a throwaway SQLite database and a fake Claude client, and the frontend tests mock `fetch`.

```bash
# Backend (pytest)
cd backend
pip install -r requirements-dev.txt
pytest                      # everything
pytest tests/unit           # pure functions: auth/JWT, config, AI prompt building, scraper, CV export
pytest tests/integration    # real FastAPI app + DB over HTTP: auth, profile, jobs, AI endpoints

# Frontend (Vitest + React Testing Library)
cd frontend
npm install
npm test                    # everything
npm run test:unit           # API client, UI helpers
npm run test:integration    # login page, AuthGuard, add-from-URL modal wired to the real API client
```

---

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic request/response shapes
│   │   ├── ai.py            # Claude (Anthropic) integration
│   │   ├── scraper.py       # SSRF-guarded fetch + BeautifulSoup text extraction
│   │   ├── indeed.py        # Indeed URL parsing / job-id import helpers
│   │   ├── auth.py          # JWT issuance and verification
│   │   └── db.py            # SQLAlchemy session + lightweight migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx              # Pipeline overview (home)
│       │   ├── applications/         # Job list + detail
│       │   ├── profile/              # User profile editor
│       │   └── login/                # JWT login
│       ├── components/
│       │   ├── Sidebar.tsx           # Mobile drawer + AI score filter
│       │   ├── tabs/                 # Per-job AI feature tabs
│       │   └── ...
│       └── lib/
│           └── api.ts                # Typed API client
├── infra/
│   ├── main.tf                       # EC2 + security groups (Terraform)
│   └── README.md                     # Deploy instructions
└── docker-compose.yml                # Local dev (hot reload)
└── docker-compose.prod.yml           # EC2 production
```

---

## About the author

Built by **Saw Thu Naing** — Senior Software Engineer specialising in C# / .NET, distributed systems, and FinTech infrastructure.

10+ years building secure, high-scale systems across payment platforms (VISA, Mastercard, Alipay, WeChat), digital wallets, banking integrations, and live streaming. Currently based in London, UK.

- 🌐 LinkedIn: [linkedin.com/in/saw-thu-naing](https://www.linkedin.com/in/saw-thu-naing/)
- 🐙 GitHub: [github.com/sawthunaing](https://github.com/sawthunaing)
- 🏆 HackerRank: [hackerrank.com/profile/sawthunaing](https://www.hackerrank.com/profile/sawthunaing)
- ✉️ Email: sawthunaing@gmail.com

**Certifications:**
- Google Professional Cloud Architect
- AWS Certified Solutions Architect — Associate

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

If you found this useful, ⭐ the repo or [reach out](https://www.linkedin.com/in/saw-thu-naing/) — always open to interesting engineering conversations.

</div>
