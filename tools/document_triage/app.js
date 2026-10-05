const STORAGE_KEY="document-triage-workbench-v2";
const LEGACY_STORAGE_KEY="document-triage-workbench-v1";
const LANG_KEY="document-triage-language";

const DOCS=[
["6c7bf55e9532cd1b6960821ac4c91fa8ebc1a48cc5aafa5405ec73b7966aa932",1391160],
["b8d9062cbbfea994df41cf051a0a798c5c6631fc68a9f3154720a4b9f6268e5e",453058],
["c9d5de97bec7b5369833c294ffc618b0a7e468d45e7ca9a01612d37fde703c37",179605],
["2c231744ff1afe723d521677aa850b1399dfed6168fc9eaefd20c33ec43adfc4",76974],
["2ee2da5e302cf220a7943f79e52e77543aba22a553ffeaf6a83720c1667dd17d",276307],
["a87698f974d473374e813213d55640270e4ba23b73ea90c0d5a3fd0ba730c89b",577291],
["162e7a729c48807356677eea16760270461812d82e9ad53670cd7fe004c6d01a",515504],
["3c6ff626f77d1682c55e2135f8577c1492a541e04497ec7af053d88499a75f85",541549],
["86382eaa9112533f4ccf0cfc3ab5479ae7d986fcaed997088ade34f58bbf1554",764540],
["109e982aaebafc5e39707507335523b658d493d6bbd25599fe5b45481ee82a27",265726]
].map(x=>({id:x[0],size:x[1]}));

const ROLE_DEFS={
 TASK_SET:{ru:"Комплект заданий",en:"Task set",help_ru:"Документ с заданиями для участника: вопросы, тексты, упражнения, инструкции. Ключей ответов может не быть.",help_en:"A participant-facing document containing tasks, questions, texts, exercises or instructions. It may not contain answer keys."},
 ANSWER_KEY:{ru:"Ключи / ответы",en:"Answer key",help_ru:"Документ, где приведены правильные ответы без обязательного подробного решения.",help_en:"A document containing correct answers, without necessarily including full worked solutions."},
 CRITERIA:{ru:"Критерии оценивания",en:"Scoring criteria",help_ru:"Рубрика или схема выставления баллов: показатели, уровни, максимальные баллы, условия снижения оценки.",help_en:"A scoring rubric: dimensions, levels, maximum points and conditions for awarding or reducing points."},
 LISTENING_SCRIPT:{ru:"Скрипт / текст аудирования",en:"Listening script",help_ru:"Текст, который читается или звучит в аудиозадании. Это не само задание и не ключ.",help_en:"The text read or played for a listening task. It is neither the task itself nor the answer key."},
 AUDIO_REFERENCE:{ru:"Аудиоматериал",en:"Audio material",help_ru:"Аудиофайл либо документ, роль которого — дать аудиоматериал для задания.",help_en:"An audio file, or a document whose role is to provide audio material for a task."},
 METHODOLOGY:{ru:"Методические материалы",en:"Methodology",help_ru:"Инструкции для организаторов, жюри или преподавателей; методические рекомендации, порядок проведения.",help_en:"Guidance for organizers, jurors or teachers; methodology and administration instructions."},
 ANSWER_SHEET:{ru:"Бланк ответов",en:"Answer sheet",help_ru:"Пустой или шаблонный бланк, куда участник переносит ответы.",help_en:"A blank or template form where participants record or transfer their answers."},
 OTHER:{ru:"Другое",en:"Other",help_ru:"Документ не подходит ни под одну из перечисленных ролей.",help_en:"The document does not fit any of the listed roles."}
};

