#!/usr/bin/env python3
"""nicetoken v2 完整页面"""
html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NiceToken · 市场看板</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0b1a;--bg-card:#111328;--bg-card-hover:#181b35;
  --border:#1e2040;--text:#e2e4f0;--text-dim:#6b6f9a;
  --cyan:#22d3ee;--emerald:#34d399;--rose:#fb7185;
  --amber:#fbbf24;--violet:#a78bfa;--red:#ef4444;--green:#22c55e;
}
body{background:var(--bg);color:var(--text);font-family:'Noto Sans SC',sans-serif;min-height:100vh;padding:20px}
.container{max-width:1440px;margin:0 auto}

/* Header */
.header{display:flex;justify-content:space-between;align-items:flex-end;padding-bottom:16px;border-bottom:1px solid var(--border);margin-bottom:20px}
.header h1{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header .update{font-size:12px;color:var(--text-dim);text-align:right}

h2{font-size:15px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px}
h2 .badge{font-size:10px;padding:2px 8px;border-radius:12px;background:rgba(34,211,238,0.1);color:var(--cyan);border:1px solid rgba(34,211,238,0.2);font-weight:400}

/* Grid layout */
.grid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px;margin-bottom:16px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px}

/* Cards */
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.card-header .badge{font-size:10px;padding:2px 8px;border-radius:12px;background:rgba(34,211,238,0.1);color:var(--cyan);border:1px solid rgba(34,211,238,0.2)}

/* Index rows */
.idx-row{display:flex;flex-wrap:wrap;gap:8px}
.idx-item{flex:1;min-width:80px;padding:10px;border-radius:8px;background:rgba(30,32,64,0.4);text-align:center}
.idx-item .name{font-size:11px;color:var(--text-dim);margin-bottom:4px}
.idx-item .val{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700}
.idx-item .chg{font-family:'JetBrains Mono',monospace;font-size:12px;margin-top:2px}

/* Sector tables */
.sector-item{display:flex;align-items:center;padding:8px 0;border-bottom:1px solid rgba(30,32,64,0.4);cursor:pointer;transition:all .15s}
.sector-item:last-child{border-bottom:none}
.sector-item:hover{padding-left:4px;background:rgba(34,211,238,0.03);border-radius:6px}
.sector-rank{width:20px;font-size:11px;color:var(--text-dim);text-align:center;margin-right:8px}
.sector-name{flex:1;font-size:13px;font-weight:500}
.sector-bar-wrap{flex:1;max-width:80px;margin:0 8px}
.sector-bar{height:3px;border-radius:2px;transition:width .3s}
.sector-chg{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;min-width:54px;text-align:right}

.up{color:var(--red)}.down{color:var(--green)}

/* 多市场板块分组 */
.mkt-group{margin-bottom:10px}
.mkt-group:last-child{margin-bottom:0}
.mkt-label{font-size:11px;color:var(--text-dim);margin-bottom:6px;font-weight:500}

/* 趋势迷你柱 */
.trend-mini{display:flex;align-items:flex-end;gap:2px;height:20px;margin:0 6px}
.mini-bar{width:3px;border-radius:1px}

/* 分布 */
.dist-row{display:flex;gap:6px;text-align:center}
.dist-item{flex:1;padding:10px 4px;border-radius:8px;border:1px solid var(--border)}
.dist-item .num{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700}
.dist-item .lbl{font-size:10px;color:var(--text-dim);margin-top:2px}
.dist-up{background:rgba(239,68,68,0.08);border-color:rgba(239,68,68,0.2)}
.dist-down{background:rgba(34,197,94,0.08);border-color:rgba(34,197,94,0.2)}
.dist-flat{background:rgba(107,114,128,0.08);border-color:rgba(107,114,128,0.2)}

/* 情绪小格子 */
.sent-row{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.sent-item{text-align:center;padding:10px 4px;border-radius:8px;background:rgba(30,32,64,0.4)}
.sent-item .v{font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:700}
.sent-item .l{font-size:10px;color:var(--text-dim);margin-top:2px}

/* 资讯列表 */
.news-item{padding:10px 0;border-bottom:1px solid rgba(30,32,64,0.4)}
.news-item:last-child{border-bottom:none}
.news-item .title{font-size:13px;font-weight:500;cursor:pointer}
.news-item .title:hover{color:var(--cyan)}
.news-item .meta{font-size:11px;color:var(--text-dim);margin-top:4px;display:flex;gap:12px}

/* 弹窗 */
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:24px;max-width:800px;width:90%;max-height:80vh;overflow-y:auto}
.modal h2{font-size:18px;margin-bottom:8px}
.modal-close{float:right;background:none;border:1px solid var(--border);color:var(--text-dim);font-size:13px;padding:4px 10px;border-radius:8px;cursor:pointer}
.modal-close:hover{border-color:var(--text);color:var(--text)}
.trend-chart{display:flex;align-items:flex-end;gap:2px;height:140px;padding:10px 0;margin:12px 0}
.trend-bar{flex:1;border-radius:2px 2px 0 0;position:relative;min-width:8px;transition:height .3s}
.trend-bar .bl{position:absolute;bottom:-16px;left:50%;transform:translateX(-50%);font-size:8px;color:var(--text-dim);white-space:nowrap}
.trend-bar .bv{position:absolute;top:-14px;left:50%;transform:translateX(-50%);font-size:9px;font-family:'JetBrains Mono',monospace;font-weight:600}

