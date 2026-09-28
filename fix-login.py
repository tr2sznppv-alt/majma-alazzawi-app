import sys, os, shutil
from datetime import datetime

SOURCE = "www/index.html"
TARGET = "android/app/src/main/assets/public/index.html"

if not os.path.exists(SOURCE):
    print("❌ لم يُعثر على www/index.html")
    sys.exit(1)

# نسخة احتياطية
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = f"backups/login-fix-{stamp}"
os.makedirs(backup_dir, exist_ok=True)
shutil.copy(SOURCE, f"{backup_dir}/index.html.before")
print(f"📦 نسخة احتياطية في: {backup_dir}/")

with open(SOURCE, "r", encoding="utf-8") as f:
    html = f.read()

changes = 0

# ---- 1) loginApiAdmin: تمييز رفض الخادم عن انقطاع الشبكة ----
old1 = """  if(!response.ok || !data || !data.success || !data.token){
   return {
    success:false,
    error:data?.error || ("HTTP " + response.status)
   };
  }"""
new1 = """  if(!response.ok || !data || !data.success || !data.token){
   return {
    success:false,
    serverResponded:true,
    error:data?.error || ("HTTP " + response.status)
   };
  }"""
if old1 in html:
    html = html.replace(old1, new1, 1)
    changes += 1
    print("✅ 1/3 loginApiAdmin (رفض الخادم)")

# ---- 2) catch في loginApiAdmin ----
old2 = """ }catch(error){
  console.error("API login error:",error);
  return {
   success:false,
   error:"تعذر الاتصال بخادم الإدارة"
  };
 }"""
new2 = """ }catch(error){
  console.error("API login error:",error);
  return {
   success:false,
   serverResponded:false,
   error:"تعذر الاتصال بخادم الإدارة"
  };
 }"""
if old2 in html:
    html = html.replace(old2, new2, 1)
    changes += 1
    print("✅ 2/3 catch loginApiAdmin")

# ---- 3) منطق loginAdmin: الموظف يدخل محليًا ----
old3 = """ // المستخدم الإداري يجب أن ينجح في توثيق الخادم
 const apiLogin=await loginApiAdmin(username,password);

 if(!apiLogin.success){
  showToast(
   apiLogin.error ||
   "تعذر التحقق من بيانات الإدارة"
  );
  return;
 }"""
new3 = """ // المالك فقط يجب أن ينجح توثيقه على الخادم
 if(user.role==="OWNER"){
  const apiLogin=await loginApiAdmin(username,password);

  if(!apiLogin.success){
   if(apiLogin.serverResponded){
    showToast(apiLogin.error || "بيانات الدخول مرفوضة من الخادم");
    return;
   }
   console.warn("الخادم غير متاح، تسجيل دخول المالك محليًا");
  }
 }else{
  // الموظفون: محاولة صامتة، لا تمنع الدخول
  loginApiAdmin(username,password).catch(()=>{});
 }"""
if old3 in html:
    html = html.replace(old3, new3, 1)
    changes += 1
    print("✅ 3/3 منطق loginAdmin")

# ---- 4) نظام رقم الإصدار ----
if "APP_VERSION" not in html:
    version_block = """const APP_VERSION = "1.1.0";

"""
    anchor = "const DEFAULT_WHATSAPP"
    if anchor in html:
        html = html.replace(anchor, version_block + anchor, 1)
        changes += 1
        print("✅ 4/4 إضافة APP_VERSION")

with open(SOURCE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n{'='*50}")
print(f"✅ {changes} تعديلات على {SOURCE}")

if os.path.exists(TARGET):
    shutil.copy(SOURCE, TARGET)
    print(f"✅ نُسخ إلى مجلد Android")
print(f"{'='*50}")