const SIGNAL_DEFS={
 EMBEDDED_ANSWERS:{ru:"Ответы внутри документа",en:"Embedded answers",help_ru:"В документе задания и ответы находятся вместе.",help_en:"Tasks and answers are contained in the same document."},
 HAS_RATIONALE_OR_EXPLANATIONS:{ru:"Есть пояснения к ответам",en:"Has rationale / explanations",help_ru:"Есть объяснение, почему ответ верный или почему другой вариант неверен.",help_en:"The document explains why an answer is correct or why another option is wrong."},
 VISUAL_ANSWER_MARKING:{ru:"Ответы отмечены визуально",en:"Visual answer marking",help_ru:"Правильность передана оформлением: подчёркиванием, цветом, жирным, галочкой, рамкой и т.п.",help_en:"Correctness is encoded visually: underline, color, bold, check mark, box, etc."},
 HAS_TABLES:{ru:"Есть таблицы",en:"Has tables",help_ru:"Содержит значимые таблицы, которые важно сохранить при дальнейшем парсинге.",help_en:"Contains meaningful tables that must be preserved during later parsing."},
 HAS_IMAGES_OR_DIAGRAMS:{ru:"Есть изображения / схемы",en:"Has images / diagrams",help_ru:"Есть изображения, схемы, карты, графики или другие визуальные элементы, важные для смысла.",help_en:"Contains images, diagrams, maps, charts or other visuals important to meaning."},
 HAS_CROSSWORD:{ru:"Есть кроссворд",en:"Has crossword",help_ru:"Содержит кроссворд или сетку, где геометрия расположения важна для задания.",help_en:"Contains a crossword or grid where spatial layout is part of the task."},
 HAS_MULTIPLE_SECTIONS:{ru:"Несколько разделов",en:"Multiple sections",help_ru:"В одном файле есть несколько самостоятельных разделов, например Listening, Reading, Writing.",help_en:"One file contains multiple distinct sections, such as Listening, Reading and Writing."},
 HAS_DISTRACTOR_OPTIONS:{ru:"Есть лишние варианты-ловушки",en:"Has distractors",help_ru:"Есть варианты, которые специально не используются или выглядят правдоподобно, но неверны.",help_en:"Contains intentionally unused or plausible-but-wrong options."},
 MIXED_DOCUMENT:{ru:"Смешанный документ",en:"Mixed document",help_ru:"Один файл выполняет несколько ролей, например ключи + критерии оценивания.",help_en:"One file has multiple roles, for example answer key plus scoring criteria."},
 UNCLEAR_OR_AMBIGUOUS:{ru:"Неоднозначно / непонятно",en:"Unclear / ambiguous",help_ru:"Проверяющий не уверен, как классифицировать документ или отдельный признак.",help_en:"The reviewer is unsure how to classify the document or a specific feature."}
};

