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
function renderPass2(doc){
  const nodes=ensureStructure(doc),tree=$("structureTree");tree.innerHTML="";
  const shown=conflictsOnly?nodes.filter(n=>n.confidence<.8):nodes;
  shown.forEach(n=>{
    const el=document.createElement("div");el.className="tree-node "+(selectedNode===n.id?"selected ":"")+(n.confidence<.8?"conflict":"");
    const children=n.tasks.map(t=>'<div class="task-child">-> '+t.label+(t.subtasks.length?" - "+t.subtasks.join(", "):"")+'</div>').join("");
    el.innerHTML='<div class="tree-title"><span>'+n.label+'</span><span>p.'+n.start+'-'+n.end+' - '+Math.round(n.confidence*100)+'%</span></div>'+children;
    el.onclick=()=>{selectedNode=n.id;focusEvidence(n.evidence||{page:n.start,search:n.label,snippet:n.label});renderPass2(doc);renderBoundaryEditor(doc,n)};
    tree.appendChild(el);
    el.querySelectorAll(".task-child").forEach((child,idx)=>{
      const task=n.tasks[idx];
      child.style.cursor="pointer";
      child.onclick=(event)=>{event.stopPropagation();focusEvidence(task.evidence||n.evidence||{page:n.start,search:task.label,snippet:task.label})};
    });
  });
  if(!selectedNode&&nodes[0]){selectedNode=nodes[0].id;renderBoundaryEditor(doc,nodes[0])}
}
function renderBoundaryEditor(doc,node){
  const box=$("boundaryEditor");if(!node){box.innerHTML="<span class='muted'>Select a node</span>";return}
  box.innerHTML='<h3>'+node.label+'</h3><div class="muted mono">'+node.id+'</div><p>Pages <b>'+node.start+'-'+node.end+'</b> - confidence '+Math.round(node.confidence*100)+'%</p><label class="muted">Label</label><input id="nodeLabel" class="human-input" value="'+node.label.replaceAll('"','&quot;')+'"><div class="boundary-actions"><button data-op="left">boundary -</button><button data-op="right">boundary +</button><button data-op="split">Split</button><button data-op="merge">Merge next</button><button data-op="accept">Accept node</button></div>';
  $("nodeLabel").onchange=e=>{node.label=e.target.value.trim()||node.label;node.corrected=true;armSave();renderPass2(doc)};
  box.querySelectorAll("[data-op]").forEach(b=>b.onclick=()=>boundaryOp(doc,node,b.dataset.op));
}
function boundaryOp(doc,node,op){
  const nodes=ensureStructure(doc),i=nodes.findIndex(n=>n.id===node.id);
  if(op==="accept"){node.confirmed=true;node.confidence=1}
  if(op==="left"&&i>0&&node.start>1){node.start--;nodes[i-1].end=Math.max(nodes[i-1].start,node.start-1);node.corrected=true}
  if(op==="right"&&i<nodes.length-1){node.end++;nodes[i+1].start=Math.max(node.end+1,nodes[i+1].start);node.corrected=true}
  if(op==="split"&&node.end>node.start){const mid=Math.floor((node.start+node.end)/2),copy=structuredClone(node),cut=Math.ceil((node.tasks||[]).length/2);node.end=mid;copy.start=mid+1;copy.id=stable("section",doc.id+copy.label+copy.start+copy.end+Date.now());copy.label=node.label+" B";node.label=node.label+" A";copy.confidence=Math.min(copy.confidence,.72);copy.tasks=(node.tasks||[]).slice(cut);node.tasks=(node.tasks||[]).slice(0,cut);recalcChildren(node);recalcChildren(copy);nodes.splice(i+1,0,copy)}
  if(op==="merge"&&i<nodes.length-1){const next=nodes[i+1];node.end=Math.max(node.end,next.end);node.tasks=[...(node.tasks||[]),...(next.tasks||[])];node.label=node.label+" + "+next.label;node.corrected=true;recalcChildren(node);nodes.splice(i+1,1)}
  nodes.forEach(recalcChildren);armSave();selectedNode=node.id;renderPass2(doc);renderBoundaryEditor(doc,node);
}
function bindPass2(){
  $("conflictsOnly").onclick=()=>{conflictsOnly=!conflictsOnly;$("conflictsOnly").textContent=conflictsOnly?"Show all":"Conflicts only";renderPass2(docs[current])};
  $("confirmStructure").onclick=()=>{const ds=docState(docs[current]);ensureStructure(docs[current]).forEach(n=>n.confirmed=true);ds.pass2.confirmed=true;armSave();renderPass2(docs[current])};
}
