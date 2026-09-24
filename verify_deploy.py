#!/usr/bin/env python3
"""verify_deploy.py — 部署后字节级验证 nicetoken.top 是否已上线新内容。

注意：默认会实时抓取线上页面。若设置 LIVE_HTML 环境变量则改用该本地文件
（离线对比用）。此前脚本只读 /tmp 缓存文件，容易拿旧快照做对比而产生
假阴性（NOT VERIFIED），已在 2026-09-23 修正为默认实时抓取。
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from urllib.request import urlopen

BASE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.environ.get("LIVE_HTML")  # 若为空则实时抓取
URL = os.environ.get("SITE_URL", "https://nicetoken.top/")
LOCAL = os.path.join(BASE, "index.html")
DATA = os.path.join(BASE, "data.json")


def fetch_live():
    """实时抓取线上 HTML（curl --noproxy 绕过 macOS 代理/SSL 问题）。"""
    fd, path = tempfile.mkstemp(suffix=".html", prefix="nt_live_")
    os.close(fd)
    try:
        subprocess.run(
            ["curl", "--noproxy", "*", "-s", "-H", "Cache-Control: no-cache",
             "%s?v=%d" % (URL.rstrip("/"), os.getpid()), "-o", path],
            check=True, timeout=60)
        if os.path.getsize(path) == 0:
            raise RuntimeError("live fetch returned 0 bytes")
        return path
    except Exception as e:
        print("LIVE FETCH FAILED: %s" % e)
        return None


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    live_path = LIVE
    tmp_made = None
    if not live_path:
        live_path = fetch_live()
        tmp_made = live_path
    if not live_path or not os.path.exists(live_path):
        print("MISSING live file: %s" % live_path)
        return 1
    if not os.path.exists(LOCAL):
        print("MISSING local file: %s" % LOCAL)
        return 1
    try:
        return _verify(live_path)
    finally:
        if tmp_made and os.path.exists(tmp_made):
            os.unlink(tmp_made)


def _verify(LIVE):
    live_body = open(LIVE, encoding="utf-8", errors="replace").read()
    live_hash = sha256(LIVE)
    local_hash = sha256(LOCAL)

    print("live  sha256 = %s" % live_hash)
    print("local sha256 = %s" % local_hash)

    same = live_hash == local_hash
    print("CHECK1 sha256: %s" % ("MATCH" if same else "DIFF"))
    print("  live size = %d bytes" % len(open(LIVE, "rb").read()))

    ts_live = re.findall(r"2026-\d{2}-\d{2} \d{2}:\d{2}", live_body)
    ts_local = re.findall(r"2026-\d{2}-\d{2} \d{2}:\d{2}",
                          open(LOCAL, encoding="utf-8", errors="replace").read())
    print("CHECK2 timestamp: live=%s local=%s" % (
        ts_live[0] if ts_live else "n/a",
        ts_local[0] if ts_local else "n/a"))
    if os.path.exists(DATA):
        try:
            print("  data.json updated_at = %s" % json.load(open(DATA))["updated_at"])
        except Exception:
            pass

    pe = re.findall(r"PE TTM[^<\"]{0,40}", live_body)
    print("CHECK3 PE entries on live page (%d):" % len(pe))
    for p in pe[:6]:
        print("   %s" % p)
    print("  sector rows: %d" % len(re.findall(r'class="[^"]*sector', live_body)))

    print("\nRESULT: %s" % ("DEPLOY VERIFIED (live == local)"
                            if same else "NOT VERIFIED (live differs from local)"))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
