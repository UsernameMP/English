function initialStructure(doc){
  const role=inferDocument(doc).values.role,base=stable("asset",doc.id);
  const pageCount=Math.max(1,Number(doc.pageCount)||Number(armViewer.getPageCount&&armViewer.getPageCount())||1);
  const mk=(label,s,e,conf,tasks,evidence)=>({
    id:stable("section",base+label+s+e),
    type:"SECTION",
    label,
    start:s,
    end:e,
    confidence:conf,
    confirmed:false,
    human_created:false,
    proposal_source:doc.id==="6c7bf55e9532cd1b6960821ac4c91fa8ebc1a48cc5aafa5405ec73b7966aa932"?"CALIBRATION_PRESET":"FILENAME_HEURISTIC",
    tasks:tasks||[],
    evidence:evidence||{page:s,search:label,snippet:label}
  });

  if(doc.id==="6c7bf55e9532cd1b6960821ac4c91fa8ebc1a48cc5aafa5405ec73b7966aa932")return[
    mk("Listening",2,2,.99,[
      {id:stable("task",base+"listening-task1"),label:"Task 1",subtasks:["Part 1 · 1-5 · gap fill","Part 2 · 6-10 · open response","Part 3 · 11-13 · single choice"],evidence:{page:2,search:"Task 1. You will hear a speech",snippet:"Task 1 · three parts"},confirmed:false,human_created:false}
    ],{page:2,search:"Listening",snippet:"Listening (15 min - 20 points)"}),
    mk("Reading",3,6,.99,[
      {id:stable("task",base+"reading-task1"),label:"Task 1",subtasks:["1-9 · open / vocabulary"],evidence:{page:3,search:"water shortages",snippet:"Task 1 · water shortages · questions 1-9"},confirmed:false,human_created:false},
      {id:stable("task",base+"reading-task2"),label:"Task 2",subtasks:["10-14 · A/B/C/D"],evidence:{page:4,search:"vacuum travel",snippet:"Task 2 · vacuum travel · questions 10-14"},confirmed:false,human_created:false}
    ],{page:3,search:"Reading",snippet:"Reading (25 min - 20 points)"}),
    mk("Use of English",6,8,.99,[
      {id:stable("task",base+"use-task1"),label:"Task 1",subtasks:["1-8 · open cloze"],evidence:{page:6,search:"For questions 1-8",snippet:"Task 1 · questions 1-8 · one word per gap"},confirmed:false,human_created:false},
      {id:stable("task",base+"use-task2"),label:"Task 2",subtasks:["9-14 · key word transformation"],evidence:{page:6,search:"For questions 9-14",snippet:"Task 2 · questions 9-14 · transformation"},confirmed:false,human_created:false},
      {id:stable("task",base+"use-task3"),label:"Task 3",subtasks:["15-19 · idioms"],evidence:{page:7,search:"For questions 15-19",snippet:"Task 3 · questions 15-19 · idioms"},confirmed:false,human_created:false},
      {id:stable("task",base+"use-task4"),label:"Task 4",subtasks:["20-28 · word formation"],evidence:{page:7,search:"For questions 20-28",snippet:"Task 4 · questions 20-28 · word formation"},confirmed:false,human_created:false},
      {id:stable("task",base+"use-task5"),label:"Task 5",subtasks:["29-34 · A/B/C/D"],evidence:{page:7,search:"For questions 29-34",snippet:"Task 5 · questions 29-34 · single choice"},confirmed:false,human_created:false}
    ],{page:6,search:"Use of English",snippet:"Use of English (40 min - 40 points)"}),
    mk("Writing",9,9,.99,[
      {id:stable("task",base+"writing"),label:"Article",subtasks:["180-200 words"],evidence:{page:9,search:"ARTICLES WANTED",snippet:"Writing · article · 180-200 words"},confirmed:false,human_created:false}
    ],{page:9,search:"Writing",snippet:"Writing (40 min - 20 points)"})
  ];

  if(role==="TASK_SET")return[
    mk("Listening",2,2,.80,[{id:stable("task",base+"1"),label:"Task 1",subtasks:[],evidence:{page:2,search:"Task 1",snippet:"Task 1"},confirmed:false,human_created:false}],{page:2,search:"Listening",snippet:"Listening"}),
    mk("Reading",3,5,.76,[{id:stable("task",base+"3"),label:"Task 1",subtasks:[],evidence:{page:3,search:"Task 1",snippet:"Reading task"},confirmed:false,human_created:false}],{page:3,search:"Reading",snippet:"Reading"}),
    mk("Use of English",6,8,.72,[{id:stable("task",base+"4"),label:"Task 1",subtasks:[],evidence:{page:6,search:"Task 1",snippet:"Use of English task"},confirmed:false,human_created:false}],{page:6,search:"Use of English",snippet:"Use of English"}),
    mk("Writing",9,9,.70,[{id:stable("task",base+"5"),label:"Writing task",subtasks:[],evidence:{page:9,search:"Writing",snippet:"Writing"},confirmed:false,human_created:false}],{page:9,search:"Writing",snippet:"Writing"})
  ];
  if(role==="ANSWER_KEY")return[
    mk("Listening answers",1,1,.80,[{id:stable("answer",base+"a1"),label:"Answers",subtasks:[],evidence:{page:1,search:"Listening",snippet:"Listening answers"},confirmed:false,human_created:false}]),
    mk("Reading answers",2,2,.78,[{id:stable("answer",base+"a2"),label:"Answers",subtasks:[],evidence:{page:2,search:"Reading",snippet:"Reading answers"},confirmed:false,human_created:false}]),
    mk("Use of English answers",3,3,.75,[{id:stable("answer",base+"a3"),label:"Answers",subtasks:[],evidence:{page:3,search:"Use of English",snippet:"Use of English answers"},confirmed:false,human_created:false}]),
    mk("Criteria / rationale",4,5,.64,[{id:stable("criterion",base+"c1"),label:"Rubric / rationale",subtasks:[],evidence:{page:4,search:"criteria",snippet:"Criteria / rationale"},confirmed:false,human_created:false}])
  ];
  if(role==="LISTENING_SCRIPT")return[
    mk("Transcription",1,pageCount,.84,[
      {id:stable("transcript",base+"part1"),label:"Part 1",subtasks:[],evidence:{page:1,search:"Part 1",snippet:"Transcription Part 1"},confirmed:false,human_created:false,proposal_source:"FILENAME_HEURISTIC"}
    ],{page:1,search:"",snippet:"Listening transcription"})
  ];
  return[mk("Document",1,1,.55,[],{page:1,search:"",snippet:"Document"})];
}

