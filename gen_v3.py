#!/usr/bin/env python3
"""nicetoken v3 — 含建议关注板块 + AI资讯沉淀"""
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

.header{display:flex;justify-content:space-between;align-items:flex-end;padding-bottom:16px;border-bottom:1px solid var(--border);margin-bottom:20px}
.header h1{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header .update{font-size:12px;color:var(--text-dim);text-align:right}

h2{font-size:15px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px}
h2 .badge{font-size:10px;padding:2px 8px;border-radius:12px;background:rgba(34,211,238,0.1);color:var(--cyan);border:1px solid rgba(34,211,238,0.2);font-weight:400}

.grid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px;margin-bottom:14px}

.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.card-header .badge{font-size:10px;padding:2px 8px;border-radius:12px;background:rgba(34,211,238,0.1);color:var(--cyan);border:1px solid rgba(34,211,238,0.2)}

/* 指数 */
.idx-row{display:flex;flex-wrap:wrap;gap:6px}
.idx-item{flex:1;min-width:70px;padding:8px;border-radius:8px;background:rgba(30,32,64,0.4);text-align:center}
.idx-item .name{font-size:10px;color:var(--text-dim);margin-bottom:3px}
.idx-item .val{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700}
.idx-item .chg{font-family:'JetBrains Mono',monospace;font-size:11px;margin-top:1px}
.up{color:var(--red)}.down{color:var(--green)}

