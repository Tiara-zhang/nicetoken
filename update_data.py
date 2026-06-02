#!/usr/bin/env python3
"""
nicetoken.top 数据更新脚本
双数据源：腾讯（指数，24h 稳定）+ 东方财富（板块/涨跌，交易时段）
非交易时段自动用上交易日缓存
"""
import json, os, sys, subprocess, re, time
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(OUTPUT_DIR, "data.json")
HIST_FILE = os.path.join(OUTPUT_DIR, "history.json")
CACHE_FILE = os.path.join(OUTPUT_DIR, "last_sectors.json")

BJT = timezone(timedelta(hours=8))
now_bj = datetime.now(BJT)
today_str = now_bj.strftime("%Y-%m-%d")
hour = now_bj.hour
is_trading = 9 <= hour < 16

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

def curl(url, timeout=15):
    try:
        r = subprocess.run(
            ["curl", "-s", "-k", "--max-time", str(timeout),
             "-H", f"User-Agent: {UA}",
             "-H", "Referer: https://quote.eastmoney.com/",
             url],
            capture_output=True, timeout=timeout+5
        )
        if r.returncode != 0 or not r.stdout:
            return None
        # 自动检测编码
        try:
            return r.stdout.decode("utf-8")
        except:
            return r.stdout.decode("gbk", errors="replace")
    except:
        return None

# ─────────── 指数（腾讯 24h） ───────────

def fetch_indices():
    raw = curl("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688")
    if not raw: return {}
    code_map = {"sh000001":"sh","sz399001":"sz","sz399006":"cy","sh000688":"kc"}
    result = {}
    for line in raw.strip().split("\n"):
        if "=" not in line: continue
        var = line.split("=",1)[0].replace("v_","").strip()
        key = code_map.get(var)
        if not key: continue
        fields = line.split("=",1)[1].strip('"').strip(";").split("~")
        if len(fields) < 33: continue
        try:
            result[key] = {
                "val": round(float(fields[3]), 2),
                "chg": round(float(fields[32]), 2)
            }
        except: continue
    return result

# ─────────── 板块 ───────────

def fetch_sectors_em():
    """东方财富行业板块"""
    raw = curl("https://push2.eastmoney.com/api/qt/clist/get"
               "?pn=1&pz=30&po=1&np=1&fltt=2&invt=2&fid=f3"
               "&fs=m:90+t:2&fields=f2,f3,f12,f14")
    if not raw: return None
    try:
        items = json.loads(raw).get("data",{}).get("diff",[])
    except: return None
    if not items: return None
    sectors = []
    for item in items:
        name = item.get("f14","")
        try: chg = float(item.get("f3",0))
        except: continue
        if name:
            sectors.append({"name":name,"chg":round(chg,2),"code":item.get("f12","")})
    return sectors

def fetch_overview_em():
    """东方财富涨跌分布"""
    result = {"up":0,"flat":0,"down":0,"zt":0,"dt":0}
    raw = curl("https://push2.eastmoney.com/api/qt/clist/get"
               "?pn=1&pz=6000&po=1&np=1&fltt=2&invt=2&fid=f3"
               "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
               "&fields=f3", timeout=30)
    if raw:
        try:
            items = json.loads(raw).get("data",{}).get("diff",[])
            up=down=flat=0
            for item in items:
                try: c = float(item.get("f3",0))
                except: continue
                if c>0: up+=1
                elif c<0: down+=1
                else: flat+=1
            result["up"],result["down"],result["flat"] = up,down,flat
        except: pass
    # 涨停跌停
    for tag, key in [("UP","zt"),("DOWN","dt")]:
        r = curl(f"https://push2.eastmoney.com/api/qt/clist/get"
                 f"?pn=1&pz=500&po=1&np=1&fltt=2&invt=2&fid=f3"
                 f"&fs=m:0+t:6+T:{tag}&fields=f12", timeout=20)
        if r:
            try: result[key] = len(json.loads(r).get("data",{}).get("diff",[]))
            except: pass
    return result

def fetch_sector_hist(code, days=20):
    raw = curl(f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
               f"?secid=90.{code}&fields1=f1,f2,f3&fields2=f51,f53"
               f"&klt=101&fqt=1&end=20500101&lmt={days}")
    if not raw: return None
    try:
        klines = json.loads(raw).get("data",{}).get("klines",[])
    except: return None
    result = []
    for k in klines:
        parts = k.split(",")
        if len(parts) >= 2:
            try: result.append({"date":parts[0],"chg":round(float(parts[1]),2)})
            except: continue
    return result if result else None

def main():
    print(f"[{now_bj.strftime('%H:%M:%S')}] nicetoken 更新 (交易时段={is_trading})")
    
    # 1. 指数
    indices = fetch_indices()
    detail = ', '.join([f'{k}={v["val"]}({v["chg"]}%)' for k,v in indices.items()])
    print(f"  指数: {len(indices)} 个 {detail}")
    
    # 2. 板块（交易时段用东方财富，非交易时段用缓存）
    vol = 0
    overview = {"up":0,"flat":0,"down":0,"zt":0,"dt":0}
    sectors = []
    sector_hist = {}
    
    if is_trading:
        sectors = fetch_sectors_em()
        if sectors:
            print(f"  板块: 东方财富 {len(sectors)} 个")
            overview = fetch_overview_em()
            # 缓存板块数据
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"sectors":sectors,"overview":overview,"updated":today_str},
                          f, ensure_ascii=False)
            # 历史趋势
            for s in sectors[:10]:
                hist = fetch_sector_hist(s["code"], 20)
                if hist:
                    sector_hist[s["name"]] = hist
                time.sleep(0.3)
            print(f"  趋势: {len(sector_hist)} 个板块")
    
    # 非交易时段/东方财富失败时——用缓存
    if not sectors and os.path.exists(CACHE_FILE):
        try:
            cache = json.load(open(CACHE_FILE, encoding="utf-8"))
            sectors = cache.get("sectors", [])
            overview = cache.get("overview", overview)
            print(f"  板块: 缓存 {len(sectors)} 个 (来自 {cache.get('updated','?')})")
            # 从 history.json 加载历史趋势
            if os.path.exists(HIST_FILE):
                sector_hist = json.load(open(HIST_FILE, encoding="utf-8"))
        except: pass
    
    # 3. 成交额（腾讯指数）
    raw_idx = curl("https://qt.gtimg.cn/q=sh000001")
    if raw_idx:
        for line in raw_idx.strip().split("\n"):
            if "sh000001" not in line: continue
            fields = line.split("=",1)[1].strip('"').strip(";").split("~")
            if len(fields) > 18:
                try: vol = int(float(fields[18]) / 100000000)
                except: pass
            break
    
    overview["vol"] = vol
    print(f"  成交额: {vol}亿 涨停:{overview['zt']} 跌停:{overview['dt']}")
    print(f"  涨跌: ↑{overview['up']} →{overview['flat']} ↓{overview['down']}")
    
    # 输出
    data = {
        "updated_at": now_bj.strftime("%Y-%m-%d %H:%M:%S"),
        "date": today_str,
        "indices": indices,
        "sectors": [{"name":s["name"],"chg":s["chg"]} for s in sectors[:15]],
        "distribution": {"up":overview["up"],"flat":overview["flat"],"down":overview["down"]},
        "sentiment": {"zt":overview["zt"],"dt":overview["dt"],"vol":overview["vol"]},
    }
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(HIST_FILE, "w", encoding="utf-8") as f:
        json.dump(sector_hist, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] data.json + history.json  {len(sectors)} 板块, {len(sector_hist)} 历史趋势")

if __name__ == "__main__":
    main()
