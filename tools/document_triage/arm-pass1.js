const PASS1_FIELDS=["role","subject","language","academic_year","grades","competition","stage","tour","region","problemset"];

const PASS1_OPTIONS={
  role:["TASK_SET","ANSWER_KEY","CRITERIA","LISTENING_SCRIPT","OTHER"],
  subject:["ENGLISH","RUSSIAN","MATHEMATICS","GEOGRAPHY","BIOLOGY","PHYSICS","INFORMATICS","CHEMISTRY","HISTORY","OTHER"],
  language:["RU+EN","RU","EN","UNKNOWN","OTHER"],
  competition:["VSOSh","OTHER"],
  stage:["MUNICIPAL","REGIONAL","OTHER"],
  tour:["WRITTEN","ORAL","OTHER"]
};

function confClass(v){return v>=.9?"":v>=.7?"mid":"low"}

function displayStatus(status){
  if(status==="CONFIRMED")return t("confirmed");
  if(status==="NEEDS_REVIEW")return t("needsReviewStatus");
  if(status==="IN_REVIEW")return t("inReview");
  return t("unreviewed");
}

function fieldDisplay(key,value){
  if(PASS1_OPTIONS[key])return valueLabel(key,value);
  return String(value==null?"":value);
}

function storePass1Field(doc,key,value){
  const machine=inferDocument(doc),ds=docState(doc),m=machine.values[key];
  ds.pass1.fields[key]={
    machine_value:m,
    human_value:value,
    confidence:machine.confidence[key],
    evidence:machine.evidence[key],
    proposal_source:machine.proposal_source[key],
    decision:String(value)===String(m)?"CONFIRMED":"CORRECTED"
  };
  ds.pass1.status="IN_REVIEW";
  armSave();
  renderPass1(doc);
}

function renderFieldControl(key,current){
  const opts=PASS1_OPTIONS[key];
  if(!opts){
    return '<input class="human-input" data-field="'+key+'" value="'+String(current).replaceAll('"','&quot;')+'">';
  }
  const known=opts.includes(String(current));
  const selected=known?String(current):"__CUSTOM__";
  const optionHtml=opts.map(v=>'<option value="'+v+'" '+(selected===v?"selected":"")+'>'+valueLabel(key,v)+'</option>').join("");
  const custom='<option value="__CUSTOM__" '+(selected==="__CUSTOM__"?"selected":"")+'>'+(uiLocale==="ru"?"Другое / вручную":"Other / custom")+'</option>';
  const free=selected==="__CUSTOM__"
    ?'<input class="human-input custom-field" data-custom-field="'+key+'" value="'+String(current==="__CUSTOM__"?"":current).replaceAll('"','&quot;')+'" placeholder="'+(uiLocale==="ru"?"Введите значение":"Enter value")+'">'
    :"";
  return '<div class="field-control"><select class="human-input controlled-field" data-field="'+key+'">'+optionHtml+custom+'</select>'+free+'</div>';
}

function renderPass1(doc){
  const machine=inferDocument(doc),ds=docState(doc),wrap=$("profileRows");
  wrap.innerHTML="";

  PASS1_FIELDS.forEach(key=>{
    const m=machine.values[key],c=machine.confidence[key],existing=ds.pass1.fields[key],human=existing?existing.human_value:m,row=document.createElement("div");
    row.className="field-row "+(existing&&existing.decision==="CORRECTED"?"corrected":existing&&existing.decision==="CONFIRMED"?"confirmed":"");
    row.innerHTML=
      '<div class="field-name">'+t("field_"+key)+'</div>'+
      '<div class="machine-value"><div>'+fieldDisplay(key,m)+'</div><div class="muted">'+t("proposalSource")+': '+proposalSourceLabel(machine.proposal_source[key])+'</div></div>'+
      '<div class="confidence '+confClass(c)+'">'+Math.round(c*100)+'%</div>'+
      renderFieldControl(key,human)+
      '<button class="evidence-btn" data-evidence="'+key+'">'+t("evidence")+'</button>';
    wrap.appendChild(row);
  });

  wrap.querySelectorAll(".human-input[data-field]").forEach(input=>{
    input.addEventListener("change",e=>storePass1Field(doc,e.target.dataset.field,e.target.value.trim()));
  });

  wrap.querySelectorAll(".controlled-field").forEach(select=>{
    select.addEventListener("change",e=>{
      const key=e.target.dataset.field;
      if(e.target.value==="__CUSTOM__"){
        const holder=e.target.closest(".field-control");
        if(!holder.querySelector("[data-custom-field]")){
          const free=document.createElement("input");
          free.className="human-input custom-field";
          free.dataset.customField=key;
          free.placeholder=uiLocale==="ru"?"Введите значение":"Enter value";
          holder.appendChild(free);
          free.focus();
          free.addEventListener("change",x=>storePass1Field(doc,key,x.target.value.trim()));
        }
        return;
      }
      storePass1Field(doc,key,e.target.value);
    });
  });

  wrap.querySelectorAll("[data-custom-field]").forEach(input=>{
    input.addEventListener("change",e=>storePass1Field(doc,e.target.dataset.customField,e.target.value.trim()));
  });

  wrap.querySelectorAll("[data-evidence]").forEach(b=>b.onclick=()=>focusEvidence(machine.evidence[b.dataset.evidence]));

  const confirm=$("confirmDocument"),needs=$("needsReview");
  confirm.textContent=ds.pass1.status==="CONFIRMED"?t("undoConfirm"):t("confirmDocument");
  confirm.classList.toggle("primary",ds.pass1.status==="CONFIRMED");
  needs.textContent=ds.pass1.status==="NEEDS_REVIEW"?t("clearNeedsReview"):t("needsReview");
  needs.classList.toggle("primary",ds.pass1.status==="NEEDS_REVIEW");

  renderBundle(doc);
  renderPass1Audit(doc);
}