const T={
 ru:{
  title:"Разметчик документов",prev:"← Назад",next:"Далее →",openPdf:"Открыть PDF",loading:"Загрузка…",loaded:"Загружено",
  roles:"Роль документа",metadata:"Основные данные",signals:"Признаки и содержимое (необязательно)",signalsNote:"Эти признаки нужны для будущего парсера. Если не уверены — можно не отмечать.",
  notes:"Комментарий проверяющего (необязательно)",notesPlaceholder:"Только если есть важная особенность, которую нельзя выразить полями выше.",
  subject:"Предмет",competition:"Олимпиада",competitionOther:"Название другой олимпиады",year:"Учебный год",stage:"Этап",grades:"Класс / классы",region:"Регион",tour:"Тур / часть",duration:"Время, мин",maxScore:"Максимальный балл",reviewStatus:"Статус проверки",
  save:"Сохранить",saveHelp:"Сохранить текущую разметку и остаться на этом документе.",saveNext:"Сохранить и далее",exportJsonl:"Экспорт JSONL",exportCsv:"Экспорт CSV",
  saved:"сохранено",notSaved:"не сохранено",touched:"размечено",done:"готово",
  unknown:"Не определено",other:"Другое",
  status_IN_PROGRESS:"В работе",status_DONE:"Готово",status_NEEDS_SECOND_REVIEW:"Нужна вторая проверка",status_BROKEN_OR_UNREADABLE:"Файл повреждён / не читается",
  help_subject:"Предмет выбирается из единого справочника. В данных хранится канонический код, а русский и английский названия формируются автоматически.",
  help_competition:"Олимпиада выбирается из справочника. Сейчас в нём есть ВсОШ, «другая» и «не определено»; список будет расширяться.",
  help_year:"Учебный год в формате 2025/26. Для части текущих файлов он подставляется автоматически из имени исходника.",
  help_stage:"Этап выбирается из справочника и автоматически имеет русскую и английскую подпись.",
  help_grades:"Класс или диапазон классов так, как указано в документе, например 9–11.",
  help_region:"Регион соревнования, если он явно указан или однозначно определяется.",
  help_tour:"Письменный, устный или смешанный тур. Хранится канонически и отображается на выбранном языке.",
  help_duration:"Общее время выполнения, если оно указано в документе.",
  help_maxScore:"Максимально возможный балл за документ / тур, если он указан.",
  help_reviewStatus:"«Готово» означает, что документ полностью просмотрен и разметка считается ground truth.",
  otherPlaceholder:"Введите название так, как оно указано в документе",regionPlaceholder:"Если указан",gradesPlaceholder:"Например: 9–11"
 },
 en:{
  title:"Document Triage Workbench",prev:"← Prev",next:"Next →",openPdf:"Open PDF",loading:"Loading…",loaded:"Loaded",
  roles:"Document role",metadata:"Core metadata",signals:"Signals & content (optional)",signalsNote:"These signals help the future parser. Leave them unchecked if you are unsure.",
  notes:"Reviewer note (optional)",notesPlaceholder:"Use only for an important detail that cannot be represented by the fields above.",
  subject:"Subject",competition:"Competition",competitionOther:"Other competition name",year:"Academic year",stage:"Stage",grades:"Grade(s)",region:"Region",tour:"Round / section",duration:"Duration, min",maxScore:"Maximum score",reviewStatus:"Review status",
  save:"Save",saveHelp:"Save the current annotation and stay on this document.",saveNext:"Save & Next",exportJsonl:"Export JSONL",exportCsv:"Export CSV",
  saved:"saved",notSaved:"not saved",touched:"touched",done:"done",
  unknown:"Unknown",other:"Other",
  status_IN_PROGRESS:"In progress",status_DONE:"Done",status_NEEDS_SECOND_REVIEW:"Needs second review",status_BROKEN_OR_UNREADABLE:"Broken / unreadable",
  help_subject:"Subject is selected from a shared taxonomy. Data stores a canonical ID; Russian and English labels are generated automatically.",
  help_competition:"Competition is selected from a taxonomy. It currently contains VSOSh, Other and Unknown and will be expanded.",
  help_year:"Academic year in 2025/26 format. For part of the current batch it is inferred automatically from the source filename.",
  help_stage:"Stage is selected from a taxonomy and automatically has both Russian and English labels.",
  help_grades:"Grade or grade range exactly as stated in the document, for example 9–11.",
  help_region:"Competition region when it is explicitly stated or unambiguous.",
  help_tour:"Written, oral or mixed round. Stored canonically and displayed in the selected language.",
  help_duration:"Total completion time when stated in the document.",
  help_maxScore:"Maximum possible score for the document / round when stated.",
  help_reviewStatus:"Done means the whole document was reviewed and the annotation can be treated as ground truth.",
  otherPlaceholder:"Enter the name as stated in the document",regionPlaceholder:"If stated",gradesPlaceholder:"Example: 9–11"
 }
};

let lang=localStorage.getItem(LANG_KEY)||"ru";
let taxonomy={subjects:[],competitions:[],stages:[],tours:[]};
let sourceUrls={};
let current=0;
let annotations={...JSON.parse(localStorage.getItem(LEGACY_STORAGE_KEY)||"{}"),...JSON.parse(localStorage.getItem(STORAGE_KEY)||"{}")};
const el=id=>document.getElementById(id);

