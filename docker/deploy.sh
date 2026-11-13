#!/bin/sh
# Запускается на сервере из CI: загружает новый образ и перезапускает контейнер (rootless podman — Docker на сервере нет).
set -eu

IMAGE=kubsu-users:latest
NAME="${USER:-app}-users"
APP_PORT="${APP_PORT:-8016}"

echo "Загружаю образ..."
gunzip -c /tmp/image.tar.gz | podman load
rm -f /tmp/image.tar.gz

echo "Перезапускаю контейнер $NAME на порту $APP_PORT..."
podman rm -f "$NAME" 2>/dev/null || true

set -- podman run -d --name "$NAME" --restart unless-stopped --network host \
    -e PORT="$APP_PORT" -e PATH_PREFIX="${PATH_PREFIX:-}"
if [ -n "${DATABASE_URL:-}" ]; then
    set -- "$@" -e DATABASE_URL="$DATABASE_URL"
fi
"$@" "$IMAGE"

# Ждём, пока приложение ответит на /health
for i in $(seq 1 20); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$APP_PORT/health', timeout=2)" 2>/dev/null \
       || curl -fsS "http://127.0.0.1:$APP_PORT/health" >/dev/null 2>&1; then
        echo "Приложение запущено"
        podman image prune -f >/dev/null
        exit 0
    fi
    sleep 1
done

echo "Приложение не ответило, логи:"
podman logs --tail 50 "$NAME"
exit 1
