import os, shutil
from datetime import datetime

FILE = "www/index.html"

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
os.makedirs(f'backups/bootstrap-fix-{stamp}', exist_ok=True)
shutil.copy(FILE, f'backups/bootstrap-fix-{stamp}/index.html.before')
print(f"backup: backups/bootstrap-fix-{stamp}/")

with open(FILE, 'r', encoding='utf-8') as f:
    html = f.read()

# ابحث عن بداية ونهاية البوتسترب
start = html.find('<script id="live-bootstrap">')
end = html.find('</script>', start) + len('</script>')

if start < 0:
    print("❌ لم يُعثر على البوتسترب")
    exit(1)

new_bootstrap = '''<script id="live-bootstrap">
/* Live Update Bootstrap v2 - uses location.replace */
(function(){
  var LB = "https://vkjsynailhrjtfbzysjn.supabase.co/storage/v1/object/public/app-live/"\;
  var LV = "1.4.0";

  try{
    // منع التكرار اللانهائي
    if(sessionStorage.getItem("liveBootstrapped") === "yes"){
      return;
    }
    sessionStorage.setItem("liveBootstrapped", "yes");

    // إذا كنا محمّلين من app-live، لا نُعيد الفحص
    if(window.location.href.indexOf("app-live") >= 0){
      return;
    }

    var xhr = new XMLHttpRequest();
    xhr.open("GET", LB + "version.json?t=" + Date.now(), false);
    xhr.send();

    if(xhr.status !== 200) return;

    var info = JSON.parse(xhr.responseText);
    if(!info || !info.version) return;

    if(info.version === LV) return;

    console.log("Live Update: " + LV + " -> " + info.version);

    // انتقل إلى النسخة السحابية بدل document.write
    window.location.replace(LB + "index.html?v=" + info.version);

  }catch(e){
    console.warn("Live bootstrap skipped:", e);
  }
})();
</script>'''

html = html[:start] + new_bootstrap + html[end:]

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ تم استبدال البوتسترب بـ location.replace")
