function makeLinks(doc){
  const bundle=bundleMembers(doc),roles=bundle.map(d=>inferDocument(d).values.role);
  const hasTask=roles.includes("TASK_SET"),hasAns=roles.includes("ANSWER_KEY"),hasCrit=roles.includes("CRITERIA"),hasScript=roles.includes("LISTENING_SCRIPT");
  const audioDoc=bundle.find(d=>d.audioUrl)||(doc.audioUrl?doc:null),hasAudio=!!audioDoc,edges=[];

  bundle.forEach(d=>edges.push({
    id:stable("edge",bundleKey(doc)+d.id),
    from:stable("problemset",bundleKey(doc)),
    to:stable("asset",d.id),
    from_label:"ProblemSet",
    to_label:d.filename,
    type:"CONTAINS_ASSET",
    confidence:bundle.length>1?.96:.78,
    status:"SUGGESTED",
    provenance:{method:"bundle_key",reason:"same canonical bundle key"}
  }));

  if(audioDoc)edges.push({
    id:stable("edge",bundleKey(doc)+"audio"),
    from:stable("problemset",bundleKey(doc)),
    to:stable("media",audioDoc.audioSha||audioDoc.audioUrl),
    from_label:"ProblemSet",
    to_label:"MP3 · "+(audioDoc.audioSource?audioDoc.audioSource.split("/").pop():"Listening audio"),
    type:"CONTAINS_MEDIA",
    confidence:.99,
    status:"SUGGESTED",
    provenance:{method:"source_filename_contract",source_url:audioDoc.audioSource,reason:"task PDF and audio share the same source filename contract"},
    start_sec:null,
    end_sec:null
  });

  if(hasTask&&hasAns)edges.push({
    id:stable("edge",bundleKey(doc)+"task-answer"),
    from:"Task set",to:"Answer set",from_label:"Task set",to_label:"Answer key",
    type:"HAS_ANSWER",confidence:.94,status:"SUGGESTED",
    provenance:{method:"problemset_structure",reason:"task and answer assets are in the same proposed ProblemSet"}
  });

  if(hasTask&&hasCrit)edges.push({
    id:stable("edge",bundleKey(doc)+"criteria"),
    from:"Writing",to:"Criterion rubric",from_label:"Writing",to_label:"Criterion rubric",
    type:"SCORED_BY",confidence:.88,status:"SUGGESTED",
    provenance:{method:"problemset_structure",reason:"criteria asset is compatible with the task bundle"}
  });

  if(hasTask&&hasScript)edges.push({
    id:stable("edge",bundleKey(doc)+"script"),
    from:"Listening",to:"Transcript",from_label:"Listening",to_label:"Listening transcript",
    type:"USES_TRANSCRIPT",confidence:.91,status:"SUGGESTED",
    provenance:{method:"problemset_structure",reason:"script asset is compatible with the Listening section"}
  });

  if(hasTask&&hasAudio)edges.push({
    id:stable("edge",bundleKey(doc)+"listening-audio"),
    from:"Listening",
    to:stable("media",audioDoc.audioSha||audioDoc.audioUrl),
    from_label:"Listening",
    to_label:"MP3 · "+(audioDoc.audioSource?audioDoc.audioSource.split("/").pop():"Listening audio"),
    type:"USES_AUDIO",
    confidence:.99,
    status:"SUGGESTED",
    provenance:{method:"problemset_media_link",source_url:audioDoc.audioSource,reason:"audio asset is linked to the same ProblemSet and Listening is present"},
    start_sec:null,
    end_sec:null
  });

  return{edges,flags:{hasTask,hasAns,hasCrit,hasScript,hasAudio}};
}

function linkQuestion(edge){
  const ru=uiLocale==="ru";
  if(edge.type==="CONTAINS_ASSET")return ru
    ?'Этот файл действительно входит в этот ProblemSet?'
    :'Does this file really belong to this ProblemSet?';
  if(edge.type==="CONTAINS_MEDIA")return ru
    ?'Этот MP3 действительно относится к этому ProblemSet?'
    :'Does this MP3 really belong to this ProblemSet?';
  if(edge.type==="HAS_ANSWER")return ru
    ?'Этот ключ ответов соответствует этому набору заданий?'
    :'Does this answer key correspond to this task set?';
  if(edge.type==="SCORED_BY")return ru
    ?'Эти критерии оценивания относятся к секции Writing?'
    :'Do these scoring criteria apply to the Writing section?';
  if(edge.type==="USES_TRANSCRIPT")return ru
    ?'Этот transcript относится к секции Listening?'
    :'Does this transcript belong to the Listening section?';
  if(edge.type==="USES_AUDIO")return ru
    ?'Этот MP3 используется именно секцией Listening?'
    :'Is this MP3 the audio used by the Listening section?';
  return ru?'Подтвердить эту связь?':'Confirm this relationship?';
}

