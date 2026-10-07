const ARM_STORE="corpus-assessor-arm-v4";
const LOCALE_STORE="corpus-assessor-locale";
let uiLocale=localStorage.getItem(LOCALE_STORE)||"ru";
let sourceUrls={},deployedAssets={},calibrationGold={documents:{}},taskTaxonomy={},docs=[],current=0,armState=JSON.parse(localStorage.getItem(ARM_STORE)||"{}"),selectedNode=null,selectedTask=null,conflictsOnly=false,unresolvedOnly=false;

const I18N={
  ru:{
    interface:"Интерфейс",exportAudit:"Экспорт audit JSON",
    pass1Tab:"Pass 1 · Документ + ProblemSet",pass2Tab:"Pass 2 · Секции + задания",linksTab:"Pass 3 · Связи",
    machineProfile:"Профиль документа",machineProfileHint:"Подтверди корректный профиль целиком или исправь только ошибки.",
    needsReview:"Нужна проверка",clearNeedsReview:"Снять флаг",confirmDocument:"Подтвердить документ",undoConfirm:"Отменить подтверждение",
    problemsetProposal:"Предлагаемый ProblemSet",problemsetHint:"Предлагаемый комплект связанных файлов.",confirmBundle:"Подтвердить комплект",undoBundle:"Отменить комплект",
    audit:"Аудит",evidence:"Evidence",decision:"Решение",
    pass2Title:"Проверка границ секций и заданий",pass2Hint:"Машина предлагает структуру. Ассессор подтверждает, исправляет или создаёт пропущенные объекты.",
    addSection:"+ Секция",addTask:"+ Задание",conflictsOnly:"Только конфликты",showAll:"Показать всё",confirmStructure:"Подтвердить структуру",undoStructure:"Отменить подтверждение структуры",
    structureTree:"Структура",contextInspector:"Контекст и правки",
    linksTitle:"Проверка связей",linksHint:"Подтверди, что предложенные файлы и сущности действительно относятся друг к другу.",
    unresolvedOnly:"Только нерешённые",confirmSuggested:"Подтвердить предложенные",undoSuggested:"Отменить массовое подтверждение",proposedLinks:"Предлагаемые связи",exceptionQueue:"Исключения",
    answers:"Ответы",criteria:"Критерии",scriptTranscript:"Скрипт / транскрипт",audioMedia:"Аудио / медиа",coverage:"покрытие",
    confirmed:"Подтверждено",rejected:"Отклонено",needsReviewStatus:"Нужна проверка",unreviewed:"Не проверено",inReview:"В работе",
    proposalSource:"Источник предложения",calibrationPreset:"Калибровочный preset",calibrationGold:"Проверенная калибровка",layoutRules:"Layout parser",filenameHeuristic:"Эвристика по имени файла",documentEvidence:"Текст документа",human:"Создано человеком",
    linkedAudio:"Связанное аудио",listeningAudio:"Аудио Listening",openAudio:"Открыть аудио",documentComplete:"Документ завершён",documentInReview:"Документ в работе",nextDocument:"Следующий документ →",
    field_role:"Тип документа",field_subject:"Предмет",field_language:"Язык документа",field_academic_year:"Учебный год",field_grades:"Классы",
    field_competition:"Олимпиада",field_stage:"Этап",field_tour:"Тур",field_region:"Регион",field_problemset:"ProblemSet",
    value_TASK_SET:"Задания",value_ANSWER_KEY:"Ответы",value_CRITERIA:"Критерии",value_LISTENING_SCRIPT:"Скрипт аудирования",value_OTHER:"Другое",
    value_ENGLISH:"Английский язык",value_RUSSIAN:"Русский язык",value_UNKNOWN:"Не определено",
    value_RU:"Русский",value_EN:"Английский",value_RU_EN:"Русский + английский",
    value_VSOSh:"Всероссийская олимпиада школьников",
    value_MUNICIPAL:"Муниципальный этап",value_REGIONAL:"Региональный этап",
    value_WRITTEN:"Письменный тур",value_ORAL:"Устный тур",
    progress:"завершено"
  },
  en:{
    interface:"Interface",exportAudit:"Export audit JSON",
    pass1Tab:"Pass 1 · Document + ProblemSet",pass2Tab:"Pass 2 · Sections + Tasks",linksTab:"Pass 3 · Links",
    machineProfile:"Document profile",machineProfileHint:"Confirm the whole correct profile or change only the wrong fields.",
    needsReview:"Needs review",clearNeedsReview:"Clear flag",confirmDocument:"Confirm document",undoConfirm:"Undo confirmation",
    problemsetProposal:"ProblemSet proposal",problemsetHint:"Proposed bundle of related files.",confirmBundle:"Confirm bundle",undoBundle:"Undo bundle",
    audit:"Audit",evidence:"Evidence",decision:"Decision",
    pass2Title:"Section / Task boundary review",pass2Hint:"The machine proposes structure. The reviewer confirms, corrects, or creates missing objects.",
    addSection:"+ Section",addTask:"+ Task",conflictsOnly:"Conflicts only",showAll:"Show all",confirmStructure:"Confirm structure",undoStructure:"Undo structure confirmation",
    structureTree:"Structure tree",contextInspector:"Context inspector",
    linksTitle:"Link verification",linksHint:"Confirm that the proposed files and entities really belong together.",
    unresolvedOnly:"Unresolved only",confirmSuggested:"Confirm suggested",undoSuggested:"Undo bulk confirmation",proposedLinks:"Proposed links",exceptionQueue:"Exception queue",
    answers:"Answers",criteria:"Criteria",scriptTranscript:"Script / Transcript",audioMedia:"Audio / Media",coverage:"coverage",
    confirmed:"Confirmed",rejected:"Rejected",needsReviewStatus:"Needs review",unreviewed:"Unreviewed",inReview:"In review",
    proposalSource:"Proposal source",calibrationPreset:"Calibration preset",calibrationGold:"Reviewed calibration",layoutRules:"Layout parser",filenameHeuristic:"Filename heuristic",documentEvidence:"Document text",human:"Human-created",
    linkedAudio:"Linked audio",listeningAudio:"Listening audio",openAudio:"Open audio",documentComplete:"Document complete",documentInReview:"Document in review",nextDocument:"Next document →",
    field_role:"Document type",field_subject:"Subject",field_language:"Document language",field_academic_year:"Academic year",field_grades:"Grades",
    field_competition:"Competition",field_stage:"Stage",field_tour:"Tour",field_region:"Region",field_problemset:"ProblemSet",
    value_TASK_SET:"Task set",value_ANSWER_KEY:"Answer key",value_CRITERIA:"Criteria",value_LISTENING_SCRIPT:"Listening script",value_OTHER:"Other",
    value_ENGLISH:"English",value_RUSSIAN:"Russian",value_UNKNOWN:"Unknown",
    value_RU:"Russian",value_EN:"English",value_RU_EN:"Russian + English",
    value_VSOSh:"All-Russian School Olympiad",
    value_MUNICIPAL:"Municipal stage",value_REGIONAL:"Regional stage",
    value_WRITTEN:"Written round",value_ORAL:"Oral round",
    progress:"complete"
  }
};

