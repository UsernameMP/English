"""RIFT operations dashboard: privacy-preserving metrics, no network access.

The generated dashboard is a self-contained HTML snapshot, suitable for a
GitHub Actions artifact, GitHub Pages, or direct opening in a browser.
Only aggregate counts and hostnames are displayed; source URLs, credentials,
error strings and original document contents never enter the public JSON.
"""
import argparse
import html
import json
import math
import re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

from .db import connect,summary

def _utc(timestamp=None):
    return datetime.fromtimestamp(timestamp,tz=timezone.utc).isoformat() if timestamp else datetime.now(timezone.utc).isoformat()

def build_metrics(db, *, run_state='snapshot', stop_reason=None, limit_new_urls=None, run_id=None):
    data=summary(db)
    codes=data['http_response_codes']
    statuses=data['resource_statuses']
    attempts=int(data['requests_attempted'])
    unique=db.execute("SELECT COUNT(DISTINCT resource_id) FROM attempts").fetchone()[0]
    source_hosts=db.execute("""SELECT COUNT(DISTINCT a.domain) FROM attempts a
                                JOIN resources r ON r.resource_id=a.resource_id
                                WHERE r.status='completed'""").fetchone()[0]
    last_http=db.execute("SELECT MAX(at) FROM http_events").fetchone()[0]
    last_attempt=db.execute("SELECT MAX(started_at) FROM attempts").fetchone()[0]
    last_save=db.execute("SELECT MAX(verified_at) FROM objects WHERE verified_at IS NOT NULL").fetchone()[0]
    first_attempt=db.execute("SELECT MIN(started_at) FROM attempts").fetchone()[0]
    timeline=[]
    for row in db.execute("""SELECT CAST(started_at/3600 AS INTEGER)*3600 bucket,
        COUNT(*) requests,COUNT(DISTINCT resource_id) urls
        FROM attempts GROUP BY bucket ORDER BY bucket"""):
        timeline.append({'hour':_utc(row['bucket']),'requests':row['requests'],'urls':row['urls']})
    if len(timeline)>168:timeline=timeline[-168:]
    http_latency=[r[0] for r in db.execute(
        "SELECT elapsed_ms FROM http_events WHERE elapsed_ms IS NOT NULL ORDER BY elapsed_ms")]
    p95=(http_latency[math.ceil(len(http_latency)*.95)-1] if http_latency else None)
    hosts=[]
    for row in db.execute("""SELECT domain,
           COUNT(*) requests,
           SUM(CASE WHEN http_status IN (403,429) THEN 1 ELSE 0 END) rejections,
           SUM(CASE WHEN http_status=429 THEN 1 ELSE 0 END) rate_limited
         FROM http_events WHERE domain IS NOT NULL
         GROUP BY domain ORDER BY requests DESC,domain LIMIT 20"""):
        hosts.append(dict(row))
    mime=dict(sorted(data['stored_mime'].items(),key=lambda x:-x[1]))
    errors={k:int(v) for k,v in sorted(statuses.items())
            if k in ('blocked','failed','skipped','retry','html_deferred','image_deferred')}
    return {
      'schema_version':1,
      'generated_at':_utc(),
      'state':run_state,
      'stop_reason':stop_reason,
      'run_id':str(run_id) if run_id else None,
      'limit_new_urls':limit_new_urls,
      'source':'SQLite RIFT operations ledger',
      'last_activity_at':_utc(max([v for v in (last_http,last_attempt,last_save) if v],default=0)) if (last_http or last_attempt or last_save) else None,
      'first_attempt_at':_utc(first_attempt) if first_attempt else None,
      'metrics':{
         'indexed_urls':sum(statuses.values()),
         'unique_urls_checked':unique,
         'total_url_attempts':attempts,
         'successful_links':statuses.get('completed',0),
         'unique_files':data['uploaded_files'],
         'stored_bytes':data['uploaded_bytes'],
         'successful_domains':source_hosts,
         'http_requests':data['http_requests'],
         'robots_requests':data['robots_requests'],
         'http_403':int(codes.get('403',0)),
         'http_404':int(codes.get('404',0)),
         'http_429':int(codes.get('429',0)),
         'http_5xx':sum(int(v) for code,v in codes.items() if code.isdigit() and 500<=int(code)<=599),
         'http_p95_ms':p95,
         'unresolved_urls':sum(errors.values()),
      },
      'http_codes':codes,
      'url_statuses':statuses,
      'mime_types':mime,
      'error_categories':errors,
      'top_hosts':hosts,
      'hourly':timeline,
      'links':{
         'drive_folder':'https://drive.google.com/drive/folders/1uyPU91NHIfIf-wGXO5UAAnNCG9CqQD1o',
         'github_actions':'https://github.com/UsernameMP/English/actions',
      },
      'notes':[
        'Attempted URLs and unique stored files are distinct counters.',
        'HTTP requests include robots.txt and redirects.',
        'No source document bytes or tokens are published in dashboard metrics.',
      ],
    }