/* 板块 */
.sector-item{display:flex;align-items:center;padding:6px 0;border-bottom:1px solid rgba(30,32,64,0.3);cursor:pointer;transition:all .15s}
.sector-item:last-child{border-bottom:none}
.sector-item:hover{padding-left:4px;background:rgba(34,211,238,0.03);border-radius:6px}
.sector-rank{width:18px;font-size:10px;color:var(--text-dim);text-align:center;margin-right:6px}
.sector-name{flex:1;font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sector-bar-wrap{flex:1;max-width:60px;margin:0 6px}
.sector-bar{height:3px;border-radius:2px;transition:width .3s}
.sector-chg{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;min-width:48px;text-align:right}

/* 建议关注板块 */
.pick-card{background:linear-gradient(135deg,rgba(34,211,238,0.05),rgba(167,139,250,0.05));border:1px solid rgba(34,211,238,0.2)}
.pick-item{display:flex;align-items:flex-start;padding:12px 0;border-bottom:1px solid rgba(34,211,238,0.08)}
.pick-item:last-child{border-bottom:none}
.pick-tag{flex-shrink:0;font-size:10px;padding:2px 8px;border-radius:6px;font-weight:600;margin-right:12px;margin-top:1px}
.pick-hot{background:rgba(239,68,68,0.15);color:var(--red)}
.pick-warm{background:rgba(251,191,36,0.15);color:var(--amber)}
.pick-cold{background:rgba(107,114,128,0.15);color:var(--text-dim)}
.pick-body{flex:1}
.pick-body .title{font-size:13px;font-weight:600}
.pick-body .reason{font-size:11px;color:var(--text-dim);margin-top:3px;line-height:1.5}
.pick-body .reason .hl{color:var(--cyan)}

/* 情绪 */
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

/* 资讯 */
.news-item{padding:10px 0;border-bottom:1px solid rgba(30,32,64,0.4)}
.news-item:last-child{border-bottom:none}
.news-item .title{font-size:13px;font-weight:500;cursor:pointer;display:flex;align-items:flex-start;gap:8px}
.news-item .title:hover{color:var(--cyan)}
.news-item .title .date-tag{font-size:10px;padding:1px 6px;border-radius:4px;background:rgba(107,114,128,0.15);color:var(--text-dim);flex-shrink:0;margin-top:2px;font-family:'JetBrains Mono',monospace}
.news-item .meta{font-size:11px;color:var(--text-dim);margin-top:4px;margin-left:0;display:flex;gap:12px}

/* 弹窗 */
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

@media(max-width:900px){.grid-4{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <div>
    <h1>⸙ nicetoken.top</h1>
    <div style="font-size:12px;color:var(--text-dim);margin-top:2px">全球情绪 · A股情绪 · 板块趋势 · 投资机会 · AI资讯</div>
  </div>
  <div class="update" id="updateBadge">--</div>
</div>

<!-- 四栏 -->
<div class="grid-4">
  <!-- 全球 -->
  <div class="card">
    <h2>🌍 全球情绪</h2>
    <div class="idx-row" id="globalIndices"></div>
  </div>
  <!-- A股 -->
  <div class="card">
    <h2>🇨🇳 A股情绪</h2>
    <div class="idx-row" id="aIndices"></div>
    <div style="margin-top:8px"><div class="dist-row" id="distRow"></div></div>
    <div class="sent-row" id="sentRow"></div>
  </div>
  <!-- 美股板块 -->
  <div class="card">
    <h2>🇺🇸 美股板块</h2>
    <div id="usSectors"></div>
  </div>
  <!-- A股板块 -->
  <div class="card">
    <h2>🇨🇳 A股板块</h2>
    <div id="cnSectors"></div>
  </div>
</div>

<!-- 建议关注 -->
<div class="card pick-card" style="margin-bottom:14px">
  <div class="card-header">
    <h2>🎯 建议关注 · 近期投资机会</h2>
    <span class="badge">AI驱动 · 仅供参考</span>
  </div>
  <div id="pickList"></div>
</div>

<!-- AI资讯 -->
<div class="card" style="margin-bottom:14px">
  <div class="card-header">
    <h2>🤖 AI 资讯 · 每日推送沉淀</h2>
    <span class="badge" id="newsCount">0 条</span>
  </div>
  <div id="newsList"></div>
</div>

</div>

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
  global:[{n:'道琼斯',v:40123.45,c:1.28},{n:'纳斯达克',v:18567.89,c:1.86},{n:'标普500',v:5678.12,c:0.95},{n:'恒生',v:22134.56,c:-0.45},{n:'日经',v:38901.23,c:0.78}],
  a:[{n:'上证',v:4075.10,c:0.43},{n:'深证',v:15591.13,c:1.63},{n:'创业板',v:4055.87,c:2.66},{n:'科创50',v:1690.56,c:1.62}],
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

// ====== 建议关注 ======
const picks = [
  {tag:'🔥 重点',tagType:'hot',title:'半导体 / AI算力',reason:'全球AI资本开支高景气，英伟达业绩超预期，国内政策持续加码。<span class="hl">半导体板块</span>近3月涨幅28%，资金持续流入。关注：中芯国际、北方华创、寒武纪'},
  {tag:'⚡ 趋势',tagType:'warm',title:'电力电网 / 特高压',reason:'夏季用电高峰+新能源并网需求，<span class="hl">电力电网</span>板块受益确定性强。关注：国电南瑞、许继电气、特变电工'},
  {tag:'📈 成长',tagType:'warm',title:'机器人 / 具身智能',reason:'特斯拉Optimus量产预期+国内政策扶持，<span class="hl">机器人</span>板块回调后性价比显现。关注：汇川技术、绿的谐波、拓普集团'},
  {tag:'👀 观察',tagType:'cold',title:'消费电子 / 果链',reason:'苹果Vision Pro新品周期+AI手机换机预期，<span class="hl">消费电子</span>下半年有望回暖。关注：立讯精密、歌尔股份、韦尔股份'}
];

// ====== AI 资讯 ======
const news = [
  {date:'2026-06-07',title:'英伟达发布新一代AI芯片Rubin，性能提升3倍',source:'Reuters',url:'#'},
  {date:'2026-06-07',title:'国内大模型价格战持续，百度文心4.5 Turbo免费开放',source:'36氪',url:'#'},
  {date:'2026-06-07',title:'特斯拉Optimus开始在工厂执行物料搬运任务',source:'Bloomberg',url:'#'},
  {date:'2026-06-06',title:'国务院发文支持人工智能+制造业深度融合',source:'新华社',url:'#'},
  {date:'2026-06-06',title:'台积电3nm产能满载，CoWoS扩产超预期',source:'Digitimes',url:'#'}
];

// ====== 渲染 ======
function fmt(v){return v>=0?'+'+v.toFixed(2)+'%':v.toFixed(2)+'%'}
function renderIdx(el,data){
  el.innerHTML=data.map(i=>`<div class="idx-item"><div class="name">${i.n}</div><div class="val">${i.v.toLocaleString()}</div><div class="chg ${i.c>=0?'up':'down'}">${fmt(i.c)}</div></div>`).join('');
}
function renderSectors(el,data,prefix){
  el.innerHTML=data.map((s,i)=>{
    const cls=s.c>=0?'up':'down';const sign=s.c>=0?'+':'';
    return `<div class="sector-item" onclick="openSector('${prefix}:${s.n}')">
      <span class="sector-rank">${i+1}</span>
      <span class="sector-name">${s.n}</span>
      <div class="sector-bar-wrap"><div class="sector-bar" style="width:${Math.max(5,Math.abs(s.c)*15)}%;background:${s.c>=0?'var(--red)':'var(--green)'}"></div></div>
      <span class="sector-chg ${cls}">${sign}${s.c.toFixed(2)}%</span>
    </div>`;
  }).join('');
}

renderIdx(document.getElementById('globalIndices'),mock.global);
renderIdx(document.getElementById('aIndices'),mock.a);

const d=mock.dist;
document.getElementById('distRow').innerHTML=
  `<div class="dist-item dist-up"><div class="num">${d.up}</div><div class="lbl">涨</div></div>`+
  `<div class="dist-item dist-flat"><div class="num">${d.flat}</div><div class="lbl">平</div></div>`+
  `<div class="dist-item dist-down"><div class="num">${d.down}</div><div class="lbl">跌</div></div>`;

const s=mock.sent;const ratio=Math.round(d.up/(d.up+d.down)*100);const lb=Math.round(s.zt/(s.zt+s.dt)*100);
document.getElementById('sentRow').innerHTML=
  `<div class="sent-item"><div class="v">${s.zt}</div><div class="l">涨停</div></div>`+
  `<div class="sent-item"><div class="v">${s.dt}</div><div class="l">跌停</div></div>`+
  `<div class="sent-item"><div class="v">${s.vol}</div><div class="l">成交(亿)</div></div>`+
  `<div class="sent-item"><div class="v ${ratio>=50?'up':'down'}">${ratio}%</div><div class="l">涨跌比</div></div>`+
  `<div class="sent-item"><div class="v">${lb}%</div><div class="l">封板率</div></div>`;

renderSectors(document.getElementById('usSectors'),usSectors,'US');
renderSectors(document.getElementById('cnSectors'),cnSectors,'CN');

// 建议关注
document.getElementById('pickList').innerHTML=picks.map(p=>
  `<div class="pick-item">
    <span class="pick-tag pick-${p.tagType}">${p.tag}</span>
    <div class="pick-body">
      <div class="title">${p.title}</div>
      <div class="reason">${p.reason}</div>
    </div>
  </div>`
).join('');

// 资讯
document.getElementById('newsCount').textContent=news.length+'条';
document.getElementById('newsList').innerHTML=news.map(n=>
  `<div class="news-item">
    <div class="title" onclick="window.open('${n.url||'#'}','_blank')">
      <span class="date-tag">${n.date.slice(5)}</span>
      <span>${n.title}</span>
    </div>
    <div class="meta"><span>${n.source}</span></div>
  </div>`
).join('');

document.getElementById('updateBadge').textContent=new Date().toLocaleDateString('zh-CN',{year:'numeric',month:'long',day:'numeric'});

function openSector(name){
  document.getElementById('modalTitle').textContent=name;
  const chart=document.getElementById('modalChart');
  // 模拟12月趋势
  const months=['25/07','08','09','10','11','12','26/01','02','03','04','05','06'];
  const vals=months.map(()=>Math.round((Math.random()*10-2)*10)/10);
  const max=Math.max(...vals.map(Math.abs),1);
  chart.innerHTML=vals.map((v,i)=>{
    const pct=Math.max(3,Math.abs(v)/max*85);
    return `<div class="trend-bar ${v>=0?'up':'down'}" style="height:${pct}%"><div class="bv">${v>=0?'+':''}${v.toFixed(1)}%</div><div class="bl">${months[i]}</div></div>`;
  }).join('');
  document.getElementById('modalOverlay').classList.add('active');
}
function closeModal(){document.getElementById('modalOverlay').classList.remove('active')}
document.getElementById('modalOverlay').addEventListener('click',function(e){if(e.target===this)closeModal()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal()});
</script>
</body>
</html>
"""

with open("/Users/silinzhang/Desktop/nicetoken/index.html","w",encoding="utf-8") as f:
    f.write(html)
print("OK")
