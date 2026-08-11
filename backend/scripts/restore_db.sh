#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -r "$PROJECT_DIR/.env" ]; then
  eval "$(grep -v '^#' "$PROJECT_DIR/.env" | grep -v '^$' | sed 's/^/export /')"
fi

INPUT="${1:-}"
if [ -z "$INPUT" ] || [ ! -f "$INPUT" ]; then
  echo "用法: bash scripts/restore_db.sh <备份文件.sql>"
  exit 1
fi

DB_USER="${DB_USER:-wallpaper}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-wallpaper_db}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-wallpaper_mysql}"
DOCKER="sudo docker"

if [ -z "$DB_PASSWORD" ]; then
  echo "❌ 未设置 DB_PASSWORD"
  exit 1
fi

echo "⚠  即将用 $INPUT 覆盖数据库 $DB_NAME"
echo "   按 Ctrl+C 取消，10 秒后自动执行..."
sleep 10

echo "🗑  正在清空旧数据..."
$DOCKER exec -i "$MYSQL_CONTAINER" mysql \
  -u"$DB_USER" \
  -p"$DB_PASSWORD" \
  -e "DROP DATABASE IF EXISTS \`$DB_NAME\`; CREATE DATABASE \`$DB_NAME\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/tmp/restore_err.txt || {
  echo "❌ 清空数据库失败:"
  cat /tmp/restore_err.txt 2>/dev/null || true
  exit 1
}

echo "📥 正在导入数据..."
if $DOCKER exec -i "$MYSQL_CONTAINER" mysql \
  -u"$DB_USER" \
  -p"$DB_PASSWORD" \
  --default-character-set=utf8mb4 \
  "$DB_NAME" < "$INPUT" 2>/tmp/restore_err.txt; then
  echo "✅ 恢复完成: $INPUT → $DB_NAME"
  echo "   请运行 cd $PROJECT_DIR && sudo docker compose up -d 让后端重新初始化"
else
  echo "❌ 恢复失败:"
  cat /tmp/restore_err.txt 2>/dev/null || true
  exit 1
fi
