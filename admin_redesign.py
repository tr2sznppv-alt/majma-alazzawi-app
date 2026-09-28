from pathlib import Path

path = Path("www/index.html")
s = path.read_text()

# 1) زر الإعدادات العامة
s = s.replace(
    '<button class="header-icon" onclick="openAdmin()">⚙️</button>',
    '<button class="header-icon" onclick="openSettings()" aria-label="إعدادات التطبيق">⚙️</button>',
    1
)

# 2) جعل legacyOpenAdmin آمناً
old = '''function legacyOpenAdmin(){
 renderAdmin();
 document.getElementById("adminModal").classList.add("show");
}'''

new = '''function legacyOpenAdmin(){
 openAdmin();
}'''

if old in s:
    s = s.replace(old, new, 1)

# 3) حماية لوحة الإدارة
old = '''function openAdmin(){
 if(!currentUser){
  document.getElementById("loginMessage").textContent =
   "هذه المنطقة مخصصة للمسؤول والمشرفين.";
  document.getElementById("loginModal").classList.add("show");
  return;
 }
 if(!currentUser.active){
  showToast("هذا الحساب غير مفعل");
  return;
 }
 renderAdmin();
 document.getElementById("adminModal").classList.add("show");
}'''

new = '''function isManagementUser(){
 if(!currentUser || !currentUser.active) return false;
 return ["OWNER","ADMIN","MANAGER","EMPLOYEE"].includes(currentUser.role);
}

function openAdmin(){
 if(!currentUser){
  document.getElementById("loginMessage").textContent =
   "هذه المنطقة مخصصة للمسؤول وموظفي الإدارة.";
  document.getElementById("loginModal").classList.add("show");
  return;
 }

 if(!currentUser.active){
  showToast("هذا الحساب غير مفعل");
  return;
 }

 if(!isManagementUser()){
  showToast("ليس لديك صلاحية الدخول إلى الإدارة");
  return;
 }

 renderAdmin();
 document.getElementById("adminModal").classList.add("show");
}'''

if old in s:
    s = s.replace(old, new, 1)
else:
    print("WARNING: openAdmin block not found")

# 4) استبدال renderAdmin
start = s.find("function renderAdmin(){")

if start != -1:
    end = s.find("\nfunction ", start + 10)

    if end == -1:
        end = s.find("\n</script>", start)

    if end != -1:
        render = '''function renderAdmin(){
 const accountName=document.getElementById("adminAccountName");
 const accountRole=document.getElementById("adminAccountRole");
 const manageStaffBtn=document.getElementById("manageStaffBtn");

 if(accountName && accountRole && manageStaffBtn){
  if(currentUser){
   accountName.textContent =
    (currentUser.role==="OWNER" ? "👑 " : "🛠️ ") +
    (currentUser.name || currentUser.username);

   const roleNames={
    OWNER:"المسؤول الرئيسي",
    ADMIN:"مشرف إداري",
    MANAGER:"مدير",
    EMPLOYEE:"موظف",
    CUSTOMER:"عميل"
   };

   accountRole.textContent =
    roleNames[currentUser.role] || "حساب مستخدم";

   manageStaffBtn.style.display =
    hasPermission("manageStaff")
     ? "inline-block"
     : "none";
  }else{
   accountName.textContent="👤 غير مسجل الدخول";
   accountRole.textContent="";
   manageStaffBtn.style.display="none";
  }
 }

 const box=document.getElementById("adminList");
 if(!box)return;

 box.innerHTML="";

 if(!products.length){
  box.innerHTML="<p>لا توجد منتجات.</p>";
  return;
 }

 const canEdit=hasPermission("editProduct");
 const canDelete=hasPermission("deleteProduct");

 products.forEach((p,i)=>{
  const div=document.createElement("div");
  div.className="admin-item";

  div.innerHTML=`
   <img src="${escapeHtml(p.image || PLACEHOLDER)}"
    onerror="this.src='${PLACEHOLDER}'">

   <div class="admin-info">
    <strong>${escapeHtml(p.name)}</strong>
    <small>${money(p.price)}</small>
   </div>

   <div class="admin-actions">
    ${
     canEdit
      ? `<button class="edit-btn" onclick="editProduct(${i})">تعديل</button>`
      : ""
    }

    ${
     canDelete
      ? `<button class="delete-btn" onclick="deleteProduct(${i})">حذف</button>`
      : ""
    }
   </div>
  `;

  box.appendChild(div);
 });
}'''

        s = s[:start] + render + s[end:]
    else:
        print("WARNING: renderAdmin end not found")
else:
    print("WARNING: renderAdmin not found")

# 5) إعدادات عامة
marker = '<div id="toast" class="toast"></div>'

