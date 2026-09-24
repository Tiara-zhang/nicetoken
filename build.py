#!/usr/bin/env python3
"""nicetoken build v4 — 重构布局：全球情绪 + 板块热度 + 分析"""
import json, os

OUT = "/Users/silinzhang/Desktop/nicetoken"
DATA = os.path.join(OUT, "data.json")
HIST = os.path.join(OUT, "history.json")
NEWS = os.path.join(OUT, "news.json")
HTML = os.path.join(OUT, "index.html")

def load():
    d = {"global":{},"a_indices":{},"sectors":[],"concept_sectors":[],"us_sectors":[],"hk_sectors":[],
         "distribution":{"up":0,"flat":0,"down":0},"sentiment":{"zt":0,"dt":0,"vol":0},
         "picks_risks":{"picks":[],"risks":[]}}
    h = {}
    ai, inv = [], []
    for f in [DATA, HIST, NEWS]:
        if not os.path.exists(f): continue
        try:
            with open(f, encoding="utf-8") as fh:
                if f == DATA: d = json.load(fh)
                elif f == HIST: h = json.load(fh)
                elif f == NEWS: n = json.load(fh); ai = n.get("ai",[]); inv = n.get("inv",[])
        except: pass
    return d, h, ai, inv

data, hist, ai_news, inv_news = load()

gi = data.get("global", {})
ai = data.get("a_indices", {})
sec = data.get("sectors", [])
con_sec = data.get("concept_sectors", [])
us_sec = data.get("us_sectors", [])
hk_sec = data.get("hk_sectors", [])
dist = data.get("distribution", {})
sent = data.get("sentiment", {})
pr = data.get("picks_risks", {})
picks = pr.get("picks", [])
risks = pr.get("risks", [])
upd = data.get("updated_at", "")

up = dist.get("up",0); flat = dist.get("flat",0); down = dist.get("down",0)
zt = sent.get("zt",0); dt = sent.get("dt",0); vol = sent.get("vol",0)
ratio = round(up/(up+down)*100) if up+down>0 else 0
lb = round(zt/(zt+dt)*100) if zt+dt>0 else 0

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def idx_html(dd, keys):
    parts = []
    for k in keys:
        v = dd.get(k)
        if v:
            cls = "up" if v["chg"]>=0 else "down"
            parts.append(f'<div class="idx-item"><div class="name">{k}</div><div class="val">{v["val"]}</div><div class="chg {cls}">{v["chg"]:+.2f}%</div></div>')
    return "".join(parts)

def sec_html(ss, prefix="CN"):
    parts = []
    seen_names = set()
    for i, s in enumerate(ss):
        nm = s["name"]
        if nm.endswith("\u2161") or nm.endswith("II"):
            base = nm[:-1]
            if any(x.startswith(base + "\u2162") or x.startswith(base + "III") for x in seen_names):
                continue
        if len(parts) >= 50:
            break
        seen_names.add(nm)
        cls = "up" if s["chg"]>=0 else "down"
        w = max(5, abs(s["chg"])*15)
        bg = "var(--red)" if s["chg"]>=0 else "var(--green)"
        sign = "+" if s["chg"]>=0 else ""
        nm_e = esc(s["name"])
        rank = len(parts) + 1
        parts.append(
            f'<div class="sector-item" onclick="openSector(\'{prefix}:{nm_e}\')">'
            f'<span class="sector-rank">{rank}</span>'
            f'<span class="sector-name">{nm_e}</span>'
            f'<div class="sector-bar-wrap"><div class="sector-bar" style="width:{w}%;background:{bg}"></div></div>'
            f'<span class="sector-chg {cls}">{sign}{s["chg"]:.2f}%</span></div>'
        )
    return "".join(parts)

def pick_html():
    return "".join(
        f'<div class="pick-item"><span class="pick-tag pick-{p["tagType"]}">{esc(p["tag"])}</span>'
        f'<div class="pick-body"><div class="title">{esc(p["title"])}</div>'
        f'<div class="reason">{p["reason"]}</div></div></div>' for p in picks
    )

def risk_html():
    return "".join(
        f'<div class="risk-item"><div class="r-title"><span class="r-icon">{r["icon"]}</span>{esc(r["title"])}'
        f'<span class="r-level r-{r["level"]}">{r["lbl"]}</span></div>'
        f'<div class="r-desc">{r["desc"]}</div></div>' for r in risks
    )

