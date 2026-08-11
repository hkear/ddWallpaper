#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 加载 .env
if [ -r "$PROJECT_DIR/.env" ]; then
  eval "$(grep -v '^#' "$PROJECT_DIR/.env" | grep -v '^$' | sed 's/^/export /')"
fi

DB_USER="${DB_USER:-wallpaper}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-wallpaper_db}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-wallpaper_mysql}"
# kay 用户通过 sudo 访问 docker
DOCKER="sudo docker"

if [ -z "$DB_PASSWORD" ]; then
  echo "❌ 未设置 DB_PASSWORD"
  exit 1
fi

OUTPUT="${1:-}"
BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"

if [ -z "$OUTPUT" ]; then
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  OUTPUT="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
fi

echo "📦 正在备份 $DB_NAME → $OUTPUT ..."

# 执行 mysqldump 并保留错误信息
if $DOCKER exec "$MYSQL_CONTAINER" mysqldump \
  -u"$DB_USER" \
  -p"$DB_PASSWORD" \
  --single-transaction \
  --routines \
  --triggers \
  --no-tablespaces \
  --default-character-set=utf8mb4 \
  "$DB_NAME" > "$OUTPUT" 2>/tmp/backup_err.txt; then
  
  SIZE=$(du -h "$OUTPUT" | cut -f1)
  echo "✅ 备份完成: $OUTPUT ($SIZE)"
else
  echo "❌ 备份失败:"
  cat /tmp/backup_err.txt 2>/dev/null || true
  rm -f "$OUTPUT"
  exit 1
fi
