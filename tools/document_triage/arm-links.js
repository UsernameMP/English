function makeLinks(doc){
  const bundle=bundleMembers(doc),roles=bundle.map(d=>inferDocument(d).values.role);
  const hasTask=roles.includes("TASK_SET"),hasAns=roles.includes("ANSWER_KEY"),hasCrit=roles.includes("CRITERIA"),hasScript=roles.includes("LISTENING_SCRIPT");
  const audioDoc=bundle.find(d=>d.audioUrl)||(doc.audioUrl?doc:null),hasAudio=!!audioDoc,edges=[];
  bundle.forEach(d=>edges.push({
    id:stable("edge",bundleKey(doc)+d.id),
    from:stable("problemset",bundleKey(doc)),
    to:stable("asset",d.id),
    type:"CONTAINS_ASSET",
    confidence:bundle.length>1?.96:.78,
    status:"SUGGESTED",
    provenance:{method:"bundle_key"}
  }));
  if(audioDoc)edges.push({
    id:stable("edge",bundleKey(doc)+"audio"),
    from:stable("problemset",bundleKey(doc)),
    to:stable("media",audioDoc.audioSha||audioDoc.audioUrl),
    type:"CONTAINS_MEDIA",
    confidence:.99,
    status:"SUGGESTED",
    provenance:{method:"source_filename_contract",source_url:audioDoc.audioSource},
    start_sec:null,
    end_sec:null
  });
  if(hasTask&&hasAns)edges.push({id:stable("edge",bundleKey(doc)+"task-answer"),from:"Task set",to:"Answer set",type:"HAS_ANSWER",confidence:.94,status:"SUGGESTED"});
  if(hasTask&&hasCrit)edges.push({id:stable("edge",bundleKey(doc)+"criteria"),from:"Writing",to:"Criterion rubric",type:"SCORED_BY",confidence:.88,status:"SUGGESTED"});
  if(hasTask&&hasScript)edges.push({id:stable("edge",bundleKey(doc)+"script"),from:"Listening",to:"Transcript",type:"USES_TRANSCRIPT",confidence:.91,status:"SUGGESTED"});
  if(hasTask&&hasAudio)edges.push({
    id:stable("edge",bundleKey(doc)+"listening-audio"),
    from:"Listening",
    to:stable("media",audioDoc.audioSha||audioDoc.audioUrl),
    type:"USES_AUDIO",
    confidence:.99,
    status:"SUGGESTED",
    provenance:{method:"problemset_media_link",source_url:audioDoc.audioSource},
    start_sec:null,
    end_sec:null
  });
  return{edges,flags:{hasTask,hasAns,hasCrit,hasScript,hasAudio}};
}
function detectLinkExceptions(doc,pack){
  const flags=pack.flags,ex=[],nodes=ensureStructure(doc),taskLabels=[],criterionTargets={};
  const hasListening=nodes.some(section=>/listening/i.test(String(section.label||"")));
  nodes.forEach(section=>(section.tasks||[]).forEach(task=>taskLabels.push(String(task.label||"").trim().toLowerCase())));
  const duplicates=[...new Set(taskLabels.filter((x,i)=>x&&taskLabels.indexOf(x)!==i))];
  if(flags.hasTask&&!flags.hasAns)ex.push(["task without answer","No answer asset linked to this ProblemSet"]);
  if(flags.hasAns&&!flags.hasTask)ex.push(["answer without task","Answer key exists without task asset"]);
  if(flags.hasScript&&!flags.hasTask)ex.push(["media without task","Listening script exists without task asset"]);
  if(hasListening&&!flags.hasAudio)ex.push(["listening without audio","Listening section exists but no MP3 is linked"]);
  if(flags.hasAudio&&!flags.hasTask)ex.push(["audio without task","Audio asset exists without a task asset"]);
  if(bundleMembers(doc).length===1&&!flags.hasAudio)ex.push(["bundle incomplete","Only one asset is currently present in proposed ProblemSet"]);
  if(duplicates.length)ex.push(["ambiguous numbering","Duplicate task labels: "+duplicates.join(", ")]);
  pack.edges.filter(e=>e.type==="SCORED_BY").forEach(e=>{criterionTargets[e.to]=(criterionTargets[e.to]||0)+1});
  const multi=Object.entries(criterionTargets).filter(x=>x[1]>1);
  if(multi.length)ex.push(["criterion linked to multiple tasks","Criterion target reused: "+multi.map(x=>x[0]).join(", ")]);
  return ex;
}
function renderLinks(doc){
  const ds=docState(doc),pack=makeLinks(doc),edges=pack.edges,flags=pack.flags,dec=ds.links.decisions||{};
  const answerCov=flags.hasTask?(flags.hasAns?100:0):(flags.hasAns?0:null);
  const criteriaCov=flags.hasTask?(flags.hasCrit?100:0):null;
  const mediaCov=flags.hasTask?(flags.hasAudio?100:(flags.hasScript?50:0)):null;
  const cards=[["Answers",answerCov],["Criteria",criteriaCov],["Audio / Media",mediaCov]];
  $("coverageCards").innerHTML=cards.map(x=>'<div class="coverage"><strong>'+(x[1]==null?"-":x[1]+"%")+'</strong><span>'+x[0]+' coverage</span></div>').join("");
  const visible=unresolvedOnly?edges.filter(e=>!dec[e.id]||dec[e.id]==="UNRESOLVED"):edges;
  const rows=visible.map(e=>{
    const seg=(e.start_sec!=null||e.end_sec!=null)?(' · '+(e.start_sec??"")+"-"+(e.end_sec??"")+" sec"):"";
    return '<div class="edge"><div><b>'+e.type+'</b><div class="muted">'+e.from+' -> '+e.to+' - '+Math.round(e.confidence*100)+'%'+seg+'</div></div><div class="edge-actions"><button data-edge="'+e.id+'" data-d="CONFIRMED">OK</button><button data-edge="'+e.id+'" data-d="REJECTED">X</button></div></div>';
  }).join("");
  $("linkTable").innerHTML='<div class="edge-list">'+(rows||"<div class='muted'>No links in this filter.</div>")+'</div>';
  document.querySelectorAll("[data-edge]").forEach(b=>b.onclick=()=>{ds.links.decisions[b.dataset.edge]=b.dataset.d;armSave();renderLinks(doc)});
  const ex=detectLinkExceptions(doc,pack);
  const erows=ex.map(x=>'<div class="exception"><div><b class="status-warn">'+x[0]+'</b><div class="muted">'+x[1]+'</div></div><button>Needs review</button></div>').join("");
  $("exceptions").innerHTML='<div class="exception-list">'+(erows||"<div class='status-ok'>No structural exceptions detected.</div>")+'</div>';
}
function bindLinks(){
  $("unresolvedOnly").onclick=()=>{unresolvedOnly=!unresolvedOnly;$("unresolvedOnly").textContent=unresolvedOnly?"Show all":"Unresolved only";renderLinks(docs[current])};
  $("confirmLinks").onclick=()=>{const ds=docState(docs[current]),pack=makeLinks(docs[current]);pack.edges.forEach(e=>ds.links.decisions[e.id]="CONFIRMED");armSave();renderLinks(docs[current])};
}
