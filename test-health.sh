#!/bin/bash
TOKEN="$1"
echo "═══ اختبار الصحة ═══"
for endpoint in users used-products/all used-products/regular-products used-products/pending; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://vkjsynailhrjtfbzysjn.supabase.co/functions/v1/$endpoint" -H "Authorization: Bearer $TOKEN")
  echo "$endpoint → HTTP $code"
done
