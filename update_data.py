#!/usr/bin/env python3
"""nicetoken.top 数据更新 v3 — 多数据源融合"""
import json, os, subprocess, re, time, sys
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(OUTPUT_DIR, "data.json")
HIST_FILE = os.path.join(OUTPUT_DIR, "history.json")
GOOD_FILE = os.path.join(OUTPUT_DIR, ".last_good.json")

# 腾讯 proxy.finance 兜底时顺带采集的龙头股（nzg_* 字段），供 main() 填充 leaders
TQ_LEADERS = {}

BJT = timezone(timedelta(hours=8))
now = datetime.now(BJT)
today = now.strftime("%Y-%m-%d")
# 交易时段：9:30-15:00 周一至周五（精确到分钟）
# 用"当日分钟数"比较，避免多子句区间拼接在 10:00-10:29 等时段漏判
_mins = now.hour * 60 + now.minute
is_trading = now.weekday() < 5 and (9 * 60 + 30) <= _mins <= (15 * 60)

def curl(url, timeout=15, retries=2):
    """通用curl请求，带--noproxy绕过macOS代理问题，失败自动重试
    push2.eastmoney等接口偶发空响应/超时，重试能显著提高成功率"""
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(["curl", "-s", "-k", "--noproxy", "*", "--max-time", str(timeout),
                "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "-H", "Referer: https://quote.eastmoney.com/", url],
                capture_output=True, timeout=timeout+5)
            if r.returncode == 0 and r.stdout:
                try: return r.stdout.decode("utf-8")
                except: return r.stdout.decode("gbk", errors="replace")
            # 空响应或非0返回码 → 重试
        except Exception:
            pass
        if attempt < retries:
            time.sleep(0.6)
    return None

def safe_float(v, default=0):
    try: return round(float(v), 2)
    except: return default

# ═══════════════════════════════════════════
# 1. 全球指数 — 东方财富 push2（已有，稳定）
def fetch_global():
    """全球指数 — 东方财富 push2（主）+ 腾讯兜底（24h稳定）"""
    ids = "100.DJIA,100.NDX,100.SPX,100.HSI,100.N225"
    names = {"DJIA": "道琼斯", "NDX": "纳斯达克", "SPX": "标普500", "HSI": "恒生指数", "N225": "日经225"}
    result = {}
    raw = curl(f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f2,f3,f12&secids={ids}")
    if raw:
        try:
            items = json.loads(raw).get("data", {}).get("diff", [])
            for item in items:
                name = names.get(item.get("f12", ""))
                if not name: continue
                val = safe_float(item.get("f2", 0))
                chg = safe_float(item.get("f3", 0))
                if val != 0: result[name] = {"val": val, "chg": chg}
        except: pass

    # 腾讯兜底（东财失败或字段缺失时补全）
    # 腾讯代码：usDJI道琼斯 usIXIC纳斯达克 usINX标普500 hkHSI恒生指数。
    # 日经225腾讯无稳定代码，依赖东财主源(100.N225)。
    tencent_ids = "usDJI,usIXIC,usINX,hkHSI"
    tnames = {"usDJI": "道琼斯", "usIXIC": "纳斯达克", "usINX": "标普500", "hkHSI": "恒生指数"}
    troot = curl(f"https://qt.gtimg.cn/q={tencent_ids}")
    if troot:
        for line in troot.strip().split("\n"):
            if "=" not in line: continue
            var = line.split("=", 1)[0].replace("v_", "").strip()
            name = tnames.get(var)
            if not name or name in result: continue
            try:
                f = line.split("=", 1)[1].strip('"').strip(";").split("~")
                # 腾讯：f[3]=现价 f[4]=昨收 涨跌幅%在 f[32]（美股）或 f[32]（部分）
                val = safe_float(f[3])
                chg = safe_float(f[32]) if len(f) > 32 else 0
                if val != 0: result[name] = {"val": val, "chg": chg}
            except: pass

    # 韩国KOSPI — 腾讯
    kospi = curl("https://qt.gtimg.cn/q=kr.KS11")
    if kospi:
        for line in kospi.strip().split("\n"):
            if "KS11" not in line: continue
            f = line.split("=", 1)[1].strip('"').strip(";").split("~")
            if len(f) > 32:
                val = safe_float(f[3]); chg = safe_float(f[32])
                if val != 0: result["韩国KOSPI"] = {"val": val, "chg": chg}
            break

    return result

# ═══════════════════════════════════════════
# 2. A股指数 — 腾讯 qt.gtimg.cn（24h稳定）
# ═══════════════════════════════════════════
def fetch_a():
    raw = curl("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688")
    if not raw: return {}
    cm = {"sh000001": "上证", "sz399001": "深证", "sz399006": "创业板", "sh000688": "科创50"}
    result = {}
    for line in raw.strip().split("\n"):
        if "=" not in line: continue
        var = line.split("=", 1)[0].replace("v_", "").strip()
        key = cm.get(var)
        if not key: continue
        f = line.split("=", 1)[1].strip('"').strip(";").split("~")
        if len(f) < 33: continue
        val = safe_float(f[3])
        chg = safe_float(f[32])
        if val != 0: result[key] = {"val": val, "chg": chg}
    return result

# ═══════════════════════════════════════════
# 3. 新！A股板块 — 东方财富行业板块（已有）+ 腾讯补充
# ═══════════════════════════════════════════
def fetch_sectors():
    """东方财富行业板块排行（主源）+ 腾讯 proxy.finance 兜底
    非交易时段东财push2时好时坏，腾讯源稳定返回最近交易日数据。"""
    raw = curl("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f2,f3,f12,f14")
    if raw:
        try:
            items = json.loads(raw).get("data", {}).get("diff", [])
            sectors = []
            for item in items:
                name = item.get("f14", "")
                chg = safe_float(item.get("f3", 0))
                if name: sectors.append({"name": name, "chg": chg, "code": item.get("f12", "")})
            # 只有拿到"非全零"涨跌幅时才用东财（非交易时段东财常返回名称但 chg 全 0，
            # 此时应落到腾讯兜底拿最近交易日真实涨跌幅）
            if sectors and any(s["chg"] != 0 for s in sectors):
                return sectors
        except: pass

    # 腾讯兜底（申万行业板块，非交易时段稳定）
    tq = curl("https://proxy.finance.qq.com/ifzqgtimg/appstock/app/mktHs/rank?l=20&p=1&t=01/averatio&o=-1")
    if tq:
        try:
            items = json.loads(tq).get("data", [])
            sectors = []
            for item in items:
                name = item.get("bd_name", "")
                chg = safe_float(item.get("bd_zdf", 0))
                if name: sectors.append({"name": name, "chg": chg, "code": item.get("bd_code", "")})
                # 顺带采集龙头股（nzg_* 字段）— 腾讯源带真实龙头，填补 leaders 空档
                _nk = item.get("nzg_name", "").strip()
                if name and _nk:
                    TQ_LEADERS.setdefault(name, []).append({
                        "n": _nk.replace(" ", ""),
                        "code": item.get("nzg_code", ""),
                        "c": safe_float(item.get("nzg_zdf", 0)),
                        "mv": 0,
                    })
            if sectors: return sectors
        except: pass
    return None

# ═══════════════════════════════════════════
# 4. 新！概念板块 — 同花顺热点题材（通过东方财富概念板块替代）
# ═══════════════════════════════════════════
def harvest_tq_leaders():
    """无条件从腾讯 rank 接口采集真实龙头股（nzg_* 字段）。
    腾讯 proxy.finance 24h 稳定，非交易时段也返回最近交易日龙头。
    用于补 East Money fs:b:{code} 成分股接口失败时的 leaders 空档。
    返回 {板块名: [ {n, code, c, mv}, ... ]}"""
    out = {}
    for t in ("01", "02"):
        tq = curl(f"https://proxy.finance.qq.com/ifzqgtimg/appstock/app/mktHs/rank?l=20&p=1&t={t}/averatio&o=-1")
        if not tq:
            continue
        try:
            for item in json.loads(tq).get("data", []):
                name = item.get("bd_name", "")
                _nk = (item.get("nzg_name", "") or "").strip()
                if name and _nk:
                    out.setdefault(name, []).append({
                        "n": _nk.replace(" ", ""),
                        "code": (item.get("nzg_code", "") or "").upper(),
                        "c": safe_float(item.get("nzg_zdf", 0)),
                        "mv": 0,
                    })
        except Exception:
            pass
    return out


def fetch_concept_sectors():
    """东方财富概念板块排行（主源）+ 腾讯 proxy.finance 兜底（t=02 概念板块）"""
    raw = curl("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:3&fields=f2,f3,f12,f14")
    if raw:
        try:
            items = json.loads(raw).get("data", {}).get("diff", [])
            concepts = []
            for item in items:
                name = item.get("f14", "")
                chg = safe_float(item.get("f3", 0))
                if name: concepts.append({"name": name, "chg": chg, "code": item.get("f12", "")})
            # 同 fetch_sectors：非交易时段东财常返回名称但 chg 全 0 → 落腾讯兜底
            if concepts and any(c["chg"] != 0 for c in concepts):
                return concepts
        except: pass

    # 腾讯兜底（概念板块，非交易时段稳定）
    tq = curl("https://proxy.finance.qq.com/ifzqgtimg/appstock/app/mktHs/rank?l=20&p=1&t=02/averatio&o=-1")
    if tq:
        try:
            items = json.loads(tq).get("data", [])
            concepts = []
            for item in items:
                name = item.get("bd_name", "")
                chg = safe_float(item.get("bd_zdf", 0))
                if name: concepts.append({"name": name, "chg": chg, "code": item.get("bd_code", "")})
                # 顺带采集龙头股（与 fetch_sectors 同一套 nzg_* 字段）
                _nk = item.get("nzg_name", "").strip()
                if name and _nk:
                    TQ_LEADERS.setdefault(name, []).append({
                        "n": _nk.replace(" ", ""),
                        "code": item.get("nzg_code", ""),
                        "c": safe_float(item.get("nzg_zdf", 0)),
                        "mv": 0,
                    })
            if concepts: return concepts
        except: pass
    return None

# ═══════════════════════════════════════════
# 5. 美股板块 — 腾讯us系列ETF（24h稳定，数据源修复）
# ═══════════════════════════════════════════
def fetch_us_sectors():
    """美股板块 — 腾讯 qt.gtimg.cn us系列ETF（稳定）
    东财push2的secids=100.QQQ接口在非交易时段不稳/返回空，改用腾讯。
    f[3]=现价, f[32]=涨跌幅%。数据非交易时段也返回最近交易日收盘值。"""
    etfs = "usQQQ,usSPY,usIWM,usXLK,usXLI,usXLV,usXLF,usXLE,usXLU,usXLY"
    raw = curl(f"https://qt.gtimg.cn/q={etfs}")
    if not raw:
        return None
    etf_map = {"usQQQ": "科技", "usSPY": "标普", "usIWM": "小盘", "usXLK": "信息技术",
               "usXLI": "工业", "usXLV": "医疗", "usXLF": "金融",
               "usXLE": "能源", "usXLU": "公用事业", "usXLY": "消费"}
    sectors = []
    for line in raw.strip().split("\n"):
        if "=" not in line: continue
        var = line.split("=", 1)[0].replace("v_", "").strip()
        name = etf_map.get(var)
        if not name: continue
        try:
            f = line.split("=", 1)[1].strip('"').strip(";").split("~")
            chg = safe_float(f[32]) if len(f) > 32 else 0
            val = safe_float(f[3]) if len(f) > 3 else 0
        except: continue
        if val != 0:
            sectors.append({"name": name, "chg": chg})
    return sectors[:10] if sectors else None

# ═══════════════════════════════════════════
# 6. 新！主力资金流向（百度股市通 PAE 替代）
#    东方财富资金流向：板块资金净流入排行
# ═══════════════════════════════════════════
def fetch_moneyflow():
    """东方财富板块资金流向排行（主源，非交易时段返回最近交易日数据）"""
    raw = curl("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t:2&fields=f12,f14,f62,f64,f66,f69,f70,f78")
    if not raw: return None
    try: items = json.loads(raw).get("data", {}).get("diff", [])
    except: return None
    if not items: return None
    flows = []
    for item in items:
        name = item.get("f14", "")
        if not name: continue
        flows.append({
            "name": name,
            "net_in_main": safe_float(item.get("f62", 0)),    # 主力净流入
            "net_in_small": safe_float(item.get("f66", 0)),   # 小单净流入
            "net_in_mid": safe_float(item.get("f64", 0)),     # 中单净流入
            "net_in_big": safe_float(item.get("f69", 0)),     # 大单净流入
            "net_in_super": safe_float(item.get("f70", 0)),   # 超大单净流入
            "net_main_pct": safe_float(item.get("f78", 0)),   # 主力净占比%
        })
    return flows

# ═══════════════════════════════════════════
# 7. 板块历史趋势 + 成分股（已有，略优化）
# ═══════════════════════════════════════════
def fetch_sector_stocks(code, limit=5):
    raw = curl(f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz={limit}&po=1&np=1&fltt=2&invt=2&fid=f3&fs=b:{code}&fields=f2,f3,f12,f14,f20")
    if not raw: return None
    try: items = json.loads(raw).get("data", {}).get("diff", [])
    except: return None
    if not items: return None
    stocks = []
    for item in items:
        name = item.get("f14", "")
        code_s = item.get("f12", "")
        chg = safe_float(item.get("f3", 0))
        try: mv = int(float(item.get("f20", 0)) / 100000000)
        except: mv = 0
        if name: stocks.append({"n": name, "code": code_s, "c": chg, "mv": mv})
    return stocks if stocks else None

def fetch_sector_hist(code, days=250):
    raw = curl(f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{code}&fields1=f1,f2,f3&fields2=f51,f53&klt=101&fqt=1&end=20500101&lmt={days}")
    if not raw: return None
    try: klines = json.loads(raw).get("data", {}).get("klines", [])
    except: return None
    result = []
    for k in klines:
        p = k.split(",")
        if len(p) >= 2:
            chg = safe_float(p[1])
            result.append({"date": p[0], "chg": chg})
    return result if result else None

# ═══════════════════════════════════════════
# 8. 新！个股PE/估值 — baostock + 新浪财经
# ═══════════════════════════════════════════
def fetch_pe_sina(code):
    """新浪财经PE核实"""
    raw = curl(f"https://finance.sina.com.cn/realstock/company/{code}/nc.shtml", timeout=10)
    if not raw: return None
    # 查找"市盈率TTM"
    m = re.search(r'市盈率.*?(\d+\.?\d*)', raw)
    if m: return safe_float(m.group(1))
    return None

def fetch_last_trade_date():
    """通过baostock获取最近交易日"""
    try:
        sys.path.insert(0, "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages")
        import baostock as bs
        lg = bs.login()
        if lg.error_code != "0": return None
        rs = bs.query_all_stock(today)
        dates = set()
        while rs.next():
            row = rs.get_row_data()
            if len(row) >= 6 and row[2]:
                dates.add(row[2][:10])
        bs.logout()
        if not dates: return None
        dates = sorted(dates, reverse=True)
        return dates[0]
    except:
        return None

# ═══════════════════════════════════════════
# 9. 涨跌分布 + 成交额（修复非交易时段bug）
# ═══════════════════════════════════════════
def fetch_overview():
    """涨跌分布+成交额（非交易时段也尝试获取最近交易日数据，失败用缓存）"""
    result = {"up": 0, "flat": 0, "down": 0, "zt": 0, "dt": 0, "vol": 0.0}
    # 涨跌家数 — 东财全市场（非交易时段返回最近交易日数据）
    raw = curl("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=6000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f3", timeout=30)
    if raw:
        try:
            items = json.loads(raw).get("data", {}).get("diff", [])
            up = down = flat = 0
            for item in items:
                c = safe_float(item.get("f3", 0))
                if c > 0: up += 1
                elif c < 0: down += 1
                else: flat += 1
            # 合理性校验：A股全市场约 5000+ 只，若样本 <1000 说明东财返回被截断/降级
            # （实测会返回 up:100,flat:0,down:0 的伪数据），弃用并由调用方走快照恢复
            if up + down + flat >= 1000:
                result["up"], result["down"], result["flat"] = up, down, flat
            else:
                print(f"  涨跌分布: 东财样本仅 {up + down + flat} 只(疑似截断), 弃用")
        except: pass
    # 涨跌家数兜底 — 指数成分聚合（上证 f104/f105/f106 = 涨/跌/平 家数，深证同理）
    # 东财 clist 常被截断返回 100 只伪数据；此接口稳定返回权威家数，上证+深证≈全A。
    if result["up"] + result["down"] + result["flat"] < 1000:
        raw2 = curl("https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001&fields=f12,f104,f105,f106&ut=fa5fd1943c7b386f172d6893dbfba10b", timeout=20)
        if raw2:
            try:
                diff = json.loads(raw2).get("data", {}).get("diff", [])
                u = d = fl = 0
                for it in diff:
                    u += int(safe_float(it.get("f104", 0)))
                    d += int(safe_float(it.get("f105", 0)))
                    fl += int(safe_float(it.get("f106", 0)))
                if u + d + fl >= 1000:
                    result["up"], result["down"], result["flat"] = u, d, fl
                    print(f"  涨跌分布: 指数聚合兜底 ↑{u} →{fl} ↓{d}")
            except: pass
    # 涨停/跌停 — 专用涨跌停池接口（权威，返回 tc=总数）
    for api, key in [
        ("https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=1&sort=fbt%3Aasc&date=", "zt"),
        ("https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=1&sort=fund%3Aasc&date=", "dt"),
    ]:
        r = curl(api + today.replace("-", ""), timeout=20)
        if r:
            try:
                tc = int(safe_float(json.loads(r).get("data", {}).get("tc", 0)))
                if tc >= 0:
                    result[key] = tc
            except: pass
    # 兜底：若涨跌停池仍为 0，用 clist T:UP/T:DOWN 计数
    for tag, key in [("UP", "zt"), ("DOWN", "dt")]:
        if result[key] > 0:
            continue
        r = curl(f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=500&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6+T:{tag}&fields=f12", timeout=20)
        if r:
            try:
                n = len(json.loads(r).get("data", {}).get("diff", []))
                if n > 0:
                    result[key] = n
            except: pass
    # 成交额 — 腾讯接口24h可用。
    # f[35] 形如 "3926.64/45014514/87233056497"（价/量/成交额元），第三段/1e8 = 亿元
    ri = curl("https://qt.gtimg.cn/q=sh000001")
    if ri:
        for line in ri.strip().split("\n"):
            if "sh000001" not in line: continue
            f = line.split("=", 1)[1].strip('"').strip(";").split("~")
            try:
                parts = f[35].split("/")
                if len(parts) >= 3:
                    v = float(parts[2]) / 1e8
                    if v > 0:
                        result["vol"] = round(v, 1)
            except Exception:
                pass
            break
    return result

# ═══════════════════════════════════════════
# 10. 建议关注 + 风险提示（保留为默认，后续可接入AI生成）
# ═══════════════════════════════════════════
def default_picks():
    return {
        "picks": [
            {"tag": "🔥", "tagType": "hot", "title": "半导体 / AI算力", "reason": "全球AI资本开支持续高景气。关注：中芯国际、北方华创"},
            {"tag": "⚡", "tagType": "warm", "title": "电力电网 / 特高压", "reason": "夏季用电高峰+新能源并网需求。关注：国电南瑞、许继电气"},
            {"tag": "📈", "tagType": "warm", "title": "机器人 / 具身智能", "reason": "Optimus量产预期+国内政策扶持。关注：汇川技术、绿的谐波"},
            {"tag": "👀", "tagType": "cold", "title": "消费电子 / 果链", "reason": "Vision Pro新品+AI换机预期。关注：立讯精密、韦尔股份"}
        ],
        "risks": [
            {"level": "high", "icon": "🔴", "lbl": "高", "title": "半导体短期过热", "desc": "近3月涨幅超25%，PE高企，勿追高"},
            {"level": "mid", "icon": "🟡", "lbl": "中", "title": "美联储降息预期反复", "desc": "非农超预期或推迟降息，成长股承压"},
            {"level": "mid", "icon": "🟡", "lbl": "中", "title": "人民币汇率波动", "desc": "美元走强影响进口依赖型企业利润"},
            {"level": "low", "icon": "🟢", "lbl": "低", "title": "地缘政治摩擦", "desc": "关注实体清单风险"}
        ]
    }

# ═══════════════════════════════════════════
# 11. 缓存管理
# ═══════════════════════════════════════════
def load_last_data():
    last = {"global": {}, "a_indices": {}, "sectors": [], "us_sectors": [], "concept_sectors": [],
            "moneyflow": [], "distribution": {"up": 0, "flat": 0, "down": 0},
            "sentiment": {"zt": 0, "dt": 0, "vol": 0}, "leaders": {}}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                last = json.load(f)
        except: pass
    return last

# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════
def main():
    print(f"[{now.strftime('%H:%M:%S')}] nicetoken v3 更新 交易={is_trading} 日期={today}")

    # ── 并行采集所有数据 ──
    global_idx = fetch_global()
    a_idx = fetch_a()
    sectors = fetch_sectors()
    concepts = fetch_concept_sectors()
    us_sectors = fetch_us_sectors()
    moneyflow = fetch_moneyflow()
    overview = fetch_overview()
    sector_hist = {}
    leaders = {}

    # ── 兜底数据源：优先 .last_good.json 快照（含上次完整好数据），退回上次 data.json ──
    # 注意：交易时段也必须加载快照 —— 东财 push2 间歇性挂掉时，本轮 moneyflow/sectors
    # 会为空，需要从快照恢复；否则 data.json 里这些字段会被清空。
    last_data = load_last_data()
    good_data = None
    if os.path.exists(GOOD_FILE):
        try:
            good_data = json.load(open(GOOD_FILE, encoding="utf-8"))
        except Exception:
            good_data = None
    if not good_data:
        good_data = last_data
    if not good_data:
        good_data = {}

    if not is_trading:
        use_good = False
        # 检查哪些数据缺了
        if not global_idx:
            global_idx = good_data.get("global", {})
            if global_idx: print("  全球: 使用上次数据")
        if not a_idx:
            a_idx = good_data.get("a_indices", {})
            if a_idx: print("  A股: 使用上次数据")
        if not sectors:
            sectors = good_data.get("sectors", [])
            if sectors: print(f"  板块: 使用上次数据 {len(sectors)} 个")
        if not concepts:
            concepts = good_data.get("concept_sectors", [])
            if concepts: print(f"  概念: 使用上次数据 {len(concepts)} 个")
        if not us_sectors:
            us_sectors = good_data.get("us_sectors", [])
            if us_sectors: print(f"  美股: 使用上次数据 {len(us_sectors)} 个")
        if not moneyflow:
            moneyflow = good_data.get("moneyflow", [])
            if moneyflow: print(f"  资金: 使用上次数据 {len(moneyflow)} 个")

    # ── 涨跌分布无条件兜底（交易时段东财也可能返回截断伪数据 up:100,flat:0,down:0）──
    # 合理性判定：真实市场 up/down 不会同时为 0（除非全平），且 up+flat+down 应 > 1000
    _dist_ok = lambda dv: (dv.get("up", 0) + dv.get("down", 0) + dv.get("flat", 0)) >= 1000
    if not _dist_ok({"up": overview["up"], "down": overview["down"], "flat": overview["flat"]}):
        _ld = good_data.get("distribution", {})
        _ls = good_data.get("sentiment", {})
        if _dist_ok(_ld):
            overview = {"up": _ld.get("up", 0), "flat": _ld.get("flat", 0), "down": _ld.get("down", 0),
                       "zt": _ls.get("zt", 0), "dt": _ls.get("dt", 0), "vol": _ls.get("vol", 0)}
            print("  涨跌: 使用上次数据")
        elif not any([overview["up"], overview["down"]]):
            # 所有源都拿不到真实分布 → 标注为不展示（置 0），避免显示伪数据
            print("  涨跌: 无可用数据（东财降级），本轮不展示涨跌分布")
    # 成交额同理：0 视为无数据
    if not overview.get("vol"):
        _ls = good_data.get("sentiment", {})
        if _ls.get("vol"):
            overview["vol"] = _ls["vol"]

    # ── 资金流向无条件兜底（东财 push2 间歇性挂掉时为空）──
    if not moneyflow and good_data.get("moneyflow"):
        moneyflow = good_data["moneyflow"]
        print(f"  资金: 东财无响应，使用上次数据 {len(moneyflow)} 条")
    # 板块/概念/美股 无条件兜底（交易时段东财降级时避免半成品页面）
    if not sectors and good_data.get("sectors"):
        sectors = good_data["sectors"]
        print(f"  板块: 东财无响应，使用上次数据 {len(sectors)} 个")
    if not concepts and good_data.get("concept_sectors"):
        concepts = good_data["concept_sectors"]
        print(f"  概念: 使用上次数据 {len(concepts)} 个")
    if not us_sectors and good_data.get("us_sectors"):
        us_sectors = good_data["us_sectors"]
        print(f"  美股: 使用上次数据 {len(us_sectors)} 个")

    # ── 打印状态 ──
    if global_idx:
        print("  全球: " + " ".join([f'{k}={v["val"]}({v["chg"]}%)' for k, v in global_idx.items()]))
    if a_idx:
        print("  A股: " + " ".join([f'{k}={v["val"]}({v["chg"]}%)' for k, v in a_idx.items()]))
    print(f"  行业板块: {len(sectors) if sectors else 0} 个")
    print(f"  概念板块: {len(concepts) if concepts else 0} 个")
    print(f"  美股板块: {len(us_sectors) if us_sectors else 0} 个")
    print(f"  资金流向: {len(moneyflow) if moneyflow else 0} 条")
    print(f"  涨跌: ↑{overview['up']} →{overview['flat']} ↓{overview['down']} 涨停:{overview['zt']} 跌停:{overview['dt']} 成交:{overview['vol']}亿")

    # ── 板块历史趋势（行业板块前10，仅交易时段）──
    if sectors and is_trading:
        for s in sectors[:10]:
            code = s.get("code")
            if code:
                hist = fetch_sector_hist(code, 250)
                if hist:
                    sector_hist[s["name"]] = hist
                    print(f"  趋势: {s['name']} ({len(hist)}天)")
                time.sleep(0.3)

    # ── 板块成分股（龙头股）──
    if sectors:
        for s in sectors[:10]:
            code = s.get("code")
            if code:
                if is_trading:
                    stocks = fetch_sector_stocks(code, 5)
                    if stocks:
                        leaders[s["name"]] = stocks
                        print(f"  龙头: {s['name']} ({len(stocks)}只)")
                    time.sleep(0.3)
                else:
                    if s["name"] in good_data.get("leaders", {}):
                        leaders[s["name"]] = good_data["leaders"][s["name"]]
    if not is_trading:
        ld = good_data.get("leaders", {})
        if ld:
            if not leaders:
                leaders = dict(ld)
                print(f"  龙头: 使用上次数据 {len(leaders)} 个板块")
            else:
                for k, v in ld.items():
                    if k not in leaders:
                        leaders[k] = v

    # ── 腾讯兜底顺带采集的龙头股（真实数据）优先覆盖 ──
    if TQ_LEADERS:
        for k, v in TQ_LEADERS.items():
            leaders[k] = v
        print(f"  龙头: 腾讯源补充 {len(TQ_LEADERS)} 个板块")
    else:
        # 东财板块排行成功时不会走腾讯兜底分支 → TQ_LEADERS 为空。
        # 而东财 fs:b:{code} 成分股接口极不稳定（push2 间歇 Empty reply），
        # 交易时段 leaders 经常为空。此处无条件再拉一次腾讯 rank 补 leaders。
        _tq_leaders = harvest_tq_leaders()
        if _tq_leaders:
            for k, v in _tq_leaders.items():
                leaders.setdefault(k, v)
                if not leaders[k]:
                    leaders[k] = v
            print(f"  龙头: 腾讯源补采 {len(_tq_leaders)} 个板块")
    # 若仍然为空，从快照恢复（避免页面龙头股区全空）
    if not leaders:
        _ld = good_data.get("leaders", {}) if good_data else {}
        if _ld:
            leaders = dict(_ld)
            print(f"  龙头: 使用快照数据 {len(leaders)} 个板块")

    # ── 构建data.json ──
    data = {
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": today,
        "global": global_idx,
        "a_indices": a_idx,
        "sectors": [{"name": s["name"], "chg": s["chg"], "code": s.get("code", "")} for s in (sectors or [])[:15]],
        "concept_sectors": [{"name": s["name"], "chg": s["chg"], "code": s.get("code", "")} for s in (concepts or [])[:15]],
        "us_sectors": us_sectors[:10] if us_sectors else [],
        "hk_sectors": good_data.get("hk_sectors", []) if not is_trading and not sectors else [],
        "moneyflow": moneyflow[:10] if moneyflow else [],
        "distribution": {"up": overview["up"], "flat": overview["flat"], "down": overview["down"]},
        "sentiment": {"zt": overview["zt"], "dt": overview["dt"], "vol": overview["vol"]},
        "picks_risks": default_picks(),
        "leaders": leaders
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ── history.json ──
    with open(HIST_FILE, "w", encoding="utf-8") as f:
        json.dump(sector_hist, f, ensure_ascii=False, indent=2)

    # ── 保存完整数据快照（供非交易时段恢复使用）──
    # 修复：只有交易时段且有真实板块数据时才更新快照，避免空数据污染.last_good.json。
    # 另外：本轮若某些字段为空（东财降级），保留快照中已有的非空值，防止把好数据覆盖成空。
    if is_trading and sectors:
        _good_data = dict(data)
        _prev = {}
        try:
            _prev = json.load(open(GOOD_FILE, encoding="utf-8"))
        except Exception:
            pass
        for _k in ("moneyflow", "sectors", "concept_sectors", "us_sectors"):
            if not _good_data.get(_k) and _prev.get(_k):
                _good_data[_k] = _prev[_k]
        # 涨跌分布：本轮不可信（全 0）时保留快照旧值
        _d = _good_data.get("distribution", {})
        if (_d.get("up", 0) + _d.get("down", 0) + _d.get("flat", 0)) < 1000:
            _pd = _prev.get("distribution", {})
            if (_pd.get("up", 0) + _pd.get("down", 0) + _pd.get("flat", 0)) >= 1000:
                _good_data["distribution"] = _pd
                _ps = _prev.get("sentiment", {})
                if _ps.get("zt") or _ps.get("dt"):
                    _good_data["sentiment"] = _ps
        # leaders 同理：本轮为空时保留旧值
        if not _good_data.get("leaders") and _prev.get("leaders"):
            _good_data["leaders"] = _prev["leaders"]
        _good_data["saved_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
        with open(GOOD_FILE, "w", encoding="utf-8") as f:
            json.dump(_good_data, f, ensure_ascii=False, indent=2)
        print(f"  [快照] .last_good.json 已更新（{len(sectors)} 个板块）")
    else:
        print(f"  [快照] 非交易时段或板块为空，保留原有 .last_good.json")

    print(f"\n[OK] data.json + history.json 已保存")

if __name__ == "__main__":
    main()
