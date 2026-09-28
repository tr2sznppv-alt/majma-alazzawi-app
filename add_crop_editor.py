from pathlib import Path
import re

p = Path("www/index.html")
s = p.read_text(encoding="utf-8")

# =========================
# CSS
# =========================
css = r'''
/* ===== Product Image Crop Editor ===== */
.crop-editor-modal{
 position:fixed;
 inset:0;
 background:rgba(0,0,0,.78);
 z-index:99999;
 display:none;
 align-items:center;
 justify-content:center;
 padding:12px;
}
.crop-editor-modal.show{display:flex}
.crop-editor-box{
 width:min(540px,100%);
 max-height:96vh;
 background:#fff;
 border-radius:20px;
 overflow:hidden;
 display:flex;
 flex-direction:column;
 box-shadow:0 15px 50px rgba(0,0,0,.45);
}
.crop-editor-header{
 padding:14px 16px;
 display:flex;
 align-items:center;
 justify-content:space-between;
 border-bottom:1px solid #eee;
}
.crop-editor-header strong{font-size:16px}
.crop-editor-close{
 border:0;
 background:#f1f1f1;
 width:38px;
 height:38px;
 border-radius:50%;
 font-size:23px;
 cursor:pointer;
}
.crop-toolbar{
 padding:10px;
 display:flex;
 flex-wrap:wrap;
 gap:7px;
 justify-content:center;
 border-bottom:1px solid #eee;
}
.crop-toolbar button,
.crop-toolbar select{
 border:1px solid #ddd;
 background:#fff;
 border-radius:10px;
 padding:8px 11px;
 font-size:13px;
 cursor:pointer;
}
.crop-workspace{
 position:relative;
 width:100%;
 height:min(58vh,420px);
 min-height:260px;
 background:#111;
 overflow:hidden;
 touch-action:none;
}
#cropCanvas{
 position:absolute;
 left:50%;
 top:50%;
 transform:translate(-50%,-50%);
 max-width:none;
 max-height:none;
 pointer-events:none;
 user-select:none;
}
.crop-frame{
 position:absolute;
 border:2px solid #fff;
 box-shadow:0 0 0 9999px rgba(0,0,0,.52);
 cursor:move;
 touch-action:none;
}
.crop-grid{
 position:absolute;
 inset:0;
 pointer-events:none;
 background:
 linear-gradient(to right,
 transparent 33.333%,
 rgba(255,255,255,.4) 33.333%,
 rgba(255,255,255,.4) calc(33.333% + 1px),
 transparent calc(33.333% + 1px),
 transparent 66.666%,
 rgba(255,255,255,.4) 66.666%,
 rgba(255,255,255,.4) calc(66.666% + 1px),
 transparent calc(66.666% + 1px)),
 linear-gradient(to bottom,
 transparent 33.333%,
 rgba(255,255,255,.4) 33.333%,
 rgba(255,255,255,.4) calc(33.333% + 1px),
 transparent calc(33.333% + 1px),
 transparent 66.666%,
 rgba(255,255,255,.4) 66.666%,
 rgba(255,255,255,.4) calc(66.666% + 1px),
 transparent calc(66.666% + 1px));
}
.crop-handle{
 position:absolute;
 width:20px;
 height:20px;
 background:#fff;
 border:2px solid #111;
 border-radius:5px;
}
.crop-handle.br{
 right:-10px;
 bottom:-10px;
 cursor:nwse-resize;
}
.crop-controls{
 padding:12px;
 display:grid;
 gap:9px;
}
.crop-zoom-row{
 display:flex;
 align-items:center;
 gap:10px;
}
.crop-zoom-row input{flex:1}
.crop-preview-title{
 font-size:12px;
 color:#666;
 text-align:center;
}
#cropResultPreview{
 width:120px;
 height:120px;
 object-fit:contain;
 display:block;
 margin:auto;
 border-radius:12px;
 background:#f2f2f2;
}
.crop-actions{
 display:flex;
 gap:8px;
 padding:0 12px 12px;
}
.crop-actions button{
 flex:1;
 border:0;
 border-radius:12px;
 padding:12px;
 font-size:14px;
 cursor:pointer;
}
.crop-cancel-btn{background:#eee}
.crop-save-btn{
 background:#111;
 color:#fff;
}
.image-size-info{
 text-align:center;
 font-size:11px;
 color:#777;
 margin-top:5px;
}
.product-image-preview img{
 max-width:100%;
 max-height:190px;
 object-fit:contain;
 border-radius:12px;
}
@media(max-width:420px){
 .crop-workspace{
  height:52vh;
  min-height:240px;
 }
}
'''