function bytes(n){return n<1024?n+" B":n<1048576?(n/1024).toFixed(1)+" KB":(n/1048576).toFixed(2)+" MB"}
function dict(list,id){return list.find(x=>x.id===id)||list.find(x=>x.id==="unknown")||null}
function label(list,id,l=lang){const x=dict(list,id);return x?(x[l]||x.en||x.ru||id):id||""}
function bilingual(list,id){const x=dict(list,id);return x?{id:x.id,ru:x.ru,en:x.en}:{id:id||"unknown",ru:"",en:""}}
function helpNode(text){const s=document.createElement("span");s.className="help";s.tabIndex=0;s.textContent="?";s.dataset.tip=text;return s}
function fieldLabel(containerId,textKey,helpKey){
 const c=el(containerId);c.innerHTML="";const s=document.createElement("span");s.textContent=T[lang][textKey];c.append(s,helpNode(T[lang][helpKey]));
}
function setOptions(id,list,value){
 const s=el(id);s.innerHTML="";
 list.forEach(x=>{const o=document.createElement("option");o.value=x.id;o.textContent=x[lang]||x.en||x.ru||x.id;s.appendChild(o)});
 if(value&&[...s.options].some(o=>o.value===value))s.value=value;
}
function renderRoleChecks(){
 const c=el("roles");c.innerHTML="";
 Object.entries(ROLE_DEFS).forEach(([id,d])=>{const row=document.createElement("label");row.className="check-row";const cb=document.createElement("input");cb.type="checkbox";cb.name="roles";cb.value=id;const txt=document.createElement("span");txt.textContent=d[lang];row.append(cb,txt,helpNode(d["help_"+lang]));c.appendChild(row)});
}
function renderSignalChecks(){
 const c=el("signals");c.innerHTML="";
 Object.entries(SIGNAL_DEFS).forEach(([id,d])=>{const row=document.createElement("label");row.className="check-row";const cb=document.createElement("input");cb.type="checkbox";cb.name="signals";cb.value=id;const txt=document.createElement("span");txt.textContent=d[lang];row.append(cb,txt,helpNode(d["help_"+lang]));c.appendChild(row)});
}
function renderStatusOptions(value){
 const s=el("reviewStatus"),vals=["IN_PROGRESS","DONE","NEEDS_SECOND_REVIEW","BROKEN_OR_UNREADABLE"];s.innerHTML="";
 vals.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=T[lang]["status_"+v];s.appendChild(o)});s.value=value||"IN_PROGRESS";
}
function renderStaticText(){
 document.documentElement.lang=lang;el("appTitle").textContent=T[lang].title;el("prevBtn").textContent=T[lang].prev;el("nextBtn").textContent=T[lang].next;el("openPdf").textContent=T[lang].openPdf;
 el("rolesTitle").textContent=T[lang].roles;el("metadataTitle").textContent=T[lang].metadata;el("signalsTitle").textContent=T[lang].signals;el("signalsNote").textContent=T[lang].signalsNote;el("notesTitle").textContent=T[lang].notes;el("notes").placeholder=T[lang].notesPlaceholder;
 el("saveStayBtn").textContent=T[lang].save;el("saveStayBtn").title=T[lang].saveHelp;el("saveBtn").textContent=T[lang].saveNext;el("exportJsonl").textContent=T[lang].exportJsonl;el("exportCsv").textContent=T[lang].exportCsv;
 fieldLabel("subjectLabel","subject","help_subject");fieldLabel("competitionLabel","competition","help_competition");fieldLabel("yearLabel","year","help_year");fieldLabel("stageLabel","stage","help_stage");fieldLabel("gradesLabel","grades","help_grades");fieldLabel("regionLabel","region","help_region");fieldLabel("tourLabel","tour","help_tour");fieldLabel("durationLabel","duration","help_duration");fieldLabel("maxScoreLabel","maxScore","help_maxScore");fieldLabel("reviewStatusLabel","reviewStatus","help_reviewStatus");
 el("competitionOtherLabel").textContent=T[lang].competitionOther;el("competitionOther").placeholder=T[lang].otherPlaceholder;el("region").placeholder=T[lang].regionPlaceholder;el("grades").placeholder=T[lang].gradesPlaceholder;
}
function currentChecks(name){return [...document.querySelectorAll('input[name="'+name+'"]:checked')].map(x=>x.value)}
function setChecks(name,values){const set=new Set(values||[]);document.querySelectorAll('input[name="'+name+'"]').forEach(x=>x.checked=set.has(x.value))}
function mapLegacySubject(v){const x=(v||"").toLowerCase();if(x.includes("english")||x.includes("англ"))return"english";if(x.includes("math")||x.includes("матем"))return"mathematics";if(x.includes("informat")||x.includes("информ"))return"informatics";return"unknown"}
function mapLegacyCompetition(v){const x=(v||"").toLowerCase();if(x.includes("vsosh")||x.includes("всош")||x.includes("всероссий"))return"vsosh";return x?"other":"unknown"}
function mapLegacyStage(v){const x=(v||"").toLowerCase();if(x.includes("mun")||x.includes("муницип"))return"municipal";if(x.includes("region")||x.includes("регион"))return"regional";if(x.includes("school")||x.includes("школь"))return"school";if(x.includes("final")||x.includes("заключ"))return"final";return x?"other":"unknown"}
function mapLegacyTour(v){const x=(v||"").toLowerCase();if(x.includes("written")||x.includes("письм"))return"written";if(x.includes("oral")||x.includes("устн"))return"oral";return x?"other":"unknown"}
function infer(d){
 const u=sourceUrls[d.id]||"";const out={subject_id:"english",competition_id:"vsosh",stage_id:"unknown",tour_id:"unknown",academic_year:"",grades:""};
 if(/-mun-/.test(u))out.stage_id="municipal";else if(/-reg-/.test(u))out.stage_id="regional";
 if(/-pism-/.test(u))out.tour_id="written";else if(/-ustn-/.test(u))out.tour_id="oral";
 const g=u.match(/engl-(\d+)-(\d+)/);if(g)out.grades=g[1]+"–"+g[2];
 const y=u.match(/-(\d{2})-(\d{2})\.pdf/i);if(y)out.academic_year="20"+y[1]+"/"+y[2];
 return out;
}
function normalize(raw,d){
 const inf=infer(d),m=raw?.metadata||{};
 const subject_id=m.subject_id||mapLegacySubject(m.subject)||inf.subject_id;
 const competition_id=m.competition_id||mapLegacyCompetition(m.olympiad)||inf.competition_id;
 const stage_id=m.stage_id||mapLegacyStage(m.stage)||inf.stage_id;
 const tour_id=m.tour_id||mapLegacyTour(m.tour)||inf.tour_id;
 return{
  schema_version:"0.2",document_sha256:d.id,
  roles:raw?.roles||[],signals:raw?.signals||[],
  metadata:{
   subject_id:subject_id==="unknown"?inf.subject_id:subject_id,
   competition_id:competition_id==="unknown"?inf.competition_id:competition_id,
   competition_other:m.competition_other||(competition_id==="other"?(m.olympiad||""):""),
   academic_year:m.academic_year||inf.academic_year,
   stage_id:stage_id==="unknown"?inf.stage_id:stage_id,
   grades:m.grades||inf.grades,
   region:m.region||"",
   tour_id:tour_id==="unknown"?inf.tour_id:tour_id,
   duration_min:m.duration_min??null,max_score:m.max_score??null
  },
  notes:raw?.notes||"",review_status:raw?.review_status||"IN_PROGRESS",reviewed_at:raw?.reviewed_at||null
 };
}
function assetUrl(d){return sourceUrls[d.id]||""}
function load(i){
 current=Math.max(0,Math.min(DOCS.length-1,i));const d=DOCS[current],a=normalize(annotations[d.id],d);annotations[d.id]=a;
 renderRoleChecks();renderSignalChecks();renderStaticText();
 setOptions("subject",taxonomy.subjects,a.metadata.subject_id);setOptions("competition",taxonomy.competitions,a.metadata.competition_id);setOptions("stage",taxonomy.stages,a.metadata.stage_id);setOptions("tour",taxonomy.tours,a.metadata.tour_id);renderStatusOptions(a.review_status);
 setChecks("roles",a.roles);setChecks("signals",a.signals);
 el("competitionOther").value=a.metadata.competition_other||"";toggleCompetitionOther();
 el("year").value=a.metadata.academic_year||"";el("grades").value=a.metadata.grades||"";el("region").value=a.metadata.region||"";el("duration").value=a.metadata.duration_min??"";el("maxScore").value=a.metadata.max_score??"";el("notes").value=a.notes||"";
 el("shaLabel").textContent=d.id;el("indexPill").textContent=(current+1)+" / "+DOCS.length;el("sizePill").textContent=bytes(d.size);
 const pdf=assetUrl(d);el("openPdf").href=pdf||"#";el("viewerStatus").textContent=T[lang].loading;el("docFrame").src=pdf;
 el("savedState").textContent=annotations[d.id]?.reviewed_at?T[lang].saved:T[lang].notSaved;el("savedState").className=annotations[d.id]?.reviewed_at?"done":"muted";
 prefetchNext();updateProgress();
}
function toggleCompetitionOther(){el("competitionOtherWrap").classList.toggle("hidden",el("competition").value!=="other")}
function readForm(){
 const d=DOCS[current],sid=el("subject").value,cid=el("competition").value,stid=el("stage").value,tid=el("tour").value;
 const sb=bilingual(taxonomy.subjects,sid),cb=bilingual(taxonomy.competitions,cid),stb=bilingual(taxonomy.stages,stid),tb=bilingual(taxonomy.tours,tid);
 return{
  schema_version:"0.2",document_sha256:d.id,source_url:assetUrl(d),roles:currentChecks("roles"),signals:currentChecks("signals"),
  metadata:{
   subject_id:sb.id,subject_ru:sb.ru,subject_en:sb.en,
   competition_id:cb.id,competition_ru:cb.ru,competition_en:cb.en,competition_other:el("competitionOther").value.trim(),
   academic_year:el("year").value.trim(),
   stage_id:stb.id,stage_ru:stb.ru,stage_en:stb.en,
   grades:el("grades").value.trim(),region:el("region").value.trim(),
   tour_id:tb.id,tour_ru:tb.ru,tour_en:tb.en,
   duration_min:el("duration").value===""?null:Number(el("duration").value),max_score:el("maxScore").value===""?null:Number(el("maxScore").value)
  },
  notes:el("notes").value.trim(),review_status:el("reviewStatus").value,reviewed_at:new Date().toISOString()
 };
}
function save(stay){
 const d=DOCS[current];annotations[d.id]=readForm();localStorage.setItem(STORAGE_KEY,JSON.stringify(annotations));el("savedState").textContent=T[lang].saved;el("savedState").className="done";updateProgress();if(!stay&&current<DOCS.length-1)load(current+1);
}
function updateProgress(){const touched=DOCS.filter(d=>annotations[d.id]?.reviewed_at).length,done=DOCS.filter(d=>annotations[d.id]?.review_status==="DONE").length;el("progress").textContent=T[lang].touched+" "+touched+"/"+DOCS.length+" · "+T[lang].done+" "+done+"/"+DOCS.length}
function prefetchNext(){const n=DOCS[current+1],link=el("nextPrefetch");link.href=n?assetUrl(n):""}
function download(name,text,type){const b=new Blob([text],{type:type||"text/plain"}),u=URL.createObjectURL(b),a=document.createElement("a");a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),500)}
function exportJsonl(){download("document_triage_annotations.jsonl",DOCS.filter(d=>annotations[d.id]?.reviewed_at).map(d=>JSON.stringify(annotations[d.id])).join("\n")+"\n","application/x-ndjson")}
function csvEscape(v){if(v==null)return"";const s=Array.isArray(v)?v.join("|"):String(v);return/[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function exportCsv(){
 const h=["document_sha256","roles","subject_id","subject_ru","subject_en","competition_id","competition_ru","competition_en","competition_other","academic_year","stage_id","stage_ru","stage_en","grades","region","tour_id","tour_ru","tour_en","duration_min","max_score","signals","review_status","notes","reviewed_at"];
 const rows=[h.join(",")];DOCS.forEach(d=>{const a=annotations[d.id];if(!a?.reviewed_at)return;const m=a.metadata;rows.push([a.document_sha256,a.roles,m.subject_id,m.subject_ru,m.subject_en,m.competition_id,m.competition_ru,m.competition_en,m.competition_other,m.academic_year,m.stage_id,m.stage_ru,m.stage_en,m.grades,m.region,m.tour_id,m.tour_ru,m.tour_en,m.duration_min,m.max_score,a.signals,a.review_status,a.notes,a.reviewed_at].map(csvEscape).join(","))});download("document_triage_annotations.csv",rows.join("\n")+"\n","text/csv");
}
function switchLanguage(newLang){annotations[DOCS[current].id]=readForm();lang=newLang;localStorage.setItem(LANG_KEY,lang);load(current)}
async function init(){
 const [tr,sr]=await Promise.all([fetch("taxonomy.json",{cache:"no-store"}),fetch("source_urls.json",{cache:"no-store"})]);
 if(!tr.ok||!sr.ok)throw new Error("Could not load triage configuration");
 taxonomy=await tr.json();sourceUrls=await sr.json();
 el("langSwitch").value=lang;el("langSwitch").onchange=e=>switchLanguage(e.target.value);
 el("competition").onchange=toggleCompetitionOther;
 el("prevBtn").onclick=()=>{save(true);load(current-1)};el("nextBtn").onclick=()=>{save(true);load(current+1)};el("saveBtn").onclick=()=>save(false);el("saveStayBtn").onclick=()=>save(true);el("exportJsonl").onclick=exportJsonl;el("exportCsv").onclick=exportCsv;
 el("docFrame").onload=()=>{el("viewerStatus").textContent=T[lang].loaded};
 document.addEventListener("keydown",e=>{if(e.altKey&&e.key==="ArrowRight"){e.preventDefault();save(true);load(current+1)}if(e.altKey&&e.key==="ArrowLeft"){e.preventDefault();save(true);load(current-1)}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="s"){e.preventDefault();save(true)}});
 load(0);
}
init().catch(e=>{console.error(e);el("viewerStatus").textContent="Configuration error";});
