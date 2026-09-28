import os, shutil
from datetime import datetime

FILE = "www/index.html"

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
os.makedirs(f'backups/admin-ui-{stamp}', exist_ok=True)
shutil.copy(FILE, f'backups/admin-ui-{stamp}/index.html.before')
print(f"backup: backups/admin-ui-{stamp}/")

with open(FILE, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

cloud_helpers = '''

// دوال إدارة المستخدمين السحابية

async function cloudChangePassword(userId, newPassword){
 try{
  const res = await fetch(USERS_URL + "/change-password", {
   method:"POST",
   headers:{
    "Content-Type":"application/json",
    "apikey": window.CATALOG_API_KEY || ""
   },
   body:JSON.stringify({ userId: userId, newPassword: newPassword })
  });
  const data = await res.json();
  return data.success === true;
 }catch(e){
  console.warn("cloudChangePassword error:", e);
  return false;
 }
}

async function cloudUpdateUser(userId, updates){
 try{
  const res = await fetch(USERS_URL + "/" + encodeURIComponent(userId), {
   method:"PUT",
   headers:{
    "Content-Type":"application/json",
    "apikey": window.CATALOG_API_KEY || ""
   },
   body:JSON.stringify(updates)
  });
  const data = await res.json();
  return data.success === true;
 }catch(e){
  console.warn("cloudUpdateUser error:", e);
  return false;
 }
}

async function cloudDeleteUser(userId){
 try{
  const res = await fetch(USERS_URL + "/" + encodeURIComponent(userId), {
   method:"DELETE",
   headers:{
    "apikey": window.CATALOG_API_KEY || ""
   }
  });
  const data = await res.json();
  return data.success === true;
 }catch(e){
  console.warn("cloudDeleteUser error:", e);
  return false;
 }
}

async function adminChangePassword(userId, username){
 if(!currentUser || currentUser.role !== "OWNER"){
  showToast("المسؤول الرئيسي فقط");
  return;
 }
 const newPass = prompt("كلمة مرور جديدة ل " + username + ":");
 if(!newPass) return;
 if(newPass.length < 4){
  showToast("كلمة المرور قصيرة");
  return;
 }
 const ok = await cloudChangePassword(userId, newPass);
 if(ok){
  showToast("تم تغيير كلمة المرور");
 }else{
  showToast("فشل تغيير كلمة المرور");
 }
}

async function adminToggleActive(userId, username, currentActive){
 if(!currentUser || currentUser.role !== "OWNER"){
  showToast("المسؤول الرئيسي فقط");
  return;
 }
 const newActive = !currentActive;
 const label = newActive ? "تفعيل" : "تعطيل";
 if(!confirm("هل تريد " + label + " حساب " + username + "?")) return;
 const ok = await cloudUpdateUser(userId, { active: newActive });
 if(ok){
  showToast("تم " + label + " الحساب");
  await syncUsersFromServer();
  renderRoles();
 }else{
  showToast("فشل " + label + " الحساب");
 }
}

async function adminDeleteUser(userId, username){
 if(!currentUser || currentUser.role !== "OWNER"){
  showToast("المسؤول الرئيسي فقط");
  return;
 }
 if(!confirm("حذف حساب " + username + " نهائيا?")) return;
 const ok = await cloudDeleteUser(userId);
 if(ok){
  showToast("تم حذف الحساب");
  await syncUsersFromServer();
  renderRoles();
 }else{
  showToast("فشل حذف الحساب");
 }
}

'''

anchor = "async function cloudLogin("
if anchor in html and "cloudChangePassword" not in html:
    html = html.replace(anchor, cloud_helpers + anchor, 1)
    changes += 1
    print("OK: 1/2 cloud functions added")
else:
    print("WARN: 1/2 skipped")

old_delete = '''         <button
          class="delete-btn"
          style="margin-top:12px;"
          onclick="removeStaff('${u.id}')"
         >
          🗑️ إزالة الحساب
         </button>'''

new_delete = '''         <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px;">

          <button
           class="edit-btn"
           style="flex:1;min-width:100px;"
           onclick="adminChangePassword('${u.id}','${escapeHtml(u.username)}')"
          >
           PASS
          </button>

          <button
           class="edit-btn"
           style="flex:1;min-width:100px;background:${u.active ? '#f59e0b' : '#16a34a'};"
           onclick="adminToggleActive('${u.id}','${escapeHtml(u.username)}',${u.active ? 'true' : 'false'})"
          >
           ${u.active ? 'OFF' : 'ON'}
          </button>

          <button
           class="delete-btn"
           style="flex:1;min-width:100px;"
           onclick="adminDeleteUser('${u.id}','${escapeHtml(u.username)}')"
          >
           DEL
          </button>

         </div>'''

if old_delete in html:
    html = html.replace(old_delete, new_delete, 1)
    changes += 1
    print("OK: 2/2 buttons added")
else:
    print("WARN: 2/2 skipped")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print("===")
print(f"Applied: {changes}")
print("===")
