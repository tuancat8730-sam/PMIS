#!/usr/bin/env bash
# Triển khai PMIS lên VPS dùng chung với qlda. Không có tên miền nên chạy HTTP trên IP, cổng
# riêng (PMIS_HTTP_PORT, mặc định 8080) để không đụng vào qlda ở cổng 80.
# Image API và web được build ở máy này rồi gửi qua SSH, vì server chỉ có 1 GB RAM không build nổi.
#
# Cần: SSH key tới server (user trong group docker), docker (build linux/amd64), openssl, rsync, curl.
# Cách dùng: scripts/deploy-vps.sh                        build, gửi, migrate, khởi động, kiểm tra
#            SEED_ADMIN=1 scripts/deploy-vps.sh           thêm tài khoản ADMIN đầu tiên (in mật khẩu tạm)
#            SEED_ADMIN_EMAIL=... SEED_ADMIN_NAME=... SEED_ADMIN=1 scripts/deploy-vps.sh
set -euo pipefail

VPS_HOST="${VPS_HOST:-deploy@103.9.78.91}"
REMOTE_DIR="${REMOTE_DIR:-pmis}"
HTTP_PORT="${PMIS_HTTP_PORT:-8080}"
SEED_ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-admin@pmis.local}"
SEED_ADMIN_NAME="${SEED_ADMIN_NAME:-Quản trị viên}"
ADMIN_PASSWORD_BYTES=12
HEALTH_RETRIES=20
HEALTH_INTERVAL_SECONDS=3

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="$(date +%Y%m%d%H%M%S)"
PUBLIC_IP="${VPS_HOST#*@}"
PUBLIC_ORIGIN="http://$PUBLIC_IP:$HTTP_PORT"
SSH=(ssh -o BatchMode=yes "$VPS_HOST")
DC="cd $REMOTE_DIR && docker compose"

step() { printf '\n==> %s\n' "$*"; }
rnd() { openssl rand -hex "$1"; }
# Khóa Fernet: 32 byte mã hóa base64 URL-safe
fernet_key() { openssl rand -base64 32 | tr '+/' '-_'; }

require_tools() {
  local tool
  for tool in docker rsync openssl curl; do
    if ! command -v "$tool" >/dev/null; then
      echo "thiếu công cụ: $tool" >&2
      exit 1
    fi
  done
}

build_images() {
  step "Build image API ($TAG)"
  docker buildx build --platform linux/amd64 --load -t "pmis-api:$TAG" "$ROOT/apps/api"

  # NEXT_PUBLIC_* được nhúng vào bundle lúc build, nên địa chỉ API phải truyền ở đây
  step "Build image web ($TAG), API tại $PUBLIC_ORIGIN"
  docker buildx build --platform linux/amd64 --load --build-arg "NEXT_PUBLIC_API_URL=$PUBLIC_ORIGIN" \
    -t "pmis-web:$TAG" "$ROOT/apps/web"
}

ship_files_and_images() {
  step "Gửi file cấu hình và image"
  "${SSH[@]}" "mkdir -p $REMOTE_DIR"
  rsync -az "$ROOT/deploy/vps/docker-compose.yml" "$ROOT/deploy/vps/Caddyfile" "$VPS_HOST:$REMOTE_DIR/"
  local image
  for image in api web; do
    docker save "pmis-$image:$TAG" | gzip | "${SSH[@]}" "gunzip | docker load"
  done
}

# .env chỉ tạo một lần với bí mật ngẫu nhiên; các lần sau chỉ cập nhật IMAGE_TAG
write_env_once() {
  step "Cấu hình (.env tạo một lần, bí mật ngẫu nhiên)"
  if "${SSH[@]}" "test -f $REMOTE_DIR/.env"; then
    "${SSH[@]}" "sed -i 's/^IMAGE_TAG=.*/IMAGE_TAG=$TAG/' $REMOTE_DIR/.env"
    echo ".env đã có, đặt IMAGE_TAG=$TAG"
    return
  fi
  local pg_password
  pg_password="$(rnd 16)"
  "${SSH[@]}" "umask 077 && cat > $REMOTE_DIR/.env" <<EOF
PUBLIC_URL=$PUBLIC_ORIGIN
IMAGE_TAG=$TAG
POSTGRES_PASSWORD=$pg_password
DATABASE_URL=postgresql+asyncpg://pmis:$pg_password@db:5432/pmis
JWT_SECRET=$(rnd 32)
CCCD_ENCRYPTION_KEY=$(fernet_key)
CORS_ORIGINS=["$PUBLIC_ORIGIN"]
EOF
  echo ".env đã tạo"
}

start_database() {
  step "Database"
  "${SSH[@]}" "$DC up -d db"
  "${SSH[@]}" "$DC exec -T db sh -c 'until pg_isready -U pmis >/dev/null 2>&1; do sleep 1; done'"
}

migrate() {
  step "Migrate"
  "${SSH[@]}" "$DC run --rm migrate"
}

# Mật khẩu đi qua stdin: create-admin đọc bằng getpass, không có TTY thì lấy từng dòng từ stdin
seed_admin() {
  step "Tạo ADMIN đầu tiên ($SEED_ADMIN_EMAIL)"
  local admin_password
  admin_password="$(rnd "$ADMIN_PASSWORD_BYTES")"
  printf '%s\n' "$admin_password" | "${SSH[@]}" \
    "$DC run --rm -T api python -m app.cli create-admin --email $SEED_ADMIN_EMAIL --name '$SEED_ADMIN_NAME'"
  printf '\nMật khẩu tạm của %s: %s\nLưu lại ngay, script không hiện lại được.\n' \
    "$SEED_ADMIN_EMAIL" "$admin_password"
}

start_stack() {
  step "Khởi động"
  "${SSH[@]}" "$DC up -d --remove-orphans && docker image prune -f >/dev/null"
}

wait_for_health() {
  local health_url="$PUBLIC_ORIGIN/api/v1/health"
  step "Kiểm tra $health_url"
  local attempt
  for attempt in $(seq 1 "$HEALTH_RETRIES"); do
    if curl -fsS "$health_url"; then
      printf '\nĐã triển khai %s tại %s\n' "$TAG" "$PUBLIC_ORIGIN"
      return 0
    fi
    sleep "$HEALTH_INTERVAL_SECONDS"
  done
  echo "API chưa trả lời. Xem log: ssh $VPS_HOST 'cd $REMOTE_DIR && docker compose logs --tail=50'" >&2
  return 1
}

require_tools
build_images
ship_files_and_images
write_env_once
start_database
migrate
if [ -n "${SEED_ADMIN:-}" ]; then
  seed_admin
fi
start_stack
wait_for_health
