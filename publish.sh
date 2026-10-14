#!/data/data/com.termux/files/usr/bin/bash
set -e

cd ~/catalog-app

# ═══ تحميل المفتاح ═══
[ -z "$SUPABASE_KEY" ] && [ -f "$HOME/.supabase_key" ] && export SUPABASE_KEY="$(cat "$HOME/.supabase_key")"

VERSION="$1"
if [ -z "$VERSION" ]; then
  echo "❌ الاستخدام: ./publish.sh 1.5.2"
  exit 1
fi

if [ -z "$SUPABASE_KEY" ]; then
  echo "❌ SUPABASE_KEY غير مضبوط"
  exit 1
fi

SUPABASE_URL="https://vkjsynailhrjtfbzysjn.supabase.co"
GITHUB_REPO="tr2sznppv-alt/majma-alazzawi-app"
APK_FILENAME="catalog-v$VERSION.apk"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 نشر الإصدار v$VERSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ═══ 1) تحديث الإصدار ═══
echo "[1/6] 🔢 تحديث الإصدار..."
OLD=$(grep -oP 'const APP_VERSION = "\K[^"]+' www/index.html | head -1)
echo "      $OLD → $VERSION"

sed -i "s/const APP_VERSION = \".*\"/const APP_VERSION = \"$VERSION\"/" www/index.html

grep -q "const APP_VERSION = \"$VERSION\"" www/index.html || exit 1
echo "      ✅"

# ═══ 2) نسخة احتياطية ═══
echo ""
echo "[2/6] 📦 نسخة احتياطية..."
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups/publish-v$VERSION-$STAMP"
mkdir -p "$BACKUP_DIR"
cp www/index.html "$BACKUP_DIR/"
cp www/api-config.js "$BACKUP_DIR/" 2>/dev/null || true
echo "      ✅ $BACKUP_DIR/"

# ═══ 3) بناء APK ═══
echo ""
echo "[3/6] 🔨 بناء APK..."
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

# ═══ 4) نسخ APK محليًا ═══
echo ""
echo "[4/6] 📱 نسخ APK محليًا..."
cp "$APK_SOURCE" "$BACKUP_DIR/$APK_FILENAME"
cp "$APK_SOURCE" "$HOME/storage/shared/Download/$APK_FILENAME"
SIZE=$(du -h "$APK_SOURCE" | cut -f1)
echo "      ✅ $APK_FILENAME ($SIZE)"

# ═══ 5) نشر على GitHub Release ═══
echo ""
echo "[5/6] 🐙 نشر على GitHub Release..."

cd "$BACKUP_DIR"

gh release create "v$VERSION" \
  "$APK_FILENAME" \
  --title "الإصدار $VERSION" \
  --notes "التحديث التلقائي عبر GitHub Releases" \
  --repo "$GITHUB_REPO" > /dev/null 2>&1 || {
    echo "      ⚠️  فشل إنشاء Release — قد يكون موجودًا"
  }

cd ~/catalog-app

GH_APK_URL="https://github.com/$GITHUB_REPO/releases/download/v$VERSION/$APK_FILENAME"
echo "      ✅ $GH_APK_URL"

# ═══ 6) تحديث app_versions ═══
echo ""
echo "[6/6] 📋 تحديث Supabase..."

# عطّل كل الإصدارات القديمة
curl -s -o /dev/null -X PATCH \
  "$SUPABASE_URL/rest/v1/app_versions?is_active=eq.true" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# أدرج أو حدّث الإصدار الجديد
curl -s -o /dev/null -X POST "$SUPABASE_URL/rest/v1/app_versions" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: resolution=merge-duplicates" \
  -d "{
    \"version\": \"$VERSION\",
    \"min_required\": \"1.0.0\",
    \"apk_url\": \"$GH_APK_URL\",
    \"notes\": \"الإصدار $VERSION\",
    \"force_update\": false,
    \"is_active\": true
  }"

echo "      ✅ تم تسجيل v$VERSION"

# ═══ الخلاصة ═══
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 اكتمل النشر بنجاح!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 الإصدار: v$VERSION"
echo "📦 APK:     ~/storage/shared/Download/$APK_FILENAME"
echo "💾 نسخة:    $BACKUP_DIR/"
echo "🐙 GitHub:  $GH_APK_URL"
echo ""
echo "✨ المستخدمون سيرون الإشعار عند فتح التطبيق"
echo ""
