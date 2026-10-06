function initialStructure(doc){
  const role=inferDocument(doc).values.role,base=stable("asset",doc.id);
  const mk=(label,s,e,conf,tasks,evidence)=>({id:stable("section",base+label+s+e),type:"SECTION",label,start:s,end:e,confidence:conf,confirmed:false,tasks:tasks||[],evidence:evidence||{page:s,search:label,snippet:label}});

  if(doc.id==="6c7bf55e9532cd1b6960821ac4c91fa8ebc1a48cc5aafa5405ec73b7966aa932")return[
    mk("Listening",2,2,.99,[
      {id:stable("task",base+"listening-task1"),label:"Task 1",subtasks:["Part 1 · 1-5 · gap fill","Part 2 · 6-10 · open response","Part 3 · 11-13 · single choice"],evidence:{page:2,search:"Task 1. You will hear a speech",snippet:"Task 1 · three parts"}},
    ],{page:2,search:"Listening",snippet:"Listening (15 min - 20 points)"}),
    mk("Reading",3,6,.99,[
      {id:stable("task",base+"reading-task1"),label:"Task 1",subtasks:["1-9 · open / vocabulary"],evidence:{page:3,search:"water shortages",snippet:"Task 1 · water shortages · questions 1-9"}},
      {id:stable("task",base+"reading-task2"),label:"Task 2",subtasks:["10-14 · A/B/C/D"],evidence:{page:4,search:"vacuum travel",snippet:"Task 2 · vacuum travel · questions 10-14"}},
    ],{page:3,search:"Reading",snippet:"Reading (25 min - 20 points)"}),
    mk("Use of English",6,8,.99,[
      {id:stable("task",base+"use-task1"),label:"Task 1",subtasks:["1-8 · open cloze"],evidence:{page:6,search:"For questions 1-8",snippet:"Task 1 · questions 1-8 · one word per gap"}},
      {id:stable("task",base+"use-task2"),label:"Task 2",subtasks:["9-14 · key word transformation"],evidence:{page:6,search:"For questions 9-14",snippet:"Task 2 · questions 9-14 · transformation"}},
      {id:stable("task",base+"use-task3"),label:"Task 3",subtasks:["15-19 · idioms"],evidence:{page:7,search:"For questions 15-19",snippet:"Task 3 · questions 15-19 · idioms"}},
      {id:stable("task",base+"use-task4"),label:"Task 4",subtasks:["20-28 · word formation"],evidence:{page:7,search:"For questions 20-28",snippet:"Task 4 · questions 20-28 · word formation"}},
      {id:stable("task",base+"use-task5"),label:"Task 5",subtasks:["29-34 · A/B/C/D"],evidence:{page:7,search:"For questions 29-34",snippet:"Task 5 · questions 29-34 · single choice"}},
    ],{page:6,search:"Use of English",snippet:"Use of English (40 min - 40 points)"}),
    mk("Writing",9,9,.99,[
      {id:stable("task",base+"writing"),label:"Article",subtasks:["180-200 words"],evidence:{page:9,search:"ARTICLES WANTED",snippet:"Writing · article · 180-200 words"}},
    ],{page:9,search:"Writing",snippet:"Writing (40 min - 20 points)"})
  ];

  if(role==="TASK_SET")return[
    mk("Listening",2,2,.80,[{id:stable("task",base+"1"),label:"Task 1",subtasks:[],evidence:{page:2,search:"Task 1",snippet:"Task 1"}}],{page:2,search:"Listening",snippet:"Listening"}),
    mk("Reading",3,5,.76,[{id:stable("task",base+"3"),label:"Task 1",subtasks:[],evidence:{page:3,search:"Task 1",snippet:"Reading task"}}],{page:3,search:"Reading",snippet:"Reading"}),
    mk("Use of English",6,8,.72,[{id:stable("task",base+"4"),label:"Task 1",subtasks:[],evidence:{page:6,search:"Task 1",snippet:"Use of English task"}}],{page:6,search:"Use of English",snippet:"Use of English"}),
    mk("Writing",9,9,.70,[{id:stable("task",base+"5"),label:"Writing task",subtasks:[],evidence:{page:9,search:"Writing",snippet:"Writing"}}],{page:9,search:"Writing",snippet:"Writing"})
  ];
  if(role==="ANSWER_KEY")return[
    mk("Listening answers",1,1,.80,[{id:stable("answer",base+"a1"),label:"Answers",subtasks:[],evidence:{page:1,search:"Listening",snippet:"Listening answers"}}]),
    mk("Reading answers",2,2,.78,[{id:stable("answer",base+"a2"),label:"Answers",subtasks:[],evidence:{page:2,search:"Reading",snippet:"Reading answers"}}]),
    mk("Use of English answers",3,3,.75,[{id:stable("answer",base+"a3"),label:"Answers",subtasks:[],evidence:{page:3,search:"Use of English",snippet:"Use of English answers"}}]),
    mk("Criteria / rationale",4,5,.64,[{id:stable("criterion",base+"c1"),label:"Rubric / rationale",subtasks:[],evidence:{page:4,search:"criteria",snippet:"Criteria / rationale"}}])
  ];
  if(role==="LISTENING_SCRIPT")return[
    mk("Part 1",1,1,.80,[{id:stable("media",base+"m1"),label:"Transcript Part 1",subtasks:[],evidence:{page:1,search:"Part 1",snippet:"Transcript Part 1"}}]),
    mk("Part 2",2,2,.76,[{id:stable("media",base+"m2"),label:"Transcript Part 2",subtasks:[],evidence:{page:2,search:"Part 2",snippet:"Transcript Part 2"}}]),
    mk("Part 3",3,3,.72,[{id:stable("media",base+"m3"),label:"Transcript Part 3",subtasks:[],evidence:{page:3,search:"Part 3",snippet:"Transcript Part 3"}}])
  ];
  return[mk("Document",1,1,.55,[],{page:1,search:"",snippet:"Document"})];
}
function recalcChildren(node){
  const span={page_start:node.start,page_end:node.end};
  (node.tasks||[]).forEach((task,index)=>{
    task.span={...span};
    (task.subtasks||[]).forEach((subtask,subIndex)=>{
      if(typeof subtask==="string")return;
      subtask.span={...span};
      subtask.order=subIndex;
    });
    task.order=index;
  });
}
function ensureStructure(doc){
  const ds=docState(doc);
  if(!ds.pass2.nodes)ds.pass2.nodes=initialStructure(doc);
  ds.pass2.nodes.forEach(recalcChildren);
  return ds.pass2.nodes
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
function selectReviewItem(doc,node,task=null,options={}){
  selectedNode=node.id;
  selectedTask=task?task.id:null;
  const evidence=(task&&task.evidence)||node.evidence||{page:node.start,search:(task&&task.label)||node.label,snippet:(task&&task.label)||node.label};
  focusEvidence(evidence);
  renderPass2(doc);
  if(options.playAudio&&isListeningSection(node)&&doc.audioUrl){
    const startSec=task&&task.audio_start_sec!=null?task.audio_start_sec:0;
    audioPlayFrom(startSec);
  }
}
function navigateReview(doc,delta){
  const items=reviewSequence(doc);
  const currentId=selectedTask||selectedNode;
  let i=items.findIndex(item=>item.id===currentId);
  if(i<0)i=0;
  i=Math.max(0,Math.min(items.length-1,i+delta));
  const item=items[i];
  if(item)selectReviewItem(doc,item.node,item.task,{playAudio:false});
}
function renderPass2(doc){
  const nodes=ensureStructure(doc),tree=$("structureTree");
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
      selectReviewItem(doc,n,null,{playAudio:isListeningSection(n)});
    };
    tree.appendChild(el);

    el.querySelectorAll(".task-child").forEach((child,idx)=>{
      const task=n.tasks[idx];
      child.onclick=event=>{
        event.stopPropagation();
        selectReviewItem(doc,n,task,{playAudio:isListeningSection(n)});
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
  if(!isListeningSection(node)||!doc.audioUrl)return "";
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
  if(!node){box.innerHTML="<span class='muted'>Select a node</span>";return}

  const selected=task||node;
  const kind=task?"Task":"Section";
  const subtasks=task&&task.subtasks&&task.subtasks.length
    ?'<div class="context-subtasks">'+task.subtasks.map(s=>'<div class="context-chip">'+s+'</div>').join("")+'</div>'
    :"";
  const taskEditor=task
    ?'<label class="muted">Task label</label><input id="taskLabel" class="human-input" value="'+String(task.label||"").replaceAll('"','&quot;')+'"><div class="boundary-actions"><button data-task-op="accept">Accept task</button></div>'
    :"";
  const sectionEditor=!task
    ?'<label class="muted">Section label</label><input id="nodeLabel" class="human-input" value="'+String(node.label||"").replaceAll('"','&quot;')+'">'
    :'<div class="muted">Parent section: <b>'+node.label+'</b> · pages '+node.start+'-'+node.end+'</div>';

  box.innerHTML=
    '<div class="context-title"><div><div class="context-kind">'+kind+'</div><h3>'+selected.label+'</h3></div><span class="confidence '+confClass(selected.confidence==null?node.confidence:selected.confidence)+'">'+Math.round((selected.confidence==null?node.confidence:selected.confidence)*100)+'%</span></div>'+
    '<div class="muted mono">'+selected.id+'</div>'+
    '<div class="context-nav"><button data-nav="prev">← Previous</button><button data-nav="next">Next →</button></div>'+
    subtasks+
    renderListeningTransport(doc,node,task)+
    taskEditor+
    sectionEditor+
    '<div class="subhead" style="margin-top:14px">Parent section boundary</div>'+
    '<div class="boundary-actions"><button data-op="left">boundary −</button><button data-op="right">boundary +</button><button data-op="split">Split</button><button data-op="merge">Merge next</button><button data-op="accept">Accept section</button></div>';

  const nodeLabel=$("nodeLabel");
  if(nodeLabel)nodeLabel.onchange=e=>{
    node.label=e.target.value.trim()||node.label;
    node.corrected=true;
    armSave();
    renderPass2(doc);
  };
  const taskLabel=$("taskLabel");
  if(taskLabel)taskLabel.onchange=e=>{
    task.label=e.target.value.trim()||task.label;
    task.corrected=true;
    armSave();
    renderPass2(doc);
  };

  box.querySelectorAll("[data-op]").forEach(b=>b.onclick=()=>boundaryOp(doc,node,b.dataset.op));
  box.querySelectorAll("[data-task-op]").forEach(b=>b.onclick=()=>{
    if(b.dataset.taskOp==="accept"&&task){
      task.confirmed=true;
      armSave();
      renderPass2(doc);
    }
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
  if(op==="accept"){node.confirmed=true;node.confidence=1}
  if(op==="left"&&i>0&&node.start>1){node.start--;nodes[i-1].end=Math.max(nodes[i-1].start,node.start-1);node.corrected=true}
  if(op==="right"&&i<nodes.length-1){node.end++;nodes[i+1].start=Math.max(node.end+1,nodes[i+1].start);node.corrected=true}
  if(op==="split"&&node.end>node.start){
    const mid=Math.floor((node.start+node.end)/2),copy=structuredClone(node),cut=Math.ceil((node.tasks||[]).length/2);
    node.end=mid;
    copy.start=mid+1;
    copy.id=stable("section",doc.id+copy.label+copy.start+copy.end+Date.now());
    copy.label=node.label+" B";
    node.label=node.label+" A";
    copy.confidence=Math.min(copy.confidence,.72);
    copy.tasks=(node.tasks||[]).slice(cut);
    node.tasks=(node.tasks||[]).slice(0,cut);
    recalcChildren(node);recalcChildren(copy);nodes.splice(i+1,0,copy)
  }
  if(op==="merge"&&i<nodes.length-1){
    const next=nodes[i+1];
    node.end=Math.max(node.end,next.end);
    node.tasks=[...(node.tasks||[]),...(next.tasks||[])];
    node.label=node.label+" + "+next.label;
    node.corrected=true;
    recalcChildren(node);
    nodes.splice(i+1,1)
  }
  nodes.forEach(recalcChildren);
  armSave();
  selectedNode=node.id;
  if(selectedTask&&!(node.tasks||[]).some(t=>t.id===selectedTask))selectedTask=null;
  renderPass2(doc);
}
function bindPass2(){
  $("conflictsOnly").onclick=()=>{
    conflictsOnly=!conflictsOnly;
    $("conflictsOnly").textContent=conflictsOnly?"Show all":"Conflicts only";
    renderPass2(docs[current])
  };
  $("confirmStructure").onclick=()=>{
    const ds=docState(docs[current]);
    ensureStructure(docs[current]).forEach(n=>{
      n.confirmed=true;
      (n.tasks||[]).forEach(t=>t.confirmed=true);
    });
    ds.pass2.confirmed=true;
    armSave();
    renderPass2(docs[current])
  };
}
