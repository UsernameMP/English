const armViewer=(()=>{
  const PDFJS_VERSION="4.10.38";
  const PDFJS_URL="https://cdn.jsdelivr.net/npm/pdfjs-dist@"+PDFJS_VERSION+"/build/pdf.min.mjs";
  const PDFJS_WORKER="https://cdn.jsdelivr.net/npm/pdfjs-dist@"+PDFJS_VERSION+"/build/pdf.worker.min.mjs";

  let pdfjs=null,pdf=null,layout=null,currentDoc=null,scale=1,lastEvidence=null,loadToken=0;

  async function ensurePdfJs(){
    if(pdfjs)return pdfjs;
    pdfjs=await import(PDFJS_URL);
    pdfjs.GlobalWorkerOptions.workerSrc=PDFJS_WORKER;
    return pdfjs;
  }

  function norm(s){
    return String(s||"")
      .toLowerCase()
      .replace(/[–—−]/g,"-")
      .replace(/\s+/g," ")
      .trim();
  }

  async function fetchJson(url){
    if(!url)return null;
    const r=await fetch(url,{cache:"no-store"});
    if(!r.ok)throw new Error("layout "+r.status);
    return r.json();
  }

  function viewer(){return document.getElementById("pdfViewer")}

  async function load(doc){
    const token=++loadToken;
    currentDoc=doc; lastEvidence=null;
    const host=viewer();
    host.innerHTML='<div class="pdf-loading">Loading PDF…</div>';
    const lib=await ensurePdfJs();
    if(token!==loadToken)return;
    layout=null;
    if(doc.layoutUrl){
      try{layout=await fetchJson(doc.layoutUrl)}catch(e){console.warn("layout unavailable",e)}
    }
    const task=lib.getDocument({url:doc.viewerUrl,withCredentials:false});
    pdf=await task.promise;
    if(token!==loadToken)return;
    await fitWidth(false);
    return {pageCount:pdf.numPages};
  }

  async function fitWidth(reapply=true){
    if(!pdf)return;
    const host=viewer();
    const first=await pdf.getPage(1);
    const base=first.getViewport({scale:1});
    const available=Math.max(320,host.clientWidth-34);
    scale=Math.max(.45,Math.min(2.6,available/base.width));
    await renderAll();
    if(reapply&&lastEvidence)await focusEvidence(lastEvidence,false);
  }

  async function setScale(next){
    if(!pdf)return;
    scale=Math.max(.4,Math.min(3.2,next));
    await renderAll();
    if(lastEvidence)await focusEvidence(lastEvidence,false);
  }

  async function renderAll(){
    const token=loadToken,host=viewer();
    host.innerHTML="";
    for(let pageNo=1;pageNo<=pdf.numPages;pageNo++){
      if(token!==loadToken)return;
      const page=await pdf.getPage(pageNo);
      const viewport=page.getViewport({scale});
      const shell=document.createElement("div");
      shell.className="pdf-page";
      shell.dataset.page=String(pageNo);
      shell.style.width=viewport.width+"px";
      shell.style.height=viewport.height+"px";

      const canvas=document.createElement("canvas");
      const dpr=window.devicePixelRatio||1;
      canvas.width=Math.floor(viewport.width*dpr);
      canvas.height=Math.floor(viewport.height*dpr);
      canvas.style.width=viewport.width+"px";
      canvas.style.height=viewport.height+"px";

      const overlay=document.createElement("div");
      overlay.className="pdf-overlay";
      const badge=document.createElement("div");
      badge.className="page-badge";
      badge.textContent=String(pageNo);

      shell.append(canvas,overlay,badge);
      host.appendChild(shell);
      const ctx=canvas.getContext("2d",{alpha:false});
      await page.render({canvasContext:ctx,viewport,transform:dpr===1?null:[dpr,0,0,dpr,0,0]}).promise;
    }
    const zoom=document.getElementById("zoomValue");
    if(zoom)zoom.textContent=Math.round(scale*100)+"%";
  }

  function pageLayout(pageNo){
    if(!layout||!Array.isArray(layout.pages))return null;
    return layout.pages.find(p=>Number(p.page_number)===Number(pageNo))||null;
  }

  function findBboxes(ev){
    if(ev&&Array.isArray(ev.bbox)&&ev.bbox.length===4)return [ev.bbox];
    const p=pageLayout(ev&&ev.page||1);
    if(!p)return [];
    const q=norm(ev&&ev.search||ev&&ev.snippet||"");
    if(!q)return [];
    const exact=[];
    const lines=[];
    const blocks=[];
    for(const block of p.blocks||[]){
      if(norm(block.text).includes(q))blocks.push(block.bbox);
      for(const line of block.lines||[]){
        if(norm(line.text).includes(q))lines.push(line.bbox);
        for(const span of line.spans||[]){
          if(norm(span.text).includes(q))exact.push(span.bbox);
        }
      }
    }
    return exact.length?exact:lines.length?lines:blocks.length?blocks:[];
  }

  function clearHighlights(){
    document.querySelectorAll(".pdf-overlay").forEach(o=>o.innerHTML="");
    document.querySelectorAll(".pdf-page.evidence-page").forEach(p=>p.classList.remove("evidence-page"));
  }

  async function focusEvidence(ev,remember=true){
    if(!pdf||!ev)return;
    if(remember)lastEvidence=ev;
    clearHighlights();
    const source=String(ev.source||"document");
    const hasPdfTarget=Array.isArray(ev.bbox)||(String(ev.search||"").trim().length>0&&Number(ev.page)>0);
    if(!hasPdfTarget&&source!=="document"&&source!=="human-boundary"&&source!=="human"){
      const hint=document.getElementById("viewerHint");
      const detail=ev.snippet||ev.label||"";
      if(hint)hint.textContent="Evidence · "+source+(detail?" · "+detail:"");
      return;
    }
    const pageNo=Math.max(1,Math.min(pdf.numPages,Number(ev.page||1)));
    const shell=document.querySelector('.pdf-page[data-page="'+pageNo+'"]');
    if(!shell)return;
    const overlay=shell.querySelector(".pdf-overlay");
    const p=pageLayout(pageNo);
    const boxes=findBboxes(ev);

    if(p&&boxes.length){
      const sx=shell.clientWidth/Number(p.width||shell.clientWidth);
      const sy=shell.clientHeight/Number(p.height||shell.clientHeight);
      for(const box of boxes){
        const mark=document.createElement("div");
        mark.className="layout-highlight";
        mark.style.left=(box[0]*sx)+"px";
        mark.style.top=(box[1]*sy)+"px";
        mark.style.width=Math.max(5,(box[2]-box[0])*sx)+"px";
        mark.style.height=Math.max(5,(box[3]-box[1])*sy)+"px";
        overlay.appendChild(mark);
      }
      shell.classList.add("evidence-page");
      const label=ev.snippet||ev.search||"evidence";
      const hint=document.getElementById("viewerHint");
      if(hint)hint.textContent='Evidence · page '+pageNo+' · "'+label+'" · layout bbox';
    }else{
      shell.classList.add("evidence-page");
      const hint=document.getElementById("viewerHint");
      if(hint)hint.textContent="Evidence · page "+pageNo+" · bbox unavailable";
    }
    const host=viewer();
    let focusY=shell.offsetTop+shell.clientHeight/2;
    if(p&&boxes.length){
      const sy=shell.clientHeight/Number(p.height||shell.clientHeight);
      const minY=Math.min(...boxes.map(b=>Number(b[1])));
      const maxY=Math.max(...boxes.map(b=>Number(b[3])));
      focusY=shell.offsetTop+((minY+maxY)/2)*sy;
    }
    const maxScroll=Math.max(0,host.scrollHeight-host.clientHeight);
    const targetTop=Math.max(0,Math.min(maxScroll,focusY-host.clientHeight/2));
    host.scrollTo({top:targetTop,behavior:"smooth"});
  }

  function getPageCount(){
    return pdf?pdf.numPages:0;
  }

  function getCurrentPage(){
    const host=viewer();
    const center=host.scrollTop+host.clientHeight/2;
    let bestPage=1,bestDistance=Infinity;
    host.querySelectorAll(".pdf-page").forEach(shell=>{
      const pageCenter=shell.offsetTop+shell.offsetHeight/2;
      const distance=Math.abs(pageCenter-center);
      if(distance<bestDistance){
        bestDistance=distance;
        bestPage=Number(shell.dataset.page||1);
      }
    });
    return bestPage;
  }

  return {
    load,
    focusEvidence,
    fitWidth:()=>fitWidth(true),
    zoomIn:()=>setScale(scale*1.15),
    zoomOut:()=>setScale(scale/1.15),
    getScale:()=>scale,
    getPageCount,
    getCurrentPage
  };
})();
