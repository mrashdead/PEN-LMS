#!/usr/bin/env bash
set -euo pipefail
umask 0007

backup_root=/app/backups
media_root=/app/media
mkdir -p "$backup_root"

backup_once() {
    local filename stamp stage archive_tmp
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    filename="pen-auto-${stamp}.tar.gz"
    while [[ -e "$backup_root/$filename" ]]; do
        sleep 1
        stamp="$(date -u +%Y%m%dT%H%M%SZ)"
        filename="pen-auto-${stamp}.tar.gz"
    done
    stage="$(mktemp -d "$backup_root/.stage.XXXXXX")"
    archive_tmp="$backup_root/.${filename}.partial"
    cleanup() {
        rm -rf -- "$stage"
        rm -f -- "$archive_tmp"
    }
    trap cleanup EXIT INT TERM

    export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
    pg_dump --host="${PGHOST:-db}" --port="${PGPORT:-5432}" \
        --username="${POSTGRES_USER:?POSTGRES_USER is required}" \
        --dbname="${POSTGRES_DB:?POSTGRES_DB is required}" \
        --format=custom --no-owner --no-privileges \
        --file="$stage/database.dump"
    pg_restore --list "$stage/database.dump" > "$stage/database-toc.txt"
    tar -C "$media_root" -czf "$stage/media.tar.gz" .
    tar -tzf "$stage/media.tar.gz" >/dev/null
    (cd "$stage" && sha256sum database.dump media.tar.gz > SHA256SUMS)
    tar -C "$stage" -czf "$archive_tmp" database.dump media.tar.gz SHA256SUMS
    chmod 0660 "$archive_tmp"
    mv -- "$archive_tmp" "$backup_root/$filename"
    trap - EXIT INT TERM
    cleanup
    unset PGPASSWORD

    mapfile -t retained < <(
        find "$backup_root" -regextype posix-extended -mindepth 1 -maxdepth 1 \
            -type f -regex "$backup_root/pen-auto-[0-9]{8}T[0-9]{6}Z\\.tar\\.gz" \
            -printf '%f\n' | LC_ALL=C sort -r
    )
    local index name stamp created_epoch cutoff
    local -a current=()
    cutoff="$(($(date -u +%s) - 5 * 24 * 60 * 60))"
    for name in "${retained[@]}"; do
        stamp="${name#pen-auto-}"
        stamp="${stamp%.tar.gz}"
        created_epoch="$(date -u -d "${stamp:0:4}-${stamp:4:2}-${stamp:6:2} ${stamp:9:2}:${stamp:11:2}:${stamp:13:2}" +%s)"
        if (( created_epoch < cutoff )); then
            rm -f -- "$backup_root/$name"
        else
            current+=("$name")
        fi
    done
    for ((index = 5; index < ${#current[@]}; index++)); do
        rm -f -- "$backup_root/${current[$index]}"
    done
    printf 'Daily backup created: %s\n' "$filename"
}

seconds_until_0200_utc() {
    local now today_run next_run
    now="$(date -u +%s)"
    today_run="$(date -u -d 'today 02:00:00' +%s)"
    if (( today_run > now )); then
        next_run="$today_run"
    else
        next_run="$(date -u -d 'tomorrow 02:00:00' +%s)"
    fi
    printf '%s\n' "$((next_run - now))"
}

while true; do
    backup_once
    sleep "$(seconds_until_0200_utc)"
done
