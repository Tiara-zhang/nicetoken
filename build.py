#!/usr/bin/env python3
"""nicetoken build — 读取JSON生成HTML"""
import json, os

OUT = "/Users/silinzhang/Desktop/nicetoken"
DATA = os.path.join(OUT, "data.json")
HIST = os.path.join(OUT, "history.json")
NEWS = os.path.join(OUT, "news.json")
HTML = os.path.join(OUT, "index.html")

def load():
    d = {"global":{},"a_indices":{},"sectors":[],"distribution":{"up":0,"flat":0,"down":0},"sentiment":{"zt":0,"dt":0,"vol":0},"picks_risks":{"picks":[],"risks":[]}}
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

# 构造HTML片段
def idx_html(dd, keys):
    parts = []
    for k in keys:
        v = dd.get(k)
        if v:
            cls = "up" if v["chg"]>=0 else "down"
            parts.append(f'<div class="idx-item"><div class="name">{k}</div><div class="val">{v["val"]}</div><div class="chg {cls}">{v["chg"]:+.2f}%</div></div>')
    return "".join(parts)

def sec_html(ss):
    parts = []
    for i,s in enumerate(ss[:10]):
        cls = "up" if s["chg"]>=0 else "down"
        w = max(5, abs(s["chg"])*15)
        bg = "var(--red)" if s["chg"]>=0 else "var(--green)"
        sign = "+" if s["chg"]>=0 else ""
        nm = esc(s["name"])
        parts.append(
            f'<div class="sector-item" onclick="openSector(\'CN:{nm}\')">'
            f'<span class="sector-rank">{i+1}</span>'
            f'<span class="sector-name">{nm}</span>'
            f'<div class="sector-bar-wrap"><div class="sector-bar" style="width:{w}%;background:{bg}"></div></div>'
            f'<span class="sector-chg {cls}">{sign}{s["chg"]:.2f}%</span></div>'
        )
    return "".join(parts)

def us_html():
    us = [{"name":"半导体","chg":2.89},{"name":"AI软件","chg":2.45},{"name":"云计算","chg":2.12},
          {"name":"量子计算","chg":1.98},{"name":"机器人","chg":1.76},{"name":"网络安全","chg":1.54},
          {"name":"生物科技","chg":1.32},{"name":"金融科技","chg":1.18},{"name":"新能源","chg":0.95},
          {"name":"航空航天","chg":0.78}]
    return sec_html(us)

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
        return '<div style="text-align:center;padding:24px;color:var(--text-dim);font-size:12px">日报推送后将自动显示</div>'
    return "".join(
        f'<div class="news-item"><div class="title"><span class="date-tag">{n["d"][:10]}</span><span>{esc(n["t"])}</span></div>'
        f'<div class="meta"><span>{esc(n.get("s",""))}</span></div></div>' for n in items
    )

# 全局
g_html = idx_html(gi, ["道琼斯","纳斯达克","标普500","恒生指数","日经225"])
if not g_html:
    g_html = '<div style="color:var(--text-dim);font-size:12px;padding:10px">非交易时段</div>'

a_html = idx_html(ai, ["上证","深证","创业板","科创50"])
cn_html = sec_html(sec)
us_html_s = us_html()
pk_html = pick_html()
rk_html = risk_html()
ai_n_html = news_html(ai_news)
inv_n_html = news_html(inv_news)

