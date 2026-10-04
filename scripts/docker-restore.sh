#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PEN_ENV_FILE="${PEN_ENV_FILE:-.env.docker}"
compose() { docker compose --env-file "$PEN_ENV_FILE" "$@"; }
destination="${1:?Usage: bash scripts/docker-restore.sh backups/pen-TIMESTAMP}"
for filename in database.dump media.tar.gz SHA256SUMS; do
    [[ -f "$destination/$filename" ]] || { echo "Missing $filename" >&2; exit 1; }
done
(cd "$destination" && sha256sum --check SHA256SUMS)
echo "WARNING: replaces the database and ALL media of this Compose project."
echo "Use only with a trusted backup and take a fresh backup first."
read -r -p "Type RESTORE to continue: " confirmation
[[ "$confirmation" == RESTORE ]] || exit 1
compose up -d --wait db redis
compose stop proxy web worker beat
compose exec -T db sh -ec 'dropdb -U "$POSTGRES_USER" --force --if-exists "$POSTGRES_DB"; createdb -U "$POSTGRES_USER" --owner="$POSTGRES_USER" "$POSTGRES_DB"'
compose exec -T db sh -ec 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges --exit-on-error' < "$destination/database.dump"
compose run --rm --no-deps --entrypoint python web -c 'from pathlib import Path; import shutil; root = Path("/app/media"); [(shutil.rmtree(path) if path.is_dir() and not path.is_symlink() else path.unlink()) for path in root.iterdir()]'
compose run --rm -T --no-deps --entrypoint tar web -C /app/media --no-same-owner -xzf - < "$destination/media.tar.gz"
for database in 0 1 2; do
    compose exec -T redis redis-cli -n "$database" FLUSHDB
done
compose up -d --force-recreate init web worker beat proxy
echo "Restore applied. Check logs, readiness, login and a private attachment download."