if "Product Image Crop Editor" not in s:
    pos = s.find("</style>")
    if pos == -1:
        raise SystemExit("ERROR: لم يتم العثور على </style>")
    s = s[:pos] + css + "\n" + s[pos:]

# =========================
# Image picker
# =========================
pattern = r'<div class="product-image-picker">.*?<input type="hidden" id="image">\s*</div>'

new_picker = r'''
<div class="product-image-picker">

 <label class="image-picker-label">
  📷 صورة المنتج
 </label>

 <input
  id="imageFile"
  type="file"
  accept="image/*"
  onchange="previewProductImage(event)">

 <div id="productImagePreview"
      class="product-image-preview"
      style="display:none;">

  <img id="productImagePreviewImg"
       alt="معاينة صورة المنتج">

  <div id="productImageSizeInfo"
       class="image-size-info"></div>

  <button
   type="button"
   class="image-remove-btn"
   onclick="clearProductImage()">
   🗑️ إزالة الصورة
  </button>

 </div>

 <input type="hidden" id="image">

</div>
'''

s, count = re.subn(
    pattern,
    new_picker,
    s,
    count=1,
    flags=re.S
)

if count != 1:
    raise SystemExit("ERROR: لم يتم العثور على product-image-picker")

# =========================
# Crop modal
# =========================
modal = r'''
<!-- ===== Product Image Crop Editor ===== -->
<div id="cropEditorModal" class="crop-editor-modal">

 <div class="crop-editor-box">

  <div class="crop-editor-header">
   <strong>✂️ تعديل وقص الصورة</strong>

   <button
    type="button"
    class="crop-editor-close"
    onclick="closeCropEditor()">×</button>
  </div>

  <div class="crop-toolbar">

   <select id="cropRatio"
           onchange="setCropRatio(this.value)">
    <option value="free">حر</option>
    <option value="1:1">1 : 1</option>
    <option value="4:3">4 : 3</option>
    <option value="3:4">3 : 4</option>
    <option value="16:9">16 : 9</option>
   </select>

   <button type="button" onclick="rotateCropImage()">
    🔄 تدوير
   </button>

   <button type="button" onclick="resetCropEditor()">
    ↩️ إعادة
   </button>

  </div>

  <div id="cropWorkspace" class="crop-workspace">

   <canvas id="cropCanvas"></canvas>

   <div id="cropFrame" class="crop-frame">

    <div class="crop-grid"></div>

    <div class="crop-handle br"></div>

   </div>

  </div>

  <div class="crop-controls">

   <div class="crop-zoom-row">

    <span>🔍</span>

    <input
     id="cropZoom"
     type="range"
     min="0.5"
     max="3"
     step="0.01"
     value="1"
     oninput="setCropZoom(this.value)">

    <span id="cropZoomValue">100%</span>

   </div>

   <div class="crop-preview-title">
    👁️ معاينة النتيجة
   </div>

   <img id="cropResultPreview"
        alt="معاينة القص">

  </div>

  <div class="crop-actions">

   <button
    type="button"
    class="crop-cancel-btn"
    onclick="closeCropEditor()">
    إلغاء
   </button>

   <button
    type="button"
    class="crop-save-btn"
    onclick="applyCropImage()">
    💾 حفظ الصورة
   </button>

  </div>

 </div>

</div>
'''

if 'id="
cd ~/catalog-app
rm -f add_crop_editor.py
cd ~/catalog-app
cp -f www/index.html.before-crop-v1 www/index.html
grep -n "Product Image Crop Editor" www/index.html || echo "جاهز"
cd ~/catalog-app
grep -n "Product Image Crop Editor" www/index.html || echo "جاهز: محرر القص غير موجود"
cd ~/catalog-app

cp -f www/index.html www/index.html.before-crop-v1

python - <<'PY'
from pathlib import Path

p = Path("www/index.html")
s = p.read_text(encoding="utf-8")