function recalcChildren(node){
  const span={page_start:node.start,page_end:node.end};
  (node.tasks||[]).forEach((task,index)=>{
    task.span={...span};
    task.order=index;
    (task.subtasks||[]).forEach((subtask,subIndex)=>{
      if(typeof subtask==="string")return;
      subtask.span={...span};
      subtask.order=subIndex;
    });
  });
}

function ensureStructure(doc){
  const ds=docState(doc),role=inferDocument(doc).values.role;
  const legacyScriptDefault=role==="LISTENING_SCRIPT"&&Array.isArray(ds.pass2.nodes)&&ds.pass2.nodes.length===3&&
    ds.pass2.nodes.map(n=>String(n.label||"")).join("|")==="Part 1|Part 2|Part 3"&&
    ds.pass2.nodes.every(n=>!n.human_created&&!n.corrected&&!n.confirmed);
  if(legacyScriptDefault)ds.pass2.nodes=null;
  if(!ds.pass2.nodes)ds.pass2.nodes=initialStructure(doc);
  ds.pass2.nodes.forEach(node=>{
    if(!node.proposal_source)node.proposal_source=node.human_created?"HUMAN":(doc.id==="6c7bf55e9532cd1b6960821ac4c91fa8ebc1a48cc5aafa5405ec73b7966aa932"?"CALIBRATION_PRESET":"FILENAME_HEURISTIC");
    (node.tasks||[]).forEach(task=>{
      if(!task.proposal_source)task.proposal_source=task.human_created?"HUMAN":node.proposal_source;
    });
    recalcChildren(node);
  });
  return ds.pass2.nodes;
}

function invalidateStructure(doc){
  docState(doc).pass2.confirmed=false;
}

function isListeningSection(node){
  return /listening/i.test(String(node&&node.label||""));
}

function reviewSequence(doc){
  const items=[];
  ensureStructure(doc).forEach(node=>{
    items.push({kind:"section",node,task:null,id:node.id});
    (node.tasks||[]).forEach(task=>items.push({kind:"task",node,task,id:task.id}));
  });
  return items;
}