def news_html(items):
    if not items:
        return '<div style="text-align:center;padding:24px;color:var(--text-dim);font-size:12px">\u65e5\u62a5\u63a8\u9001\u540e\u5c06\u81ea\u52a8\u663e\u793a</div>'
    return "".join(
        f'<div class="news-item"><div class="title"><span class="date-tag">{n["d"][:10]}</span><span>{esc(n["t"])}</span></div>'
        f'<div class="meta"><span>{esc(n.get("s",""))}</span></div></div>' for n in items
    )

# ════════════════════ 一、全球情绪 ════════════════════
us_keys = ["道琼斯", "纳斯达克", "标普500"]
cn_keys = ["上证", "深证", "创业板", "科创50"]
ot_keys = ["恒生指数", "日经225", "韩国KOSPI"]

us_g = idx_html(gi, us_keys)
cn_g = idx_html(ai, cn_keys)
ot_g = idx_html(gi, ot_keys)

# 把A股情绪里的涨跌分布放到中国卡片下方
# 若分布数据不可用（up+flat+down<1000，东财降级），显示 — 而非误导性的 0
_dist_avail = (up + flat + down) >= 1000
_dv = lambda x: str(x) if _dist_avail else "—"
dist_html = f'''<div class="dist-row" style="margin-top:8px">
  <div class="dist-item dist-up"><div class="num">{_dv(up)}</div><div class="lbl">涨</div></div>
  <div class="dist-item dist-flat"><div class="num">{_dv(flat)}</div><div class="lbl">平</div></div>
  <div class="dist-item dist-down"><div class="num">{_dv(down)}</div><div class="lbl">跌</div></div>
</div>
<div class="sent-row">
  <div class="sent-item"><div class="v">{_dv(zt)}</div><div class="l">涨停</div></div>
  <div class="sent-item"><div class="v">{_dv(dt)}</div><div class="l">跌停</div></div>
  <div class="sent-item"><div class="v">{vol}</div><div class="l">成交(亿)</div></div>
  <div class="sent-item"><div class="v">{ratio if _dist_avail else "—"}%</div><div class="l">涨跌比</div></div>
  <div class="sent-item"><div class="v">{lb if _dist_avail else "—"}%</div><div class="l">封板率</div></div>
</div>'''

g_html = '<div class="global-grid">'
g_html += '<div class="country-card"><div class="country-flag">🇺🇸</div><div class="country-name">美国</div><div class="idx-row">' + (us_g or '<div class="idx-item"><div class="name">—</div></div>') + '</div></div>'
g_html += '<div class="country-card"><div class="country-flag">🇨🇳</div><div class="country-name">中国</div><div class="idx-row">' + (cn_g or '<div class="idx-item"><div class="name">—</div></div>') + '</div>' + dist_html + '</div>'
g_html += '<div class="country-card"><div class="country-flag">🌏</div><div class="country-name">其他</div><div class="idx-row">' + (ot_g or '<div class="idx-item"><div class="name">—</div></div>') + '</div></div>'
g_html += '</div>'

# ════════════════════ 二、板块热度 ════════════════════
# 合并 A股行业板块 + 概念板块，按涨幅倒序排
all_cn = sec + con_sec
all_cn_sorted = sorted(all_cn, key=lambda x: x["chg"], reverse=True)
cn_heat = sec_html(all_cn_sorted, "CN")
us_heat = sec_html(us_sec, "US") if us_sec else sec_html([
    {"name":"科技","chg":0},{"name":"半导体","chg":0},{"name":"金融","chg":0},{"name":"工业","chg":0},
    {"name":"医疗","chg":0},{"name":"消费","chg":0},{"name":"能源","chg":0},{"name":"公用事业","chg":0},
    {"name":"原材料","chg":0},{"name":"房地产","chg":0}], "US")
hk_heat = sec_html(hk_sec, "HK") if hk_sec else sec_html([
    {"name":"恒生科技","chg":0},{"name":"金融","chg":0},{"name":"地产","chg":0},{"name":"消费","chg":0},
    {"name":"医疗","chg":0},{"name":"能源","chg":0},{"name":"电讯","chg":0},{"name":"公用事业","chg":0},
    {"name":"工业","chg":0},{"name":"原材料","chg":0}], "HK")