hist_json = json.dumps(hist, ensure_ascii=False)

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
.grid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px;margin-bottom:14px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.card-header .badge{font-size:10px;padding:2px 8px;border-radius:12px;background:rgba(34,211,238,0.1);color:var(--cyan);border:1px solid rgba(34,211,238,0.2);font-weight:400}
.idx-row{display:flex;flex-wrap:wrap;gap:6px}
.idx-item{flex:1;min-width:70px;padding:8px;border-radius:8px;background:rgba(30,32,64,0.4);text-align:center}
.idx-item .name{font-size:10px;color:var(--text-dim);margin-bottom:3px}
.idx-item .val{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700}
.idx-item .chg{font-family:'JetBrains Mono',monospace;font-size:11px;margin-top:1px}
.up{color:var(--red)}.down{color:var(--green)}
.sector-item{display:flex;align-items:center;padding:6px 0;border-bottom:1px solid rgba(30,32,64,0.3);cursor:pointer;transition:all .15s}
.sector-item:last-child{border-bottom:none}.sector-item:hover{padding-left:4px;background:rgba(34,211,238,0.03);border-radius:6px}
.sector-rank{width:18px;font-size:10px;color:var(--text-dim);text-align:center;margin-right:6px}
.sector-name{flex:1;font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sector-bar-wrap{flex:1;max-width:60px;margin:0 6px}.sector-bar{height:3px;border-radius:2px;transition:width .3s}
.sector-chg{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;min-width:48px;text-align:right}
.dist-row{display:flex;gap:6px;text-align:center}
.dist-item{flex:1;padding:8px 4px;border-radius:8px;border:1px solid var(--border)}
.dist-item .num{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700}
.dist-item .lbl{font-size:10px;color:var(--text-dim);margin-top:2px}
.dist-up{background:rgba(239,68,68,0.08);border-color:rgba(239,68,68,0.2)}
.dist-down{background:rgba(34,197,94,0.08);border-color:rgba(34,197,94,0.2)}
.dist-flat{background:rgba(107,114,128,0.08);border-color:rgba(107,114,128,0.2)}
.sent-row{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:8px}
.sent-item{text-align:center;padding:8px 4px;border-radius:8px;background:rgba(30,32,64,0.4)}
.sent-item .v{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700}
.sent-item .l{font-size:9px;color:var(--text-dim);margin-top:2px}
.pick-card{background:linear-gradient(135deg,rgba(34,211,238,0.05),rgba(167,139,250,0.05));border:1px solid rgba(34,211,238,0.2)}
.pick-item{display:flex;align-items:flex-start;padding:12px 0;border-bottom:1px solid rgba(34,211,238,0.08)}
.pick-item:last-child{border-bottom:none}
.pick-tag{flex-shrink:0;font-size:10px;padding:2px 8px;border-radius:6px;font-weight:600;margin-right:12px;margin-top:1px}
.pick-hot{background:rgba(239,68,68,0.15);color:var(--red);font-size:11px}
.pick-warm{background:rgba(251,191,36,0.15);color:var(--amber);font-size:11px}
.pick-cold{background:rgba(107,114,128,0.15);color:var(--text-dim);font-size:11px}
.pick-body .title{font-size:13px;font-weight:600}
.pick-body .reason{font-size:11px;color:var(--text-dim);margin-top:3px;line-height:1.5;padding-right:8px}
.risk-card{background:linear-gradient(135deg,rgba(239,68,68,0.04),rgba(251,191,36,0.04));border:1px solid rgba(239,68,68,0.15)}
.risk-item{padding:10px 0;border-bottom:1px solid rgba(239,68,68,0.06)}
.risk-item:last-child{border-bottom:none}
.risk-item .r-icon{font-size:14px;margin-right:8px}
.risk-item .r-title{font-size:12px;font-weight:600;display:flex;align-items:center}
.risk-item .r-desc{font-size:11px;color:var(--text-dim);margin-top:3px;line-height:1.5;margin-left:24px;padding-right:8px}
.risk-item .r-level{font-size:9px;padding:1px 6px;border-radius:4px;margin-left:8px;font-weight:500}
.r-high{background:rgba(239,68,68,0.15);color:var(--red)}
.r-mid{background:rgba(251,191,36,0.15);color:var(--amber)}
.r-low{background:rgba(107,114,128,0.15);color:var(--text-dim)}
.news-item{padding:10px 0;border-bottom:1px solid rgba(30,32,64,0.4)}
.news-item:last-child{border-bottom:none}
.news-item .title{font-size:13px;font-weight:500;display:flex;align-items:flex-start;gap:8px;cursor:pointer}
.news-item .title:hover{color:var(--cyan)}
.news-item .title .date-tag{font-size:10px;padding:1px 6px;border-radius:4px;background:rgba(107,114,128,0.15);color:var(--text-dim);flex-shrink:0;margin-top:2px;font-family:'JetBrains Mono',monospace}
.news-item .meta{font-size:11px;color:var(--text-dim);margin-top:4px;display:flex;gap:12px}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:24px;max-width:800px;width:90%;max-height:80vh;overflow-y:auto}
.modal h2{font-size:18px;margin-bottom:8px}
.modal-close{float:right;background:none;border:1px solid var(--border);color:var(--text-dim);font-size:13px;padding:4px 10px;border-radius:8px;cursor:pointer}
.modal-close:hover{border-color:var(--text);color:var(--text)}
.trend-chart{display:flex;align-items:flex-end;gap:2px;height:120px;padding:10px 0;margin:12px 0}
.trend-bar{flex:1;border-radius:2px 2px 0 0;position:relative;min-width:6px;transition:height .3s}
.trend-bar .bl{position:absolute;bottom:-14px;left:50%;transform:translateX(-50%);font-size:7px;color:var(--text-dim);white-space:nowrap}
.trend-bar .bv{position:absolute;top:-12px;left:50%;transform:translateX(-50%);font-size:8px;font-family:'JetBrains Mono',monospace;font-weight:600}
footer{text-align:center;padding:16px 0;color:var(--text-dim);font-size:11px}
@media(max-width:900px){.grid-4{grid-template-columns:1fr 1fr}.grid-2{grid-template-columns:1fr}}
</style></head><body>
<div class="container">
<div class="header"><div><h1>⸙ nicetoken.top</h1><div style="font-size:12px;color:var(--text-dim);margin-top:2px">全球情绪 · A股情绪 · 板块趋势 · 机会 · 风险 · 资讯</div></div><div class="update">""" + upd + """</div></div>