function renderBundle(doc){
  const members=bundleMembers(doc),ds=docState(doc),box=$("bundleCard");
  let assets=members.map(d=>
    '<div class="asset"><div class="asset-main"><div class="filename">'+d.filename+'</div><div class="muted">'+fieldDisplay("role",inferDocument(d).values.role)+' · '+stable("asset",d.id)+'</div></div><span class="confidence">'+(members.length>1?"96":"78")+'%</span></div>'
  ).join("");

  const audioDoc=members.find(d=>d.audioUrl)||(doc.audioUrl?doc:null);
  if(audioDoc){
    assets+='<div class="asset"><div class="asset-main"><div class="filename">'+t("linkedAudio")+'</div><div class="muted">AUDIO · '+stable("media",audioDoc.audioSha||audioDoc.audioUrl)+'</div></div><span class="confidence">99%</span></div>';
  }

  const decision=ds.pass1.bundleDecision==="CONFIRMED"?t("confirmed"):t("unreviewed");
  box.innerHTML=
    '<div class="muted">ProblemSet ID: <span class="mono">'+stable("problemset",bundleKey(doc))+'</span></div>'+
    '<div class="asset-list">'+assets+'</div>'+
    '<div class="muted" style="margin-top:8px">'+t("decision")+': <b>'+decision+'</b></div>';

  $("confirmBundle").textContent=ds.pass1.bundleDecision==="CONFIRMED"?t("undoBundle"):t("confirmBundle");
  $("confirmBundle").classList.toggle("primary",ds.pass1.bundleDecision==="CONFIRMED");
}

function renderPass1Audit(doc){
  const ds=docState(doc);
  $("pass1Audit").textContent=JSON.stringify({
    document_id:stable("asset",doc.id),
    status:ds.pass1.status,
    fields:ds.pass1.fields,
    bundle_decision:ds.pass1.bundleDecision
  },null,2);
}

function confirmCurrentDocument(){
  const doc=docs[current],m=inferDocument(doc),ds=docState(doc);

  if(ds.pass1.status==="CONFIRMED"){
    ds.pass1.status="IN_REVIEW";
    ds.pass1.unconfirmed_at=new Date().toISOString();
    armSave();
    renderPass1(doc);
    return;
  }

  PASS1_FIELDS.forEach(k=>{
    if(!ds.pass1.fields[k]){
      ds.pass1.fields[k]={
        machine_value:m.values[k],
        human_value:m.values[k],
        confidence:m.confidence[k],
        evidence:m.evidence[k],
        proposal_source:m.proposal_source[k],
        decision:"CONFIRMED"
      };
    }
  });
  ds.pass1.status="CONFIRMED";
  ds.pass1.reviewed_at=new Date().toISOString();
  armSave();
  renderPass1(doc);
}

function bindPass1(){
  $("confirmDocument").onclick=confirmCurrentDocument;

  $("needsReview").onclick=()=>{
    const ds=docState(docs[current]);
    ds.pass1.status=ds.pass1.status==="NEEDS_REVIEW"?"IN_REVIEW":"NEEDS_REVIEW";
    armSave();
    renderPass1(docs[current]);
  };

  $("confirmBundle").onclick=()=>{
    const ds=docState(docs[current]);
    ds.pass1.bundleDecision=ds.pass1.bundleDecision==="CONFIRMED"?"UNREVIEWED":"CONFIRMED";
    armSave();
    renderBundle(docs[current]);
    renderPass1Audit(docs[current]);
  };
}