function t(key){return (I18N[uiLocale]&&I18N[uiLocale][key])||I18N.en[key]||key}
function valueLabel(field,value){
  const normalized=String(value==null?"":value);
  const key="value_"+normalized.replace("+","_");
  return (I18N[uiLocale]&&I18N[uiLocale][key])||normalized.replaceAll("_"," ");
}
function proposalSourceLabel(source){
  const map={CALIBRATION_PRESET:"calibrationPreset",CALIBRATION_GOLD:"calibrationGold",LAYOUT_RULES:"layoutRules",FILENAME_HEURISTIC:"filenameHeuristic",DOCUMENT_EVIDENCE:"documentEvidence",HUMAN:"human"};
  return t(map[source]||"filenameHeuristic");
}

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

function armSave(){
  localStorage.setItem(ARM_STORE,JSON.stringify(armState));
  renderProgress();
  if(docs[current])renderReviewStatus(docs[current]);
}
function armFilename(url){return decodeURIComponent(new URL(url).pathname.split("/").pop()||"")}
function canonicalStem(name){return name.replace(/\.[^.]+$/,"").replace(/^(tasks?|ans(?:wers?)?|script|criteria|solutions?|audio)-/i,"").toLowerCase()}
function stable(prefix,s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return prefix+"_"+(h>>>0).toString(16).padStart(8,"0")}
function docState(doc){
  if(!armState[doc.id])armState[doc.id]={};
  const ds=armState[doc.id];
  ds.pass1=ds.pass1||{};
  ds.pass1.status=ds.pass1.status||"UNREVIEWED";
  ds.pass1.fields=ds.pass1.fields||{};
  ds.pass1.bundleDecision=ds.pass1.bundleDecision||"UNREVIEWED";
  ds.pass2=ds.pass2||{};
  if(typeof ds.pass2.confirmed!=="boolean")ds.pass2.confirmed=false;
  if(!Object.prototype.hasOwnProperty.call(ds.pass2,"nodes"))ds.pass2.nodes=null;
  ds.links=ds.links||{};
  ds.links.decisions=ds.links.decisions||{};
  return ds;
}
function bundleKey(doc){return canonicalStem(doc.filename)}
function bundleMembers(doc){const key=bundleKey(doc);return docs.filter(d=>bundleKey(d)===key)}
function filenameEvidence(doc,label,token=""){
  const detail=token?doc.filename+' · token "'+token+'"':doc.filename;
  return {page:null,search:"",snippet:detail,source:"filename",label};
}
function inferDocument(doc){
  const name=doc.filename.toLowerCase();
  const roleToken=name.startsWith("tasks-")?"tasks":name.startsWith("ans-")?"ans":name.startsWith("script-")?"script":name.startsWith("criteria-")?"criteria":"";
  const role=roleToken==="tasks"?"TASK_SET":roleToken==="ans"?"ANSWER_KEY":roleToken==="script"?"LISTENING_SCRIPT":roleToken==="criteria"?"CRITERIA":"OTHER";
  const yr=name.match(/-(\d{2})-(\d{2})\.pdf$/); const academic_year=yr?("20"+yr[1]+"/"+yr[2]):"UNKNOWN";
  const gr=name.match(/engl-(\d+)-(\d+)/); const grades=gr?(gr[1]+"-"+gr[2]):"UNKNOWN";
  const stageToken=name.includes("-mun-")?"mun":name.includes("-reg-")?"reg":"";
  const stage=stageToken==="mun"?"MUNICIPAL":stageToken==="reg"?"REGIONAL":"UNKNOWN";
  const tourToken=name.includes("-pism-")?"pism":name.includes("-ustn-")?"ustn":"";
  const tour=tourToken==="pism"?"WRITTEN":tourToken==="ustn"?"ORAL":"UNKNOWN";
  const rm=name.match(/-(?:mun|reg)-([a-z0-9]+)-\d{2}-\d{2}\.pdf$/); const rawRegion=rm?rm[1].toLowerCase():""; const region=rawRegion?(REGION_CODES[rawRegion]||rawRegion.toUpperCase()):"UNKNOWN";
  const values={role,subject:"ENGLISH",language:"UNKNOWN",academic_year,grades,competition:"VSOSh",stage,tour,region,problemset:canonicalStem(doc.filename)};
  const confidence={role:.99,subject:.99,language:.35,academic_year:academic_year==="UNKNOWN"?.45:.98,grades:grades==="UNKNOWN"?.45:.98,competition:.72,stage:stage==="UNKNOWN"?.55:.97,tour:tour==="UNKNOWN"?.55:.97,region:region==="UNKNOWN"?.52:.88,problemset:.91};
  const proposal_source={
    role:"FILENAME_HEURISTIC",subject:"FILENAME_HEURISTIC",language:"FILENAME_HEURISTIC",academic_year:"FILENAME_HEURISTIC",
    grades:"FILENAME_HEURISTIC",competition:"FILENAME_HEURISTIC",stage:"FILENAME_HEURISTIC",tour:"FILENAME_HEURISTIC",region:"FILENAME_HEURISTIC",problemset:"FILENAME_HEURISTIC"
  };
  const evidence={
    role:filenameEvidence(doc,"filename prefix",roleToken),
    subject:filenameEvidence(doc,"filename token","engl"),
    language:{page:null,search:"",snippet:"No direct language evidence in filename",source:"heuristic",label:"language requires document text"},
    academic_year:filenameEvidence(doc,"filename academic-year token",yr?yr[1]+"-"+yr[2]:""),
    grades:filenameEvidence(doc,"filename grade token",gr?gr[1]+"-"+gr[2]:""),
    competition:{page:null,search:"",snippet:"VSOSh is a corpus-source default, not a PDF-text claim",source:"heuristic",label:"corpus source default"},
    stage:filenameEvidence(doc,"filename stage token",stageToken),
    tour:filenameEvidence(doc,"filename tour token",tourToken),
    region:filenameEvidence(doc,"filename region token",rawRegion),
    problemset:{page:null,search:"",snippet:canonicalStem(doc.filename),source:"derived",label:"canonical filename stem"}
  };

  if(PASS1_EVIDENCE_OVERRIDES[doc.id]){
    Object.assign(evidence,PASS1_EVIDENCE_OVERRIDES[doc.id]);
    ["subject","language","academic_year","grades","competition","stage","tour","region"].forEach(k=>proposal_source[k]="DOCUMENT_EVIDENCE");
    if(evidence.language&&evidence.language.source==="document"){
      values.language="RU+EN";
      confidence.language=.98;
    }
  }

  const gold=calibrationGold&&calibrationGold.documents&&calibrationGold.documents[doc.id];
  if(gold){
    if(gold.language){
      values.language=gold.language;
      confidence.language=.995;
      proposal_source.language="CALIBRATION_GOLD";
      evidence.language={page:null,search:"",snippet:"Human-reviewed language: "+gold.language,source:"calibration",label:"10-document calibration"};
    }
    if(Array.isArray(gold.roles)&&gold.roles.length){
      values.role=gold.roles[0];
      confidence.role=.995;
      proposal_source.role="CALIBRATION_GOLD";
      evidence.role={page:null,search:"",snippet:"Human-reviewed roles: "+gold.roles.join(" + "),source:"calibration",label:"10-document calibration"};
    }
  }
  return {values,confidence,evidence,proposal_source};
}
function focusEvidence(ev){
  return armViewer.focusEvidence(ev);
}
function formatAudioTime(sec){
  sec=Math.max(0,Number(sec)||0);
  const m=Math.floor(sec/60),s=Math.floor(sec%60);
  return m+":"+String(s).padStart(2,"0");
}
function updateContextAudioTime(){
  const el=document.getElementById("contextAudioTime"),player=document.getElementById("audioPlayer");
  if(!el||!player)return;
  const dur=Number.isFinite(player.duration)?formatAudioTime(player.duration):"--:--";
  el.textContent=formatAudioTime(player.currentTime)+" / "+dur;
}
function audioPlayFrom(sec=null){
  const player=$("audioPlayer");
  if(!player||!player.src)return;
  if(sec!=null&&Number.isFinite(Number(sec)))player.currentTime=Math.max(0,Number(sec));
  const p=player.play();
  if(p&&typeof p.catch==="function")p.catch(()=>{});
  updateContextAudioTime();
}
function audioToggle(){
  const player=$("audioPlayer");
  if(!player||!player.src)return;
  if(player.paused)audioPlayFrom();
  else player.pause();
}
function audioSeek(delta){
  const player=$("audioPlayer");
  if(!player||!player.src)return;
  player.currentTime=Math.max(0,Math.min(Number.isFinite(player.duration)?player.duration:Infinity,player.currentTime+delta));
  updateContextAudioTime();
}
function audioRestart(){
  audioPlayFrom(0);
}
function renderAudioDock(doc){
  const dock=$("audioDock"),player=$("audioPlayer");
  if(!doc.audioUrl){
    dock.classList.add("hidden");
    player.pause();
    player.removeAttribute("src");
    player.load();
    return;
  }
  dock.classList.remove("hidden");
  $("audioLabel").textContent=t("listeningAudio");
  $("audioProvenance").textContent=doc.audioSha?("sha256 "+doc.audioSha.slice(0,12)+"…"):"linked media";
  $("openAudio").href=doc.audioSource||doc.audioUrl;
  $("openAudio").textContent=t("openAudio");
  if(player.getAttribute("src")!==doc.audioUrl){
    player.src=doc.audioUrl;
    player.load();
  }
  updateContextAudioTime();
}
function linkReviewState(doc){
  const ds=docState(doc);
  const edges=typeof makeLinks==="function"?(makeLinks(doc).edges||[]):[];
  if(!edges.length)return "NA";
  const decisions=edges.map(e=>ds.links.decisions[e.id]||"UNREVIEWED");
  if(decisions.some(v=>v==="NEEDS_REVIEW"))return "NEEDS_REVIEW";
  if(decisions.every(v=>v==="CONFIRMED"||v==="REJECTED"))return "COMPLETE";
  if(decisions.some(v=>v!=="UNREVIEWED"))return "IN_REVIEW";
  return "UNREVIEWED";
}
function reviewState(doc,pass){
  const ds=docState(doc);
  if(pass==="pass1"){
    if(ds.pass1.status==="NEEDS_REVIEW")return "NEEDS_REVIEW";
    if(ds.pass1.status==="CONFIRMED"&&ds.pass1.bundleDecision==="CONFIRMED")return "COMPLETE";
    if(ds.pass1.status!=="UNREVIEWED"||ds.pass1.bundleDecision!=="UNREVIEWED"||Object.keys(ds.pass1.fields).length)return "IN_REVIEW";
    return "UNREVIEWED";
  }
  if(pass==="pass2"){
    if(ds.pass2.confirmed)return "COMPLETE";
    return ds.pass2.nodes?"IN_REVIEW":"UNREVIEWED";
  }
  return linkReviewState(doc);
}
function isDocumentComplete(doc){
  const p1=reviewState(doc,"pass1"),p2=reviewState(doc,"pass2"),p3=reviewState(doc,"links");
  return p1==="COMPLETE"&&p2==="COMPLETE"&&(p3==="COMPLETE"||p3==="NA");
}
function reviewStatusLabel(state){
  if(state==="COMPLETE")return t("confirmed");
  if(state==="NEEDS_REVIEW")return t("needsReviewStatus");
  if(state==="IN_REVIEW")return t("inReview");
  if(state==="NA")return "N/A";
  return t("unreviewed");
}
function renderReviewStatus(doc){
  const labels={pass1:t("pass1Tab"),pass2:t("pass2Tab"),links:t("linksTab")};
  Object.keys(labels).forEach(pass=>{
    const tab=document.querySelector('[data-pass="'+pass+'"]');
    if(!tab)return;
    const state=reviewState(doc,pass);
    tab.classList.remove("review-complete","review-needs-review","review-in-review","review-unreviewed","review-na");
    tab.classList.add("review-"+state.toLowerCase().replaceAll("_","-"));
    tab.textContent=labels[pass]+" · "+reviewStatusLabel(state);
  });
  const complete=isDocumentComplete(doc),status=$("documentStatus"),next=$("nextIncompleteDoc");
  if(status){
    status.textContent=complete?t("documentComplete"):t("documentInReview");
    status.classList.toggle("complete",complete);
  }
  if(next){
    next.textContent=t("nextDocument");
    next.classList.toggle("hidden",!complete);
  }
}
function renderProgress(){
  const n=docs.filter(d=>isDocumentComplete(d)).length;
  $("globalProgress").textContent=n+"/"+docs.length+" "+t("progress");
}
function renderLocale(){
  $("localeLabel").textContent=t("interface");
  $("exportState").textContent=t("exportAudit");
  document.querySelector('[data-pass="pass1"]').textContent=t("pass1Tab");
  document.querySelector('[data-pass="pass2"]').textContent=t("pass2Tab");
  document.querySelector('[data-pass="links"]').textContent=t("linksTab");
  document.querySelector("#pass1 h2").textContent=t("machineProfile");
  document.querySelector("#pass1 .section-head p").textContent=t("machineProfileHint");
  document.querySelector("#pass1 .card h3").textContent=t("problemsetProposal");
  document.querySelector("#pass1 .card .section-head p").textContent=t("problemsetHint");
  document.querySelector("#pass1 .card:last-child h3").textContent=t("audit");
  document.querySelector("#pass2 h2").textContent=t("pass2Title");
  document.querySelector("#pass2 .section-head p").textContent=t("pass2Hint");
  $("addSection").textContent=t("addSection");
  $("addTask").textContent=t("addTask");
  $("conflictsOnly").textContent=conflictsOnly?t("showAll"):t("conflictsOnly");
  $("confirmStructure").textContent=t("confirmStructure");
  document.querySelector(".pass2-tree-pane .sticky-subhead").textContent=t("structureTree");
  document.querySelector(".pass2-inspector-pane .sticky-subhead").textContent=t("contextInspector");
  document.querySelector("#links h2").textContent=t("linksTitle");
  document.querySelector("#links .section-head p").textContent=t("linksHint");
  $("unresolvedOnly").textContent=unresolvedOnly?t("showAll"):t("unresolvedOnly");
  $("confirmLinks").textContent=t("confirmSuggested");
  document.querySelectorAll("#links .card h3")[0].textContent=t("proposedLinks");
  document.querySelectorAll("#links .card h3")[1].textContent=t("exceptionQueue");
  if(docs[current])renderReviewStatus(docs[current]);
}
function switchPass(pass){
  document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.pass===pass));
  document.querySelectorAll(".pass-view").forEach(v=>v.classList.toggle("active",v.id===pass));
  const review=document.querySelector(".review-pane");
  if(review)review.classList.toggle("pass2-mode",pass==="pass2");
}
function renderDoc(){
  const doc=docs[current];if(!doc)return;
  switchPass("pass1");
  $("docIndex").textContent=(current+1)+" / "+docs.length;
  $("docSha").textContent=doc.id;
  $("openSource").href=doc.url;
  $("viewerHint").textContent="";
  renderAudioDock(doc);
  renderPass1(doc);
  selectedNode=null;
  selectedTask=null;
  $("structureTree").innerHTML="<div class='muted'>Loading document structure…</div>";
  $("boundaryEditor").innerHTML="";
  $("coverageCards").innerHTML="";
  $("linkTable").innerHTML="<div class='muted'>Loading document…</div>";
  $("exceptions").innerHTML="";
  renderProgress();
  renderReviewStatus(doc);
  armViewer.load(doc).then(meta=>{
    if(docs[current]!==doc)return;
    doc.pageCount=Math.max(1,Number(meta&&meta.pageCount)||Number(armViewer.getPageCount())||1);
    renderPass2(doc);
    renderLinks(doc);
    renderReviewStatus(doc);
  }).catch(e=>{
    console.error(e);
    $("viewerHint").textContent="PDF viewer failed: "+e.message;
  });
}
function downloadAudit(){const blob=new Blob([JSON.stringify({schema_version:"assessor-audit.v1",exported_at:new Date().toISOString(),state:armState},null,2)],{type:"application/json"}),u=URL.createObjectURL(blob),a=document.createElement("a");a.href=u;a.download="corpus_assessor_audit.json";a.click();setTimeout(()=>URL.revokeObjectURL(u),500)}
async function initArm(){
  $("uiLocale").value=uiLocale;
  sourceUrls=await fetch("source_urls.json",{cache:"no-store"}).then(r=>r.json());
  try{calibrationGold=await fetch("calibration_gold.json",{cache:"no-store"}).then(r=>r.ok?r.json():({documents:{}}));}
  catch(e){console.warn("calibration gold unavailable",e);calibrationGold={documents:{}};}
  try{taskTaxonomy=await fetch("task_taxonomy.json",{cache:"no-store"}).then(r=>r.ok?r.json():({task_kinds:[]}));}
  catch(e){console.warn("task taxonomy unavailable",e);taskTaxonomy={task_kinds:[]};}
  try{
    const r=await fetch("deployed_assets.json",{cache:"no-store"});
    deployedAssets=r.ok?await r.json():{};
  }catch(e){
    console.warn("deployed_assets unavailable",e);
    deployedAssets={};
  }
  docs=Object.entries(sourceUrls).map(([id,url])=>{
    const asset=deployedAssets[id]||{};
    return {
      id,
      url,
      filename:armFilename(url),
      viewerUrl:asset.pdf||url,
      layoutUrl:asset.layout||null,
      structureUrl:asset.structure||null,
      machineStructure:null,
      audioUrl:asset.audio||null,
      audioSource:asset.source_audio||null,
      audioSha:asset.audio_sha256||null
    };
  });
  await Promise.all(docs.map(async doc=>{
    if(!doc.structureUrl)return;
    try{
      const r=await fetch(doc.structureUrl,{cache:"no-store"});
      if(r.ok)doc.machineStructure=await r.json();
    }catch(e){console.warn("machine structure unavailable",doc.filename,e);}
  }));
  document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>switchPass(t.dataset.pass));
  $("prevDoc").onclick=()=>{current=(current-1+docs.length)%docs.length;renderDoc()};
  $("nextDoc").onclick=()=>{current=(current+1)%docs.length;renderDoc()};
  $("nextIncompleteDoc").onclick=()=>{current=(current+1)%docs.length;renderDoc()};
  $("zoomOut").onclick=()=>armViewer.zoomOut();
  $("zoomIn").onclick=()=>armViewer.zoomIn();
  $("fitWidth").onclick=()=>armViewer.fitWidth();
  $("exportState").onclick=downloadAudit;
  $("uiLocale").onchange=e=>{
    uiLocale=e.target.value==="en"?"en":"ru";
    localStorage.setItem(LOCALE_STORE,uiLocale);
    renderLocale();
    renderPass1(docs[current]);
    renderPass2(docs[current]);
    renderLinks(docs[current]);
    renderAudioDock(docs[current]);
    renderProgress();
  };
  const player=$("audioPlayer");
  ["timeupdate","loadedmetadata","durationchange","play","pause"].forEach(evt=>player.addEventListener(evt,updateContextAudioTime));
  renderLocale();bindPass1();bindPass2();bindLinks();renderDoc();
}
window.addEventListener("DOMContentLoaded",()=>initArm().catch(e=>{$("viewerHint").textContent="Initialization failed: "+e.message;console.error(e)}));
