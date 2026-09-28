import sys, os, shutil
from datetime import datetime

FILE = "www/index.html"

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
os.makedirs(f'backups/cloud-admin-{stamp}', exist_ok=True)
shutil.copy(FILE, f'backups/cloud-admin-{stamp}/index.html.before')
print(f"backup: backups/cloud-admin-{stamp}/")

with open(FILE, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# ═══════════════════════════════════════════════════════
# 1) استبدال loginAdmin (منطق أنظف: السحابة أولًا)
# ═══════════════════════════════════════════════════════

start_marker = "async function loginAdmin(){"
end_marker = "\nfunction logoutAdmin()"

if start_marker in html and end_marker in html:
    s = html.find(start_marker)
    e = html.find(end_marker, s)
    
    if s > 0 and e > s:
        new_login = '''async function loginAdmin(){

 const username = document.getElementById("loginUsername").value.trim();
 const password = document.getElementById("loginPassword").value;

 if(!username || !password){
  showToast("أدخل اسم المستخدم وكلمة المرور");
  return;
 }

 // 1) جرب السحابة أولًا
 let user = null;
 const cloudUser = await cloudLogin(username, password);

 if(cloudUser){
  user = cloudUser;
 }else{
  // 2) fallback محلي (للعمل بدون إنترنت)
  const localUser = authUsers.find(function(u){
   return u.username === username &&
          u.active !== false &&
          u.password === password;
  });
  if(localUser){
   user = localUser;
  }
 }

 if(!user){
  showToast("اسم المستخدم أو كلمة المرور غير صحيحة");
  return;
 }

 // 3) احفظ الجلسة
 currentUser = user;
 localStorage.setItem("currentUser", JSON.stringify(user));

 // 4) مسح الحقول
 document.getElementById("loginUsername").value = "";
 document.getElementById("loginPassword").value = "";

 closeModal("loginModal");

 if(!isManagementUser()){
  showToast("ليس لديك صلاحية الدخول إلى الإدارة");
  return;
 }

 showToast(
  user.role === "OWNER"
   ? "مرحبًا بك أيها المسؤول الرئيسي 👑"
   : "تم تسجيل الدخول بنجاح ✅"
 );
}
'''
        html = html[:s] + new_login + html[e+1:]
        changes += 1
        print("✅ 1/5 loginAdmin محدّث")
    else:
        print("❌ loginAdmin: لم يتم العثور على النهاية")
else:
    print("❌ loginAdmin: لم يُعثر على البداية")

# ═══════════════════════════════════════════════════════
# 2) استبدال syncUsersFromServer (السحابة مصدر أساسي)
# ═══════════════════════════════════════════════════════

start_marker = "async function syncUsersFromServer(){"
end_marker = "async function cloudLogin("

if start_marker in html and end_marker in html:
    s = html.find(start_marker)
    e = html.find(end_marker, s)
    
    if s > 0 and e > s:
        new_sync = '''async function syncUsersFromServer(){
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
  if(!data.success || !Array.isArray(data.users)) return false;

  // السحابة مصدر أساسي
  authUsers = data.users.map(function(u){
   return {
    id: u.id,
    username: u.username,
    name: u.name,
    role: u.role,
    active: u.active !== false,
    permissions: u.permissions || {}
   };
  });

  localStorage.setItem("authUsers", JSON.stringify(authUsers));
  console.log("✅ مزامنة " + authUsers.length + " حساب من السحابة");
  return true;

 }catch(e){
  console.warn("فشل تحميل المستخدمين:", e);
  return false;
 }
}

'''
        html = html[:s] + new_sync + html[e:]
        changes += 1
        print("✅ 2/5 syncUsersFromServer محدّث")
    else:
        print("❌ sync: لم يتم العثور على النهاية")
else:
    print("❌ sync: لم يُعثر على البداية")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n{'='*50}")
print(f"✅ {changes} تعديلات مطبّقة")
print(f"{'='*50}")
