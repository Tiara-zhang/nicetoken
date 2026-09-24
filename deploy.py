#!/usr/bin/env python3
"""部署 index.html 到 Cloudflare Workers

注意：本脚本用 curl --noproxy 子进程（避开 macOS 系统代理残留导致的
urllib ProxyError / SSL 问题）。早期 urllib 版本会静默返回假成功
（打印 "✅ Deploy OK" 但线上未更新）。务必用 verify_deploy.py 核实。
"""
import json, os, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, ".cf_token")) as f:
    token = f.read().strip()

with open(os.path.join(BASE, "index.html"), encoding="utf-8") as f:
    html = f.read()

# 嵌入 HTML 到 Service Worker（模板字面量方式）
escaped = html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
worker_js = (
    "addEventListener('fetch', event => {\n"
    "  event.respondWith(handleRequest(event.request));\n"
    "});\n\n"
    "async function handleRequest(request) {\n"
    "  const url = new URL(request.url);\n"
    "  if (url.pathname === '/' || url.pathname === '/index.html') {\n"
    "    return new Response(`" + escaped + "`, {\n"
    "      headers: {\n"
    "        'content-type': 'text/html;charset=UTF-8',\n"
    "        'cache-control': 'no-cache, must-revalidate',\n"
    "      },\n"
    "    });\n"
    "  }\n"
    "  return new Response('Not Found', { status: 404 });\n"
    "}\n"
)

worker_path = "/tmp/nicetoken_worker.js"
with open(worker_path, "w", encoding="utf-8") as f:
    f.write(worker_js)

metadata = json.dumps({"body_part": "script", "content_type": "application/javascript"})
ac = "82c6b3cdfc3b460ed2923c95690d3b27"
url = f"https://api.cloudflare.com/client/v4/accounts/{ac}/workers/services/nicetoken/environments/production"

cmd = [
    "curl", "--noproxy", "*", "-s", "-X", "PUT", url,
    "-H", "Authorization: Bearer " + token,
    "-F", "metadata=" + metadata,
    "-F", "script=@/tmp/nicetoken_worker.js;type=application/javascript",
    "--connect-timeout", "20",
    "--max-time", "60",
]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    print("❌ curl error:", result.stderr[:300])
    raise SystemExit(1)

try:
    r = json.loads(result.stdout)
    if r.get("success"):
        print("✅ Deploy OK")
    else:
        print("❌", json.dumps(r.get("errors", []), ensure_ascii=False)[:500])
        raise SystemExit(1)
except json.JSONDecodeError:
    print("❌ parse error:", result.stdout[:500])
    raise SystemExit(1)
