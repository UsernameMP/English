"""Self-contained, offline-safe RIFT operations dashboard template. No CDNs or remote scripts."""

TEMPLATE = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RIFT / Downloader Control</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:dark;
--bg:#080d18;--panel:#111c2e;--card:#15243a;--line:#29384f;--muted:#9aaac1;--text:#eef4ff;
--blue:#719af8;--teal:#3dcab6;--amber:#f3b96c;--red:#ef7f82;--purple:#ae93f2}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 85% -10%,#1b3459 0%,#0a1425 50%,var(--bg) 100%);color:var(--text)}
main{max-width:1280px;margin:0 auto;padding:29px 23px 66px}header,.topline,.actions,.panel-head,.kpi-top,.detail-row,.timeline-controls,.legend-line,.footer-row{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
header{padding:4px 0 18px;border-bottom:1px solid var(--line)}.wordmark{letter-spacing:.18em;font-weight:850;font-size:13px}.wordmark em{font-style:normal;color:var(--teal)}.tag{background:#1d2e45;border:1px solid #3b5471;border-radius:50px;color:#b4c6df;padding:7px 11px;font-size:12px}
.topline{margin:28px 0}.topline h1{font-size:clamp(27px,3.5vw,41px);letter-spacing:-.045em;margin:0 0 7px;font-weight:750}.eyebrow{color:var(--blue);font-size:11px;font-weight:750;letter-spacing:.15em;text-transform:uppercase;margin-bottom:7px}
p{margin:0;color:var(--muted);font-size:13px;line-height:1.65}.actions a,.actions button,.range button{border:1px solid #3c5473;color:#e2ecff;text-decoration:none;cursor:pointer;font:inherit;font-weight:650;background:#20334f;border-radius:9px;padding:10px 13px;font-size:12px}.actions a:hover,.actions button:hover,.range button:hover{background:#314d70}
.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}.kpi,.panel{background:linear-gradient(150deg,rgba(24,40,63,.96),rgba(16,27,44,.97));border:1px solid var(--line);border-radius:16px}.kpi{padding:20px 20px 18px;min-width:0;position:relative;overflow:hidden}.kpi::before{content:'';position:absolute;top:0;left:0;height:3px;width:100%;background:var(--tone,var(--blue));opacity:.9}.kpi .kpi-top{color:#acbdd4;font-size:12px;font-weight:550}.kpi .kpi-top .dot{height:8px;width:8px;border-radius:50%;background:var(--tone,var(--blue))}.kpi strong{display:block;font-variant-numeric:tabular-nums;font-size:clamp(27px,3vw,37px);letter-spacing:-.045em;margin:12px 0 7px}.kpi small{display:block;color:var(--muted);font-size:11px;line-height:1.4}
.flow{margin:16px 0;display:grid;grid-template-columns:2fr 1fr;gap:14px}.panel{padding:20px;min-width:0}.panel-head{margin-bottom:15px}.panel h2{margin:0;font-size:15px;font-weight:730;letter-spacing:-.01em}.hint{font-size:11px;color:var(--muted);font-weight:450}.progressline{height:12px;border-radius:20px;overflow:hidden;background:#26364d;display:flex;margin:15px 0 11px}.progressline div{height:100%;min-width:0;transition:width .3s}.progress-note{font-size:11px;color:var(--muted);display:flex;justify-content:space-between}.stat-numbers{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:13px}.stat-numbers b{font-size:13px}
.panels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.panel.full{grid-column:1 / -1}
.timeline-controls .range{display:flex;border-radius:9px;gap:3px}.range button{padding:6px 11px;border-radius:7px;background:#14253b;border-color:#2d4058}.range button.active{color:#081628;background:var(--blue);border-color:var(--blue)}
.timeline{height:210px;position:relative;display:flex;gap:3px;align-items:stretch;padding:8px 0 21px;border-bottom:1px solid #31415a;margin:13px 0 5px;background:repeating-linear-gradient(to top,transparent 0,transparent 47px,#26364b 48px,#26364b 49px)}
.hour{height:100%;display:flex;flex:1;align-items:flex-end;justify-content:center;min-width:0;gap:1px;position:relative}.hour .columns{height:100%;width:100%;display:flex;align-items:flex-end;justify-content:center;gap:1px}.hour .column{min-width:1px;width:42%;border-radius:3px 3px 0 0}.hour .attempt{background:linear-gradient(0deg,#365fb6,#759cf7)}.hour .saved{background:linear-gradient(0deg,#138e82,#48d1b9)}
.hour:hover{background:#253a5660}.axis{display:flex;justify-content:space-between;color:#93a7c4;font-size:10px;margin-top:9px}.legend{display:flex;gap:19px;flex-wrap:wrap;color:#a6b7ce;font-size:11px;margin-top:14px}.legend .swatch{width:9px;height:9px;border-radius:3px;display:inline-block;margin-right:5px}
.empty{color:#8fa4c3;padding:45px 12px;text-align:center;font-size:12px;line-height:1.6}.chart-cells{display:flex;gap:3px;align-items:flex-end;height:156px;padding-top:10px;border-bottom:1px solid #334159}.chart-cell{min-width:0;flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;position:relative}.chart-cell span{display:block;width:70%;border-radius:5px 5px 0 0;background:var(--blue);min-height:2px}.chart-cell.hot span{background:var(--red)}.chart-cell.amber span{background:var(--amber)}
.chart-cell .count{display:block;position:absolute;bottom:calc(var(--h) + 6px);font-size:10px;color:#dbe9fc;font-variant-numeric:tabular-nums}.chart-keys{display:flex;gap:6px;margin-top:10px}.chart-keys>div{flex:1;text-align:center;font-size:10px;color:#a6b8d0;overflow:hidden;text-overflow:ellipsis}
.bar-line{display:grid;grid-template-columns:minmax(95px,1.25fr) minmax(65px,3fr) 48px;gap:11px;align-items:center;margin:13px 0;font-size:11px;color:#adbed7}.bar-line>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar{background:#243752;border-radius:10px;height:10px;overflow:hidden}.bar>span{display:block;height:100%;border-radius:10px;background:var(--blue)}.bar.warn>span{background:var(--amber)}.bar-line strong{text-align:right;font-size:11px;font-variant-numeric:tabular-nums;color:#e5f0ff}
.format-wrap{display:grid;grid-template-columns:185px 1fr;align-items:center;gap:20px}.donut{height:173px;width:173px;border-radius:50%;display:grid;place-items:center;position:relative;background:conic-gradient(var(--blue) 0 100%)}.donut::before{content:'';height:114px;width:114px;border-radius:50%;position:absolute;background:#15243a}.donut>div{z-index:1;text-align:center}.donut strong{display:block;font-size:29px}.donut small{display:block;color:var(--muted);font-size:11px}.format-legend{min-width:0}.legend-line{font-size:11px;color:#afc2db;padding:8px 0;border-bottom:1px solid #2a3b52}.legend-line span:first-child{display:flex;align-items:center;gap:8px}.legend-line i{display:block;width:10px;height:10px;border-radius:3px;flex:none}
.detail-row{border-top:1px solid #2a3a51;padding:11px 0;font-size:12px}.detail-row span{color:#a5b8d2}.detail-row b{font-variant-numeric:tabular-nums;text-align:right;font-weight:650;overflow-wrap:anywhere}
.hosts{max-height:230px;overflow-y:auto}.hosts .bar-line{grid-template-columns:minmax(120px,1.8fr) 3fr 44px}
footer{margin-top:22px;padding-top:21px;border-top:1px solid var(--line);color:#8da0b9;font-size:11px;line-height:1.7}
@media(max-width:1000px){.cards{grid-template-columns:repeat(2,1fr)}.flow{grid-template-columns:1fr}.format-wrap{grid-template-columns:140px 1fr}.donut{height:130px;width:130px}.donut::before{height:86px;width:86px}}
@media(max-width:650px){main{padding:17px 12px 40px}.cards,.panels{grid-template-columns:1fr}.panel.full{grid-column:1}.format-wrap{grid-template-columns:130px 1fr;gap:8px}.topline{gap:16px}.topline h1{font-size:27px}.kpi{padding:15px}.panel{padding:16px}.hour{gap:0}.hour .columns{gap:0}}
</style></head><body><main>
<header><div class="wordmark">RIFT <em>/</em> OPERATIONS</div><div class="tag" id="state">Инициализация отчёта</div></header>
<div class="topline">
<div><div class="eyebrow">Downloader telemetry / source archive</div><h1>Панель скачивателя</h1>
<p>Контроль очереди URL, оригиналов в Google Drive, ошибок и производительности. Только проверенные показатели.</p></div>
<div class="actions"><a id="actions" target="_blank" rel="noopener">Запустить / история</a><a id="drive" target="_blank" rel="noopener">Архив Google Drive</a>
<button onclick="location.reload()">Обновить снимок</button></div>
</div>
<div class="cards">
<div class="kpi" style="--tone:var(--blue)"><div class="kpi-top">Проверено URL <i class="dot"></i></div><strong id="urls">—</strong><small id="attempts">Сколько ссылок обработано</small></div>
<div class="kpi" style="--tone:var(--teal)"><div class="kpi-top">Уникальные оригиналы <i class="dot"></i></div><strong id="files">—</strong><small id="size">Суммарный объём в raw</small></div>
<div class="kpi" style="--tone:var(--amber)"><div class="kpi-top">Отказы 403 / 429 <i class="dot"></i></div><strong id="denials">—</strong><small id="deny-detail">Доступ запрещён / частота ограничена</small></div>
<div class="kpi" style="--tone:var(--red)"><div class="kpi-top">HTTP 404 <i class="dot"></i></div><strong id="not-found">—</strong><small id="total-http">Ошибки HTTP / общее число запросов</small></div>
</div>
<div class="flow">
<section class="panel"><div class="panel-head"><h2>Прогресс обработки мастер-списка</h2><span class="hint" id="master-label">Отношение проверенных URL к общему числу</span></div>
<div class="progressline"><div id="progress-done" style="background:var(--teal);width:0%"></div><div id="progress-rest" style="background:var(--blue);width:0%"></div></div>
<div class="progress-note"><span id="progress-caption">—</span><span id="progress-percent">—</span></div>
<div class="stat-numbers"><span class="hint">Сохранено оригиналов: <b id="progress-files">—</b></span>
<span class="hint">Успешных URL: <b id="completed-links">—</b></span></div>
</section>
<section class="panel"><div class="panel-head"><h2>Показатели эффективности</h2></div>
<div class="detail-row"><span>Оригиналов / проверенных URL</span><b id="yield">—</b></div>
<div class="detail-row"><span>Занято на Drive</span><b id="drive-bytes">—</b></div>
<div class="detail-row"><span>Российских хостов в первых 200 URL</span><b id="ru-first">—</b></div>
<div class="detail-row"><span>Последнее событие</span><b id="last">—</b></div>
</section>
</div>
<div class="panels">
<section class="panel full"><div class="panel-head timeline-controls">
<div><h2>Активность загрузчика</h2><p class="hint">Попытки URL и сохранённые оригиналы по часам (необработанные данные не дорисовываются)</p></div>
<div class="range"><button data-hours="24" class="active" aria-pressed="true">24 ч</button><button data-hours="72" aria-pressed="false">3 дня</button><button data-hours="168" aria-pressed="false">7 дней</button></div>
</div>
<div class="timeline" id="timeline"><div class="empty">Пока нет временного ряда для графика</div></div>
<div class="axis" id="time-axis"></div>
<div class="legend"><span><i class="swatch" style="background:var(--blue)"></i>Обращения к URL</span><span><i class="swatch" style="background:var(--teal)"></i>Сохранённые файлы</span></div>
</section>
<section class="panel"><div class="panel-head"><h2>HTTP-коды</h2><span class="hint">Включая robots и перенаправления</span></div><div id="http-columns"></div></section>
<section class="panel"><div class="panel-head"><h2>Форматы сохранённых файлов</h2><span class="hint">Без анализа содержимого</span></div><div class="format-wrap"><div class="donut" id="donut"><div><strong id="donut-total">—</strong><small>файлов</small></div></div><div class="format-legend" id="format-legend"></div></div></section>
<section class="panel"><div class="panel-head"><h2>Состояния ссылок</h2><span class="hint">Без ожидающих 300+ тысяч</span></div><div id="statuses"></div></section>
<section class="panel"><div class="panel-head"><h2>Причины неудач</h2><span class="hint">Уникальные URL, не HTTP-запросы</span></div><div id="errors"></div></section>
<section class="panel"><div class="panel-head"><h2>Наиболее нагруженные хосты</h2><span class="hint">Число HTTP-запросов</span></div><div class="hosts" id="hosts"></div></section>
<section class="panel"><div class="panel-head"><h2>Диагностика текущего запуска</h2><span class="hint" id="run-id">—</span></div>
<div class="detail-row"><span>Статус</span><b id="mode">—</b></div>
<div class="detail-row"><span>Причина остановки</span><b id="stop">—</b></div>
<div class="detail-row"><span>robots.txt</span><b id="robots">—</b></div>
<div class="detail-row"><span>HTTP p95</span><b id="latency">—</b></div>
<div class="detail-row"><span>Домены с сохранёнными файлами</span><b id="domains">—</b></div>
<div class="detail-row"><span>Обновлено</span><b id="generated">—</b></div>
</section>
</div>
<footer><div class="footer-row"><span id="notes">Исторические данные. Запуск из панели недоступен: управление происходит через GitHub Actions.</span></div>
<p>Снимок отчёта, не потоковое наблюдение. Результаты конкретного запуска обновляются только при новой генерации. Никаких Google OAuth-токенов, скачанных документов или скрытых URL в этой HTML-панели нет.</p></footer>
<script id="metrics" type="application/json">__METRICS__</script>
<script>
"use strict";
const $=id=>document.getElementById(id);
const fmt=n=>new Intl.NumberFormat("ru-RU").format(Number(n||0));
const bytes=n=>{n=Number(n||0);let i=0;while(n>=1024&&i<4){n/=1024;i++}return n.toFixed(i?1:0)+" "+["Б","КиБ","МиБ","ГиБ","ТиБ"][i]};
const set=(id,v)=>{$(id).textContent=String(v)};
const pct=(n,d)=>d?Math.min(100,100*n/d):0;
const palette=["#719af8","#3dcab6","#f3b96c","#ae93f2","#ef7f82","#8dabc9"];
const mimeLabel={"application/pdf":"PDF","application/zip":"ZIP","application/x-zip-compressed":"ZIP","application/msword":"DOC","application/vnd.openxmlformats-officedocument.wordprocessingml.document":"DOCX","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":"XLSX","application/vnd.rar":"RAR","application/x-rar-compressed":"RAR","text/x-tex":"TeX"};
function barRows(id,entries,{warn=false,limit=9}={}){const el=$(id);el.replaceChildren();
const sorted=Object.entries(entries||{}).filter(([_,v])=>Number(v)>0).sort((a,b)=>b[1]-a[1]).slice(0,limit),max=Math.max(1,...sorted.map(x=>Number(x[1])));
for(const [k,val]of sorted){const r=document.createElement("div");r.className="bar-line";const name=document.createElement("span");name.textContent=k;name.title=k;
const track=document.createElement("div");track.className="bar"+(warn?" warn":"");
const fill=document.createElement("span");fill.style.width=pct(val,max)+"%";track.append(fill);
const value=document.createElement("strong");value.textContent=fmt(val);r.append(name,track,value);el.append(r)}
if(!sorted.length){const note=document.createElement("div");note.className="empty";note.textContent="Нет данных для отображения";el.append(note)}}
function httpChart(codes){const el=$("http-columns");el.replaceChildren();const pairs=Object.entries(codes||{}).filter(([_,v])=>v>0).sort((a,b)=>Number(a[0])-Number(b[0]));if(!pairs.length){el.textContent="Нет HTTP-статистики";return}
const max=Math.max(1,...pairs.map(x=>x[1]));const bars=document.createElement("div");bars.className="chart-cells";const keys=document.createElement("div");keys.className="chart-keys";
for(const [code,count]of pairs){const cell=document.createElement("div");cell.className="chart-cell"+(Number(code)>=400?" hot":Number(code)>=300?" amber":"");
const span=document.createElement("span");const height=Math.max(2,100*count/max);span.style.height=height+"%";cell.style.setProperty("--h",height+"%");
const c=document.createElement("b");c.className="count";c.textContent=fmt(count);cell.title="HTTP "+code+": "+fmt(count)+" запросов";cell.append(span,c);bars.append(cell);
const n=document.createElement("div");n.textContent=code;keys.append(n)}
el.append(bars,keys)}
function formatChart(data){const merged={};for(const [key,v]of Object.entries(data||{})){const label=mimeLabel[key]||key.split("/").pop().slice(0,20).toUpperCase();merged[label]=(merged[label]||0)+v}
const sorted=Object.entries(merged).sort((a,b)=>b[1]-a[1]);const total=sorted.reduce((s,x)=>s+x[1],0);set("donut-total",fmt(total));
const chosen=sorted.slice(0,5);const other=sorted.slice(5).reduce((s,x)=>s+x[1],0);if(other)chosen.push(["Прочее",other]);
const stops=[];let start=0;for(let i=0;i<chosen.length;i++){const end=start+pct(chosen[i][1],total||1);stops.push(palette[i%palette.length]+" "+start+"% "+end+"%");start=end}
$("donut").style.background=stops.length?"conic-gradient("+stops.join(",")+")":"#26364f";
$("format-legend").replaceChildren();
for(let i=0;i<chosen.length;i++){const line=document.createElement("div");line.className="legend-line";const name=document.createElement("span");const swatch=document.createElement("i");swatch.style.background=palette[i%palette.length];name.append(swatch,document.createTextNode(chosen[i][0]));const value=document.createElement("b");value.textContent=fmt(chosen[i][1]);line.append(name,value);$("format-legend").append(line)}}
let history=[],hoursShown=24;
function timeline(){const el=$("timeline");el.replaceChildren();const values=history.slice(-hoursShown);if(!values.length){const message=document.createElement("div");message.className="empty";message.textContent="Исторические данные не содержат разбивки по часам. Она появится после нового запуска.";el.append(message);$("time-axis").replaceChildren();return}
const maximum=Math.max(1,...values.flatMap(x=>[Number(x.requests)||0,Number(x.saved)||0]));
for(const item of values){const col=document.createElement("div");col.className="hour";const group=document.createElement("div");group.className="columns";col.title=new Date(item.hour).toLocaleString("ru-RU")+": "+fmt(item.requests)+" обращений, "+fmt(item.saved)+" сохранений";
for(const [key,cls]of [["requests","attempt"],["saved","saved"]]){const part=document.createElement("div");part.className="column "+cls;part.style.height=Math.max(0,100*(Number(item[key])||0)/maximum)+"%";group.append(part)}col.append(group);el.append(col)}
$("time-axis").replaceChildren();for(const ix of [0,Math.floor((values.length-1)/2),values.length-1]){const sp=document.createElement("span");sp.textContent=new Date(values[ix].hour).toLocaleString("ru-RU",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"});$("time-axis").append(sp)}}
function draw(data){const m=data.metrics||{},urls=Number(m.unique_urls_checked||0),files=Number(m.unique_files||0),master=Number(m.master_rows||m.indexed_urls||0);
set("state",data.state==="historical"?"Исторический пилот • не LIVE":String(data.state||"снимок"));
set("urls",fmt(urls));set("attempts",fmt(m.total_url_attempts)+" попыток обработки ссылок");
set("files",fmt(files));set("size",bytes(m.stored_bytes)+" оригиналов в Google Drive");
set("denials",fmt((m.http_403||0)+(m.http_429||0)));set("deny-detail","403: "+fmt(m.http_403)+" · 429: "+fmt(m.http_429));
set("not-found",fmt(m.http_404));set("total-http",fmt(m.http_requests)+" HTTP-запросов всего");
const value=pct(urls,master);$("progress-done").style.width=value+"%";set("progress-caption",fmt(urls)+" / "+fmt(master)+" URL");set("progress-percent",value.toFixed(2)+"%");
set("progress-files",fmt(files));set("completed-links",fmt(m.successful_links));set("yield",urls?(100*files/urls).toFixed(1)+"%":"—");
set("drive-bytes",bytes(m.stored_bytes));
set("ru-first",m.ru_first_200===null||m.ru_first_200===undefined?"нет данных":fmt(m.ru_first_200)+" / "+fmt(m.master_preview_count||200));
set("last",data.last_activity_at?new Date(data.last_activity_at).toLocaleString("ru-RU"):"—");
set("mode",data.state||"—");set("stop",data.stop_reason||"—");set("robots",fmt(m.robots_requests));set("latency",m.http_p95_ms===null||m.http_p95_ms===undefined?"нет данных":fmt(m.http_p95_ms)+" мс");
set("domains",fmt(m.successful_domains));set("generated",data.generated_at?new Date(data.generated_at).toLocaleString("ru-RU"):"—");set("run-id",data.run_id?"Запуск #"+data.run_id:"Без идентификатора запуска");
$("actions").href=data.links?.github_actions||"https://github.com/UsernameMP/English/actions";$("drive").href=data.links?.drive_folder||"https://drive.google.com/drive/u/0/my-drive";
httpChart(data.http_codes);formatChart(data.mime_types);barRows("statuses",Object.fromEntries(Object.entries(data.url_statuses||{}).filter(x=>x[0]!=="pending")));barRows("errors",data.error_categories,{warn:true});barRows("hosts",Object.fromEntries((data.top_hosts||[]).map(x=>[x.domain,x.requests])),{limit:8});
history=data.hourly||[];timeline();set("notes",data.source+" · "+(data.notes||[]).join(" "));
}
document.querySelectorAll("[data-hours]").forEach(b=>b.addEventListener("click",()=>{hoursShown=Number(b.dataset.hours);document.querySelectorAll("[data-hours]").forEach(x=>{const active=x===b;x.classList.toggle("active",active);x.setAttribute("aria-pressed",active?"true":"false")});timeline()}));
try{draw(JSON.parse($("metrics").textContent))}catch(error){set("state","Ошибка данных отчёта")}
</script></main></body></html>"""
