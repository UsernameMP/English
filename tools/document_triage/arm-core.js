const ARM_STORE="corpus-assessor-arm-v2";
let sourceUrls={},docs=[],current=0,armState=JSON.parse(localStorage.getItem(ARM_STORE)||"{}"),selectedNode=null,conflictsOnly=false,unresolvedOnly=false;

const REGION_CODES={
  lenobl:"Ленинградская область",
  kaluga:"Калужская область",
  omsk:"Омская область",
  novgorod:"Новгородская область",
  kamchat:"Камчатский край",
  kamchatka:"Камчатский край",
  chel:"Челябинская область",
  bash:"Республика Башкортостан",
  irk:"Иркутская область"
};

const PASS1_EVIDENCE_OVERRIDES={
  "6c7bf55e9532cd1b6960821ac4c91fa8ebc1a48cc5aafa5405ec73b7966aa932":{
    role:{page:1,search:"Вам предстоит выполнить задания письменного тура",snippet:"Вам предстоит выполнить задания письменного тура",source:"document"},
    subject:{page:1,search:"Английский язык",snippet:"Английский язык",source:"document"},
    language:{page:1,search:"Английский язык",snippet:"Английский язык",source:"document"},
    academic_year:{page:1,search:"2024 – 2025 учебный год",snippet:"2024 – 2025 учебный год",source:"document"},
    grades:{page:1,search:"9 – 11 класс",snippet:"9 – 11 класс",source:"document"},
    competition:{page:1,search:"Всероссийская олимпиада школьников",snippet:"Всероссийская олимпиада школьников",source:"document"},
    stage:{page:1,search:"Муниципальный этап",snippet:"Муниципальный этап",source:"document"},
    tour:{page:1,search:"письменного тура",snippet:"задания письменного тура",source:"document"},
    region:{page:1,search:"Ленинградская область",snippet:"Ленинградская область",source:"document"},
    problemset:{page:1,search:"Ленинградская область",snippet:"Ленинградская область · 2024-2025 · муниципальный этап · 9-11 класс",source:"derived"}
  }
};
const $=id=>document.getElementById(id);

