from pathlib import Path

path = Path("www/index.html")
text = path.read_text(encoding="utf-8")

marker = '<div id="toast" class="toast"></div>'

insert = r'''
<!-- نظام الحسابات والصلاحيات -->
<div id="loginModal" class="modal" onclick="closeOnBackground(event,'loginModal')">
 <div class="modal-content">
  <div class="modal-header">
   <h2>🔐 دخول الإدارة</h2>
   <button class="close" onclick="closeModal('loginModal')">×</button>
  </div>

  <div class="login-box">
   <p id="loginMessage">أدخل بيانات حساب الإدارة</p>

   <input id="loginUsername" placeholder="اسم المستخدم" autocomplete="username">
   <input id="loginPassword" type="password" placeholder="كلمة المرور" autocomplete="current-password">

   <button class="primary-btn" onclick="loginAdmin()">
    🔐 تسجيل الدخول
   </button>
  </div>
 </div>
</div>

<div id="rolesModal" class="modal" onclick="closeOnBackground(event,'rolesModal')">
 <div class="modal-content">
  <div class="modal-header">
   <h2>👥 إدارة الصلاحيات</h2>
   <button class="close" onclick="closeModal('rolesModal')">×</button>
  </div>

  <div id="rolesContent"></div>
 </div>
</div>
'''

if marker not in text:
    raise SystemExit("ERROR: marker not found")

if "id=\"loginModal\"" in text:
    raise SystemExit("INFO: roles UI already exists; no changes made")

text = text.replace(marker, marker + "\n" + insert, 1)

css_marker = '</style>'

css = r'''
/* نظام الصلاحيات */
.login-box{
 display:flex;
 flex-direction:column;
 gap:12px;
 padding:8px 0 4px;
}

.login-box p{
 margin:0 0 4px;
 color:var(--muted);
 font-size:14px;
}

.role-card{
 background:#f9fafb;
 border:1px solid var(--border);
 border-radius:15px;
 padding:14px;
 margin-bottom:10px;
}

.role-card strong{
 display:block;
 margin-bottom:5px;
}

.role-card small{
 color:var(--muted);
}

.permission-list{
 display:grid;
 gap:8px;
 margin-top:12px;
}

.permission-row{
 display:flex;
 align-items:center;
 justify-content:space-between;
 gap:10px;
 background:white;
 border:1px solid var(--border);
 padding:10px 12px;
 border-radius:10px;
}

.permission-row input{
 width:20px;
 height:20px;
}

.role-badge{
 display:inline-block;
 padding:5px 9px;
 border-radius:20px;
 background:#eef2ff;
 color:#3730a3;
 font-size:12px;
 font-weight:bold;
}
'''

if css_marker not in text:
    raise SystemExit("ERROR: style marker not found")

text = text.replace(css_marker, css + "\n" + css_marker, 1)

js_marker = '<script>'

