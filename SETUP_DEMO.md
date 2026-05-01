# Demo stack — operator guide

This document explains how to run a public read-only demo of the app on the
**same EC2** that runs the private app, isolated by ports and DB volume.

## Architecture

```
EC2 instance (51.24.16.185)
├── Private stack (existing, daily use)
│   ├── frontend  port 3000   (docker-compose.prod.yml)
│   ├── api       port 8000
│   └── db        volume: pgdata
│
└── Demo stack (NEW, public-facing)
    ├── frontend  port 3001   (docker-compose.demo.yml)
    ├── api       port 8001
    └── db        volume: pgdata_demo
```

Both stacks run from the same code on disk. Differences:

| Aspect | Private | Demo |
|---|---|---|
| Compose file | `docker-compose.prod.yml` | `docker-compose.demo.yml` |
| Project name | `trajectory` (default) | `trajectory-demo` |
| Backend config | `backend/config.json` | `backend/config.demo.json` |
| Postgres volume | `pgdata` | `pgdata_demo` |
| Demo mode flag | `false` | **`true`** — enforces read-only |
| Public URL | `http://51.24.16.185:3000` | `http://51.24.16.185:3001` |

---

## One-time setup

### 1. Open ports 3001 and 8001 in AWS Security Group

AWS Console → EC2 → Security Groups → select the SG attached to your EC2 → Edit inbound rules. Add two rules:

| Type | Port | Source |
|---|---|---|
| Custom TCP | 3001 | 0.0.0.0/0 (Anywhere-IPv4) |
| Custom TCP | 8001 | 0.0.0.0/0 (Anywhere-IPv4) |

Description: "Demo frontend" / "Demo API". Save.

### 2. Create the demo config files on EC2

SSH into your EC2:

```bash
ssh ec2-user@51.24.16.185
cd ~/trajectory
```

Create `backend/config.demo.json` from the example:

```bash
cp backend/config.demo.example.json backend/config.demo.json
nano backend/config.demo.json
```

Fill in:
- `openai_api_key`: your real key (used ONLY during seeding; demo mode blocks runtime AI)
- `admin_username` and `admin_password`: anything random (unused in demo, but must be set)
- `jwt_secret`: a different long random string (generate with `openssl rand -hex 32`)
- `cors_origin`: `http://51.24.16.185:3001`
- `demo_mode`: must stay `true`

Create `.env.demo`:

```bash
cp .env.demo.example .env.demo
nano .env.demo
```

Fill in:
- `DEMO_DB_PASSWORD`: a strong random password (use `openssl rand -base64 24`)
- `DEMO_PUBLIC_API_URL`: `http://51.24.16.185:8001`

Both files are gitignored — never get committed.

### 3. Build and start the demo stack

```bash
sudo COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 \
  docker compose -p trajectory-demo \
  -f docker-compose.demo.yml \
  --env-file .env.demo \
  up -d --build
```

First build takes ~5-10 min (frontend `npm run build` on t4g.small is slow).

If the frontend build OOM-kills (exit code 137), see "Memory troubleshooting" below.

### 4. Verify both stacks are running

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

You should see 6 containers:
- `trajectory-frontend-1` (or similar) on 3000
- `trajectory-api-1` on 8000
- `trajectory-db-1` (no published port)
- `trajectory-demo-frontend` on 3001
- `trajectory-demo-api` on 8001
- `trajectory-demo-db` (no published port)

Health checks:

```bash
curl http://localhost:8000/health           # private
curl http://localhost:8001/health           # demo
curl http://localhost:8001/demo-info        # should return {"demo_mode":true}
```

### 5. Seed the demo DB

This populates curated jobs + pre-runs AI analyses. ~3 minutes, costs ~$2 of OpenAI.

```bash
sudo docker compose -p trajectory-demo \
  -f docker-compose.demo.yml \
  exec api python -m app.scripts.seed_demo
```

Watch the output:
```
[seed] Initialising DB schema...
[seed] Wiping existing data...
[seed] Inserting profile...
[seed] [1/6] Acme Corp - Senior Backend Engineer (.NET / FinTech)
  ├─ Running suitability analysis...
  │  └─ Score: 91/100
  ├─ Generating interview prep...
  │  └─ Done.
  └─ Generating tailored CV...
     └─ ATS match: 84%
... (5 more jobs)
[seed] Done!
[seed]   Jobs in DB: 6
[seed]   With AI scores: 6
```

### 6. Verify in browser

Open `http://51.24.16.185:3001` from your laptop or phone.

You should see:
- Demo banner at top: "Public demo · read-only · AI analyses pre-computed"
- Pipeline funnel populated with the 6 seed jobs
- Top opportunities shows the high-scoring ones
- No "+ Add", "Edit", "Delete" buttons anywhere
- Login is bypassed — direct landing on the dashboard

---

## Day-to-day operations

### Stopping just the demo stack

```bash
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml down
```

(Doesn't affect the private stack on 3000/8000.)

### Stopping just the private stack

```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env down
```

### Starting both stacks

```bash
# Private
sudo docker compose -f docker-compose.prod.yml --env-file .env up -d

# Demo
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml --env-file .env.demo up -d
```

### Re-seeding the demo (e.g. after prompt changes)

```bash
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml \
  exec api python -m app.scripts.seed_demo
```

This wipes and re-runs from scratch. Costs ~$2 again.

### Updating demo with new code

```bash
cd ~/trajectory
git pull

# Rebuild + restart demo (private unchanged)
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml \
  --env-file .env.demo up -d --build

# Re-seed if prompt or model changed
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml \
  exec api python -m app.scripts.seed_demo
```

### Logs

```bash
# Demo stack
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml logs -f

# Or just one service
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml logs -f api
```

---

## Memory troubleshooting

t4g.small has 2 GB RAM. With both stacks running, memory is tight:

| Container | RAM at idle |
|---|---|
| Each frontend | ~150 MB |
| Each api | ~100 MB |
| Each db | ~50 MB |
| **6 containers total** | **~900 MB** |
| OS + buffers | **~600 MB** |
| Headroom | **~500 MB** |

If `npm run build` exit-codes 137 during demo build:

**Option 1: Stop private stack temporarily during build**

```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env down
# Now build demo (with full 2GB available)
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml --env-file .env.demo up -d --build
# Restart private once demo is built
sudo docker compose -f docker-compose.prod.yml --env-file .env up -d
```

**Option 2: Add swap to the EC2** (one-time, persistent)

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

Adds 2 GB swap. Slow during compilation but won't OOM-kill.

---

## Costs

| Item | Cost |
|---|---|
| Existing EC2 ($AWS credits cover) | ~$15/month |
| Extra Elastic IP | $0 (already attached) |
| Demo DB data (~50 MB on existing volume) | $0 |
| OpenAI seeding | ~$2-3 once |
| OpenAI ongoing | $0 (demo mode blocks AI) |
| **Recurring extra cost** | **$0** |

---

## Sharing the demo

URL to share: `http://51.24.16.185:3001`

Heads-up: it's HTTP not HTTPS. Recruiters will see a "Not Secure" warning in the browser bar. Most won't care, but if you want HTTPS, that's the next phase (Cloudflare Tunnel + custom domain).

For now, you can paste the URL directly into LinkedIn featured / job applications / cover letters.

---

## Tearing down the demo

If you ever want to remove it completely:

```bash
sudo docker compose -p trajectory-demo -f docker-compose.demo.yml down -v
```

The `-v` flag removes the `pgdata_demo` volume too (deletes all demo data). Private stack is untouched.

To remove from AWS, also close the security group rules for ports 3001/8001.