function armSave(){localStorage.setItem(ARM_STORE,JSON.stringify(armState));renderProgress()}
function armFilename(url){return decodeURIComponent(new URL(url).pathname.split("/").pop()||"")}
function canonicalStem(name){return name.replace(/\.[^.]+$/,"").replace(/^(tasks?|ans(?:wers?)?|script|criteria|solutions?|audio)-/i,"").toLowerCase()}
function stable(prefix,s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return prefix+"_"+(h>>>0).toString(16).padStart(8,"0")}
function docState(doc){if(!armState[doc.id])armState[doc.id]={pass1:{status:"UNREVIEWED",fields:{},bundleDecision:"UNREVIEWED"},pass2:{confirmed:false,nodes:null},links:{decisions:{}}};return armState[doc.id]}
function bundleKey(doc){return canonicalStem(doc.filename)}
function bundleMembers(doc){const key=bundleKey(doc);return docs.filter(d=>bundleKey(d)===key)}
function inferDocument(doc){
  const name=doc.filename.toLowerCase();
  const role=name.startsWith("tasks-")?"TASK_SET":name.startsWith("ans-")?"ANSWER_KEY":name.startsWith("script-")?"LISTENING_SCRIPT":name.startsWith("criteria-")?"CRITERIA":"OTHER";
  const yr=name.match(/-(\d{2})-(\d{2})\.pdf$/); const academic_year=yr?("20"+yr[1]+"/"+yr[2]):"UNKNOWN";
  const gr=name.match(/engl-(\d+)-(\d+)/); const grades=gr?(gr[1]+"-"+gr[2]):"UNKNOWN";
  const stage=name.includes("-mun-")?"MUNICIPAL":name.includes("-reg-")?"REGIONAL":"UNKNOWN";
  const tour=name.includes("-pism-")?"WRITTEN":name.includes("-ustn-")?"ORAL":"UNKNOWN";
  const rm=name.match(/-(?:mun|reg)-([a-z0-9]+)-\d{2}-\d{2}\.pdf$/); const rawRegion=rm?rm[1].toLowerCase():""; const region=rawRegion?(REGION_CODES[rawRegion]||rawRegion.toUpperCase()):"UNKNOWN";
  const values={role,subject:"ENGLISH",language:"EN",academic_year,grades,competition:"VSOSh",stage,tour,region,problemset:canonicalStem(doc.filename)};
  const confidence={role:.99,subject:.99,language:.99,academic_year:academic_year==="UNKNOWN"?.45:.98,grades:grades==="UNKNOWN"?.45:.98,competition:.96,stage:stage==="UNKNOWN"?.55:.97,tour:tour==="UNKNOWN"?.55:.97,region:region==="UNKNOWN"?.52:.88,problemset:.91};
  const evidence={};
  Object.keys(values).forEach(k=>evidence[k]={
    page:1,
    search:"",
    snippet:"",
    source:"filename",
    label:k==="role"?"source filename":"source metadata / filename"
  });
  Object.assign(evidence,PASS1_EVIDENCE_OVERRIDES[doc.id]||{});
  return {values,confidence,evidence};
}
function focusEvidence(ev){
  const doc=docs[current];
  const page=Math.max(1,Number(ev&&ev.page||1));
  let hash="#page="+page+"&zoom=page-width";
  if(ev&&ev.search)hash+="&search="+encodeURIComponent(ev.search);
  $("pdfFrame").src=doc.url+hash;
  $("evidenceHighlight").classList.add("hidden");
  const detail=(ev&&ev.snippet)?(' · "'+ev.snippet+'"'):"";
  $("viewerHint").textContent="Evidence · page "+page+detail;
}
function renderProgress(){const n=docs.filter(d=>armState[d.id]&&armState[d.id].pass1&&armState[d.id].pass1.status==="CONFIRMED").length;$("globalProgress").textContent=n+"/"+docs.length+" confirmed"}
function switchPass(pass){document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.pass===pass));document.querySelectorAll(".pass-view").forEach(v=>v.classList.toggle("active",v.id===pass))}
function renderDoc(){
  const doc=docs[current];if(!doc)return;$("docIndex").textContent=(current+1)+" / "+docs.length;$("docSha").textContent=doc.id;$("openSource").href=doc.url;$("pdfFrame").src=doc.url+"#page=1&zoom=page-width";$("viewerHint").textContent="";
  renderPass1(doc);selectedNode=null;renderPass2(doc);renderLinks(doc);renderProgress();
}
function downloadAudit(){const blob=new Blob([JSON.stringify({schema_version:"assessor-audit.v1",exported_at:new Date().toISOString(),state:armState},null,2)],{type:"application/json"}),u=URL.createObjectURL(blob),a=document.createElement("a");a.href=u;a.download="corpus_assessor_audit.json";a.click();setTimeout(()=>URL.revokeObjectURL(u),500)}
async function initArm(){
  sourceUrls=await fetch("source_urls.json",{cache:"no-store"}).then(r=>r.json());docs=Object.entries(sourceUrls).map(x=>({id:x[0],url:x[1],filename:armFilename(x[1])}));
  document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>switchPass(t.dataset.pass));$("prevDoc").onclick=()=>{current=(current-1+docs.length)%docs.length;renderDoc()};$("nextDoc").onclick=()=>{current=(current+1)%docs.length;renderDoc()};$("exportState").onclick=downloadAudit;
  bindPass1();bindPass2();bindLinks();renderDoc();
}
window.addEventListener("DOMContentLoaded",()=>initArm().catch(e=>{$("viewerHint").textContent="Initialization failed: "+e.message;console.error(e)}));