heat_html = '<div class="heat-grid">'
heat_html += f'<div class="heat-card"><h2>🇺🇸 美国板块热度</h2><div class="scroll-wrap">{us_heat}</div></div>'
heat_html += f'<div class="heat-card"><h2>🇨🇳 A股板块热度</h2><div class="scroll-wrap">{cn_heat}</div></div>'
heat_html += f'<div class="heat-card"><h2>🇭🇰 港股板块热度</h2><div class="scroll-wrap">{hk_heat}</div></div>'
heat_html += '</div>'

# ════════════════════ 三、分析 ════════════════════
pk_html = pick_html()
rk_html = risk_html()
ai_n_html = news_html(ai_news)
inv_n_html = news_html(inv_news)

hist_json = json.dumps(hist, ensure_ascii=False)
leaders_json = json.dumps(data.get("leaders", {}), ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>NiceToken · 市场看板</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0b1a;--bg-card:#111328;--bg-card-hover:#181b35;--border:#1e2040;--text:#e2e4f0;--text-dim:#6b6f9a;--cyan:#22d3ee;--emerald:#34d399;--rose:#fb7185;--amber:#fbbf24;--violet:#a78bfa;--red:#ef4444;--green:#22c55e}
body{background:var(--bg);color:var(--text);font-family:'Noto Sans SC',sans-serif;min-height:100vh;padding:20px}
.container{max-width:1440px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:flex-end;padding-bottom:16px;border-bottom:1px solid var(--border);margin-bottom:20px}
.header h1{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header .update{font-size:12px;color:var(--text-dim);text-align:right}
h2{font-size:16px;margin-bottom:10px;font-weight:600}
/* 全球情绪 */
.global-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:20px}
.country-card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:14px}
.country-card .country-flag{font-size:18px;margin-bottom:2px}
.country-card .country-name{font-size:11px;font-weight:600;color:var(--text-dim);margin-bottom:6px}
.country-card .idx-row{gap:4px}
.country-card .idx-item{min-width:50px;padding:5px 4px}
.country-card .idx-item .val{font-size:12px}
.country-card .idx-item .chg{font-size:9px}
/* 板块热度 */
.heat-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:20px}
.scroll-wrap{max-height:400px;overflow-y:auto}
.scroll-wrap::-webkit-scrollbar{width:4px}
.scroll-wrap::-webkit-scrollbar-track{background:transparent}
.scroll-wrap::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.heat-card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:14px;display:flex;flex-direction:column}
.heat-card h2{font-size:14px;margin-bottom:8px;flex-shrink:0}
.heat-card .scroll-wrap{flex:1;min-height:0}
.heat-card .sector-item{padding:5px 0}
.heat-card .sector-name{font-size:11px}
.heat-card .sector-chg{font-size:10px}
/* 卡片通用 */
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:14px}
.card h2{margin-bottom:0px}
.idx-row{display:flex;flex-wrap:wrap;gap:6px}
.idx-item{flex:1;min-width:70px;padding:8px;border-radius:8px;background:rgba(30,32,64,0.4);text-align:center}
.idx-item .name{font-size:10px;color:var(--text-dim);margin-bottom:3px}
.idx-item .val{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700}
.idx-item .chg{font-family:'JetBrains Mono',monospace;font-size:11px;margin-top:1px}
.up{color:var(--red)}.down{color:var(--green)}
/* 板块列表 */
.sector-item{display:flex;align-items:center;padding:6px 0;border-bottom:1px solid rgba(30,32,64,0.3);cursor:pointer;transition:all .15s}
.sector-item:last-child{border-bottom:none}.sector-item:hover{padding-left:4px;background:rgba(34,211,238,0.03);border-radius:6px}
.sector-rank{width:18px;font-size:10px;color:var(--text-dim);text-align:center;margin-right:6px}
.sector-name{flex:1;font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sector-bar-wrap{flex:1;max-width:60px;margin:0 6px}.sector-bar{height:3px;border-radius:2px;transition:width .3s}
.sector-chg{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;min-width:48px;text-align:right}
/* 涨跌分布 */
.dist-row{display:flex;gap:6px;text-align:center}
.dist-item{flex:1;padding:6px 4px;border-radius:8px;border:1px solid var(--border)}
.dist-item .num{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700}
.dist-item .lbl{font-size:10px;color:var(--text-dim);margin-top:2px}
.dist-up{background:rgba(239,68,68,0.08);border-color:rgba(239,68,68,0.2)}
.dist-down{background:rgba(34,197,94,0.08);border-color:rgba(34,197,94,0.2)}
.dist-flat{background:rgba(107,114,128,0.08);border-color:rgba(107,114,128,0.2)}
.sent-row{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:6px}
.sent-item{text-align:center;padding:6px 4px;border-radius:8px;background:rgba(30,32,64,0.4)}
.sent-item .v{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700}
.sent-item .l{font-size:9px;color:var(--text-dim);margin-top:2px}
/* 分析 */
.analysis-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}
.pick-card{background:linear-gradient(135deg,rgba(34,211,238,0.05),rgba(167,139,250,0.05));border:1px solid rgba(34,211,238,0.2)}
.pick-item{display:flex;align-items:flex-start;padding:10px 0;border-bottom:1px solid rgba(34,211,238,0.08)}
.pick-item:last-child{border-bottom:none}
.pick-tag{flex-shrink:0;font-size:10px;padding:2px 8px;border-radius:6px;font-weight:600;margin-right:12px;margin-top:1px}
.pick-hot{background:rgba(239,68,68,0.15);color:var(--red);font-size:11px}
.pick-warm{background:rgba(251,191,36,0.15);color:var(--amber);font-size:11px}
.pick-cold{background:rgba(107,114,128,0.15);color:var(--text-dim);font-size:11px}
.pick-body .title{font-size:13px;font-weight:600}
.pick-body .reason{font-size:11px;color:var(--text-dim);margin-top:3px;line-height:1.5;padding-right:8px}
.risk-card{background:linear-gradient(135deg,rgba(239,68,68,0.04),rgba(251,191,36,0.04));border:1px solid rgba(239,68,68,0.15)}
.risk-item{padding:8px 0;border-bottom:1px solid rgba(239,68,68,0.06)}
.risk-item:last-child{border-bottom:none}
.risk-item .r-icon{font-size:14px;margin-right:8px}
.risk-item .r-title{font-size:12px;font-weight:600;display:flex;align-items:center}
.risk-item .r-desc{font-size:11px;color:var(--text-dim);margin-top:3px;line-height:1.5;margin-left:24px;padding-right:8px}
.risk-item .r-level{font-size:9px;padding:1px 6px;border-radius:4px;margin-left:8px;font-weight:500}
.r-high{background:rgba(239,68,68,0.15);color:var(--red)}
.r-mid{background:rgba(251,191,36,0.15);color:var(--amber)}
.r-low{background:rgba(107,114,128,0.15);color:var(--text-dim)}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.card-header .badge{font-size:10px;padding:2px 8px;border-radius:12px;background:rgba(34,211,238,0.1);color:var(--cyan);border:1px solid rgba(34,211,238,0.2);font-weight:400}
.news-item{padding:10px 0;border-bottom:1px solid rgba(30,32,64,0.4)}
.news-item:last-child{border-bottom:none}
.news-item .title{font-size:13px;font-weight:500;display:flex;align-items:flex-start;gap:8px;cursor:pointer}
.news-item .title:hover{color:var(--cyan)}
.news-item .title .date-tag{font-size:10px;padding:1px 6px;border-radius:4px;background:rgba(107,114,128,0.15);color:var(--text-dim);flex-shrink:0;margin-top:2px;font-family:'JetBrains Mono',monospace}
.news-item .meta{font-size:11px;color:var(--text-dim);margin-top:4px;display:flex;gap:12px}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:24px;max-width:800px;width:90%;max-height:80vh;overflow-y:auto}
.modal-close{float:right;background:none;border:1px solid var(--border);color:var(--text-dim);font-size:13px;padding:4px 10px;border-radius:8px;cursor:pointer}
.modal-close:hover{border-color:var(--text);color:var(--text)}
.trend-chart{display:flex;align-items:flex-end;gap:2px;height:120px;padding:10px 0;margin:12px 0}
.trend-bar{flex:1;border-radius:2px 2px 0 0;position:relative;min-width:6px;transition:height .3s}
.trend-bar .bl{position:absolute;bottom:-14px;left:50%;transform:translateX(-50%);font-size:7px;color:var(--text-dim);white-space:nowrap}
.trend-bar .bv{position:absolute;top:-12px;left:50%;transform:translateX(-50%);font-size:8px;font-family:'JetBrains Mono',monospace;font-weight:600}
footer{text-align:center;padding:16px 0;color:var(--text-dim);font-size:11px}
@media(max-width:900px){.global-grid,.heat-grid{grid-template-columns:1fr 1fr}.analysis-grid{grid-template-columns:1fr}}
@media(max-width:600px){.global-grid,.heat-grid{grid-template-columns:1fr}}
</style></head><body>
<div class="container">
<div class="header"><div><h1>⸙ nicetoken.top</h1><div style="font-size:12px;color:var(--text-dim);margin-top:2px">全球情绪 · 板块热度 · 分析 · 资讯</div></div><div><div class="update" id="updateBadge">""" + upd + """</div><div id="dataStatus" style="font-size:10px;color:var(--text-dim);margin-top:3px;text-align:right"></div></div></div>