footer{text-align:center;padding:16px 0;color:var(--text-dim);font-size:11px}

@media(max-width:900px){
  .grid-4{grid-template-columns:1fr 1fr}
  .grid-2{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <div>
    <h1>⸙ nicetoken.top</h1>
    <div style="font-size:12px;color:var(--text-dim);margin-top:2px">全球情绪 · A股概况 · 板块趋势 · AI资讯</div>
  </div>
  <div class="update" id="updateBadge">--</div>
</div>

<!-- 四栏 -->
<div class="grid-4">

  <!-- 1. 全球情绪 -->
  <div class="card">
    <h2>🌍 全球情绪</h2>
    <div class="idx-row" id="globalIndices">
      <div class="idx-item"><div class="name">道琼斯</div><div class="val">--</div><div class="chg"></div></div>
      <div class="idx-item"><div class="name">纳斯达克</div><div class="val">--</div><div class="chg"></div></div>
      <div class="idx-item"><div class="name">标普500</div><div class="val">--</div><div class="chg"></div></div>
      <div class="idx-item"><div class="name">恒生指数</div><div class="val">--</div><div class="chg"></div></div>
      <div class="idx-item"><div class="name">日经225</div><div class="val">--</div><div class="chg"></div></div>
    </div>
  </div>

  <!-- 2. A股概况 -->
  <div class="card">
    <h2>🇨🇳 A股情绪</h2>
    <div class="idx-row" id="aIndices">
      <div class="idx-item"><div class="name">上证</div><div class="val">--</div><div class="chg"></div></div>
      <div class="idx-item"><div class="name">深证</div><div class="val">--</div><div class="chg"></div></div>
      <div class="idx-item"><div class="name">创业板</div><div class="val">--</div><div class="chg"></div></div>
      <div class="idx-item"><div class="name">科创50</div><div class="val">--</div><div class="chg"></div></div>
    </div>
    <!-- 分布 + 情绪 -->
    <div style="margin-top:10px">
      <div class="dist-row" id="distRow">
        <div class="dist-item dist-up"><div class="num">--</div><div class="lbl">涨</div></div>
        <div class="dist-item dist-flat"><div class="num">--</div><div class="lbl">平</div></div>
        <div class="dist-item dist-down"><div class="num">--</div><div class="lbl">跌</div></div>
      </div>
    </div>
    <div style="margin-top:8px">
      <div class="sent-row" id="sentRow">
        <div class="sent-item"><div class="v">--</div><div class="l">涨停</div></div>
        <div class="sent-item"><div class="v">--</div><div class="l">跌停</div></div>
        <div class="sent-item"><div class="v">--</div><div class="l">成交(亿)</div></div>
        <div class="sent-item"><div class="v">--</div><div class="l">涨跌比</div></div>
        <div class="sent-item"><div class="v">--</div><div class="l">封板率</div></div>
      </div>
    </div>
  </div>

  <!-- 3. 美股板块 -->
  <div class="card">
    <h2>🇺🇸 美股热门板块</h2>
    <div id="usSectors"></div>
  </div>

  <!-- 4. A股板块 -->
  <div class="card">
    <h2>🇨🇳 A股热门板块</h2>
    <div id="cnSectors"></div>
  </div>

</div>

<!-- AI 资讯 -->
<div class="card" style="margin-top:14px">
  <div class="card-header">
    <h2>🤖 AI 资讯 · 今日热点</h2>
    <span class="badge" id="newsCount">0 条</span>
  </div>
  <div id="newsList">
    <div style="text-align:center;padding:30px;color:var(--text-dim);font-size:13px">当日资讯将在每日日报中生成</div>
  </div>
</div>

</div>

<!-- 弹窗 -->
<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <h2 id="modalTitle">--</h2>
    <div class="trend-chart" id="modalChart"></div>
  </div>
</div>

<footer>nicetoken.top · 数据仅供个人参考，不构成投资建议</footer>

<script>
// ====== 模拟数据 ======
const mock = {
  global: [
    {n:'道琼斯',v:40123.45,c:1.28},{n:'纳斯达克',v:18567.89,c:1.86},
    {n:'标普500',v:5678.12,c:0.95},{n:'恒生指数',v:22134.56,c:-0.45},
    {n:'日经225',v:38901.23,c:0.78}
  ],
  a: [
    {n:'上证',v:4075.10,c:0.43},{n:'深证',v:15591.13,c:1.63},
    {n:'创业板',v:4055.87,c:2.66},{n:'科创50',v:1690.56,c:1.62}
  ],
  dist:{up:2156,flat:189,down:876},
  sent:{zt:78,dt:3,vol:11860}
};

const usSectors = [
  {n:'半导体',c:2.89},{n:'AI软件',c:2.45},{n:'云计算',c:2.12},{n:'量子计算',c:1.98},{n:'机器人',c:1.76},
  {n:'网络安全',c:1.54},{n:'生物科技',c:1.32},{n:'金融科技',c:1.18},{n:'新能源',c:0.95},{n:'航空航天',c:0.78}
];
const cnSectors = [
  {n:'半导体',c:4.82},{n:'通信设备',c:4.15},{n:'AI算力',c:3.97},{n:'消费电子',c:3.45},{n:'军工装备',c:3.12},
  {n:'新能源车',c:2.88},{n:'光伏设备',c:2.56},{n:'创新药',c:2.23},{n:'电力电网',c:1.95},{n:'机器人',c:1.68}
];

function fmt(v){return v>=0?'+'+v.toFixed(2)+'%':v.toFixed(2)+'%'}
function renderIdx(el,data){
  el.innerHTML=data.map(i=>`<div class="idx-item"><div class="name">${i.n}</div><div class="val">${i.v.toLocaleString()}</div><div class="chg ${i.c>=0?'up':'down'}">${fmt(i.c)}</div></div>`).join('');
}
function renderSectors(el,data,prefix){
  el.innerHTML=data.map((s,i)=>{
    const cls=s.c>=0?'up':'down'; const sign=s.c>=0?'+':'';
    return `<div class="sector-item" onclick="openSector('${prefix}:${s.n}')">
      <span class="sector-rank">${i+1}</span>
      <span class="sector-name">${s.n}</span>
      <div class="sector-bar-wrap"><div class="sector-bar" style="width:${Math.max(5,Math.abs(s.c)*18)}%;background:${s.c>=0?'var(--red)':'var(--green)'}"></div></div>
      <span class="sector-chg ${cls}">${sign}${s.c.toFixed(2)}%</span>
    </div>`;
  }).join('');
}

renderIdx(document.getElementById('globalIndices'), mock.global);
renderIdx(document.getElementById('aIndices'), mock.a);
renderSectors(document.getElementById('usSectors'), usSectors, 'US');
renderSectors(document.getElementById('cnSectors'), cnSectors, 'CN');

// 分布
const d=mock.dist; const upPct=mock.sent.zt+((d.up+d.down)?Math.round(d.up/(d.up+d.down)*100):0);
document.getElementById('distRow').innerHTML=
  `<div class="dist-item dist-up"><div class="num">${d.up}</div><div class="lbl">涨</div></div>`+
  `<div class="dist-item dist-flat"><div class="num">${d.flat}</div><div class="lbl">平</div></div>`+
  `<div class="dist-item dist-down"><div class="num">${d.down}</div><div class="lbl">跌</div></div>`;

// 情绪
const s=mock.sent;
const ratio = (d.up+d.down) ? Math.round(d.up/(d.up+d.down)*100) : 0;
const lb = (s.zt+s.dt) ? Math.round(s.zt/(s.zt+s.dt)*100) : 0;
document.getElementById('sentRow').innerHTML=
  `<div class="sent-item"><div class="v">${s.zt}</div><div class="l">涨停</div></div>`+
  `<div class="sent-item"><div class="v">${s.dt}</div><div class="l">跌停</div></div>`+
  `<div class="sent-item"><div class="v">${s.vol}</div><div class="l">成交(亿)</div></div>`+
  `<div class="sent-item"><div class="v">${ratio}%</div><div class="l">涨跌比</div></div>`+
  `<div class="sent-item"><div class="v">${lb}%</div><div class="l">封板率</div></div>`;

document.getElementById('newsCount').textContent='待生成';
const now=new Date();
document.getElementById('updateBadge').textContent=now.toLocaleDateString('zh-CN',{year:'numeric',month:'long',day:'numeric'});

// 弹窗
function openSector(name){
  document.getElementById('modalTitle').textContent=name;
  document.getElementById('modalChart').innerHTML='<div style="text-align:center;padding:40px;color:var(--text-dim)">数据加载中…</div>';
  document.getElementById('modalOverlay').classList.add('active');
}
function closeModal(){document.getElementById('modalOverlay').classList.remove('active')}
document.getElementById('modalOverlay').addEventListener('click',function(e){if(e.target===this)closeModal()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal()});
</script>
</body>
</html>
"""

with open("/Users/silinzhang/Desktop/nicetoken/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("OK - index.html 已生成")
