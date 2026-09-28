import os, shutil
from datetime import datetime

FILE = "www/index.html"

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
os.makedirs(f'backups/inapp-update-{stamp}', exist_ok=True)
shutil.copy(FILE, f'backups/inapp-update-{stamp}/index.html.before')
print(f"backup: backups/inapp-update-{stamp}/")

with open(FILE, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# ═══════════════════════════════════════════════════════
# 1) أضف دالة downloadAndInstallApk قبل checkForAppUpdate
# ═══════════════════════════════════════════════════════

helpers = '''
// ═══════════════════════════════════════════════════════
// In-App Update: تنزيل وتثبيت APK من داخل التطبيق
// ═══════════════════════════════════════════════════════
async function downloadAndInstallApk(apkUrl, version){
  try{
    if(typeof Capacitor === "undefined"){
      showToast("❌ Capacitor غير متاح");
      return false;
    }

    const FS = Capacitor.Plugins.Filesystem;
    const FileOpener = Capacitor.Plugins.FileOpener;

    if(!FS || !FileOpener){
      showToast("❌ المكتبات غير مربوطة");
      return false;
    }

    // اطلب صلاحية التثبيت (Android 8+)
    if(Capacitor.Plugins.FileOpener){
      try{
        await FileOpener.checkPermissions();
      }catch(e){}
    }

    const fileName = "update-" + version + ".apk";

    showToast("⬇️ جارٍ التنزيل...");

    // نزّل الملف مباشرة باستخدام fetch + Filesystem
    const response = await fetch(apkUrl, {cache:"no-store"});
    if(!response.ok){
      throw new Error("HTTP " + response.status);
    }

    const blob = await response.blob();

    const base64 = await new Promise(function(resolve, reject){
      const reader = new FileReader();
      reader.onloadend = function(){
        const result = String(reader.result);
        const parts = result.split(",");
        if(parts.length === 2){
          resolve(parts[1]);
        }else{
          reject(new Error("فشل تحويل الملف"));
        }
      };
      reader.onerror = function(){
        reject(new Error("فشل قراءة الملف"));
      };
      reader.readAsDataURL(blob);
    });

    // اكتب الملف إلى Data directory
    const writeResult = await FS.writeFile({
      path: fileName,
      data: base64,
      directory: "CACHE"
    });

    console.log("✅ APK محفوظ:", writeResult.uri);

    showToast("✅ اكتمل التنزيل، جارٍ فتح المثبّت...");

    // احصل على URI صحيح
    const uriResult = await FS.getUri({
      path: fileName,
      directory: "CACHE"
    });

    // افتح الملف
    await FileOpener.open({
      filePath: uriResult.uri,
      contentType: "application/vnd.android.package-archive"
    });

    return true;

  }catch(error){
    console.error("downloadAndInstallApk error:", error);
    showToast("❌ فشل التنزيل: " + (error.message || "خطأ"));

    // fallback: افتح الرابط في Chrome
    try{
      window.open(apkUrl, "_blank");
    }catch(e){}

    return false;
  }
}

'''

anchor1 = 'async function checkForAppUpdate'
if anchor1 in html and 'downloadAndInstallApk' not in html:
    html = html.replace(anchor1, helpers + anchor1, 1)
    changes += 1
    print("✅ 1/2 أُضيفت downloadAndInstallApk")
else:
    print("⚠️ 1/2 لم يُطابق الموضع")

# ═══════════════════════════════════════════════════════
# 2) عدّل checkForAppUpdate ليستخدم الدالة الجديدة
# ═══════════════════════════════════════════════════════

old_block = '''    if(isForced || confirm(message)){
      if(info.apkUrl){
        window.open(info.apkUrl, "_blank");
      }
    }'''

new_block = '''    if(isForced || confirm(message)){
      if(info.apkUrl){
        // ⭐ استخدام التنزيل داخل التطبيق
        await downloadAndInstallApk(info.apkUrl, info.version);
      }
    }'''

if old_block in html:
    html = html.replace(old_block, new_block, 1)
    changes += 1
    print("✅ 2/2 checkForAppUpdate محدّث")
else:
    print("⚠️ 2/2 لم يُطابق bloc checkForAppUpdate")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n{'='*50}")
print(f"✅ {changes} تعديلات")
print(f"{'='*50}")