css = r'''
/* ===== Product Image Crop Editor ===== */
.crop-editor-modal{
 position:fixed;
 inset:0;
 background:rgba(0,0,0,.78);
 z-index:99999;
 display:none;
 align-items:center;
 justify-content:center;
 padding:12px;
}
.crop-editor-modal.show{display:flex}
.crop-editor-box{
 width:min(540px,100%);
 max-height:96vh;
 background:#fff;
 border-radius:20px;
 overflow:hidden;
 display:flex;
 flex-direction:column;
 box-shadow:0 15px 50px rgba(0,0,0,.45);
}
.crop-editor-header{
 padding:14px 16px;
 display:flex;
 align-items:center;
 justify-content:space-between;
 border-bottom:1px solid #eee;
}
.crop-editor-close{
 border:0;
 background:#f1f1f1;
 width:38px;
 height:38px;
 border-radius:50%;
 font-size:23px;
 cursor:pointer;
}
.crop-toolbar{
 padding:10px;
 display:flex;
 flex-wrap:wrap;
 gap:7px;
 justify-content:center;
 border-bottom:1px solid #eee;
}
.crop-toolbar button,
.crop-toolbar select{
 border:1px solid #ddd;
 background:#fff;
 border-radius:10px;
 padding:8px 11px;
 font-size:13px;
 cursor:pointer;
}
.crop-workspace{
 position:relative;
 width:100%;
 height:min(58vh,420px);
 min-height:260px;
 background:#111;
 overflow:hidden;
 touch-action:none;
}
#cropCanvas{
 position:absolute;
 left:50%;
 top:50%;
 transform:translate(-50%,-50%);
 max-width:none;
 max-height:none;
 pointer-events:none;
}
.crop-frame{
 position:absolute;
 border:2px solid #fff;
 box-shadow:0 0 0 9999px rgba(0,0,0,.52);
 cursor:move;
 touch-action:none;
}
.crop-grid{
 position:absolute;
 inset:0;
 pointer-events:none;
 background:
 linear-gradient(to right,
 transparent 33.333%,
 rgba(255,255,255,.4) 33.333%,
 rgba(255,255,255,.4) calc(33.333% + 1px),
 transparent calc(33.333% + 1px),
 transparent 66.666%,
 rgba(255,255,255,.4) 66.666%,
 rgba(255,255,255,.4) calc(66.666% + 1px),
 transparent calc(66.666% + 1px)),
 linear-gradient(to bottom,
 transparent 33.333%,
 rgba(255,255,255,.4) 33.333%,
 rgba(255,255,255,.4) calc(33.333% + 1px),
 transparent calc(33.333% + 1px),
 transparent 66.666%,
 rgba(255,255,255,.4) 66.666%,
 rgba(255,255,255,.4) calc(66.666% + 1px),
 transparent calc(66.666% + 1px));
}
.crop-handle{
 position:absolute;
 width:20px;
 height:20px;
 background:#fff;
 border:2px solid #111;
 border-radius:5px;
}
.crop-handle.br{
 right:-10px;
 bottom:-10px;
 cursor:nwse-resize;
}
.crop-controls{
 padding:12px;
 display:grid;
 gap:9px;
}
.crop-zoom-row{
 display:flex;
 align-items:center;
 gap:10px;
}
.crop-zoom-row input{flex:1}
.crop-preview-title{
 font-size:12px;
 color:#666;
 text-align:center;
}
#cropResultPreview{
 width:120px;
 height:120px;
 object-fit:contain;
 display:block;
 margin:auto;
 border-radius:12px;
 background:#f2f2f2;
}
.crop-actions{
 display:flex;
 gap:8px;
 padding:0 12px 12px;
}
.crop-actions button{
 flex:1;
 border:0;
 border-radius:12px;
 padding:12px;
 font-size:14px;
 cursor:pointer;
}
.crop-cancel-btn{background:#eee}
.crop-save-btn{
 background:#111;
 color:#fff;
}
.image-size-info{
 text-align:center;
 font-size:11px;
 color:#777;
 margin-top:5px;
}
'''

if "/* ===== Product Image Crop Editor ===== */" in s:
    print("CSS موجود مسبقاً")
else:
    pos = s.find("</style>")
    if pos < 0:
        raise SystemExit("ERROR: لم نجد </style>")
    s = s[:pos] + css + "\n" + s[pos:]
    p.write_text(s, encoding="utf-8")
    print("تمت إضافة CSS بنجاح")