function selectReviewItem(doc,node,task=null){
  selectedNode=node.id;
  selectedTask=task?task.id:null;
  const evidence=(task&&task.evidence)||node.evidence||{
    page:node.start,
    search:(task&&task.label)||node.label,
    snippet:(task&&task.label)||node.label
  };
  focusEvidence(evidence);
  renderPass2(doc);
}

function navigateReview(doc,delta){
  const items=reviewSequence(doc);
  const currentId=selectedTask||selectedNode;
  let i=items.findIndex(item=>item.id===currentId);
  if(i<0)i=0;
  i=Math.max(0,Math.min(items.length-1,i+delta));
  const item=items[i];
  if(item)selectReviewItem(doc,item.node,item.task);
}

function currentPdfPage(){
  return Math.max(1,Number(armViewer.getCurrentPage()||1));
}

function sectionForCurrentPage(doc){
  const page=currentPdfPage();
  const nodes=ensureStructure(doc);
  return nodes.find(n=>page>=Number(n.start||1)&&page<=Number(n.end||n.start||1))||nodes.find(n=>n.id===selectedNode)||nodes[0]||null;
}

function createSection(doc){
  const nodes=ensureStructure(doc),page=currentPdfPage();
  const id=stable("section",doc.id+"manual-"+Date.now()+"-"+page);
  const node={
    id,
    type:"SECTION",
    label:uiLocale==="ru"?"Новая секция":"New section",
    start:page,
    end:page,
    confidence:1,
    confirmed:false,
    human_created:true,
    proposal_source:"HUMAN",
    corrected:true,
    tasks:[],
    evidence:{page,search:"",snippet:"Human-created section",source:"human"}
  };
  nodes.push(node);
  nodes.sort((a,b)=>Number(a.start||1)-Number(b.start||1));
  recalcChildren(node);
  selectedNode=node.id;
  selectedTask=null;
  invalidateStructure(doc);
  armSave();
  renderPass2(doc);
}

function createTask(doc){
  const node=ensureStructure(doc).find(n=>n.id===selectedNode)||sectionForCurrentPage(doc);
  if(!node)return;
  const page=currentPdfPage();
  const task={
    id:stable("task",doc.id+"manual-"+Date.now()+"-"+page),
    label:uiLocale==="ru"?"Новое задание":"New task",
    subtasks:[],
    confidence:1,
    confirmed:false,
    human_created:true,
    proposal_source:"HUMAN",
    corrected:true,
    evidence:{page,search:"",snippet:"Human-created task",source:"human"}
  };
  node.tasks=node.tasks||[];
  node.tasks.push(task);
  recalcChildren(node);
  selectedNode=node.id;
  selectedTask=task.id;
  invalidateStructure(doc);
  armSave();
  renderPass2(doc);
}

function deleteSelectedTask(doc,node,task){
  if(!task)return;
  const message=uiLocale==="ru"?"Удалить это задание из разметки?":"Delete this task from the annotation?";
  if(!window.confirm(message))return;
  node.tasks=(node.tasks||[]).filter(t=>t.id!==task.id);
  recalcChildren(node);
  selectedTask=null;
  selectedNode=node.id;
  invalidateStructure(doc);
  armSave();
  renderPass2(doc);
}

function deleteSelectedSection(doc,node){
  if(!node)return;
  const message=uiLocale==="ru"?"Удалить секцию и все её задания?":"Delete this section and all of its tasks?";
  if(!window.confirm(message))return;
  const nodes=ensureStructure(doc);
  const i=nodes.findIndex(n=>n.id===node.id);
  nodes.splice(i,1);
  const next=nodes[Math.min(i,nodes.length-1)]||nodes[0]||null;
  selectedNode=next?next.id:null;
  selectedTask=null;
  invalidateStructure(doc);
  armSave();
  renderPass2(doc);
}