settings = r'''
<!-- إعدادات التطبيق العامة -->
<div id="settingsModal"
 class="modal"
 onclick="closeOnBackground(event,'settingsModal')">

 <div class="modal-content">

  <div class="modal-header">
   <h2>⚙️ إعدادات التطبيق</h2>
   <button class="close"
    onclick="closeModal('settingsModal')">×</button>
  </div>

  <div class="role-card">

   <strong>🎨 تخصيص المظهر</strong>

   <small style="display:block;margin-top:5px;color:var(--muted);">
    تخصيص ألوان وخط وشكل واجهة التطبيق.
   </small>

   <label>🎨 اللون الرئيسي</label>
   <input id="publicThemePrimary" type="color" value="#111827">

   <label>✨ لون التمييز</label>
   <input id="publicThemeAccent" type="color" value="#c59d5f">

   <label>🌈 لون الخلفية</label>
   <input id="publicThemeBg" type="color" value="#f5f6f8">

   <label>🃏 لون البطاقات</label>
   <input id="publicThemeCard" type="color" value="#ffffff">

   <label>🏷️ اسم التطبيق</label>
   <input id="publicThemeAppName" type="text"
    placeholder="اسم التطبيق">

   <label>📝 الوصف أسفل الاسم</label>
   <input id="publicThemeAppSubtitle" type="text"
    placeholder="وصف التطبيق">

   <label>🖼️ شعار التطبيق</label>

   <input id="publicThemeLogo" type="text"
    placeholder="رابط صورة الشعار - اختياري">

   <input id="publicThemeLogoFile"
    type="file"
    accept="image/*"
    onchange="previewLogoFile(event)">

   <div id="logoPreview"
    style="margin-top:10px;text-align:center;display:none;">

    <img id="logoPreviewImage"
     alt="معاينة الشعار"
     style="width:90px;height:90px;object-fit:contain;border-radius:18px;">
   </div>

   <button type="button"
    class="secondary-btn"
    onclick="clearLogo()">
    🗑️ إزالة الشعار
   </button>

   <label>🔤 حجم الخط</label>

   <select id="publicThemeFontSize">
    <option value="14px">صغير</option>
    <option value="16px" selected>متوسط</option>
    <option value="18px">كبير</option>
    <option value="20px">كبير جدًا</option>
   </select>

   <label>🔘 شكل الأزرار</label>

   <select id="publicThemeButtonStyle">
    <option value="rounded">مستدير</option>
    <option value="soft">ناعم</option>
    <option value="pill">كبسولة</option>
    <option value="square">مربع أنيق</option>
   </select>

   <label>🌓 نمط التطبيق</label>

   <select id="publicThemeMode">
    <option value="light">فاتح</option>
    <option value="dark">داكن</option>
   </select>

   <button type="button"
    class="primary-btn"
    onclick="saveAppearanceSettings()">
    💾 حفظ إعدادات المظهر
   </button>

   <button type="button"
    class="secondary-btn"
    onclick="resetAppearanceSettings()">
    ↩️ استعادة الافتراضي
   </button>

  </div>

 </div>
</div>
'''

if marker in s and 'id="settingsModal"' not in s:
    s = s.replace(marker, settings + "\n" + marker, 1)

# 6) وظائف المظهر
script_marker = '''/* ================================
   نظام الأدوار والصلاحيات'''