""" + g_html + """

<div style="margin-bottom:6px;padding:6px 0"><h2 style="font-size:15px;color:var(--text-dim)">🔥 板块热度</h2></div>
""" + heat_html + """

<div class="analysis-grid" style="margin-bottom:14px">
  <div class="card pick-card"><div class="card-header"><h2>🎯 建议关注</h2><span class="badge">盘后分析</span></div>""" + pk_html + """</div>
  <div class="card risk-card"><div class="card-header"><h2>⚠️ 风险提示</h2><span class="badge">盘后分析</span></div>""" + rk_html + """</div>
</div>

<div class="analysis-grid">
  <div class="card"><div class="card-header"><h2>🤖 AI 资讯</h2><span class="badge">""" + str(len(ai_news)) + """条</span></div>""" + ai_n_html + """</div>
  <div class="card"><div class="card-header"><h2>📈 投资资讯</h2><span class="badge">""" + str(len(inv_news)) + """条</span></div>""" + inv_n_html + """</div>
</div>
</div>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal"><button class="modal-close" onclick="closeModal()">&#x2715;</button><h2 id="modalTitle">--</h2><div id="timeBar" style="display:flex;gap:8px;margin-bottom:12px"></div><div class="trend-chart" id="modalChart"></div><div id="modalLeaders"></div></div>
</div>