function renderPass2(doc){
  const ds=docState(doc),nodes=ensureStructure(doc),tree=$("structureTree");
  const confirm=$("confirmStructure");
  confirm.textContent=ds.pass2.confirmed?t("undoStructure"):t("confirmStructure");
  confirm.classList.toggle("primary",ds.pass2.confirmed);
  const treePane=tree.closest(".pass2-tree-pane");
  const priorScroll=treePane?treePane.scrollTop:0;
  tree.innerHTML="";
  const shown=conflictsOnly?nodes.filter(n=>n.confidence<.8):nodes;

  if(!selectedNode&&nodes[0]){
    selectedNode=nodes[0].id;
    selectedTask=null;
  }

  shown.forEach(n=>{
    const el=document.createElement("div");
    el.className="tree-node "+(selectedNode===n.id?"selected ":"")+(n.confidence<.8?"conflict":"");
    const children=(n.tasks||[]).map(t=>{
      const cls="task-child "+(selectedTask===t.id?"selected-task":"");
      return '<div class="'+cls+'" data-task-id="'+t.id+'">→ '+t.label+(t.subtasks&&t.subtasks.length?" · "+t.subtasks.join(", "):"")+'</div>';
    }).join("");

    el.innerHTML='<div class="tree-title"><span>'+n.label+'</span><span>p.'+n.start+'-'+n.end+' · '+Math.round(n.confidence*100)+'%</span></div>'+children;
    el.onclick=()=>{
      selectedTask=null;
      selectReviewItem(doc,n,null);
    };
    tree.appendChild(el);

    el.querySelectorAll(".task-child").forEach((child,idx)=>{
      const task=n.tasks[idx];
      child.onclick=event=>{
        event.stopPropagation();
        selectReviewItem(doc,n,task);
      };
    });
  });

  if(treePane)treePane.scrollTop=priorScroll;

  let node=nodes.find(n=>n.id===selectedNode)||nodes[0]||null;
  if(node&&selectedNode!==node.id){
    selectedNode=node.id;
    selectedTask=null;
  }
  let task=node&&selectedTask?(node.tasks||[]).find(t=>t.id===selectedTask)||null:null;
  if(selectedTask&&!task)selectedTask=null;
  renderBoundaryEditor(doc,node,task);
}

function renderListeningTransport(doc,node,task){
  if(!isListeningSection(node))return "";
  if(!doc.audioUrl){
    return '<div class="missing-audio"><b>Listening verification:</b> audio is not linked to this ProblemSet. Transcript/script is a separate asset and is not treated as audio. The case remains in exception review.</div>';
  }
  const segmentStart=task&&task.audio_start_sec!=null?task.audio_start_sec:null;
  const segmentEnd=task&&task.audio_end_sec!=null?task.audio_end_sec:null;
  const segment=segmentStart!=null||segmentEnd!=null
    ?("Segment: "+(segmentStart!=null?formatAudioTime(segmentStart):"…")+" – "+(segmentEnd!=null?formatAudioTime(segmentEnd):"…"))
    :"Audio segment not timed yet";
  return '<div class="listening-transport">'+
    '<div class="context-kind">Listening verification</div>'+
    '<div class="muted" style="margin:3px 0 8px">'+segment+'</div>'+
    '<div class="transport-row">'+
      '<button data-audio="toggle">Play / Pause</button>'+
      '<button data-audio="restart">Restart</button>'+
      '<button data-audio="back">−5s</button>'+
      '<button data-audio="forward">+5s</button>'+
      '<span id="contextAudioTime" class="transport-time">0:00 / --:--</span>'+
    '</div>'+
  '</div>';
}

