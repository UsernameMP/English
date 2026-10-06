function initialStructure(doc){
  const role=inferDocument(doc).values.role,base=stable("asset",doc.id);
  const mk=(label,s,e,conf,tasks)=>({id:stable("section",base+label+s+e),type:"SECTION",label,start:s,end:e,confidence:conf,confirmed:false,tasks:tasks||[]});
  if(role==="TASK_SET")return[
    mk("Listening",1,2,.94,[{id:stable("task",base+"1"),label:"Task 1",subtasks:["1-10"]},{id:stable("task",base+"2"),label:"Task 2",subtasks:["A/B/C"]}]),
    mk("Reading",3,5,.91,[{id:stable("task",base+"3"),label:"Task 3",subtasks:["matching"]}]),
    mk("Use of English",6,8,.76,[{id:stable("task",base+"4"),label:"Task 4",subtasks:["cloze","transformation"]}]),
    mk("Writing",9,10,.68,[{id:stable("task",base+"5"),label:"Task 5",subtasks:[]}])
  ];
  if(role==="ANSWER_KEY")return[
    mk("Listening answers",1,1,.96,[{id:stable("answer",base+"a1"),label:"Answers 1-10",subtasks:[]}]),
    mk("Reading answers",2,2,.93,[{id:stable("answer",base+"a2"),label:"Answers 11-25",subtasks:[]}]),
    mk("Use of English answers",3,3,.88,[{id:stable("answer",base+"a3"),label:"Answers 26-40",subtasks:[]}]),
    mk("Criteria / rationale",4,5,.64,[{id:stable("criterion",base+"c1"),label:"Rubric / rationale",subtasks:[]}])
  ];
  if(role==="LISTENING_SCRIPT")return[
    mk("Part 1",1,1,.92,[{id:stable("media",base+"m1"),label:"Transcript Part 1",subtasks:[]}]),
    mk("Part 2",2,2,.86,[{id:stable("media",base+"m2"),label:"Transcript Part 2",subtasks:[]}]),
    mk("Part 3",3,3,.74,[{id:stable("media",base+"m3"),label:"Transcript Part 3",subtasks:[]}])
  ];
  return[mk("Document",1,1,.55,[])];
}
function ensureStructure(doc){const ds=docState(doc);if(!ds.pass2.nodes)ds.pass2.nodes=initialStructure(doc);return ds.pass2.nodes}
function renderPass2(doc){
  const nodes=ensureStructure(doc),tree=$("structureTree");tree.innerHTML="";
  const shown=conflictsOnly?nodes.filter(n=>n.confidence<.8):nodes;
  shown.forEach(n=>{
    const el=document.createElement("div");el.className="tree-node "+(selectedNode===n.id?"selected ":"")+(n.confidence<.8?"conflict":"");
    const children=n.tasks.map(t=>'<div class="task-child">-> '+t.label+(t.subtasks.length?" - "+t.subtasks.join(", "):"")+'</div>').join("");
    el.innerHTML='<div class="tree-title"><span>'+n.label+'</span><span>p.'+n.start+'-'+n.end+' - '+Math.round(n.confidence*100)+'%</span></div>'+children;
    el.onclick=()=>{selectedNode=n.id;focusEvidence({page:n.start,bbox:[.04,.05,.92,.92],label:n.label});renderPass2(doc);renderBoundaryEditor(doc,n)};tree.appendChild(el);
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
  if(op==="split"&&node.end>node.start){const mid=Math.floor((node.start+node.end)/2),copy=structuredClone(node);node.end=mid;copy.start=mid+1;copy.id=stable("section",doc.id+copy.label+copy.start+copy.end+Date.now());copy.label=node.label+" B";node.label=node.label+" A";copy.confidence=Math.min(copy.confidence,.72);nodes.splice(i+1,0,copy)}
  if(op==="merge"&&i<nodes.length-1){const next=nodes[i+1];node.end=Math.max(node.end,next.end);node.tasks=[...node.tasks,...next.tasks];node.label=node.label+" + "+next.label;node.corrected=true;nodes.splice(i+1,1)}
  armSave();selectedNode=node.id;renderPass2(doc);renderBoundaryEditor(doc,node);
}
function bindPass2(){
  $("conflictsOnly").onclick=()=>{conflictsOnly=!conflictsOnly;$("conflictsOnly").textContent=conflictsOnly?"Show all":"Conflicts only";renderPass2(docs[current])};
  $("confirmStructure").onclick=()=>{const ds=docState(docs[current]);ensureStructure(docs[current]).forEach(n=>n.confirmed=true);ds.pass2.confirmed=true;armSave();renderPass2(docs[current])};
}
