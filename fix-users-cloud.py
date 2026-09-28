import sys, os, shutil, re
from datetime import datetime

FILE = "www/index.html"
TARGET = "android/app/src/main/assets/public/index.html"

if not os.path.exists(FILE):
    print("❌ لم يُعثر على www/index.html")
    sys.exit(1)

# نسخة احتياطية
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = f"backups/users-cloud-{stamp}"
os.makedirs(backup_dir, exist_ok=True)
shutil.copy(FILE, f"{backup_dir}/index.html.before")
print(f"📦 نسخة احتياطية في: {backup_dir}/")

with open(FILE, "r", encoding="utf-8") as f:
    html = f.read()

changes = 0

# ═══════════════════════════════════════════════════
# 1) إضافة USERS_URL بعد UPDATE_URL
# ═══════════════════════════════════════════════════
anchor1 = 'const UPDATE_URL ='
if anchor1 not in html:
    print("❌ لم يُعثر على UPDATE_URL")
    sys.exit(2)

# ابحث عن نهاية تعريف UPDATE_URL
pattern = r'(const UPDATE_URL =\s*"[^"]+";)'
match = re.search(pattern, html)
if match and 'USERS_URL' not in html:
    insertion = match.group(1) + '\n\nconst USERS_URL =\n  "https://vkjsynailhrjtfbzysjn.supabase.co/functions/v1/users";'
    html = html.replace(match.group(1), insertion, 1)
    changes += 1
    print("✅ 1/5 أُضيف USERS_URL")

# ═══════════════════════════════════════════════════
# 2) إضافة دالة syncUsersFromServer + cloudLogin
# ═══════════════════════════════════════════════════
cloud_functions = '''

// ═══════════════════════════════════════════════════
// مزامنة المستخدمين من السحابة (Supabase)
// ═══════════════════════════════════════════════════
async function syncUsersFromServer(){
 try{
  const res = await fetch(
   USERS_URL + "?t=" + Date.now(),
   {
    cache:"no-store",
    headers:{ "apikey": window.CATALOG_API_KEY || "" }
   }
  );
  if(!res.ok) return false;

  const data = await res.json();
  if(!data.success) return false;

  const cloudUsers = Array.isArray(data.users) ? data.users : [];
  const localUsers = Array.isArray(authUsers) ? authUsers : [];

  const merged = [];

  // 1) أضف حساب OWNER المحلي أولًا
  localUsers.forEach(function(u){
   if(u && u.role === "OWNER"){
    merged.push(u);
   }
  });

  // 2) أضف حسابات السحابة
  cloudUsers.forEach(function(u){
   if(u && u.role !== "OWNER"){
    // احذف كلمة المرور من النسخة المحلية إن وُجدت
    const clean = {
     id: u.id,
     username: u.username,
     name: u.name,
     role: u.role,
     active: u.active !== false,
     permissions: u.permissions || {}
    };
    merged.push(clean);
   }
  });

  // 3) أضف بقية المحليين (غير OWNER وغير الموجودين في السحابة)
  localUsers.forEach(function(local){
   if(!local || local.role === "OWNER") return;
   const exists = cloudUsers.find(function(c){
    return c.username === local.username;
   });
   if(!exists) merged.push(local);
  });

  authUsers = merged;
  localStorage.setItem("authUsers", JSON.stringify(authUsers));

  console.log("✅ تمت مزامنة " + cloudUsers.length + " حساب من السحابة");
  return true;

 }catch(e){
  console.warn("فشل تحميل المستخدمين من السحابة:", e);
  return false;
 }
}

async function cloudLogin(username, password){
 try{
  const res = await fetch(
   USERS_URL + "/login",
   {
    method:"POST",
    headers:{
     "Content-Type":"application/json",
     "apikey": window.CATALOG_API_KEY || ""
    },
    body:JSON.stringify({ username, password })
   }
  );

  const data = await res.json();
  if(!data.success || !data.user) return null;

  return data.user;

 }catch(e){
  console.warn("فشل التحقق من السحابة:", e);
  return null;
 }
}

'''

# ابحث عن تعريف دالة checkForAppUpdate وأدرج قبله
anchor2 = 'async function checkForAppUpdate'
if anchor2 in html and 'syncUsersFromServer' not in html:
    html = html.replace(anchor2, cloud_functions + anchor2, 1)
    changes += 1
    print("✅ 2/5 أُضيفت syncUsersFromServer + cloudLogin")
else:
    print("⚠️ 2/5 لم يُطابق موضع الدوال")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n{'='*50}")
print(f"✅ {changes} تعديلات مطبّقة على {FILE}")
print(f"⚠️  الآن طبّق التعديلات اليدوية (راجع الرسالة)")
print(f"{'='*50}")
