const PASS1_FIELDS=[["role","Document type"],["subject","Subject"],["language","Language"],["academic_year","Year"],["grades","Grades"],["competition","Competition"],["stage","Stage"],["tour","Tour"],["region","Region"],["problemset","ProblemSet"]];
function confClass(v){return v>=.9?"":v>=.7?"mid":"low"}
function shortValue(v){return String(v==null?"":v).replaceAll("_"," ")}
function renderPass1(doc){
  const machine=inferDocument(doc),ds=docState(doc),wrap=$("profileRows");wrap.innerHTML="";
  PASS1_FIELDS.forEach(([key,label])=>{
    const m=machine.values[key],c=machine.confidence[key],existing=ds.pass1.fields[key],human=existing?existing.human_value:m,row=document.createElement("div");
    row.className="field-row "+(existing&&existing.decision==="CORRECTED"?"corrected":existing&&existing.decision==="CONFIRMED"?"confirmed":"");
    row.innerHTML='<div class="field-name">'+label+'</div><div class="machine-value">'+shortValue(m)+'</div><div class="confidence '+confClass(c)+'">'+Math.round(c*100)+'%</div><input class="human-input" data-field="'+key+'" value="'+String(human).replaceAll('"','&quot;')+'"><button class="evidence-btn" data-evidence="'+key+'">Evidence</button>';
    wrap.appendChild(row);
  });
  wrap.querySelectorAll(".human-input").forEach(input=>input.addEventListener("change",e=>{
    const key=e.target.dataset.field,m=machine.values[key],val=e.target.value.trim();
    ds.pass1.fields[key]={machine_value:m,human_value:val,confidence:machine.confidence[key],evidence:machine.evidence[key],decision:val===String(m)?"CONFIRMED":"CORRECTED"};
    ds.pass1.status="IN_REVIEW";armSave();renderPass1(doc);
  }));
  wrap.querySelectorAll("[data-evidence]").forEach(b=>b.onclick=()=>focusEvidence(machine.evidence[b.dataset.evidence]));
  renderBundle(doc);renderPass1Audit(doc);
}
function renderBundle(doc){
  const members=bundleMembers(doc),ds=docState(doc),box=$("bundleCard");
  let assets=members.map(d=>'<div class="asset"><div class="asset-main"><div class="filename">'+d.filename+'</div><div class="muted">'+inferDocument(d).values.role+' - '+stable("asset",d.id)+'</div></div><span class="confidence">'+(members.length>1?"96":"78")+'%</span></div>').join("");
  const audioDoc=members.find(d=>d.audioUrl)|| (doc.audioUrl?doc:null);
  if(audioDoc){
    assets+='<div class="asset"><div class="asset-main"><div class="filename">Listening audio</div><div class="muted">AUDIO - '+stable("media",audioDoc.audioSha||audioDoc.audioUrl)+'</div></div><span class="confidence">99%</span></div>';
  }
  box.innerHTML='<div class="muted">ProblemSet ID: <span class="mono">'+stable("problemset",bundleKey(doc))+'</span></div><div class="asset-list">'+assets+'</div><div class="muted" style="margin-top:8px">Decision: <b>'+ds.pass1.bundleDecision+'</b></div>';
}
function renderPass1Audit(doc){
  const ds=docState(doc);$("pass1Audit").textContent=JSON.stringify({document_id:stable("asset",doc.id),status:ds.pass1.status,fields:ds.pass1.fields,bundle_decision:ds.pass1.bundleDecision},null,2);
}
function confirmCurrentDocument(){
  const doc=docs[current],m=inferDocument(doc),ds=docState(doc);
  PASS1_FIELDS.forEach(([k])=>ds.pass1.fields[k]={machine_value:m.values[k],human_value:m.values[k],confidence:m.confidence[k],evidence:m.evidence[k],decision:"CONFIRMED"});
  ds.pass1.status="CONFIRMED";ds.pass1.reviewed_at=new Date().toISOString();armSave();renderPass1(doc);
}
function bindPass1(){
  $("confirmDocument").onclick=confirmCurrentDocument;
  $("needsReview").onclick=()=>{docState(docs[current]).pass1.status="NEEDS_REVIEW";armSave();renderPass1(docs[current])};
  $("confirmBundle").onclick=()=>{docState(docs[current]).pass1.bundleDecision="CONFIRMED";armSave();renderBundle(docs[current]);renderPass1Audit(docs[current])};
}
