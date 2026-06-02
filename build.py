#!/usr/bin/env python3
"""
nicetoken.top 全量构建
1. 采集最新数据（update_data.py）
2. 拼接 data.json + history.json 到 HTML
"""
import json, os, sys
from update_data import DATA_FILE, HIST_FILE, OUTPUT_DIR

INDEX_HTML = os.path.join(OUTPUT_DIR, "index.html")

def html_escape(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build():
    # 加载数据
    if not os.path.exists(DATA_FILE):
        print("[ERR] data.json 不存在，先运行 update_data.py")
        sys.exit(1)
    
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    with open(HIST_FILE, encoding="utf-8") as f:
        histories = json.load(f)
    
    indices = data.get("indices", {})
    sectors = data.get("sectors", [])
    dist = data.get("distribution", {})
    sent = data.get("sentiment", {})
    updated = data.get("updated_at", "")
    date_str = data.get("date", "")
    
    # 指数 HTML
    idx_names = {"sh":"上证指数","sz":"深证成指","cy":"创业板指","kc":"科创50"}
    idx_rows = ""
    for key, name in idx_names.items():
        i = indices.get(key, {})
        val = i.get("val", "--")
        chg = i.get("chg", 0)
        cls = "up" if chg >= 0 else "down"
        sign = "+" if chg >= 0 else ""
        chg_str = f"{sign}{chg:.2f}%"
        idx_rows += f'''<div class="index-card">
          <div class="index-name">{name}</div>
          <div class="index-value">{val}</div>
          <div class="index-change {cls}">{chg_str}</div>
        </div>'''
    
    up_n = dist.get("up",0)
    flat_n = dist.get("flat",0)
    down_n = dist.get("down",0)
    
    zt = sent.get("zt",0)
    dt = sent.get("dt",0)
    vol = sent.get("vol",0)
    
    # 板块列表
    def bar_width(chg):
        max_chg = max([abs(s.get("chg",0)) for s in sectors]) if sectors else 5
        return max(8, min(100, int(abs(chg) / max(max_chg, 1) * 95)))
    
    sector_rows = ""
    for i, s in enumerate(sectors):
        name = s.get("name","")
        chg = s.get("chg",0)
        cls = "up" if chg >= 0 else "down"
        sign = "+" if chg >= 0 else ""
        bw = bar_width(chg)
        # 趋势迷你柱状图
        hist = histories.get(name, [])
        trend_bars = ""
        if hist:
            recent = hist[-10:]
            max_abs = max([abs(h["chg"]) for h in recent]) or 1
            for h in recent:
                hc = h["chg"]
                h_cls = "bar-up" if hc >= 0 else "bar-down"
                h_pct = max(2, int(abs(hc) / max_abs * 100))
                trend_bars += f'<div class="minibar-item {h_cls}" style="height:{h_pct}%"></div>'
        rank_cls = ""
        if i == 0: rank_cls = 'gold'
        elif i == 1: rank_cls = 'silver'
        elif i == 2: rank_cls = 'bronze'
        rank_html = f'<span class="top3-badge {rank_cls}">#{i+1}</span>' if rank_cls else f'<span class="sector-rank">{i+1}</span>'
        sector_rows += f'''<div class="sector-item">
          {rank_html}
          <span class="sector-name">{html_escape(name)}</span>
          <div class="sector-trend-wrap"><div class="sector-trend">{trend_bars}</div></div>
          <div class="sector-bar-wrap"><div class="sector-bar" style="width:{bw}%;background:{'var(--red)' if chg>=0 else 'var(--green)'};"></div></div>
          <span class="sector-change {cls}">{sign}{chg:.2f}%</span>
        </div>'''
    
    histories_json = json.dumps(histories, ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NiceToken · 市场看板</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
:root {{
  --bg: #0a0b1a;
  --bg-card: #111328;
  --bg-card-hover: #181b35;
  --border: #1e2040;
  --text: #e2e4f0;
  --text-dim: #6b6f9a;
  --cyan: #22d3ee;
  --emerald: #34d399;
  --rose: #fb7185;
  --amber: #fbbf24;
  --violet: #a78bfa;
  --red: #ef4444;
  --green: #22c55e;
}}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'Noto Sans SC', sans-serif;
  min-height: 100vh;
  padding: 24px;
}}
.container {{ max-width: 1440px; margin: 0 auto; }}

