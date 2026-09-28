#!/data/data/com.termux/files/usr/bin/bash
set -e

cd ~/catalog-app

# ═══ تحميل المفتاح تلقائيًا ═══
[ -z "$SUPABASE_KEY" ] && [ -f "$HOME/.supabase_key" ] && export SUPABASE_KEY="$(cat "$HOME/.supabase_key")"

# ═══ التحقق من المدخلات ═══
VERSION="$1"
if [ -z "$VERSION" ]; then
  echo "❌ الاستخدام: ./publish.sh 1.5.0"
  exit 1
fi

if [ -z "$SUPABASE_KEY" ]; then
  echo "❌ SUPABASE_KEY غير مضبوط"
  exit 1
fi

URL="https://vkjsynailhrjtfbzysjn.supabase.co"
BUCKET_LIVE="app-live"
BUCKET_APK="app-releases"
APK_FILENAME="catalog-v$VERSION.apk"
TMP="$HOME/tmp"
mkdir -p "$TMP"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 نشر الإصدار v$VERSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ═══ 1) تحديث الإصدارات ═══
echo "[1/7] 🔢 تحديث الإصدارات في الكود..."

OLD_VERSION=$(grep -oP 'const APP_VERSION = "\K[^"]+' www/index.html | head -1)
echo "      $OLD_VERSION → $VERSION"

sed -i "s/const APP_VERSION = \".*\"/const APP_VERSION = \"$VERSION\"/" www/index.html
sed -i "s/var LV = \".*\"/var LV = \"$VERSION\"/" www/index.html

grep -q "const APP_VERSION = \"$VERSION\"" www/index.html || {
  echo "      ❌ فشل التحديث"
  exit 1
}
echo "      ✅"

# ═══ 2) نسخة احتياطية ═══
echo ""
echo "[2/7] 📦 نسخة احتياطية..."

STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups/publish-v$VERSION-$STAMP"
mkdir -p "$BACKUP_DIR"
cp www/index.html "$BACKUP_DIR/"
cp www/api-config.js "$BACKUP_DIR/" 2>/dev/null || true
echo "      ✅ $BACKUP_DIR/"

# ═══ 3) رفع الواجهة (Live) ═══
echo ""
echo "[3/7] 🌐 رفع الواجهة إلى $BUCKET_LIVE..."

for f in index.html api-config.js; do
  CT="text/html"
  [ "$f" = "api-config.js" ] && CT="application/javascript"

  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "$URL/storage/v1/object/$BUCKET_LIVE/$f" \
    -H "apikey: $SUPABASE_KEY" \
    -H "Authorization: Bearer $SUPABASE_KEY" \
    -H "Content-Type: $CT" \
    -H "x-upsert: true" \
    --data-binary "@www/$f")

  [ "$CODE" = "200" ] && echo "      ✅ $f" || echo "      ⚠️  $f ($CODE)"
done

# version.json للواجهة
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '{"version":"%s","updatedAt":"%s"}\n' "$VERSION" "$NOW" > "$TMP/v.json"

curl -s -o /dev/null -X POST \
  "$URL/storage/v1/object/$BUCKET_LIVE/version.json" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -H "x-upsert: true" \
  --data-binary "@$TMP/v.json"

echo "      ✅ version.json"

# ═══ 4) بناء APK ═══
echo ""
echo "[4/7] 🔨 بناء APK..."

npx cap sync android > /dev/null 2>&1
cd android
./gradlew assembleRelease -q
cd ..

APK_SOURCE="android/app/build/outputs/apk/release/app-release.apk"

if [ ! -f "$APK_SOURCE" ]; then
  echo "      ❌ فشل البناء"
  exit 1
fi
echo "      ✅ BUILD SUCCESSFUL"

# ═══ 5) نسخ APK محليًا ═══
echo ""
echo "[5/7] 📱 نسخ APK..."

APK_BACKUP="$BACKUP_DIR/$APK_FILENAME"
APK_DOWNLOAD="$HOME/storage/shared/Download/$APK_FILENAME"

cp "$APK_SOURCE" "$APK_BACKUP"
cp "$APK_SOURCE" "$APK_DOWNLOAD"

SIZE=$(du -h "$APK_DOWNLOAD" | cut -f1)
echo "      ✅ $APK_DOWNLOAD ($SIZE)"

# ═══ 6) رفع APK إلى Storage ═══
echo ""
echo "[6/7] ☁️  رفع APK إلى $BUCKET_APK..."

CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "$URL/storage/v1/object/$BUCKET_APK/$APK_FILENAME" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/vnd.android.package-archive" \
  -H "x-upsert: true" \
  --data-binary "@$APK_SOURCE")

[ "$CODE" = "200" ] && echo "      ✅ $APK_FILENAME" || echo "      ⚠️  ($CODE)"

# ═══ 7) تحديث جدول الإصدارات ═══
echo ""
echo "[7/7] 📋 تحديث جدول app_versions..."

# عطّل كل الإصدارات القديمة
curl -s -o /dev/null -X PATCH \
  "$URL/rest/v1/app_versions?is_active=eq.true" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# أدرج الإصدار الجديد
RESP=$(curl -s -X POST "$URL/rest/v1/app_versions" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d "{
    \"version\": \"$VERSION\",
    \"min_required\": \"1.0.0\",
    \"apk_url\": \"$URL/storage/v1/object/public/$BUCKET_APK/$APK_FILENAME\",
    \"notes\": \"الإصدار $VERSION\",
    \"force_update\": false,
    \"is_active\": true
  }")

echo "$RESP" | grep -q "$VERSION" && echo "      ✅ تم تسجيل v$VERSION" || echo "      ⚠️  تحقق يدويًا"

# ═══ الخلاصة ═══
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 اكتمل النشر بنجاح!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 الإصدار: v$VERSION"
echo "📦 APK:     $APK_DOWNLOAD"
echo "💾 نسخة:    $BACKUP_DIR/"
echo "☁️  Live:    $URL/storage/v1/object/public/$BUCKET_LIVE/index.html"
echo "☁️  APK:     $URL/storage/v1/object/public/$BUCKET_APK/$APK_FILENAME"
echo ""
echo "✨ المستخدمون سيرون الإشعار عند فتح التطبيق"
echo ""