def make_baseline():
    """Historical pilot as a clearly labeled static snapshot, not live telemetry."""
    return {
      'schema_version':1,'generated_at':'2026-10-28T09:07:18Z',
      'state':'historical','stop_reason':'file_limit_reached','run_id':None,
      'limit_new_urls':None,'source':'RIFT 200-file final audit, 2026-10-28',
      'last_activity_at':'2026-10-28T06:43:30Z','first_attempt_at':'2026-10-28T05:06:55Z',
      'metrics':{
        'indexed_urls':332292,'unique_urls_checked':328,'total_url_attempts':452,
        'successful_links':200,'unique_files':200,'stored_bytes':422184443,
        'successful_domains':200,'http_requests':817,'robots_requests':465,
        'http_403':17,'http_404':127,'http_429':5,'http_5xx':20,
        'http_p95_ms':1131,'unresolved_urls':128,
      },
      'http_codes':{'200':463,'301':134,'302':48,'307':2,'400':1,
                    '403':17,'404':127,'429':5,'500':4,'502':8,'503':8},
      'url_statuses':{'completed':200,'blocked':31,'failed':41,
                      'skipped':43,'html_deferred':13,'pending':331964},
      'error_categories':{'blocked':31,'failed':41,'skipped':43,'html_deferred':13},
      'mime_types':{'application/pdf':151,'application/zip':19,
                    'application/x-zip-compressed':1,'application/msword':6,
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document':8,
                    'application/vnd.rar':5,
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':4,
                    'text/x-tex':2,'application/vnd.oasis.opendocument.text':1,
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation':1,
                    'application/gzip':1,'application/postscript':1},
      'top_hosts':[],'hourly':[],
      'links':{
         'drive_folder':'https://drive.google.com/drive/folders/1uyPU91NHIfIf-wGXO5UAAnNCG9CqQD1o',
         'github_actions':'https://github.com/UsernameMP/English/actions',
      },
      'notes':['Historical completed 200-file pilot, not live worker state.',
               '328 distinct source URLs were tried; 200 unique files stored.',
               'Do not mistake 200 successful files for the original 200-URL trial.'],
    }

TEMPLATE=r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RIFT / Downloader Control</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
 color-scheme:dark;--ink:#f4f5fa;--muted:#9aa7c1;--line:#25324b;--bg:#080f1d;--pane:#111c31;
 --bright:#61ddac;--accent:#80a8fa;--warning:#ffc87a}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 90% -10%,#142949,#080f1d 65%);color:var(--ink)}
