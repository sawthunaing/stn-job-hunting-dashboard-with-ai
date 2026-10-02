# Deployment

Production is one AWS EC2 `t4g.small` (ARM) running `docker-compose.prod.yml`.

## 1. Provision (once)

```bash
cd infra
# create terraform.tfvars (gitignored) with your values
terraform init && terraform apply
```

`infra/main.tf` creates the security group, key pair, instance and Elastic IP.

## 2. Configure on the instance

```bash
git clone https://github.com/sawthunaing/stn-job-hunting-dashboard-with-ai.git
cd stn-job-hunting-dashboard-with-ai
cp backend/config.example.json backend/config.json   # real secrets
cat > .env <<'ENV'
DB_PASSWORD=<strong password>
PUBLIC_API_URL=http://<elastic-ip>:8000
ENV
```

Set `cors_origin` in `config.json` to the frontend's public origin.

## 3. Deploy / update

```bash
git pull
sudo docker compose -f docker-compose.prod.yml up -d --build
sudo docker compose -f docker-compose.prod.yml logs -f api
```

`NEXT_PUBLIC_API_URL` is baked in at **build time**, so rebuild the frontend if the API URL changes.

## Backups (manual for now; B-017)

```bash
sudo docker compose -f docker-compose.prod.yml exec db pg_dump -U trajectory trajectory > backup-$(date +%F).sql
```

## Analytics

GA4 is only for the public demo stack; see `SETUP_ANALYTICS.md`.
