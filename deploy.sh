#!/bin/bash
# nicetoken.top 部署脚本 - 一次性搞定
set -e

TOKEN="$1"
ACCOUNT="82c6b3cdfc3b460ed2923c95690d3b27"
ZONE="cadbd1c105f0726275f6ac5fe711b468"
WORKER="nicetoken"
DOMAIN="nicetoken.top"
WORKER_DEV="$WORKER.tiara-watermelon.workers.dev"

echo "=== 1. 添加 DNS CNAME 记录 ==="
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"type\":\"CNAME\",\"name\":\"@\",\"content\":\"$WORKER_DEV\",\"proxied\":true}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('DNS:', 'OK' if d['success'] else d.get('errors',[{}])[0].get('message','?'))"

echo ""
echo "=== 2. 添加 Workers 路由 ==="
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/workers/routes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"pattern\":\"$DOMAIN/*\",\"script\":\"$WORKER\"}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Route:', 'OK' if d['success'] else d.get('errors',[{}])[0].get('message','?'))"

echo ""
echo "=== 3. 添加自定义域名到 Workers ==="
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT/workers/services/$WORKER/environments/production" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"routes\":[{\"pattern\":\"$DOMAIN\",\"enabled\":true}]}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('CustomDomain:', 'OK' if d['success'] else d.get('errors',[{}])[0].get('message','?'))"

echo ""
echo "=== 完成！==="
echo "等待1-2分钟，打开 https://$DOMAIN 看看"