main{max-width:1220px;margin:0 auto;padding:32px 20px 70px}
header,.actions,.headline,.meter-label{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.brand{letter-spacing:.09em;font-weight:800;color:var(--accent);font-size:14px}
h1{font-size:clamp(30px,4vw,46px);font-weight:680;letter-spacing:-.035em;margin:9px 0 8px}
h2{font-size:18px;margin:0 0 16px;font-weight:650}
p{color:var(--muted);line-height:1.6}.tag{border:1px solid var(--line);border-radius:40px;
 padding:6px 10px;font-size:12px;color:var(--muted)}
a.button,button{display:inline-flex;align-items:center;justify-content:center;padding:11px 15px;
 border-radius:10px;background:#1d2b45;color:#e5eaf6;border:1px solid #374665;
 text-decoration:none;font-size:13px;font-weight:650;cursor:pointer}
a.button:hover,button:hover{background:#294268}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin-top:26px}
.kpi,.panel{background:rgba(17,28,49,.88);border:1px solid var(--line);border-radius:15px;padding:21px}
.kpi small{display:block;color:var(--muted);line-height:1.5;font-size:12px}
.kpi strong{display:block;font-size:clamp(23px,3vw,35px);letter-spacing:-.04em;margin:8px 0 5px}
.kpi span{font-size:12px;color:var(--muted)}
.secondary{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
.metric{padding:12px 0;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:15px;font-size:14px}
.metric span{color:var(--muted)}.metric strong{font-variant-numeric:tabular-nums}
.bar-line{display:grid;grid-template-columns:minmax(110px,1fr) 3fr 42px;gap:12px;
 align-items:center;margin:12px 0;font-size:12px;color:var(--muted)}
.bar{background:#1a2942;border-radius:8px;height:9px;overflow:hidden}
.bar>span{display:block;height:100%;border-radius:8px;background:var(--accent)}
.bar.warn>span{background:var(--warning)}
.status{color:var(--bright)}.tiny{font-size:12px;color:var(--muted)}
footer{border-top:1px solid var(--line);padding-top:20px;margin-top:20px}
@media(max-width:850px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.secondary{grid-template-columns:1fr}}
@media(max-width:420px){.stats{grid-template-columns:1fr}.kpi{padding:15px}main{padding:20px 12px}}
</style></head><body><main>
<header><div class="brand">RIFT / SOURCE INDEX</div><div class="tag" id="state">Загрузка отчёта…</div></header>
<div class="headline"><div><h1>Панель скачивателя</h1><p>Файлы, URL, отказы сайтов и контроль сохранности в Google Drive.</p></div>
<div class="actions"><a class="button" id="actions" target="_blank" rel="noopener">GitHub Actions</a>
<a class="button" id="drive" target="_blank" rel="noopener">Google Drive</a>
<button onclick="location.reload()">Обновить</button></div></div>
<div class="stats">
 <div class="kpi"><small>Проверено уникальных ссылок</small><strong id="urls">—</strong><span id="attempts">—</span></div>
 <div class="kpi"><small>Уникальных сохранённых файлов</small><strong id="files">—</strong><span id="size">—</span></div>
 <div class="kpi"><small>Запреты сайтов HTTP 403/429</small><strong id="denials">—</strong><span id="deny-detail">—</span></div>
 <div class="kpi"><small>Недоступные HTTP 404</small><strong id="not-found">—</strong><span id="total-http">—</span></div>
</div>
<div class="secondary">
 <section class="panel"><h2>Состояния URL</h2><div id="statuses"></div></section>
 <section class="panel"><h2>HTTP-ответы сайтов</h2><div id="http-statuses"></div></section>
 <section class="panel"><h2>Какие документы сохранены</h2><div id="mimes"></div></section>
 <section class="panel"><h2>Контроль работы</h2>
  <div class="metric"><span>Статус</span><strong id="mode">—</strong></div>
  <div class="metric"><span>Последняя активность</span><strong id="last">—</strong></div>
  <div class="metric"><span>Запросов robots.txt</span><strong id="robots">—</strong></div>
  <div class="metric"><span>HTTP p95</span><strong id="latency">—</strong></div>
  <div class="metric"><span>Разных успешных доменов</span><strong id="domains">—</strong></div>
  <div class="metric"><span>Причина остановки</span><strong id="stop">—</strong></div>
 </section>
</div>
<footer><p class="tiny" id="notes">Исторические данные / ожидаем файл отчёта. Новые загрузки не запускаются из этой страницы.</p>
<p class="tiny">Панель содержит только агрегаты. Доступ к Google Drive, управление запуском и паузой выполняются отдельно с проверкой прав в GitHub Actions. Скрытые токены и документы не передаются браузеру.</p></footer>
<script id="metrics" type="application/json">__METRICS__</script>
<script>
"use strict";
const fmt=n=>new Intl.NumberFormat('ru-RU').format(Number(n||0));
const set=(id,v)=>{document.getElementById(id).textContent=String(v)};
const bytes=v=>{let i=0;while(v>=1024&&i<4){v/=1024;i++}return v.toFixed(i?1:0)+' '+['Б','КиБ','МиБ','ГиБ','ТиБ'][i]};
function bars(id,entries,warning){const root=document.getElementById(id);root.replaceChildren();
const items=Object.entries(entries||{}).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]).slice(0,10);
const max=Math.max(1,...items.map(x=>x[1]));
for(const [key,val] of items){const line=document.createElement('div');line.className='bar-line';
const name=document.createElement('span');name.textContent=key;name.title=key;
const track=document.createElement('div');track.className='bar'+(warning?' warn':'');
const fill=document.createElement('span');fill.style.width=(100*val/max).toFixed(2)+'%';
const value=document.createElement('strong');value.textContent=fmt(val);value.style.textAlign='right';
track.append(fill);line.append(name,track,value);root.append(line);}
if(!items.length)root.textContent='Нет данных';
}
function draw(d){const m=d.metrics||{};
set('state',d.state==='historical'?'Завершённый пилот / исторические данные':String(d.state||'нет состояния'));
set('urls',fmt(m.unique_urls_checked));set('attempts',fmt(m.total_url_attempts)+' попыток URL');
set('files',fmt(m.unique_files));set('size',bytes(m.stored_bytes||0));
set('denials',fmt((m.http_403||0)+(m.http_429||0)));
set('deny-detail',fmt(m.http_403)+' запретов / '+fmt(m.http_429)+' ограничений частоты');
set('not-found',fmt(m.http_404));
set('total-http',fmt(m.http_requests)+' HTTP-запросов, включая robots и редиректы');
set('mode',String(d.state||'—'));set('last',d.last_activity_at?new Date(d.last_activity_at).toLocaleString('ru-RU'):'—');
set('robots',fmt(m.robots_requests));set('latency',m.http_p95_ms!=null?fmt(m.http_p95_ms)+' мс':'—');
set('domains',fmt(m.successful_domains));set('stop',String(d.stop_reason||'—'));
const links=d.links||{};document.getElementById('actions').href=links.github_actions||'https://github.com/UsernameMP/English/actions';
document.getElementById('drive').href=links.drive_folder||'https://drive.google.com/drive/u/0/my-drive';
bars('statuses',Object.fromEntries(Object.entries(d.url_statuses||{}).filter(x=>x[0]!=='pending')));
bars('http-statuses',d.http_codes,true);
bars('mimes',d.mime_types);
set('notes',d.source+' · обновлено '+(d.generated_at||'—')+'. '+(d.notes||[]).join(' '));
}
try{draw(JSON.parse(document.getElementById('metrics').textContent))}catch(e){set('state','Ошибка формата отчёта')}
</script></main></body></html>"""

def render_html(data):
    # A literal JSON script tag requires escaping HTML interpretation.
    blob=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return TEMPLATE.replace('__METRICS__',blob)

def write_dashboard(data,html_path,json_path=None):
    path=Path(html_path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(render_html(data),encoding='utf-8')
    if json_path:
        out=Path(json_path);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return path

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate standalone RIFT operations dashboard without network')
    p.add_argument('--db')
    p.add_argument('--baseline',action='store_true')
    p.add_argument('--output',required=True)
    p.add_argument('--json')
    p.add_argument('--state',default='snapshot')
    p.add_argument('--stop-reason')
    p.add_argument('--limit-new-urls',type=int)
    p.add_argument('--run-id')
    args=p.parse_args(argv)
    if bool(args.db)==bool(args.baseline):p.error('Pass exactly one of --db or --baseline')
    data=make_baseline() if args.baseline else build_metrics(connect(args.db),
        run_state=args.state,stop_reason=args.stop_reason,
        limit_new_urls=args.limit_new_urls,run_id=args.run_id)
    path=write_dashboard(data,args.output,args.json)
    print(json.dumps({'dashboard':str(path),'unique_urls_checked':data['metrics']['unique_urls_checked'],
                      'unique_files':data['metrics']['unique_files'],'mode':data['state']},ensure_ascii=False))

if __name__=='__main__':main()
