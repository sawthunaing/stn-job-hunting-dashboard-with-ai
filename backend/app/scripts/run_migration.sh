#!/bin/bash
# Wrapper script for running the prod→demo migration on EC2.
#
# The challenge: the demo api container can't reach the prod db container by
# default because they're on separate Docker networks. This script bridges
# them temporarily.
#
# Usage on EC2:
#   cd ~/trajectory
#   bash backend/app/scripts/run_migration.sh
set -e

cd "$(dirname "$0")/../../.."  # project root

echo "==================================================================="
echo "  Prod → Demo data migration (sanitised)"
echo "==================================================================="

# 1. Read prod DB password from .env file
if [ ! -f .env ]; then
    echo "ERROR: .env not found. Are you in the project root?"
    exit 1
fi
# shellcheck disable=SC1091
source .env
if [ -z "$DB_PASSWORD" ]; then
    echo "ERROR: DB_PASSWORD not set in .env"
    exit 1
fi

# 2. Identify the prod db container's network
PROD_DB_CONTAINER=$(sudo docker ps --filter "name=trajectory-db" --format "{{.Names}}" | grep -v demo | head -1)
if [ -z "$PROD_DB_CONTAINER" ]; then
    echo "ERROR: prod db container not found. Is the prod stack running?"
    sudo docker ps --filter "name=trajectory" --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi
PROD_NETWORK=$(sudo docker inspect "$PROD_DB_CONTAINER" --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')
echo "[run_migration]  Prod DB container: $PROD_DB_CONTAINER on network $PROD_NETWORK"

# 3. Connect demo api container to prod network (temporary)
DEMO_API="trajectory-demo-api"
echo "[run_migration]  Bridging demo api to prod network..."
sudo docker network connect "$PROD_NETWORK" "$DEMO_API" 2>/dev/null || echo "(already connected)"

# 4. Run migration script inside demo api container
echo "[run_migration]  Running migration..."
echo ""
sudo docker exec \
    -e PROD_DB_PASSWORD="$DB_PASSWORD" \
    "$DEMO_API" \
    python -m app.scripts.migrate_prod_to_demo

EXIT_CODE=$?

# 5. Disconnect demo api from prod network (cleanup)
echo ""
echo "[run_migration]  Disconnecting demo api from prod network..."
sudo docker network disconnect "$PROD_NETWORK" "$DEMO_API" 2>/dev/null || true

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "==================================================================="
    echo "  ✓ Migration complete. Visit http://51.24.16.185:3001 to verify."
    echo "==================================================================="
else
    echo ""
    echo "==================================================================="
    echo "  ✗ Migration failed (exit code $EXIT_CODE). Demo DB may be in"
    echo "    partial state. Check logs above."
    echo "==================================================================="
    exit $EXIT_CODE
fi
