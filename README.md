# Ko Saw's Job Hunting Dashboard

A personal AI-assisted job hunt dashboard. Paste in a job posting URL,
ChatGPT scrapes it, scores how well you fit, generates tailored interview prep,
and drafts a tailored CV / cover letter / recruiter email — all per job.

```
trajectory/
├── backend/    FastAPI + PostgreSQL + OpenAI
├── frontend/   Next.js 14 + Tailwind dashboard
└── infra/      Terraform for AWS (EC2 + RDS)
```

## What it does

1. **Add jobs by URL or manually.** ChatGPT extracts company / role / salary / description from the page.
2. **Suitability scoring.** Compares your `profile.md` to the JD and returns 0–100, plus per-skill strengths and gaps.
3. **Market salary intel.** ChatGPT estimates p25/p50/p75 for the role+location and proposes floor/target/ceiling negotiation numbers.
4. **Company research.** Auto-generated culture / market position / recent news / interview talking points.
5. **Contextual interview prep.** Technical and behavioral questions tailored to *this* JD and *your* CV — with a "why this is likely" rationale.
6. **One-click tailoring.** Generates a tailored CV, cover letter, or recruiter email per job, with ATS keyword match scoring.
7. **Pipeline tracking.** Status, notes, star, search, filter — all the basics of a job tracker.

## Prerequisites

- Python 3.12+ (only if running backend without Docker)
- Node 20+
- Docker Desktop
- OpenAI API key — https://platform.openai.com/api-keys
  - **Important:** ChatGPT Plus and the OpenAI API are billed separately. Add credits at platform.openai.com → Billing.
- AWS account + Terraform 1.6+ (for deployment only)

## Local development

### 1. Backend

```bash
cd backend
cp .env.example .env
cp profile.example.md profile.md   # edit profile.md with your real CV
# Edit .env: set OPENAI_API_KEY and a fresh API_KEY (any random string)

docker compose up -d
curl http://localhost:8000/health
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_KEY to match the backend's API_KEY

npm run dev
```

Open http://localhost:3000. Click **+ Add** and paste a job URL.

> **Tip:** Greenhouse, Lever, Ashby, and direct company career pages scrape reliably. LinkedIn often blocks scrapers — use "Enter manually instead" for those.

## Cost estimate

Per fully-analyzed job with `gpt-4o-mini` (the default):

| Action | Approx cost |
|---|---|
| Scrape + extract | $0.001 |
| Full analysis | $0.005 |
| Interview prep | $0.005 |
| Company research | $0.002 |
| Tailored doc (each) | $0.004 |
| **Per job, fully analyzed** | **~$0.02** |

So $5 of OpenAI credit gets you ~250 jobs. Bump to `gpt-4o` (set `OPENAI_MODEL=gpt-4o` in `.env`) for higher quality at ~10x cost.

## Deploying to AWS

### 1. Provision infrastructure

```bash
cd infra
terraform init

terraform apply \
  -var="my_ip=$(curl -s ifconfig.me)/32" \
  -var="db_password=$(openssl rand -base64 24 | tr -d '=+/')" \
  -var="api_key=$(openssl rand -base64 32 | tr -d '=+/')" \
  -var="openai_api_key=sk-proj-..." \
  -var="ssh_public_key=$(cat ~/.ssh/id_ed25519.pub)"
```

Save the outputs — you'll need `api_url` for Amplify.

> Windows PowerShell equivalent:
> ```powershell
> $myIp = (Invoke-WebRequest ifconfig.me).Content + "/32"
> $dbPass = [Convert]::ToBase64String((1..24 | ForEach-Object { Get-Random -Maximum 256 })) -replace '[+/=]',''
> $apiKey = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 })) -replace '[+/=]',''
> $sshKey = Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
> terraform apply -var="my_ip=$myIp" -var="db_password=$dbPass" -var="api_key=$apiKey" -var="openai_api_key=sk-proj-..." -var="ssh_public_key=$sshKey"
> ```

### 2. Deploy the backend container

```bash
scp -r backend/ ec2-user@<api_ip>:~/trajectory
ssh ec2-user@<api_ip>

cd trajectory/backend
sudo docker build -t trajectory-api .
sudo docker run -d --name api --restart=always \
  --env-file /etc/trajectory/api.env \
  -v /etc/trajectory/profile.md:/app/profile.md:ro \
  -p 8000:8000 \
  trajectory-api

exit
scp backend/profile.md ec2-user@<api_ip>:/tmp/
ssh ec2-user@<api_ip> "sudo mv /tmp/profile.md /etc/trajectory/profile.md && sudo docker restart api"
```

Verify: `curl http://<api_ip>:8000/health`

### 3. Deploy the frontend on Amplify

1. Push the repo to GitHub (private).
2. AWS Console → Amplify → Host web app → connect your GitHub repo.
3. Choose `frontend/` as the app root.
4. Environment variables:
   - `NEXT_PUBLIC_API_URL` = the EC2 URL (e.g. `http://1.2.3.4:8000`)
   - `NEXT_PUBLIC_API_KEY` = the API key from step 1
5. Deploy.

## AWS cost estimate

| Service | Monthly |
|---|---|
| EC2 t4g.small | ~$12 |
| RDS db.t4g.micro | ~$13 (free tier first 12 months) |
| EBS storage | ~$3 |
| Amplify | $0 for personal use under free tier |
| OpenAI API | usage-based — typically $1-5/month |
| **Total infra** | **~$28/mo** (~$15 after free tier) |

## Troubleshooting

- **"401 invalid api key"** → `NEXT_PUBLIC_API_KEY` doesn't match `API_KEY` in backend `.env`.
- **"insufficient_quota" from OpenAI** → Add credits at platform.openai.com → Billing.
- **"fetch failed" when scraping** → LinkedIn blocked it. Use Greenhouse/Lever or "Enter manually instead."
- **Frontend env changes not taking effect** → Stop dev server, delete `.next/`, run `npm run dev`.
- **CORS errors after deploying** → Set `CORS_ORIGIN` in backend env to your Amplify URL (or `*` for personal use).