function linkReason(edge){
  const method=edge.provenance&&edge.provenance.method;
  const ru=uiLocale==="ru";
  if(method==="bundle_key")return ru?"Совпадает ключ комплекта, извлечённый из имени/метаданных.":"Canonical bundle key matches.";
  if(method==="source_filename_contract")return ru?"PDF и MP3 имеют согласованное исходное имя одного комплекта.":"PDF and MP3 share the source filename contract.";
  if(method==="problemset_media_link")return ru?"MP3 уже предложен в том же ProblemSet, где найдена Listening-секция.":"MP3 is proposed in the same ProblemSet that contains Listening.";
  if(method==="problemset_structure")return ru?"Связь предложена по структуре одного ProblemSet.":"Proposed from the structure of the same ProblemSet.";
  return ru?"Автоматически предложенная связь.":"Automatically proposed relationship.";
}

function decisionLabel(decision){
  if(decision==="CONFIRMED")return t("confirmed");
  if(decision==="REJECTED")return t("rejected");
  if(decision==="NEEDS_REVIEW")return t("needsReviewStatus");
  return t("unreviewed");
}

function detectLinkExceptions(doc,pack){
  const flags=pack.flags,ex=[],nodes=ensureStructure(doc),taskLabels=[],criterionTargets={};
  const hasListening=nodes.some(section=>/listening/i.test(String(section.label||"")));
  nodes.forEach(section=>(section.tasks||[]).forEach(task=>taskLabels.push(String(task.label||"").trim().toLowerCase())));
  const duplicates=[...new Set(taskLabels.filter((x,i)=>x&&taskLabels.indexOf(x)!==i))];
  const ru=uiLocale==="ru";

  if(flags.hasTask&&!flags.hasAns)ex.push([ru?"Задания без ответов":"Task without answer",ru?"К этому ProblemSet не найден ключ ответов.":"No answer asset is linked to this ProblemSet."]);
  if(flags.hasAns&&!flags.hasTask)ex.push([ru?"Ответы без заданий":"Answer without task",ru?"Есть answer key, но не найден файл с заданиями.":"Answer key exists without a task asset."]);
  if(flags.hasScript&&!flags.hasTask)ex.push([ru?"Script без заданий":"Script without task",ru?"Listening script найден без файла заданий.":"Listening script exists without task asset."]);
  if(hasListening&&!flags.hasAudio)ex.push([ru?"Listening без аудио":"Listening without audio",ru?"Секция Listening есть, но MP3 не связан.":"Listening section exists but no MP3 is linked."]);
  if(flags.hasAudio&&!flags.hasTask)ex.push([ru?"Аудио без заданий":"Audio without task",ru?"MP3 найден без task asset.":"Audio asset exists without a task asset."]);
  if(bundleMembers(doc).length===1&&!flags.hasAudio)ex.push([ru?"Неполный комплект":"Incomplete bundle",ru?"Сейчас в ProblemSet найден только один asset.":"Only one asset is currently present in the proposed ProblemSet."]);
  if(duplicates.length)ex.push([ru?"Неоднозначная нумерация":"Ambiguous numbering",(ru?"Повторяющиеся названия заданий: ":"Duplicate task labels: ")+duplicates.join(", ")]);

  pack.edges.filter(e=>e.type==="SCORED_BY").forEach(e=>{criterionTargets[e.to]=(criterionTargets[e.to]||0)+1});
  const multi=Object.entries(criterionTargets).filter(x=>x[1]>1);
  if(multi.length)ex.push([ru?"Один критерий связан с несколькими заданиями":"Criterion linked to multiple tasks",ru?"Нужно вручную проверить область действия критерия.":"The criterion scope needs manual review."]);
  return ex;
}