.header {{
  display: flex; justify-content: space-between; align-items: flex-end;
  padding-bottom: 20px; border-bottom: 1px solid var(--border); margin-bottom: 24px;
}}
.header h1 {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px; font-weight: 700;
  background: linear-gradient(135deg, #22d3ee, #a78bfa);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.header .subtitle {{ font-size: 13px; color: var(--text-dim); margin-top: 4px; }}
.header .date-badge {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px; color: var(--text-dim);
  padding: 6px 14px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--bg-card);
}}
.header .update-badge {{ font-size: 11px; color: var(--text-dim); margin-top: 4px; text-align: right; }}

.indices-row {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px;
}}
.index-card {{
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 12px; padding: 18px 20px; transition: all .2s;
}}
.index-card:hover {{ background: var(--bg-card-hover); border-color: #2a2d5a; }}
.index-name {{ font-size: 13px; color: var(--text-dim); margin-bottom: 6px; }}
.index-value {{ font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 700; }}
.index-change {{ font-family: 'JetBrains Mono', monospace; font-size: 14px; margin-top: 4px; }}
.up {{ color: var(--red); }}
.down {{ color: var(--green); }}

.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}

.card {{
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px;
}}
.card-header {{
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
}}
.card-header h2 {{ font-size: 16px; font-weight: 600; }}
.card-header .badge {{
  font-size: 11px; padding: 3px 10px; border-radius: 20px;
  background: rgba(34,211,238,0.1); color: var(--cyan); border: 1px solid rgba(34,211,238,0.2);
}}

.sector-item {{
  display: flex; align-items: center; padding: 10px 0;
  border-bottom: 1px solid rgba(30,32,64,0.6); cursor: pointer; transition: all .15s;
}}
.sector-item:last-child {{ border-bottom: none; }}
.sector-item:hover {{ padding-left: 4px; background: rgba(34,211,238,0.03); border-radius: 6px; }}
.sector-rank {{
  width: 22px; font-family: 'JetBrains Mono', monospace; font-size: 12px;
  color: var(--text-dim); text-align: center; margin-right: 10px;
}}
.sector-name {{ flex: 1; font-size: 14px; font-weight: 500; min-width: 80px; }}

.sector-trend-wrap {{ margin: 0 8px; }}
.sector-trend {{
  display: flex; align-items: flex-end; gap: 2px; height: 24px;
}}
.minibar-item {{ width: 4px; border-radius: 1px; min-height: 2px; }}
.bar-up {{ background: var(--red); }}
.bar-down {{ background: var(--green); }}

.sector-bar-wrap {{ flex: 1; max-width: 100px; margin: 0 8px; }}
.sector-bar {{ height: 4px; border-radius: 3px; transition: width 0.5s; }}
.sector-change {{ 
  font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600;
  min-width: 62px; text-align: right;
}}
.top3-badge {{
  display: inline-block; font-size: 10px; padding: 1px 6px;
  border-radius: 4px; margin-right: 6px; font-family: 'JetBrains Mono', monospace;
}}
.gold {{ background: rgba(251,191,36,0.15); color: var(--amber); }}
.silver {{ background: rgba(167,139,250,0.15); color: var(--violet); }}
.bronze {{ background: rgba(251,146,60,0.15); color: #fb923c; }}

.dist-grid {{
  display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 16px;
}}
.dist-item {{
  text-align: center; padding: 14px 8px; border-radius: 10px;
  border: 1px solid var(--border);
}}
.dist-item .num {{ font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; }}
.dist-item .label {{ font-size: 12px; color: var(--text-dim); margin-top: 4px; }}
.dist-up {{ background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.2); }}
.dist-down {{ background: rgba(34,197,94,0.08); border-color: rgba(34,197,94,0.2); }}
.dist-flat {{ background: rgba(107,114,128,0.08); border-color: rgba(107,114,128,0.2); }}

.sentiment-row {{
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;
}}
.sentiment-item {{
  text-align: center; padding: 12px 6px; border-radius: 8px;
  background: rgba(30,32,64,0.4);
}}
.sentiment-item .val {{
  font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700;
}}
.sentiment-item .lbl {{ font-size: 11px; color: var(--text-dim); margin-top: 2px; }}

.sub-section {{ margin-top: 16px; }}
.sub-section:first-child {{ margin-top: 0; }}
.sub-section h3 {{
  font-size: 13px; color: var(--text-dim); margin-bottom: 10px;
  font-weight: 500; letter-spacing: 1px;
}}

/* 板块详情弹窗 */
.modal-overlay {{
  display: none; position: fixed; top:0; left:0; right:0; bottom:0;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
  z-index: 1000; justify-content: center; align-items: center;
}}
.modal-overlay.active {{ display: flex; }}
.modal {{
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 16px; padding: 28px; max-width: 800px; width: 90%;
  max-height: 80vh; overflow-y: auto;
}}
.modal h2 {{ font-size: 20px; margin-bottom: 8px; }}
.modal .modal-date {{ font-size: 12px; color: var(--text-dim); margin-bottom: 20px; }}
.modal-close {{
  float: right; background: none; border: 1px solid var(--border);
  color: var(--text-dim); font-size: 14px; padding: 4px 12px;
  border-radius: 8px; cursor: pointer;
}}
.modal-close:hover {{ border-color: var(--text); color: var(--text); }}
.trend-chart {{
  display: flex; align-items: flex-end; gap: 3px; height: 160px;
  padding: 10px 0; margin: 16px 0;
}}
.trend-bar {{
  flex: 1; border-radius: 3px 3px 0 0; position: relative;
  min-width: 12px; transition: height 0.3s;
}}
.trend-bar .bar-label {{
  position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%);
  font-size: 9px; color: var(--text-dim); white-space: nowrap;
}}
.trend-bar .bar-val {{
  position: absolute; top: -18px; left: 50%; transform: translateX(-50%);
  font-size: 10px; font-family: 'JetBrains Mono', monospace; font-weight: 600;
}}
.trend-stats {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 20px;
}}
.trend-stat {{ text-align: center; }}
.trend-stat .sv {{ font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; }}
.trend-stat .sl {{ font-size: 11px; color: var(--text-dim); margin-top: 2px; }}

