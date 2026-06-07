#!/usr/bin/env python3
"""nicetoken.top 数据更新 v2"""
import json, os, sys, subprocess, re, time
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(OUTPUT_DIR, "data.json")
HIST_FILE = os.path.join(OUTPUT_DIR, "history.json")
CACHE_FILE = os.path.join(OUTPUT_DIR, "last_sectors.json")

BJT = timezone(timedelta(hours=8))
now = datetime.now(BJT)
today = now.strftime("%Y-%m-%d")
is_trading = 9 <= now.hour < 16

def curl(url, timeout=15):
    try:
        r = subprocess.run(["curl","-s","-k","--max-time",str(timeout),
            "-H","User-Agent: Mozilla/5.0",
            "-H","Referer: https://quote.eastmoney.com/", url],
            capture_output=True, timeout=timeout+5)
        if r.returncode != 0 or not r.stdout: return None
        try: return r.stdout.decode("utf-8")
        except: return r.stdout.decode("gbk",errors="replace")
    except: return None

def fetch_global():
    """全球指数：东方财富"""
    ids = "100.DJIA,100.NDX,100.SPX,100.HSI,100.N225"
    names = {"DJIA":"道琼斯","NDX":"纳斯达克","SPX":"标普500","HSI":"恒生指数","N225":"日经225"}
    raw = curl(f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f2,f3,f12&secids={ids}")
    if not raw: return {}
    try: items = json.loads(raw).get("data",{}).get("diff",[])
    except: return {}
    result = {}
    for item in items:
        name = names.get(item.get("f12",""))
        if not name: continue
        try: result[name] = {"val":round(float(item.get("f2",0)),2),"chg":round(float(item.get("f3",0)),2)}
        except: continue
    return result

def fetch_a():
    """A股指数：腾讯"""
    raw = curl("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688")
    if not raw: return {}
    cm = {"sh000001":"上证","sz399001":"深证","sz399006":"创业板","sh000688":"科创50"}
    result = {}
    for line in raw.strip().split("\n"):
        if "=" not in line: continue
        var = line.split("=",1)[0].replace("v_","").strip()
        key = cm.get(var)
        if not key: continue
        f = line.split("=",1)[1].strip('"').strip(";").split("~")
        if len(f) < 33: continue
        try: result[key] = {"val":round(float(f[3]),2),"chg":round(float(f[32]),2)}
        except: continue
    return result

def fetch_sectors():
    """板块排行"""
    raw = curl("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f2,f3,f12,f14")
    if not raw: return None
    try: items = json.loads(raw).get("data",{}).get("diff",[])
    except: return None
    if not items: return None
    sectors = []
    for item in items:
        name = item.get("f14","")
        try: chg = float(item.get("f3",0))
        except: continue
        if name: sectors.append({"name":name,"chg":round(chg,2),"code":item.get("f12","")})
    return sectors

def fetch_sector_hist(code, days=250):
    raw = curl(f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{code}&fields1=f1,f2,f3&fields2=f51,f53&klt=101&fqt=1&end=20500101&lmt={days}")
    if not raw: return None
    try: klines = json.loads(raw).get("data",{}).get("klines",[])
    except: return None
    result = []
    for k in klines:
        p = k.split(",")
        if len(p) >= 2:
            try: result.append({"date":p[0],"chg":round(float(p[1]),2)})
            except: continue
    return result or None

def fetch_overview():
    """涨跌分布+成交额"""
    result = {"up":0,"flat":0,"down":0,"zt":0,"dt":0,"vol":0}
    if is_trading:
        raw = curl("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=6000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f3", timeout=30)
        if raw:
            try:
                items = json.loads(raw).get("data",{}).get("diff",[])
                up=down=flat=0
                for item in items:
                    try: c=float(item.get("f3",0))
                    except: continue
                    if c>0: up+=1
                    elif c<0: down+=1
                    else: flat+=1
                result["up"],result["down"],result["flat"]=up,down,flat
            except: pass
        for tag,key in [("UP","zt"),("DOWN","dt")]:
            r=curl(f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=500&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6+T:{tag}&fields=f12",timeout=20)
            if r:
                try: result[key]=len(json.loads(r).get("data",{}).get("diff",[]))
                except: pass
    ri=curl("https://qt.gtimg.cn/q=sh000001")
    if ri:
        for line in ri.strip().split("\n"):
            if "sh000001" not in line: continue
            f=line.split("=",1)[1].strip('"').strip(";").split("~")
            if len(f)>18:
                try: result["vol"]=int(float(f[18])/100000000)
                except: pass
            break
    return result

def default_picks():
    return {
        "picks":[
            {"tag":"🔥","tagType":"hot","title":"半导体 / AI算力","reason":"全球AI资本开支持续高景气。关注：中芯国际、北方华创"},
            {"tag":"⚡","tagType":"warm","title":"电力电网 / 特高压","reason":"夏季用电高峰+新能源并网需求。关注：国电南瑞、许继电气"},
            {"tag":"📈","tagType":"warm","title":"机器人 / 具身智能","reason":"Optimus量产预期+国内政策扶持。关注：汇川技术、绿的谐波"},
            {"tag":"👀","tagType":"cold","title":"消费电子 / 果链","reason":"Vision Pro新品+AI换机预期。关注：立讯精密、韦尔股份"}
        ],
        "risks":[
            {"level":"high","icon":"🔴","lbl":"高","title":"半导体短期过热","desc":"近3月涨幅超25%，PE高企，勿追高"},
            {"level":"mid","icon":"🟡","lbl":"中","title":"美联储降息预期反复","desc":"非农超预期或推迟降息，成长股承压"},
            {"level":"mid","icon":"🟡","lbl":"中","title":"人民币汇率波动","desc":"美元走强影响进口依赖型企业利润"},
            {"level":"low","icon":"🟢","lbl":"低","title":"地缘政治摩擦","desc":"关注实体清单风险"}
        ]
    }

def main():
    print(f"[{now.strftime('%H:%M:%S')}] nicetoken 更新 交易={is_trading}")
    
    global_idx = fetch_global()
    a_idx = fetch_a()
    a_detail = ' '.join([f'{k}={v["val"]}({v["chg"]}%)' for k,v in a_idx.items()])
    print(f"  A股: {a_detail}")
    if global_idx:
        gd = ' '.join([f'{k}={v["val"]}({v["chg"]}%)' for k,v in global_idx.items()])
        print(f"  全球: {gd}")
    
    sectors = fetch_sectors()
    if not sectors and os.path.exists(CACHE_FILE):
        try:
            sectors = json.load(open(CACHE_FILE,encoding="utf-8")).get("sectors",[])
            print(f"  板块: 缓存 {len(sectors)} 个")
        except: pass
    print(f"  板块: {len(sectors)} 个")
    
    overview = fetch_overview()
    print(f"  涨跌: ↑{overview['up']} →{overview['flat']} ↓{overview['down']} 涨停:{overview['zt']} 跌停:{overview['dt']} 成交:{overview['vol']}亿")
    
    sector_hist = {}
    for s in sectors[:10]:
        code = s.get("code")
        if code:
            hist = fetch_sector_hist(code, 250)
            if hist:
                sector_hist[s["name"]] = hist
                print(f"  趋势: {s['name']} ({len(hist)}天)")
            time.sleep(0.3)
    
    data = {
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": today,
        "global": global_idx,
        "a_indices": a_idx,
        "sectors": [{"name":s["name"],"chg":s["chg"]} for s in sectors[:15]],
        "distribution": {"up":overview["up"],"flat":overview["flat"],"down":overview["down"]},
        "sentiment": {"zt":overview["zt"],"dt":overview["dt"],"vol":overview["vol"]},
        "picks_risks": default_picks()
    }
    
    with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    with open(HIST_FILE,"w",encoding="utf-8") as f: json.dump(sector_hist,f,ensure_ascii=False,indent=2)
    if sectors:
        with open(CACHE_FILE,"w",encoding="utf-8") as f: json.dump({"sectors":sectors},f,ensure_ascii=False)
    
    print(f"\n[OK] data.json + history.json")

if __name__ == "__main__":
    main()
