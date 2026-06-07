#!/usr/bin/env python3
"""读取 cf_token 文件，通过 API 添加 DNS 记录"""
import json, urllib.request, sys, ssl

TOKEN_PATH = "/Users/silinzhang/Desktop/nicetoken/.cf_token"
with open(TOKEN_PATH) as f:
    TOKEN = f.read().strip()

ZONE = "cadbd1c105f0726275f6ac5fe711b468"
WORKER_DEV = "nicetoken.tiara-watermelon.workers.dev"

def api(method, path, data=None):
    url = f"https://api.cloudflare.com/client/v4{path}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

# 1. 删旧 CNAME
print("=== 1. 查找旧 CNAME 记录 ===")
result = api("GET", f"/zones/{ZONE}/dns_records?type=CNAME&name=nicetoken.top")
print(f"  响应: {json.dumps(result, ensure_ascii=False)[:200]}")
for r in result.get("result", []):
    rid = r["id"]
    print(f"  删除: {rid}")
    api("DELETE", f"/zones/{ZONE}/dns_records/{rid}")

# 2. 新建 CNAME
print("=== 2. 创建 CNAME nicetoken.top -> workers.dev ===")
result = api("POST", f"/zones/{ZONE}/dns_records", {
    "type": "CNAME",
    "name": "@",
    "content": WORKER_DEV,
    "proxied": True
})
if result.get("success"):
    print("  ✅ CNAME 创建成功")
else:
    for e in result.get("errors", []):
        print(f"  ❌ {e.get('message')}")

# 3. 添加 Workers 路由
print("=== 3. 添加 Workers 路由 nicetoken.top/* -> nicetoken ===")
result = api("POST", f"/zones/{ZONE}/workers/routes", {
    "pattern": "nicetoken.top/*",
    "script": "nicetoken"
})
if result.get("success"):
    print("  ✅ 路由添加成功")
else:
    for e in result.get("errors", []):
        print(f"  ❌ {e.get('message')}")

print("\n完成！等1-2分钟后打开 https://nicetoken.top")