js = r'''
/* ================================
   نظام الأدوار والصلاحيات
   ================================ */

const DEFAULT_PERMISSIONS = {
 addProduct: true,
 editProduct: true,
 editPrice: true,
 deleteProduct: false,
 reports: true,
 manageStaff: false,
 appearance: false,
 transferOwner: false
};

let authUsers = JSON.parse(
 localStorage.getItem("authUsers") || "null"
);

let currentUser = JSON.parse(
 localStorage.getItem("currentUser") || "null"
);

function initAuth(){

 if(!authUsers){

  authUsers = [{
   id:"owner-1",
   username:"owner",
   password:"1234",
   name:"المسؤول الرئيسي",
   role:"OWNER",
   active:true,
   permissions:{
    addProduct:true,
    editProduct:true,
    editPrice:true,
    deleteProduct:true,
    reports:true,
    manageStaff:true,
    appearance:true,
    transferOwner:true
   }
  }];

  localStorage.setItem(
   "authUsers",
   JSON.stringify(authUsers)
  );
 }
}

function getCurrentUser(){
 return currentUser;
}

function hasPermission(permission){

 if(!currentUser || !currentUser.active)
  return false;

 if(currentUser.role==="OWNER")
  return true;

 return !!(
  currentUser.permissions &&
  currentUser.permissions[permission]
 );
}

function openAdmin(){

 if(!currentUser){
  document.getElementById("loginMessage").textContent =
   "هذه المنطقة مخصصة للمسؤول والمشرفين.";

  document.getElementById("loginModal")
   .classList.add("show");

  return;
 }

 if(!currentUser.active){
  showToast("هذا الحساب غير مفعل");
  return;
 }

 renderAdmin();

 document.getElementById("adminModal")
  .classList.add("show");
}

function loginAdmin(){

 const username =
  document.getElementById("loginUsername")
   .value.trim();

 const password =
  document.getElementById("loginPassword")
   .value;

 const user=authUsers.find(u=>
  u.username===username &&
  u.password===password &&
  u.active
 );

 if(!user){
  showToast("اسم المستخدم أو كلمة المرور غير صحيحة");
  return;
 }

 currentUser=user;

 localStorage.setItem(
  "currentUser",
  JSON.stringify(user)
 );

 document.getElementById("loginUsername").value="";
 document.getElementById("loginPassword").value="";

 closeModal("loginModal");

 showToast(
  user.role==="OWNER"
   ? "مرحبًا بالمسؤول 👑"
   : "مرحبًا بالمشرف 🛠️"
 );

 renderAdmin();
 document.getElementById("adminModal")
  .classList.add("show");
}

function logoutAdmin(){

 currentUser=null;

 localStorage.removeItem("currentUser");

 closeModal("adminModal");
 closeModal("rolesModal");

 showToast("تم تسجيل الخروج");
}

function openRoles(){

 if(!hasPermission("manageStaff")){
  showToast("ليس لديك صلاحية إدارة المشرفين");
  return;
 }

 renderRoles();

 document.getElementById("rolesModal")
  .classList.add("show");
}

function renderRoles(){

 const box=document.getElementById("rolesContent");

 if(!box)return;

 const staff=authUsers.filter(u=>u.role!=="OWNER");

 box.innerHTML=`
  <div class="role-card">
   <strong>👑 ${escapeHtml(
    authUsers.find(u=>u.role==="OWNER")?.name ||
    "المسؤول"
   )}</strong>
   <small>المسؤول الرئيسي</small>
   <span class="role-badge">OWNER</span>
  </div>

  <h3>🛠️ المشرفون</h3>

  ${
   staff.length
    ? staff.map(u=>`
      <div class="role-card">
       <strong>${escapeHtml(u.name)}</strong>
       <small>@${escapeHtml(u.username)}</small>
       <div>
        <span class="role-badge">
         ${u.active?"مشرف مفعل":"مشرف معطل"}
        </span>
       </div>

       <div class="permission-list">
        ${Object.entries({
         addProduct:"إضافة المنتجات",
         editProduct:"تعديل المنتجات",
         editPrice:"تعديل الأسعار",
         deleteProduct:"حذف المنتجات",
         reports:"بلاغات العملاء",
         appearance:"إعدادات المظهر"
        }).map(([key,label])=>`
         <label class="permission-row">
          <span>${label}</span>
          <input type="checkbox"
           ${u.permissions?.[key]?"checked":""}
           onchange="setStaffPermission('${u.id}','${key}',this.checked)">
         </label>
        `).join("")}
       </div>

       <button class="delete-btn"
        style="margin-top:10px"
        onclick="removeStaff('${u.id}')">
        🗑️ إزالة المشرف
       </button>
      </div>
     `).join("")
    : "<p>لا يوجد مشرفون حاليًا.</p>"
  }

  <hr>

  <h3>➕ إضافة مشرف</h3>

  <input id="newStaffName" placeholder="اسم المشرف">
  <input id="newStaffUsername" placeholder="اسم المستخدم">
  <input id="newStaffPassword" type="password" placeholder="كلمة المرور">

  <button class="primary-btn" onclick="addStaff()">
   ➕ إضافة المشرف
  </button>
 `;
}

function addStaff(){

 if(!hasPermission("manageStaff")){
  showToast("غير مصرح");
  return;
 }

 const name=document.getElementById("newStaffName").value.trim();
 const username=document.getElementById("newStaffUsername").value.trim();
 const password=document.getElementById("newStaffPassword").value;

 if(!name || !username || !password){
  showToast("أكمل بيانات المشرف");
  return;
 }

 if(authUsers.some(u=>u.username===username)){
  showToast("اسم المستخدم مستخدم مسبقًا");
  return;
 }

 authUsers.push({
  id:"staff-"+Date.now(),
  username,
  password,
  name,
  role:"ADMIN",
  active:true,
  permissions:{...DEFAULT_PERMISSIONS}
 });

 localStorage.setItem(
  "authUsers",
  JSON.stringify(authUsers)
 );

 showToast("تمت إضافة المشرف ✅");

 renderRoles();
}

function setStaffPermission(id,key,value){

 if(!hasPermission("manageStaff"))
  return;

 const user=authUsers.find(u=>u.id===id);

 if(!user)return;

 user.permissions=user.permissions || {};
 user.permissions[key]=value;

 localStorage.setItem(
  "authUsers",
  JSON.stringify(authUsers)
 );

 showToast("تم تحديث الصلاحية");
}

function removeStaff(id){

 if(!hasPermission("manageStaff"))
  return;

 const user=authUsers.find(u=>u.id===id);

 if(!user)return;

 if(!confirm(
  "هل تريد إزالة المشرف "+user.name+"؟"
 ))return;

 authUsers=authUsers.filter(u=>u.id!==id);

 localStorage.setItem(
  "authUsers",
  JSON.stringify(authUsers)
 );

 renderRoles();

 showToast("تمت إزالة المشرف");
}

initAuth();
'''

if js_marker not in text:
    raise SystemExit("ERROR: script marker not found")

text = text.replace(js_marker, js_marker + "\n" + js, 1)

path.write_text(text, encoding="utf-8")

print("OK: roles system added")
