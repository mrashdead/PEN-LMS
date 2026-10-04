#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
export PEN_ENV_FILE="${PEN_ENV_FILE:-.env.docker}"
compose() { docker compose --env-file "$PEN_ENV_FILE" "$@"; }
destination="${1:-backups/pen-$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ -e "$destination" ]]; then
    echo "Backup destination already exists: $destination" >&2
    exit 1
fi
mkdir -p "$destination"
mapfile -t running_services < <(compose ps --status running --services | awk '/^(web|worker|beat|proxy)$/')
resume() {
    if (( ${#running_services[@]} )); then
        compose start "${running_services[@]}"
    fi
}
trap resume EXIT
if (( ${#running_services[@]} )); then
    compose stop "${running_services[@]}"
fi
compose exec -T db sh -ec 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$destination/database.dump"
compose exec -T db pg_restore --list < "$destination/database.dump" > "$destination/database-toc.txt"
compose run --rm -T --no-deps --entrypoint tar web -C /app/media -czf - . > "$destination/media.tar.gz"
compose images > "$destination/images.txt"
(cd "$destination" && sha256sum database.dump media.tar.gz > SHA256SUMS)
echo "Backup created: $destination (contains private data; encrypt and copy off-host)."
