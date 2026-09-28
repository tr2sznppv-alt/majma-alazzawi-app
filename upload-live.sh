#!/data/data/com.termux/files/usr/bin/bash
set -e
cd ~/catalog-app

if [ -z "$SUPABASE_KEY" ]; then
  echo "❌ SUPABASE_KEY غير مضبوط"
  echo "نفّذ: export SUPABASE_KEY='sb_secret_...'"
  exit 1
fi

URL="https://vkjsynailhrjtfbzysjn.supabase.co"
BUCKET="app-live"
VERSION="${1:-1.1.0}"
TMP="$HOME/tmp"
mkdir -p "$TMP"

echo "🚀 رفع (v$VERSION)"

echo "  → index.html"
curl -s -X POST "$URL/storage/v1/object/$BUCKET/index.html" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: text/html" \
  -H "x-upsert: true" \
  --data-binary "@www/index.html"

echo "  → api-config.js"
curl -s -X POST "$URL/storage/v1/object/$BUCKET/api-config.js" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/javascript" \
  -H "x-upsert: true" \
  --data-binary "@www/api-config.js"

echo "  → version.json"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "{\"version\":\"$VERSION\",\"updatedAt\":\"$NOW\"}" > "$TMP/v.json"

curl -s -X POST "$URL/storage/v1/object/$BUCKET/version.json" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -H "x-upsert: true" \
  --data-binary "@$TMP/v.json"

echo ""
echo "✅ تم الرفع بنجاح (v$VERSION)"