function renderLinks(doc){
  const ds=docState(doc),pack=makeLinks(doc),edges=pack.edges,flags=pack.flags,dec=ds.links.decisions||{};
  const answerCov=flags.hasTask?(flags.hasAns?100:0):(flags.hasAns?0:null);
  const criteriaCov=flags.hasTask?(flags.hasCrit?100:0):null;
  const scriptCov=flags.hasScript?100:(flags.hasTask?0:null);
  const mediaCov=flags.hasAudio?100:(flags.hasTask?0:null);
  const cards=[[t("answers"),answerCov],[t("criteria"),criteriaCov],[t("scriptTranscript"),scriptCov],[t("audioMedia"),mediaCov]];
  const allConfirmed=edges.length>0&&edges.every(e=>dec[e.id]==="CONFIRMED");
  $("confirmLinks").textContent=allConfirmed?t("undoSuggested"):t("confirmSuggested");
  $("confirmLinks").classList.toggle("primary",allConfirmed);
  $("confirmLinks").disabled=edges.length===0;

  $("coverageCards").innerHTML=cards.map(x=>
    '<div class="coverage"><strong>'+(x[1]==null?"-":x[1]+"%")+'</strong><span>'+x[0]+' · '+t("coverage")+'</span></div>'
  ).join("");

  const visible=unresolvedOnly
    ?edges.filter(e=>!dec[e.id]||dec[e.id]==="NEEDS_REVIEW")
    :edges;

  const rows=visible.map(e=>{
    const decision=dec[e.id]||"UNREVIEWED";
    const seg=(e.start_sec!=null||e.end_sec!=null)?(' · '+(e.start_sec??"")+"-"+(e.end_sec??"")+" sec"):"";
    return '<div class="edge link-review">'+
      '<div class="link-main">'+
        '<div class="link-question">'+linkQuestion(e)+'</div>'+
        '<div class="link-target">'+e.from_label+' → '+e.to_label+'</div>'+
        '<div class="muted">'+linkReason(e)+' · '+Math.round(e.confidence*100)+'%</div>'+
        '<div class="muted">'+t("decision")+': <b>'+decisionLabel(decision)+'</b>'+seg+'</div>'+
        '<details class="technical-details"><summary>'+(uiLocale==="ru"?"Технические детали":"Technical details")+'</summary><div class="mono">'+e.type+' · '+e.id+'</div><pre>'+JSON.stringify(e.provenance||{},null,2)+'</pre></details>'+
      '</div>'+
      '<div class="edge-actions">'+
        '<button class="'+(decision==="CONFIRMED"?"decision-active":"")+'" data-edge="'+e.id+'" data-d="CONFIRMED">'+(uiLocale==="ru"?"Подтвердить":"Confirm")+'</button>'+
        '<button class="'+(decision==="REJECTED"?"decision-active":"")+'" data-edge="'+e.id+'" data-d="REJECTED">'+(uiLocale==="ru"?"Отклонить":"Reject")+'</button>'+
        '<button class="'+(decision==="NEEDS_REVIEW"?"decision-active":"")+'" data-edge="'+e.id+'" data-d="NEEDS_REVIEW">'+t("needsReview")+'</button>'+
      '</div>'+
    '</div>';
  }).join("");

  $("linkTable").innerHTML='<div class="edge-list">'+(rows||"<div class='muted'>"+(uiLocale==="ru"?"Нет связей в этом фильтре.":"No links in this filter.")+"</div>")+'</div>';

  document.querySelectorAll("[data-edge]").forEach(b=>b.onclick=()=>{
    const current=ds.links.decisions[b.dataset.edge]||"UNREVIEWED";
    ds.links.decisions[b.dataset.edge]=current===b.dataset.d?"UNREVIEWED":b.dataset.d;
    armSave();
    renderLinks(doc);
  });

  const ex=detectLinkExceptions(doc,pack);
  const erows=ex.map(x=>
    '<div class="exception"><div><b class="status-warn">'+x[0]+'</b><div class="muted">'+x[1]+'</div></div></div>'
  ).join("");
  $("exceptions").innerHTML='<div class="exception-list">'+(erows||"<div class='status-ok'>"+(uiLocale==="ru"?"Структурных исключений не найдено.":"No structural exceptions detected.")+"</div>")+'</div>';
}

function bindLinks(){
  $("unresolvedOnly").onclick=()=>{
    unresolvedOnly=!unresolvedOnly;
    $("unresolvedOnly").textContent=unresolvedOnly?t("showAll"):t("unresolvedOnly");
    renderLinks(docs[current]);
  };

  $("confirmLinks").onclick=()=>{
    const doc=docs[current],ds=docState(doc),pack=makeLinks(doc);
    const allConfirmed=pack.edges.length>0&&pack.edges.every(e=>ds.links.decisions[e.id]==="CONFIRMED");
    pack.edges.forEach(e=>ds.links.decisions[e.id]=allConfirmed?"UNREVIEWED":"CONFIRMED");
    armSave();
    renderLinks(doc);
  };
}
