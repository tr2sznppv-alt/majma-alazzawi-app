import sys, os, shutil, re
from datetime import datetime

FILE = "www/index.html"

if not os.path.exists(FILE):
    print("❌ لم يُعثر على الملف")
    sys.exit(1)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = f"backups/users-cloud-2-{stamp}"
os.makedirs(backup_dir, exist_ok=True)
shutil.copy(FILE, f"{backup_dir}/index.html.before")
print(f"📦 نسخة احتياطية في: {backup_dir}/")

with open(FILE, "r", encoding="utf-8") as f:
    html = f.read()

changes = 0

# ═══════════════════════════════════════════════════
# 1) تحويل addStaff إلى async + إضافة المزامنة السحابية
# ═══════════════════════════════════════════════════

# 1-a) تحويل الدالة إلى async
old_1a = "function addStaff(){"
new_1a = "async function addStaff(){"

if old_1a in html and "async function addStaff" not in html:
    html = html.replace(old_1a, new_1a, 1)
    changes += 1
    print("✅ 1/3a تحويل addStaff إلى async")
else:
    print("⚠️ 1/3a addStaff: لم يُطابق أو معدّل مسبقًا")

# 1-b) إضافة كود المزامنة في نهاية addStaff
# نبحث عن آخر السطر: authUsers.push({...}) ثم localStorage
# لنجد نهاية دالة addStaff، نبحث عن showToast داخل addStaff

# النمط: آخر استدعاء لـ renderRoles() داخل addStaff
anchor_addStaff = """ localStorage.setItem(
  "authUsers",
  JSON.stringify(authUsers)
 );

 showToast(
  role==="CUSTOMER"
   ? "تم إنشاء حساب العميل ✅"
   : "تم إنشاء الحساب الإداري ✅"
 );

 renderRoles();
}"""

sync_code = """ localStorage.setItem(
  "authUsers",
  JSON.stringify(authUsers)
 );

 showToast(
  role==="CUSTOMER"
   ? "تم إنشاء حساب العميل ✅"
   : "تم إنشاء الحساب الإداري ✅"
 );

 renderRoles();

 // مزامنة الحساب مع السحابة
 try{
  const res = await fetch(USERS_URL, {
   method: "POST",
   headers: {
    "Content-Type": "application/json",
    "apikey": window.CATALOG_API_KEY || ""
   },
   body: JSON.stringify({
    username: username,
    password: password,
    name: name,
    role: role,
    permissions: getRolePermissions(role)
   })
  });

  const data = await res.json();

  if(data.success){
   console.log("✅ تم رفع الحساب للسحابة");
  }else{
   console.warn("فشل رفع الحساب للسحابة:", data.error);
  }
 }catch(e){
  console.warn("تعذر رفع الحساب للسحابة:", e);
 }
}"""

if anchor_addStaff in html and "تم رفع الحساب للسحابة" not in html:
    html = html.replace(anchor_addStaff, sync_code, 1)
    changes += 1
    print("✅ 1/3b إضافة المزامنة في addStaff")
else:
    print("⚠️ 1/3b addStaff: النمط لم يُطابق")

# ═══════════════════════════════════════════════════
# 2) تعديل loginAdmin للبحث في السحابة
# ═══════════════════════════════════════════════════

old_2 = """ const user=authUsers.find(u=>
  u.username===username &&
  u.active
 );

 if(!user){
  showToast("اسم المستخدم غير موجود أو غير نشط");
  return;
 }"""

new_2 = """ // 1) ابحث محليًا
 let user = authUsers.find(function(u){
  return u.username === username && u.active;
 });

 // 2) إن لم يُوجد — ابحث في السحابة
 if(!user){
  const cloudUser = await cloudLogin(username, password);

  if(cloudUser){
   user = cloudUser;

   // أضفه محليًا للمرات القادمة
   const exists = authUsers.find(function(u){
    return u.username === cloudUser.username;
   });

   if(!exists){
    authUsers.push({
     id: cloudUser.id,
     username: cloudUser.username,
     name: cloudUser.name,
     role: cloudUser.role,
     active: true,
     permissions: cloudUser.permissions || {}
    });
    localStorage.setItem("authUsers", JSON.stringify(authUsers));
   }
  }
 }

 if(!user){
  showToast("اسم المستخدم غير موجود أو غير نشط");
  return;
 }"""

if old_2 in html and "ابحث في السحابة" not in html:
    html = html.replace(old_2, new_2, 1)
    changes += 1
    print("✅ 2/3 تعديل loginAdmin")
else:
    print("⚠️ 2/3 loginAdmin: النمط لم يُطابق")

# ═══════════════════════════════════════════════════
# 3) مزامنة المستخدمين عند بدء التطبيق
# ═══════════════════════════════════════════════════

old_3 = """initAuth();
render();"""

new_3 = """initAuth();

// مزامنة المستخدمين من السحابة قبل الرسم
(async function(){
 await syncUsersFromServer();
 render();
})();"""

# يجب استبدال أول ظهور فقط (في نهاية الملف)
if old_3 in html and "await syncUsersFromServer();" not in html:
    html = html.replace(old_3, new_3, 1)
    changes += 1
    print("✅ 3/3 مزامنة عند البدء")
else:
    print("⚠️ 3/3 لم يُطابق")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n{'='*50}")
print(f"✅ {changes} تعديلات إضافية")
print(f"{'='*50}")