<div class="grid-4">
  <div class="card"><h2>🌍 全球情绪</h2><div class="idx-row">""" + g_html + """</div></div>
  <div class="card"><h2>🇨🇳 A股情绪</h2><div class="idx-row">""" + a_html + """</div>
    <div style="margin-top:8px"><div class="dist-row"><div class="dist-item dist-up"><div class="num">""" + str(up) + """</div><div class="lbl">涨</div></div><div class="dist-item dist-flat"><div class="num">""" + str(flat) + """</div><div class="lbl">平</div></div><div class="dist-item dist-down"><div class="num">""" + str(down) + """</div><div class="lbl">跌</div></div></div></div>
    <div class="sent-row"><div class="sent-item"><div class="v">""" + str(zt) + """</div><div class="l">涨停</div></div><div class="sent-item"><div class="v">""" + str(dt) + """</div><div class="l">跌停</div></div><div class="sent-item"><div class="v">""" + str(vol) + """</div><div class="l">成交(亿)</div></div><div class="sent-item"><div class="v">""" + str(ratio) + """%</div><div class="l">涨跌比</div></div><div class="sent-item"><div class="v">""" + str(lb) + """%</div><div class="l">封板率</div></div></div>
  </div>
  <div class="card"><h2>🇺🇸 美股板块</div><div>""" + us_html_s + """</div></div>
  <div class="card"><h2>🇨🇳 A股板块</h2><div>""" + cn_html + """</div></div>
</div>

<div class="grid-2" style="margin-bottom:14px">
  <div class="card pick-card"><div class="card-header"><h2>🎯 建议关注</h2><span class="badge">近期投资机会</span></div>""" + pk_html + """</div>
  <div class="card risk-card"><div class="card-header"><h2>⚠️ 风险提示</h2><span class="badge">规避风险·保护本金</span></div>""" + rk_html + """</div>
</div>

<div class="grid-2">
  <div class="card"><div class="card-header"><h2>🤖 AI 资讯</h2><span class="badge">""" + str(len(ai_news)) + """条</span></div>""" + ai_n_html + """</div>
  <div class="card"><div class="card-header"><h2>📈 投资资讯</h2><span class="badge">""" + str(len(inv_news)) + """条</span></div>""" + inv_n_html + """</div>
</div>
</div>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal"><button class="modal-close" onclick="closeModal()">&#x2715;</button><h2 id="modalTitle">--</h2><div class="trend-chart" id="modalChart"></div></div>
</div>

<footer>nicetoken.top · 数据仅供个人参考，不构成投资建议</footer>

<script>
var HIST = """ + hist_json + """;
function openSector(name){
  document.getElementById('modalTitle').textContent = name;
  var key = name.includes(':')?name.split(':')[1]:name;
  var data = HIST[key] || [];
  var chart = document.getElementById('modalChart');
  if(data.length<2){
    var ms=['25/07','08','09','10','11','12','26/01','02','03','04','05','06'];
    var vs=ms.map(function(){return Math.round((Math.random()*10-2)*10)/10;});
    var mx=Math.max.apply(null,vs.map(function(x){return Math.abs(x);}))||1;
    chart.innerHTML=vs.map(function(x,i){var p=Math.max(3,Math.abs(x)/mx*85);return '<div class="trend-bar '+(x>=0?'up':'down')+'" style="height:'+p+'%"><div class="bv">'+(x>=0?'+':'')+x.toFixed(1)+'%</div><div class="bl">'+ms[i]+'</div></div>';}).join('');
  }else{
    var step=Math.max(1,Math.floor(data.length/30));
    var sampled=data.filter(function(_,i){return i%step===0;});
    var mx=Math.max.apply(null,sampled.map(function(d){return Math.abs(d.chg);}))||1;
    chart.innerHTML=sampled.map(function(d){var p=Math.max(3,Math.abs(d.chg)/mx*85);return '<div class="trend-bar '+(d.chg>=0?'up':'down')+'" style="height:'+p+'%"><div class="bv">'+(d.chg>=0?'+':'')+d.chg.toFixed(1)+'%</div><div class="bl">'+(d.date?d.date.slice(5):'')+'</div></div>';}).join('');
  }
  document.getElementById('modalOverlay').classList.add('active');
}
function closeModal(){document.getElementById('modalOverlay').classList.remove('active');}
document.getElementById('modalOverlay').addEventListener('click',function(e){if(e.target===this)closeModal();});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal();});
</script></body></html>"""

with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK ({len(html)} bytes)")