function renderBoundaryEditor(doc,node,task=null){
  const box=$("boundaryEditor");
  if(!node){
    box.innerHTML="<span class='muted'>Select a node or create a new Section.</span>";
    return;
  }

  const selected=task||node;
  const kind=task?(uiLocale==="ru"?"Задание":"Task"):(uiLocale==="ru"?"Секция":"Section");
  const source=selected.proposal_source||node.proposal_source||(selected.human_created?"HUMAN":"FILENAME_HEURISTIC");
  const selectedConfidence=selected.confidence==null?node.confidence:selected.confidence;
  const subtasks=task&&task.subtasks&&task.subtasks.length
    ?'<div class="context-subtasks">'+task.subtasks.map(s=>'<div class="context-chip">'+s+'</div>').join("")+'</div>'
    :"";

  const taskEditor=task
    ?'<label class="muted">'+(uiLocale==="ru"?"Название задания":"Task label")+'</label><input id="taskLabel" class="human-input" value="'+String(task.label||"").replaceAll('"','&quot;')+'">'+
      '<div class="boundary-source-actions"><button data-task-op="anchor-current">'+(uiLocale==="ru"?"Привязать к текущей странице PDF":"Anchor task to current PDF page")+'</button><button data-task-op="accept">'+(uiLocale==="ru"?"Подтвердить задание":"Accept task")+'</button><button data-task-op="delete">'+(uiLocale==="ru"?"Удалить задание":"Delete task")+'</button></div>'
    :"";

  const sectionEditor=!task
    ?'<label class="muted">'+(uiLocale==="ru"?"Название секции":"Section label")+'</label><input id="nodeLabel" class="human-input" value="'+String(node.label||"").replaceAll('"','&quot;')+'">'
    :'<div class="muted">'+(uiLocale==="ru"?"Родительская секция":"Parent section")+': <b>'+node.label+'</b></div>';

  box.innerHTML=
    '<div class="context-title"><div><div class="context-kind">'+kind+'</div><h3>'+selected.label+'</h3></div><span class="confidence '+confClass(selectedConfidence)+'">'+Math.round(selectedConfidence*100)+'%</span></div>'+
    '<div class="muted mono">'+selected.id+'</div>'+
    '<div class="muted" style="margin-top:4px">'+t("proposalSource")+': <b>'+proposalSourceLabel(source)+'</b></div>'+
    '<div class="context-nav"><button data-nav="prev">← '+(uiLocale==="ru"?"Предыдущее":"Previous")+'</button><button data-nav="next">'+(uiLocale==="ru"?"Следующее":"Next")+' →</button></div>'+
    subtasks+
    renderListeningTransport(doc,node,task)+
    taskEditor+
    sectionEditor+
    '<div class="subhead" style="margin-top:14px">'+(uiLocale==="ru"?"Границы родительской секции":"Parent section boundary")+'</div>'+
    '<div class="boundary-range">'+
      '<label>'+(uiLocale==="ru"?"Начальная страница":"Start page")+'<input id="sectionStart" class="human-input" type="number" min="1" value="'+node.start+'"></label>'+
      '<label>'+(uiLocale==="ru"?"Конечная страница":"End page")+'<input id="sectionEnd" class="human-input" type="number" min="1" value="'+node.end+'"></label>'+
    '</div>'+
    '<div class="boundary-source-actions"><button data-boundary-current="start">'+(uiLocale==="ru"?"Начало = текущая страница":"Start = current PDF page")+'</button><button data-boundary-current="end">'+(uiLocale==="ru"?"Конец = текущая страница":"End = current PDF page")+'</button></div>'+
    '<div class="boundary-actions"><button data-op="left">'+(uiLocale==="ru"?"Начало −1":"Start −1")+'</button><button data-op="right">'+(uiLocale==="ru"?"Конец +1":"End +1")+'</button><button data-op="split">'+(uiLocale==="ru"?"Разделить":"Split")+'</button><button data-op="merge">'+(uiLocale==="ru"?"Объединить со следующей":"Merge next")+'</button><button data-op="accept">'+(uiLocale==="ru"?"Подтвердить секцию":"Accept section")+'</button><button data-op="delete">'+(uiLocale==="ru"?"Удалить секцию":"Delete section")+'</button></div>';

  const nodeLabel=$("nodeLabel");
  if(nodeLabel)nodeLabel.onchange=e=>{
    node.label=e.target.value.trim()||node.label;
    node.corrected=true;
    invalidateStructure(doc);
    armSave();
    renderPass2(doc);
  };

  const taskLabel=$("taskLabel");
  if(taskLabel)taskLabel.onchange=e=>{
    task.label=e.target.value.trim()||task.label;
    task.corrected=true;
    invalidateStructure(doc);
    armSave();
    renderPass2(doc);
  };

  const sectionStart=$("sectionStart");
  const sectionEnd=$("sectionEnd");
  const saveBoundary=()=>{
    const start=Math.max(1,Number(sectionStart.value)||1);
    const end=Math.max(start,Number(sectionEnd.value)||start);
    node.start=start;
    node.end=end;
    node.corrected=true;
    node.evidence={...(node.evidence||{}),page:start,source:"human-boundary"};
    recalcChildren(node);
    invalidateStructure(doc);
    armSave();
    renderPass2(doc);
  };
  sectionStart.onchange=saveBoundary;
  sectionEnd.onchange=saveBoundary;

  box.querySelectorAll("[data-boundary-current]").forEach(b=>b.onclick=()=>{
    const page=currentPdfPage();
    if(b.dataset.boundaryCurrent==="start"){
      node.start=page;
      if(node.end<page)node.end=page;
    }else{
      node.end=Math.max(node.start,page);
    }
    node.corrected=true;
    node.evidence={...(node.evidence||{}),page:node.start,source:"human-boundary"};
    recalcChildren(node);
    invalidateStructure(doc);
    armSave();
    renderPass2(doc);
  });

  box.querySelectorAll("[data-op]").forEach(b=>b.onclick=()=>boundaryOp(doc,node,b.dataset.op));

  box.querySelectorAll("[data-task-op]").forEach(b=>b.onclick=()=>{
    if(!task)return;
    if(b.dataset.taskOp==="accept"){
      task.confirmed=true;
    }
    if(b.dataset.taskOp==="delete"){
      deleteSelectedTask(doc,node,task);
      return;
    }
    if(b.dataset.taskOp==="anchor-current"){
      task.evidence={...(task.evidence||{}),page:currentPdfPage(),search:"",snippet:task.label,source:"human"};
      task.corrected=true;
      invalidateStructure(doc);
    }
    armSave();
    renderPass2(doc);
  });

  box.querySelectorAll("[data-nav]").forEach(b=>b.onclick=()=>navigateReview(doc,b.dataset.nav==="prev"?-1:1));
  box.querySelectorAll("[data-audio]").forEach(b=>b.onclick=()=>{
    const op=b.dataset.audio;
    if(op==="toggle")audioToggle();
    if(op==="restart")audioRestart();
    if(op==="back")audioSeek(-5);
    if(op==="forward")audioSeek(5);
  });
  updateContextAudioTime();
}