footer {{
  text-align: center; padding: 24px 0; color: var(--text-dim); font-size: 12px;
}}

@media (max-width: 900px) {{
  .indices-row {{ grid-template-columns: repeat(2, 1fr); }}
  .two-col {{ grid-template-columns: 1fr; }}
  .sentiment-row {{ grid-template-columns: repeat(3, 1fr); }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>⸙ nicetoken.top</h1>
      <div class="subtitle">Market Dashboard · 大盘概览 &amp; 板块趋势</div>
    </div>
    <div>
      <div class="date-badge">{date_str}</div>
      <div class="update-badge">更新于 {updated}</div>
    </div>
  </div>

  <div class="indices-row">{idx_rows}</div>

  <div class="two-col">
    <div class="card">
      <div class="card-header">
        <h2>📊 大盘情绪</h2>
        <span class="badge">今日</span>
      </div>
      <div class="sub-section">
        <h3>涨跌分布</h3>
        <div class="dist-grid">
          <div class="dist-item dist-up"><div class="num">{up_n}</div><div class="label">上涨</div></div>
          <div class="dist-item dist-flat"><div class="num">{flat_n}</div><div class="label">平盘</div></div>
          <div class="dist-item dist-down"><div class="num">{down_n}</div><div class="label">下跌</div></div>
        </div>
      </div>
      <div class="sub-section">
        <h3>市场情绪</h3>
        <div class="sentiment-row">
          <div class="sentiment-item"><div class="val">{zt}</div><div class="lbl">涨停</div></div>
          <div class="sentiment-item"><div class="val">{dt}</div><div class="lbl">跌停</div></div>
          <div class="sentiment-item"><div class="val">{vol}</div><div class="lbl">成交额(亿)</div></div>
          <div class="sentiment-item"><div class="val" id="northVal">--</div><div class="lbl">北向资金</div></div>
          <div class="sentiment-item"><div class="val" id="lbVal">--</div><div class="lbl">涨停封板率</div></div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h2>🔥 热门板块</h2>
        <span class="badge">涨幅排行 <span id="sectorCount">{len(sectors)}</span></span>
      </div>
      <div id="sectorList">{sector_rows}</div>
    </div>
  </div>

  <footer>nicetoken.top · 数据仅供个人参考，不构成投资建议</footer>
</div>

<!-- 板块详情弹窗 -->
<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <h2 id="modalTitle">--</h2>
    <div class="modal-date" id="modalDate">--</div>
    <div id="modalChart" class="trend-chart"></div>
    <div id="modalStats" class="trend-stats"></div>
  </div>
</div>

<script>
const SECTOR_HISTORIES = {histories_json};

document.querySelectorAll('.sector-item').forEach(el => {{
  el.addEventListener('click', function() {{
    const nameEl = this.querySelector('.sector-name');
    if (!nameEl) return;
    openModal(nameEl.textContent.trim());
  }});
}});

function openModal(name) {{
  const hist = SECTOR_HISTORIES[name] || [];
  document.getElementById('modalTitle').textContent = name;
  document.getElementById('modalDate').textContent = '近 ' + hist.length + ' 个交易日趋势';

  const chart = document.getElementById('modalChart');
  if (hist.length === 0) {{
    chart.innerHTML = '<div style="text-align:center;color:var(--text-dim);padding:40px;">暂无历史数据</div>';
    document.getElementById('modalStats').innerHTML = '';
  }} else {{
    const maxAbs = Math.max(...hist.map(h => Math.abs(h.chg)), 1);
    chart.innerHTML = hist.map(h => {{
      const pct = Math.max(3, Math.abs(h.chg) / maxAbs * 95);
      const cls = h.chg >= 0 ? 'bar-up' : 'bar-down';
      const sign = h.chg >= 0 ? '+' : '';
      const dateLabel = h.date ? h.date.slice(5) : '';
      return '<div class="trend-bar ' + cls + '" style="height:' + pct + '%">' +
        '<div class="bar-val">' + sign + h.chg.toFixed(2) + '%</div>' +
        '<div class="bar-label">' + dateLabel + '</div></div>';
    }}).join('');
  }}

  if (hist.length > 0) {{
    const chgs = hist.map(h => h.chg);
    const avg = chgs.reduce((a,b) => a+b, 0) / chgs.length;
    const max = Math.max(...chgs);
    const min = Math.min(...chgs);
    document.getElementById('modalStats').innerHTML =
      '<div class="trend-stat"><div class="sv ' + (avg>=0?'up':'down') + '">' + (avg>=0?'+':'') + avg.toFixed(2) + '%</div><div class="sl">日均涨跌</div></div>' +
      '<div class="trend-stat"><div class="sv up">+' + max.toFixed(2) + '%</div><div class="sl">区间最大涨幅</div></div>' +
      '<div class="trend-stat"><div class="sv down">' + min.toFixed(2) + '%</div><div class="sl">区间最大跌幅</div></div>';
  }}
  document.getElementById('modalOverlay').classList.add('active');
}}

function closeModal() {{
  document.getElementById('modalOverlay').classList.remove('active');
}}
document.getElementById('modalOverlay').addEventListener('click', function(e) {{
  if (e.target === this) closeModal();
}});
document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') closeModal(); }});

// 涨停封板率
const zt = {zt}, dtRaw = {dt};
const total = zt + dtRaw;
document.getElementById('lbVal').textContent = total > 0 ? Math.round(zt / total * 100) + '%' : '--';
document.getElementById('northVal').textContent = '--';
</script>
</body>
</html>'''

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] index.html 已生成 ({len(html)} 字节)")

if __name__ == "__main__":
    import update_data
    update_data.main()
    print("---")
    build()
