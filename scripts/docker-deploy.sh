#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PEN_ENV_FILE="${PEN_ENV_FILE:-.env.docker}"
compose() { docker compose --env-file "$PEN_ENV_FILE" "$@"; }
compose config --quiet
compose config --format json | python3 docker/validate-deploy.py
compose build web
compose pull db redis proxy
compose up -d --wait db redis
compose run --rm --no-deps init python manage.py makemigrations --check --dry-run
compose stop proxy web worker beat
compose up -d --force-recreate init web worker beat proxy
for attempt in {1..60}; do
    if compose exec -T web python docker/healthcheck.py >/dev/null 2>&1; then
        compose ps
        echo "Deployment is ready. Verify the login page and run the smoke check."
        exit 0
    fi
    sleep 2
done
echo "Deployment did not become ready; inspect: docker compose --env-file $PEN_ENV_FILE logs --tail=100" >&2
exit 1
