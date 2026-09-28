import sys, os, shutil, re
from datetime import datetime

FILE = "www/index.html"

if not os.path.exists(FILE):
    print("❌ لم يُعثر على الملف")
    sys.exit(1)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = f"backups/live-bootstrap-{stamp}"
os.makedirs(backup_dir, exist_ok=True)
shutil.copy(FILE, f"{backup_dir}/index.html.before")
print(f"📦 نسخة احتياطية: {backup_dir}/")

with open(FILE, "r", encoding="utf-8") as f:
    html = f.read()

if "live-bootstrap" in html:
    print("⚠️ Bootstrap مضاف مسبقًا")
    sys.exit(0)

bootstrap = '''<script id="live-bootstrap">
/* Live Update Bootstrap */
(function(){
  var LIVE_BASE = "https://vkjsynailhrjtfbzysjn.supabase.co/storage/v1/object/public/app-live/"\;
  var LOCAL_VERSION = "1.1.0";

  try{
    if(sessionStorage.getItem("liveBootstrapped") === "yes"){
      return;
    }
    sessionStorage.setItem("liveBootstrapped", "yes");

    var xhr = new XMLHttpRequest();
    xhr.open("GET", LIVE_BASE + "version.json?t=" + Date.now(), false);
    xhr.send();

    if(xhr.status !== 200) return;

    var info = JSON.parse(xhr.responseText);
    if(!info || !info.version) return;

    if(info.version === LOCAL_VERSION) return;

    console.log("Live Update: " + LOCAL_VERSION + " -> " + info.version);

    var xhr2 = new XMLHttpRequest();
    xhr2.open("GET", LIVE_BASE + "index.html?t=" + Date.now(), false);
    xhr2.send();

    if(xhr2.status !== 200) return;
    if(!xhr2.responseText || xhr2.responseText.length < 1000) return;

    document.open();
    document.write(xhr2.responseText);
    document.close();

  }catch(e){
    console.warn("Live bootstrap skipped:", e);
  }
})();
</script>
'''

if "</head>" in html:
    html = html.replace("</head>", bootstrap + "\n</head>", 1)
else:
    print("❌ لم يُعثر على </head>")
    sys.exit(2)

with open(FILE, "w", encoding="utf-8") as f:
    f.write(html)

print("✅ أُضيف Bootstrap")