function boundaryOp(doc,node,op){
  const nodes=ensureStructure(doc),i=nodes.findIndex(n=>n.id===node.id);
  if(op==="delete"){deleteSelectedSection(doc,node);return}
  if(["left","right","split","merge"].includes(op))invalidateStructure(doc);
  if(op==="accept"){node.confirmed=true;node.confidence=1}
  if(op==="left"&&node.start>1){
    node.start--;
    node.corrected=true;
  }
  if(op==="right"){
    node.end++;
    node.corrected=true;
  }
  if(op==="split"&&node.end>node.start){
    const mid=Math.floor((node.start+node.end)/2),copy=structuredClone(node),cut=Math.ceil((node.tasks||[]).length/2);
    node.end=mid;
    copy.start=mid+1;
    copy.id=stable("section",doc.id+"human-split-"+Date.now()+"-"+copy.start);
    copy.label=node.label+" B";
    node.label=node.label+" A";
    copy.confidence=Math.min(copy.confidence,.72);
    copy.corrected=true;
    node.corrected=true;
    copy.tasks=(node.tasks||[]).slice(cut);
    node.tasks=(node.tasks||[]).slice(0,cut);
    recalcChildren(node);
    recalcChildren(copy);
    nodes.splice(i+1,0,copy);
  }
  if(op==="merge"&&i<nodes.length-1){
    const next=nodes[i+1];
    node.end=Math.max(node.end,next.end);
    node.tasks=[...(node.tasks||[]),...(next.tasks||[])];
    node.label=node.label+" + "+next.label;
    node.corrected=true;
    recalcChildren(node);
    nodes.splice(i+1,1);
  }
  node.evidence={...(node.evidence||{}),page:node.start,source:"human-boundary"};
  nodes.forEach(recalcChildren);
  armSave();
  selectedNode=node.id;
  if(selectedTask&&!(node.tasks||[]).some(t=>t.id===selectedTask))selectedTask=null;
  renderPass2(doc);
}

function bindPass2(){
  $("addSection").onclick=()=>createSection(docs[current]);
  $("addTask").onclick=()=>createTask(docs[current]);

  $("conflictsOnly").onclick=()=>{
    conflictsOnly=!conflictsOnly;
    $("conflictsOnly").textContent=conflictsOnly?t("showAll"):t("conflictsOnly");
    renderPass2(docs[current]);
  };

  $("confirmStructure").onclick=()=>{
    const doc=docs[current],ds=docState(doc),next=!ds.pass2.confirmed;
    ensureStructure(doc).forEach(n=>{
      n.confirmed=next;
      (n.tasks||[]).forEach(t=>t.confirmed=next);
    });
    ds.pass2.confirmed=next;
    armSave();
    renderPass2(doc);
  };
}
