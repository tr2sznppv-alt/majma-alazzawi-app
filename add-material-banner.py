import os, shutil
from datetime import datetime

FILE = "www/index.html"

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
os.makedirs(f'backups/material-banner-{stamp}', exist_ok=True)
shutil.copy(FILE, f'backups/material-banner-{stamp}/index.html.before')
print(f"📦 backup: backups/material-banner-{stamp}/")

with open(FILE, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# ═══════════════════════════════════════════════════════
# 1) CSS
# ═══════════════════════════════════════════════════════

css = '''
/* ═══════════════════════════════════════════
   Material You Banner — Universal Android 5+
   ═══════════════════════════════════════════ */
.muy-overlay{
  position:fixed;
  top:0;left:0;right:0;bottom:0;
  background:rgba(10,15,25,.6);
  z-index:9998;
  opacity:0;
  visibility:hidden;
  transition:opacity .3s ease,visibility .3s ease;
}
.muy-overlay.show{opacity:1;visibility:visible;}

.muy-banner{
  position:fixed;
  bottom:0;left:0;right:0;
  z-index:9999;
  padding:24px 20px 22px;
  padding-bottom:calc(22px + 20px);
  padding-bottom:calc(22px + env(safe-area-inset-bottom, 0px));
  background:#1a1f2e;
  background:linear-gradient(180deg,#1e2538 0%,#151a28 100%);
  border-radius:32px 32px 0 0;
  box-shadow:0 -10px 40px rgba(0,0,0,.5);
  color:#e8eaf0;
  transform:translateY(110%);
  transition:transform .42s cubic-bezier(.22,1,.36,1);
  direction:rtl;
  font-family:inherit;
  overflow:hidden;
}

/* شريط علوي متدرج */
.muy-banner::before{
  content:"";
  position:absolute;
  top:0;left:0;right:0;
  height:4px;
  background:linear-gradient(90deg,#c59d5f 0%,#e8c88a 50%,#c59d5f 100%);
}

.muy-banner.show{transform:translateY(0);}

/* ─── Handle ─── */
.muy-handle{
  width:40px;
  height:4px;
  border-radius:2px;
  background:rgba(197,157,95,.4);
  margin:0 auto 20px;
}

/* ─── Icon ─── */
.muy-icon-wrap{
  display:flex;
  justify-content:center;
  margin-bottom:16px;
}

.muy-icon{
  width:72px;
  height:72px;
  border-radius:24px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:34px;
  background:linear-gradient(135deg,#c59d5f 0%,#e8c88a 50%,#c59d5f 100%);
  color:#0a0f1e;
  box-shadow:0 12px 32px rgba(197,157,95,.35);
  animation:muyFloat 3s ease-in-out infinite;
}

@keyframes muyFloat{
  0%,100%{transform:translateY(0)}
  50%{transform:translateY(-4px)}
}

/* ─── Title ─── */
.muy-title{
  margin:0 0 8px;
  text-align:center;
  font-size:22px;
  font-weight:900;
  color:#fff;
  letter-spacing:-.4px;
  line-height:1.3;
}

.muy-subtitle{
  margin:0 0 20px;
  text-align:center;
  font-size:14px;
  color:rgba(232,234,240,.7);
  line-height:1.6;
}

/* ─── Versions Chips ─── */
.muy-versions{
  display:flex;
  justify-content:center;
  align-items:center;
  gap:10px;
  margin-bottom:20px;
  flex-wrap:wrap;
}

.muy-chip{
  padding:7px 14px;
  border-radius:20px;
  font-family:monospace;
  font-size:13px;
  font-weight:800;
  letter-spacing:.5px;
}

.muy-chip-old{
  background:rgba(255,255,255,.08);
  color:rgba(232,234,240,.75);
  border:1px solid rgba(255,255,255,.1);
}

.muy-chip-new{
  background:linear-gradient(135deg,rgba(197,157,95,.3),rgba(197,157,95,.15));
  color:#e8c88a;
  border:1px solid rgba(197,157,95,.4);
  box-shadow:0 4px 12px rgba(197,157,95,.2);
}

.muy-arrow{
  color:#c59d5f;
  font-size:18px;
  font-weight:900;
}

/* ─── Notes ─── */
.muy-notes{
  margin:0 0 20px;
  padding:14px 16px;
  border-radius:20px;
  background:rgba(197,157,95,.07);
  border:1px solid rgba(197,157,95,.15);
  color:rgba(232,234,240,.85);
  font-size:13px;
  line-height:1.75;
  text-align:center;
}

.muy-notes:empty{display:none;}

/* ─── Progress ─── */
.muy-progress{
  margin:0 0 20px;
  padding:16px 18px;
  border-radius:20px;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(197,157,95,.18);
  display:none;
}

.muy-progress.show{
  display:block;
  animation:muySlideIn .35s ease;
}

@keyframes muySlideIn{
  from{opacity:0;transform:translateY(10px)}
  to{opacity:1;transform:translateY(0)}
}

.muy-progress-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:12px;
  font-size:13px;
  font-weight:800;
  color:rgba(232,234,240,.85);
}

.muy-percent{
  color:#e8c88a;
  font-family:monospace;
  font-size:16px;
  font-weight:900;
}

.muy-progress-track{
  height:10px;
  border-radius:5px;
  background:rgba(255,255,255,.06);
  overflow:hidden;
  position:relative;
}

.muy-progress-fill{
  height:100%;
  width:0%;
  border-radius:5px;
  background:linear-gradient(90deg,#c59d5f 0%,#e8c88a 50%,#c59d5f 100%);
  background-size:200% 100%;
  transition:width .4s cubic-bezier(.4,0,.2,1);
  animation:muyShimmer 2s linear infinite;
  box-shadow:0 0 16px rgba(197,157,95,.6);
}

@keyframes muyShimmer{
  0%{background-position:0% 50%}
  100%{background-position:200% 50%}
}

/* ─── Buttons (Material Pill) ─── */
.muy-actions{
  display:flex;
  gap:10px;
}

.muy-btn{
  flex:1;
  min-height:54px;
  border:0;
  border-radius:27px;
  font-size:15px;
  font-weight:800;
  font-family:inherit;
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  letter-spacing:-.2px;
  transition:transform .18s ease,box-shadow .25s ease,background .25s ease;
  position:relative;
  overflow:hidden;
  -webkit-tap-highlight-color:transparent;
}

.muy-btn::after{
  content:"";
  position:absolute;
  top:50%;left:50%;
  width:0;height:0;
  border-radius:50%;
  background:rgba(255,255,255,.35);
  transform:translate(-50%,-50%);
  transition:width .5s ease,height .5s ease;
}

.muy-btn:active::after{
  width:250px;
  height:250px;
}

.muy-btn:active{transform:scale(.96);}

.muy-btn-primary{
  background:linear-gradient(135deg,#c59d5f 0%,#e8c88a 50%,#c59d5f 100%);
  color:#0a0f1e;
  box-shadow:0 8px 24px rgba(197,157,95,.4);
}

.muy-btn-secondary{
  background:rgba(255,255,255,.06);
  color:rgba(232,234,240,.9);
  border:1px solid rgba(255,255,255,.1);
}

.muy-btn[disabled]{
  opacity:.55;
  pointer-events:none;
}

/* ─── Success Modal ─── */
.muy-success{
  position:fixed;
  top:0;left:0;right:0;bottom:0;
  z-index:10000;
  display:none;
  align-items:center;
  justify-content:center;
  background:rgba(10,15,25,.75);
  padding:24px;
}

.muy-success.show{
  display:flex;
  animation:muyFadeIn .3s ease;
}

@keyframes muyFadeIn{
  from{opacity:0}
  to{opacity:1}
}

.muy-success-box{
  padding:36px 28px;
  background:linear-gradient(180deg,#1e2538 0%,#151a28 100%);
  border-radius:32px;
  text-align:center;
  max-width:340px;
  width:100%;
  border:1px solid rgba(197,157,95,.25);
  box-shadow:0 30px 80px rgba(0,0,0,.6);
  animation:muyPop .45s cubic-bezier(.34,1.56,.64,1);
}

@keyframes muyPop{
  0%{transform:scale(.7);opacity:0}
  100%{transform:scale(1);opacity:1}
}

.muy-success-icon{
  width:88px;
  height:88px;
  border-radius:28px;
  margin:0 auto 18px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:44px;
  background:linear-gradient(135deg,#c59d5f 0%,#e8c88a 100%);
  color:#0a0f1e;
  box-shadow:0 12px 32px rgba(197,157,95,.5);
}

.muy-success h3{
  margin:0 0 10px;
  font-size:22px;
  font-weight:900;
  color:#fff;
}

.muy-success p{
  margin:0;
  color:rgba(232,234,240,.7);
  font-size:14px;
  line-height:1.75;
}

/* ─── Responsive ─── */
@media(max-width:380px){
  .muy-banner{padding:20px 16px;padding-bottom:calc(20px + env(safe-area-inset-bottom, 0px));}
  .muy-icon{width:64px;height:64px;font-size:30px;border-radius:20px;}
  .muy-title{font-size:20px;}
  .muy-btn{min-height:50px;font-size:14px;}
  .muy-chip{font-size:12px;padding:6px 12px;}
}

/* ─── Fallback للـ WebView قديمة ─── */
@supports not (backdrop-filter: blur(10px)){
  .muy-overlay{background:rgba(10,15,25,.75);}
}
'''

last_style = html.rfind('</style>')
if last_style > 0 and 'Material You Banner' not in html:
    html = html[:last_style] + css + '\n' + html[last_style:]
    changes += 1
    print("✅ 1/4 CSS مضاف")

# ═══════════════════════════════════════════════════════
# 2) HTML
# ═══════════════════════════════════════════════════════

banner_html = '''
<!-- ═══════ Material You Banner ═══════ -->
<div id="muyOverlay" class="muy-overlay" onclick="hideMuyBanner()"></div>

<div id="muyBanner" class="muy-banner" role="dialog" aria-modal="true">
  <div class="muy-handle"></div>

  <div class="muy-icon-wrap">
    <div class="muy-icon">🚀</div>
  </div>

  <h3 class="muy-title">تحديث جديد متاح</h3>
  <p class="muy-subtitle">نسخة محسّنة مع مزايا جديدة</p>

  <div class="muy-versions">
    <span class="muy-chip muy-chip-old">v<span id="muyOldVer">-</span></span>
    <span class="muy-arrow">←</span>
    <span class="muy-chip muy-chip-new">v<span id="muyNewVer">-</span></span>
  </div>

  <p class="muy-notes" id="muyNotes"></p>

  <div class="muy-progress" id="muyProgress">
    <div class="muy-progress-header">
      <span>⬇️ جارٍ التنزيل</span>
      <span class="muy-percent" id="muyPercent">0%</span>
    </div>
    <div class="muy-progress-track">
      <div class="muy-progress-fill" id="muyProgressFill"></div>
    </div>
  </div>

  <div class="muy-actions" id="muyActions">
    <button class="muy-btn muy-btn-primary" id="muyUpdateBtn" onclick="startMuyUpdate()">
      ⚡ تحديث الآن
    </button>
    <button class="muy-btn muy-btn-secondary" onclick="hideMuyBanner()">
      لاحقًا
    </button>
  </div>
</div>

<div id="muySuccess" class="muy-success">
  <div class="muy-success-box">
    <div class="muy-success-icon">✓</div>
    <h3>اكتمل التنزيل</h3>
    <p>جارٍ فتح المثبّت<br>اتبع التعليمات لإتمام التحديث</p>
  </div>
</div>
'''

last_body = html.rfind('</body>')
if last_body > 0 and 'Material You Banner' not in html:
    html = html[:last_body] + banner_html + '\n' + html[last_body:]
    changes += 1
    print("✅ 2/4 HTML مضاف")

# ═══════════════════════════════════════════════════════
# 3) JavaScript
# ═══════════════════════════════════════════════════════

banner_js = '''
// ═══════════════════════════════════════════
// Material You Banner — JavaScript
// ═══════════════════════════════════════════
let _muyPending = null;

function showMuyBanner(info){
  _muyPending = info;

  const banner = document.getElementById("muyBanner");
  const overlay = document.getElementById("muyOverlay");
  const oldVer = document.getElementById("muyOldVer");
  const newVer = document.getElementById("muyNewVer");
  const notes = document.getElementById("muyNotes");
  const progress = document.getElementById("muyProgress");
  const actions = document.getElementById("muyActions");

  if(!banner || !overlay) return;

  if(oldVer) oldVer.textContent = APP_VERSION;
  if(newVer) newVer.textContent = info.version;
  if(notes) notes.textContent = info.notes || "";

  if(progress) progress.classList.remove("show");
  if(actions) actions.style.display = "flex";

  const btn = document.getElementById("muyUpdateBtn");
  if(btn) btn.disabled = false;

  overlay.classList.add("show");
  banner.classList.add("show");
}

function hideMuyBanner(){
  const banner = document.getElementById("muyBanner");
  const overlay = document.getElementById("muyOverlay");
  if(banner) banner.classList.remove("show");
  if(overlay) overlay.classList.remove("show");
}

function showMuyProgress(percent){
  const progress = document.getElementById("muyProgress");
  const fill = document.getElementById("muyProgressFill");
  const text = document.getElementById("muyPercent");
  const actions = document.getElementById("muyActions");

  if(progress) progress.classList.add("show");
  if(fill) fill.style.width = percent + "%";
  if(text) text.textContent = Math.round(percent) + "%";
  if(actions) actions.style.display = "none";
}

function showMuySuccess(){
  const s = document.getElementById("muySuccess");
  if(s) s.classList.add("show");
}

async function startMuyUpdate(){
  if(!_muyPending || !_muyPending.apkUrl){
    showToast("لا يوجد تحديث");
    return;
  }

  const btn = document.getElementById("muyUpdateBtn");
  if(btn) btn.disabled = true;

  showMuyProgress(5);

  try{
    const ok = await downloadAndInstallApk(
      _muyPending.apkUrl,
      _muyPending.version
    );

    if(ok){
      showMuyProgress(100);
      setTimeout(function(){
        showMuySuccess();
        setTimeout(function(){
          const s = document.getElementById("muySuccess");
          if(s) s.classList.remove("show");
          hideMuyBanner();
        }, 3500);
      }, 500);
    }else{
      hideMuyBanner();
    }
  }catch(e){
    console.error(e);
    hideMuyBanner();
  }
}

'''

anchor = "async function downloadAndInstallApk"
if anchor in html and "showMuyBanner" not in html:
    html = html.replace(anchor, banner_js + anchor, 1)
    changes += 1
    print("✅ 3/4 JS أُضيف")

# ═══════════════════════════════════════════════════════
# 4) استبدال confirm في checkForAppUpdate
# ═══════════════════════════════════════════════════════

# نحذف القديم إن وُجد
old_confirm_1 = '''    if(isForced || confirm(message)){
      if(info.apkUrl){
        // ⭐ استخدام التنزيل داخل التطبيق
        await downloadAndInstallApk(info.apkUrl, info.version);
      }
    }'''

old_confirm_2 = '''    // ⭐ عرض البانر الحديث
    showUpdateBanner(info);'''

new_banner_call = '''    // ⭐ عرض بانر Material You
    showMuyBanner(info);'''

replaced = False

if old_confirm_1 in html:
    html = html.replace(old_confirm_1, new_banner_call, 1)
    replaced = True
    print("✅ 4/4 confirm ← showMuyBanner")
elif old_confirm_2 in html:
    html = html.replace(old_confirm_2, new_banner_call, 1)
    replaced = True
    print("✅ 4/4 showUpdateBanner ← showMuyBanner")
else:
    print("⚠️ 4/4 لم يُعثر على أي من النمطين")

if replaced:
    changes += 1

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n{'='*50}")
print(f"✅ {changes} تعديلات مطبّقة")
print(f"{'='*50}")
