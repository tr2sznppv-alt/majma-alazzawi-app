# بنية متجر المنتجات

## Edge Functions
- users → JWT_SECRET (HMAC)
- used-products → JWT_SECRET (نفس users)
  - /regular-products (منتجات عادية)
  - /all, /pending, /submit (منتجات مستعملة)
- smart-worker → ⚠️ معطل — لا تستخدمه

## index.html
- CATALOG_API_BASE → used-products
- USED_PRODUCTS_URL → used-products

## ملاحظات
- لا تغيّر JWT_SECRET بدون Deploy لكل Edge Functions
- التوكن صالح 24 ساعة