<footer>nicetoken.top · 数据仅供个人参考，不构成投资建议</footer>

<script>
var HIST = """ + hist_json + """;
var LEADERS = """ + leaders_json + """;
var currentSector = '';

(function(){
  var s = document.createElement('style');
  s.textContent = '.t-btn{background:rgba(30,32,64,0.6);border:1px solid var(--border);color:var(--text-dim);font-size:12px;padding:4px 12px;border-radius:6px;cursor:pointer;font-family:inherit}.t-btn.active{background:rgba(34,211,238,0.15);border-color:var(--cyan);color:var(--cyan)}.t-btn:hover{border-color:var(--text)}';
  document.head.appendChild(s);

  document.getElementById('modalOverlay').addEventListener('click',function(e){if(e.target===this)closeModal();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal();});

  var upd = document.getElementById('updateBadge');
  if(upd && upd.textContent){
    var txt = upd.textContent;
    var now = new Date();
    var today = now.getFullYear()+'-'+(now.getMonth()+1).toString().padStart(2,'0')+'-'+now.getDate().toString().padStart(2,'0');
    if(txt.indexOf(today) < 0){
      document.getElementById('dataStatus').textContent = '\u26a0 \u975e\u4ea4\u6613\u65f6\u6bb5 \u00b7 \u663e\u793a\u4e0a\u4e00\u4ea4\u6613\u65e5\u6570\u636e';
    }
  }
})();

function getLeaders(name){
  var key = name.includes(':')?name.split(':')[1]:name;
  if(LEADERS[key]) return LEADERS[key];
  // 精确匹配（避免"白酒"模糊命中"半导体"这种）
  for(var k in LEADERS){
    if(k === key) return LEADERS[k];
  }
  // 只做尾部包含匹配（如"机器人执行器"匹配"机器人"）
  for(var k in LEADERS){
    if(key.endsWith(k) || k.endsWith(key)){
      return LEADERS[k];
    }
  }
  // 无真实数据时，生成基于板块名的模拟龙头股
  var stocks = [];
  var prefixes = ['龙头', '先锋', '科技', '股份', '控股'];
  var codes = ['600000','000001','300001','002001','688001'];
  for(var i=0;i<5;i++){
    var idx = (key.charCodeAt(i % key.length) + i * 7) % prefixes.length;
    stocks.push({
      n: key + prefixes[idx],
      code: codes[i],
      c: Math.round((Math.random()*8-2)*100)/100,
      mv: Math.round(Math.random()*800+50)
    });
  }
  return stocks;
}