appearance = r'''
/* ================================
   إعدادات المظهر العامة
   ================================ */

const DEFAULT_THEME={
 primary:"#111827",
 accent:"#c59d5f",
 bg:"#f5f6f8",
 card:"#ffffff",
 appName:"كتالوج المنتجات",
 appSubtitle:"منتجات مجمع العزاوي",
 logo:"",
 fontSize:"16px",
 buttonStyle:"rounded",
 mode:"light"
};

function getTheme(){
 try{
  return {
   ...DEFAULT_THEME,
   ...(JSON.parse(localStorage.getItem("appTheme") || "{}"))
  };
 }catch(e){
  return {...DEFAULT_THEME};
 }
}

function applyTheme(theme){
 if(!theme) theme=getTheme();

 document.documentElement.style.setProperty(
  "--primary",theme.primary
 );

 document.documentElement.style.setProperty(
  "--accent",theme.accent
 );

 document.documentElement.style.setProperty(
  "--bg",theme.bg
 );

 document.documentElement.style.setProperty(
  "--card",theme.card
 );

 document.documentElement.style.setProperty(
  "--font-size",theme.fontSize
 );

 document.documentElement.setAttribute(
  "data-theme",theme.mode
 );

 document.body.style.fontSize=theme.fontSize;

 document.body.classList.remove(
  "button-style-rounded",
  "button-style-soft",
  "button-style-pill",
  "button-style-square"
 );

 document.body.classList.add(
  "button-style-"+(theme.buttonStyle || "rounded")
 );

 const title=document.querySelector(
  ".app-title,.brand-title"
 );

 if(title && theme.appName)
  title.textContent=theme.appName;

 const subtitle=document.querySelector(
  ".app-subtitle,.brand-subtitle"
 );

 if(subtitle && theme.appSubtitle)
  subtitle.textContent=theme.appSubtitle;

 const logo=document.querySelector(
  ".app-logo,.brand-logo"
 );

 if(logo && theme.logo){
  logo.src=theme.logo;
  logo.style.display="block";
 }
}

function loadTheme(){
 const theme=getTheme();
 applyTheme(theme);
 return theme;
}

function syncAppearanceFields(){
 const theme=getTheme();

 const fields={
  publicThemePrimary:theme.primary,
  publicThemeAccent:theme.accent,
  publicThemeBg:theme.bg,
  publicThemeCard:theme.card,
  publicThemeAppName:theme.appName,
  publicThemeAppSubtitle:theme.appSubtitle,
  publicThemeLogo:theme.logo,
  publicThemeFontSize:theme.fontSize,
  publicThemeButtonStyle:theme.buttonStyle,
  publicThemeMode:theme.mode,

  themePrimary:theme.primary,
  themeAccent:theme.accent,
  themeBg:theme.bg,
  themeCard:theme.card,
  themeAppName:theme.appName,
  themeAppSubtitle:theme.appSubtitle,
  themeLogo:theme.logo,
  themeFontSize:theme.fontSize,
  themeButtonStyle:theme.buttonStyle,
  themeMode:theme.mode
 };

 Object.entries(fields).forEach(([id,value])=>{
  const el=document.getElementById(id);
  if(el) el.value=value;
 });

 if(theme.logo){
  const preview=document.getElementById("logoPreview");
  const img=document.getElementById("logoPreviewImage");

  if(preview && img){
   img.src=theme.logo;
   preview.style.display="block";
  }
 }
}

function openSettings(){
 syncAppearanceFields();

 const modal=document.getElementById("settingsModal");

 if(modal)
  modal.classList.add("show");
}

function toggleAppearanceSettings(){
 const panel=document.getElementById("appearancePanel");

 if(!panel)return;

 panel.style.display =
  panel.style.display==="none" || !panel.style.display
   ? "block"
   : "none";

 syncAppearanceFields();
}

function readAppearanceFields(){
 const theme=getTheme();

 const get=(a,b)=>{
  const x=document.getElementById(a);
  if(x) return x.value;

  const y=document.getElementById(b);
  if(y) return y.value;

  return "";
 };

 theme.primary=get("publicThemePrimary","themePrimary") || theme.primary;
 theme.accent=get("publicThemeAccent","themeAccent") || theme.accent;
 theme.bg=get("publicThemeBg","themeBg") || theme.bg;
 theme.card=get("publicThemeCard","themeCard") || theme.card;

 theme.appName=
  get("publicThemeAppName","themeAppName") ||
  DEFAULT_THEME.appName;

 theme.appSubtitle=
  get("publicThemeAppSubtitle","themeAppSubtitle") ||
  DEFAULT_THEME.appSubtitle;

 theme.logo=get("publicThemeLogo","themeLogo");

 theme.fontSize=
  get("publicThemeFontSize","themeFontSize") ||
  DEFAULT_THEME.fontSize;

 theme.buttonStyle=
  get("publicThemeButtonStyle","themeButtonStyle") ||
  DEFAULT_THEME.buttonStyle;

 theme.mode=
  get("publicThemeMode","themeMode") ||
  DEFAULT_THEME.mode;

 return theme;
}

function saveAppearanceSettings(){
 const theme=readAppearanceFields();

 localStorage.setItem(
  "appTheme",
  JSON.stringify(theme)
 );

 applyTheme(theme);
 syncAppearanceFields();

 showToast("تم حفظ إعدادات المظهر ✅");
}

function resetAppearanceSettings(){
 if(!confirm("هل تريد استعادة المظهر الافتراضي؟"))
  return;

 localStorage.setItem(
  "appTheme",
  JSON.stringify(DEFAULT_THEME)
 );

 applyTheme(DEFAULT_THEME);
 syncAppearanceFields();

 showToast("تم استعادة المظهر الافتراضي");
}

function previewLogoFile(event){
 const file=event.target.files?.[0];

 if(!file)return;

 if(!file.type.startsWith("image/")){
  showToast("اختر ملف صورة صالح");
  return;
 }

 const reader=new FileReader();

 reader.onload=function(){
  const value=reader.result;

  const input=
   document.getElementById("publicThemeLogo") ||
   document.getElementById("themeLogo");

  if(input)
   input.value=value;

  const preview=document.getElementById("logoPreview");
  const img=document.getElementById("logoPreviewImage");

  if(preview && img){
   img.src=value;
   preview.style.display="block";
  }
 };

 reader.readAsDataURL(file);
}

function clearLogo(){
 const a=document.getElementById("publicThemeLogo");
 const b=document.getElementById("themeLogo");

 if(a)a.value="";
 if(b)b.value="";

 const preview=document.getElementById("logoPreview");
 if(preview)preview.style.display="none";

 const img=document.getElementById("logoPreviewImage");
 if(img)img.removeAttribute("src");
}

loadTheme();

'''

if script_marker in s and 'function getTheme()' not in s:
    s=s.replace(script_marker,appearance+script_marker,1)

path.write_text(s)
print("OK: تم تعديل index.html بنجاح")