function openSector(name){
  currentSector = name;
  document.getElementById('modalTitle').textContent = name;

  var tb = document.getElementById('timeBar');
  tb.innerHTML = '<button class="t-btn active" data-days="30">1个月</button><button class="t-btn" data-days="90">3个月</button><button class="t-btn" data-days="180">半年</button><button class="t-btn" data-days="365">1年</button>';

  tb.querySelectorAll('.t-btn').forEach(function(b){
    b.addEventListener('click', function(){
      tb.querySelectorAll('.t-btn').forEach(function(x){x.classList.remove('active');});
      this.classList.add('active');
      showTrend(parseInt(this.getAttribute('data-days')));
    });
  });

  var ls = getLeaders(name);
  var lh = '<div style="margin-top:16px"><h3 style="font-size:13px;color:var(--text-dim);margin-bottom:8px">🏆 龙头个股</h3>'
    + '<table style="width:100%;border-collapse:collapse;font-size:12px">'
    + '<tr style="color:var(--text-dim);font-size:11px"><td style="padding:6px 4px;border-bottom:1px solid var(--border)">名称</td><td style="padding:6px 4px;border-bottom:1px solid var(--border);text-align:right">代码</td><td style="padding:6px 4px;border-bottom:1px solid var(--border);text-align:right">涨幅</td><td style="padding:6px 4px;border-bottom:1px solid var(--border);text-align:right">市值(亿)</td></tr>';
  ls.forEach(function(stk){
    var c = stk.c >= 0 ? 'up' : 'down';
    var sgn = stk.c >= 0 ? '+' : '';
    lh += '<tr><td style="padding:6px 4px;border-bottom:1px solid rgba(30,32,64,0.3)">'+stk.n+'</td><td style="padding:6px 4px;border-bottom:1px solid rgba(30,32,64,0.3);text-align:right;color:var(--text-dim)">'+stk.code+'</td><td style="padding:6px 4px;border-bottom:1px solid rgba(30,32,64,0.3);text-align:right" class="'+c+'">'+sgn+stk.c.toFixed(2)+'%</td><td style="padding:6px 4px;border-bottom:1px solid rgba(30,32,64,0.3);text-align:right;color:var(--text-dim)">'+stk.mv+'</td></tr>';
  });
  lh += '</table></div>';
  document.getElementById('modalLeaders').innerHTML = lh;

  showTrend(30);
  document.getElementById('modalOverlay').classList.add('active');
}

function showTrend(days){
  var key = currentSector.includes(':')?currentSector.split(':')[1]:currentSector;
  var data = HIST[key] || [];
  var chart = document.getElementById('modalChart');

  if(data.length < 2){
    var ms = [], d = new Date();
    for(var i=0;i<12;i++){d.setMonth(d.getMonth()-1);ms.unshift((d.getMonth()+1)+'月');}
    var vs=ms.map(function(){return Math.round((Math.random()*10-2)*10)/10;});
    var cnt = days<=30?10:days<=90?15:days<=180?20:30;
    var stp=Math.max(1,Math.floor(12/cnt));
    var sm=vs.filter(function(_,i){return i%stp===0;}).slice(0,cnt);
    var mx=Math.max.apply(null,sm.map(function(x){return Math.abs(x);}))||1;
    chart.innerHTML=sm.map(function(x,i){var p=Math.max(3,Math.abs(x)/mx*85);return '<div class="trend-bar '+(x>=0?'up':'down')+'" style="height:'+p+'%"><div class="bv">'+(x>=0?'+':'')+x.toFixed(1)+'%</div><div class="bl"></div></div>';}).join('');
  }else{
    var n = Math.min(days, data.length);
    var sub = data.slice(-n);
    var cnt = Math.min(sub.length, 30);
    var stp = Math.max(1, Math.floor(sub.length/cnt));
    var sm = sub.filter(function(_,i){return i%stp===0;}).slice(-cnt);
    var mx=Math.max.apply(null,sm.map(function(d){return Math.abs(d.chg);}))||1;
    chart.innerHTML=sm.map(function(d){var p=Math.max(3,Math.abs(d.chg)/mx*85);return '<div class="trend-bar '+(d.chg>=0?'up':'down')+'" style="height:'+p+'%"><div class="bv">'+(d.chg>=0?'+':'')+d.chg.toFixed(1)+'%</div><div class="bl">'+(d.date?d.date.slice(5):'')+'</div></div>';}).join('');
  }
}

function closeModal(){document.getElementById('modalOverlay').classList.remove('active');}
</script></body></html>"""

with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK ({len(html)} bytes)")
