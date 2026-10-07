(() => {
'use strict';
const canvas=document.getElementById('game'),ctx=canvas.getContext('2d');
const COLS=8,ROWS=8,palette=['#ff4f87','#45d7e8','#7c6cff','#ffd447','#45d483','#3987ff'];
let board=[],selected=null,busy=false,score=0,bestChain=1,status='MAKE A MATCH',statusUntil=0,particles=[],pointerStart=null;
let geom={x:0,y:0,cell:0,size:0,w:0,h:0};
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),key=(r,c)=>r+':'+c,parseKey=k=>k.split(':').map(Number);
const inside=(r,c)=>r>=0&&r<ROWS&&c>=0&&c<COLS,adjacent=(a,b)=>Math.abs(a.r-b.r)+Math.abs(a.c-b.c)===1;
const randomGem=()=>({color:Math.floor(Math.random()*palette.length),special:null});

function resetBoard(){
  board=Array.from({length:ROWS},()=>Array(COLS));
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
    let g;
    do{g=randomGem();}while((c>=2&&board[r][c-1].color===g.color&&board[r][c-2].color===g.color)||
      (r>=2&&board[r-1][c].color===g.color&&board[r-2][c].color===g.color));
    board[r][c]=g;
  }
  score=0;bestChain=1;selected=null;busy=false;flash('MAKE A MATCH',1200);ensureMove();
}
function swap(a,b){const t=board[a.r][a.c];board[a.r][a.c]=board[b.r][b.c];board[b.r][b.c]=t}
function findRuns(){
  const runs=[];
  for(let r=0;r<ROWS;r++){let s=0;while(s<COLS){let e=s+1,col=board[r][s]?.color;
    while(e<COLS&&board[r][e]&&board[r][e].color===col)e++;
    if(col!=null&&e-s>=3)runs.push({horizontal:true,r,c:s,length:e-s});s=e;}}
  for(let c=0;c<COLS;c++){let s=0;while(s<ROWS){let e=s+1,col=board[s][c]?.color;
    while(e<ROWS&&board[e][c]&&board[e][c].color===col)e++;
    if(col!=null&&e-s>=3)runs.push({horizontal:false,r:s,c,length:e-s});s=e;}}
  return runs;
}
function runCells(run){const a=[];for(let i=0;i<run.length;i++)a.push({r:run.r+(run.horizontal?0:i),c:run.c+(run.horizontal?i:0)});return a}
function preferredCell(run,pref){const cells=runCells(run);if(pref)for(const p of pref)if(p&&cells.some(x=>x.r===p.r&&x.c===p.c))return p;return cells[Math.floor(cells.length/2)]}
function matchInfo(pref){
  const runs=findRuns(),matched=new Set(),h=new Set(),v=new Set();
  runs.forEach(run=>runCells(run).forEach(p=>{const k=key(p.r,p.c);matched.add(k);(run.horizontal?h:v).add(k)}));
  const creations=new Map();
  for(const k of h)if(v.has(k))creations.set(k,'bomb');
  for(const run of runs)if(run.length>=4){
    const p=preferredCell(run,pref),k=key(p.r,p.c);
    if(creations.get(k)==='bomb')continue;
    creations.set(k,run.length>=5?'color':(run.horizontal?'row':'col'));
  }
  return{matched,creations};
}
function addClear(set,r,c,targetColor,queue){
  if(!inside(r,c)||!board[r][c])return;const k=key(r,c);if(set.has(k))return;
  set.add(k);if(board[r][c].special)queue.push({r,c,targetColor});
}
function expandSpecials(set,queue){
  const activated=new Set();
  while(queue.length){
    const item=queue.shift(),k=key(item.r,item.c);if(activated.has(k)||!inside(item.r,item.c)||!board[item.r][item.c])continue;
    activated.add(k);const g=board[item.r][item.c],s=g.special;
    if(s==='row')for(let c=0;c<COLS;c++)addClear(set,item.r,c,null,queue);
    else if(s==='col')for(let r=0;r<ROWS;r++)addClear(set,r,item.c,null,queue);
    else if(s==='bomb')for(let rr=item.r-1;rr<=item.r+1;rr++)for(let cc=item.c-1;cc<=item.c+1;cc++)addClear(set,rr,cc,null,queue);
    else if(s==='color'){
      const color=item.targetColor==null?g.color:item.targetColor;
      for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++)if(board[r][c]&&(color==null||board[r][c].color===color))addClear(set,r,c,null,queue);
    }
  }
}
function burst(r,c,color,big){
  const x=geom.x+(c+.5)*geom.cell,y=geom.y+(r+.5)*geom.cell,n=big?22:10;
  for(let i=0;i<n;i++){const a=Math.random()*Math.PI*2,sp=(big?180:110)*(.35+Math.random());
    particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,life:.45+Math.random()*.35,max:.8,color:palette[color%palette.length]});}
}
async function clearAndFall(set,creations,cascade){
  const protectedKeys=new Set(creations.keys()),queue=[];
  for(const k of Array.from(set)){if(protectedKeys.has(k))continue;const [r,c]=parseKey(k);if(board[r][c]?.special)queue.push({r,c,targetColor:null})}
  expandSpecials(set,queue);
  for(const [k,special]of creations){const[r,c]=parseKey(k);if(board[r][c])board[r][c].special=special;set.delete(k)}
  if(!set.size)return;
  score+=set.size*60*Math.max(1,cascade);bestChain=Math.max(bestChain,cascade);if(cascade>1)flash('CHAIN ×'+cascade,850);
  for(const k of set){const[r,c]=parseKey(k);if(board[r][c]){burst(r,c,board[r][c].color,['bomb','color'].includes(board[r][c].special));board[r][c]=null}}
  await sleep(120);
  for(let c=0;c<COLS;c++){let w=ROWS-1;for(let r=ROWS-1;r>=0;r--)if(board[r][c])board[w--][c]=board[r][c];while(w>=0)board[w--][c]=randomGem()}
  await sleep(120);
}
async function resolve(pref){
  let cascade=1;
  while(true){
    const info=matchInfo(pref);if(!info.matched.size)break;
    for(const s of info.creations.values())flash(s==='color'?'COLOR GEM!':s==='bomb'?'BOMB!':'LINE BLAST!',850);
    await clearAndFall(new Set(info.matched),info.creations,cascade);pref=null;cascade++;
  }
  ensureMove();
}
async function activateSwapSpecial(a,b){
  const ga=board[a.r][a.c],gb=board[b.r][b.c],set=new Set(),queue=[];
  if(ga.special==='color'&&gb.special==='color'){
    for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++)addClear(set,r,c,null,queue);
  }else{
    if(ga.special){set.add(key(a.r,a.c));queue.push({r:a.r,c:a.c,targetColor:ga.special==='color'?gb.color:null})}
    if(gb.special){set.add(key(b.r,b.c));queue.push({r:b.r,c:b.c,targetColor:gb.special==='color'?ga.color:null})}
  }
  expandSpecials(set,queue);flash('POWER COMBO!',900);await clearAndFall(set,new Map(),1);await resolve(null);
}
async function trySwap(a,b){
  if(busy||!inside(b.r,b.c)||!adjacent(a,b))return;busy=true;selected=null;swap(a,b);await sleep(90);
  const ga=board[a.r][a.c],gb=board[b.r][b.c];
  if(ga?.special==='color'||gb?.special==='color'){await activateSwapSpecial(a,b);busy=false;return}
  const info=matchInfo([b,a]);
  if(!info.matched.size){
    if(ga?.special||gb?.special)await activateSwapSpecial(a,b);
    else{flash('TRY ANOTHER',650);await sleep(80);swap(a,b)}
  }else await resolve([b,a]);
  busy=false;
}
function hasMove(){
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++)for(const d of [[0,1],[1,0]]){
    const b={r:r+d[0],c:c+d[1]};if(!inside(b.r,b.c))continue;const a={r,c};
    if(board[r][c].special||board[b.r][b.c].special)return true;
    swap(a,b);const ok=findRuns().length>0;swap(a,b);if(ok)return true;
  }return false;
}
function ensureMove(){
  if(hasMove())return;flash('SHUFFLE!',850);
  const gems=[];for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++)gems.push(board[r][c]);
  for(let i=gems.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[gems[i],gems[j]]=[gems[j],gems[i]]}
  let n=0;for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++)board[r][c]=gems[n++];
  if(findRuns().length||!hasMove())resetBoard();
}
function flash(text,ms=900){status=text;statusUntil=performance.now()+ms}
function resize(){
  const dpr=Math.min(2,window.devicePixelRatio||1),w=Math.max(320,innerWidth),h=Math.max(420,innerHeight);
  canvas.width=Math.floor(w*dpr);canvas.height=Math.floor(h*dpr);canvas.style.width=w+'px';canvas.style.height=h+'px';ctx.setTransform(dpr,0,0,dpr,0,0);
  const pad=Math.max(10,Math.min(22,w*.04)),top=Math.max(112,h*.15),size=Math.min(w-pad*2,h-top-28);
  geom={x:(w-size)/2,y:top,cell:size/COLS,size,w,h};
}
function roundRect(x,y,w,h,r){const q=Math.min(r,w/2,h/2);ctx.beginPath();ctx.moveTo(x+q,y);ctx.arcTo(x+w,y,x+w,y+h,q);ctx.arcTo(x+w,y+h,x,y+h,q);ctx.arcTo(x,y+h,x,y,q);ctx.arcTo(x,y,x+w,y,q);ctx.closePath()}
function drawGem(g,r,c){
  const x=geom.x+c*geom.cell,y=geom.y+r*geom.cell,s=geom.cell,cx=x+s/2,cy=y+s/2,rad=s*.34;
  ctx.save();ctx.shadowColor='rgba(0,0,0,.28)';ctx.shadowBlur=s*.10;ctx.shadowOffsetY=s*.05;
  const gr=ctx.createRadialGradient(cx-rad*.45,cy-rad*.55,rad*.05,cx,cy,rad*1.1);gr.addColorStop(0,'#fff');gr.addColorStop(.18,palette[g.color]);gr.addColorStop(1,palette[g.color]);ctx.fillStyle=gr;
  ctx.beginPath();ctx.moveTo(cx,cy-rad);ctx.lineTo(cx+rad*.82,cy-rad*.25);ctx.lineTo(cx+rad*.62,cy+rad*.72);ctx.lineTo(cx,cy+rad);ctx.lineTo(cx-rad*.62,cy+rad*.72);ctx.lineTo(cx-rad*.82,cy-rad*.25);ctx.closePath();ctx.fill();
  ctx.shadowColor='transparent';ctx.strokeStyle='rgba(255,255,255,.55)';ctx.lineWidth=Math.max(1,s*.025);ctx.stroke();
  if(g.special==='row'||g.special==='col'){ctx.strokeStyle='#fff';ctx.lineWidth=Math.max(3,s*.08);ctx.beginPath();if(g.special==='row'){ctx.moveTo(cx-rad*.65,cy);ctx.lineTo(cx+rad*.65,cy)}else{ctx.moveTo(cx,cy-rad*.65);ctx.lineTo(cx,cy+rad*.65)}ctx.stroke()}
  else if(g.special==='bomb'){ctx.fillStyle='#111827';ctx.beginPath();ctx.arc(cx,cy,rad*.38,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=Math.max(2,s*.035);for(let i=0;i<8;i++){const a=i*Math.PI/4;ctx.beginPath();ctx.moveTo(cx+Math.cos(a)*rad*.42,cy+Math.sin(a)*rad*.42);ctx.lineTo(cx+Math.cos(a)*rad*.72,cy+Math.sin(a)*rad*.72);ctx.stroke()}}
  else if(g.special==='color'){ctx.fillStyle='#111827';ctx.beginPath();ctx.arc(cx,cy,rad*.54,0,Math.PI*2);ctx.fill();for(let i=0;i<6;i++){const a=i*Math.PI/3;ctx.fillStyle=palette[i];ctx.beginPath();ctx.arc(cx+Math.cos(a)*rad*.32,cy+Math.sin(a)*rad*.32,rad*.12,0,Math.PI*2);ctx.fill()}}
  ctx.restore();
}
function draw(){
  const{w,h}=geom,bg=ctx.createLinearGradient(0,0,w,h);bg.addColorStop(0,'#111827');bg.addColorStop(.55,'#172554');bg.addColorStop(1,'#261447');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  ctx.fillStyle='rgba(255,255,255,.94)';ctx.font='800 25px system-ui';ctx.textAlign='left';ctx.fillText('MATCH 3 DELUXE',18,36);
  ctx.font='700 13px system-ui';ctx.fillStyle='rgba(255,255,255,.62)';ctx.fillText('POWER GEMS • CHAINS • BLASTS',18,57);
  ctx.textAlign='right';ctx.font='800 27px system-ui';ctx.fillStyle='#fff';ctx.fillText(String(score),w-18,38);ctx.font='700 12px system-ui';ctx.fillStyle='rgba(255,255,255,.62)';ctx.fillText('SCORE',w-18,56);
  ctx.textAlign='center';ctx.font='800 14px system-ui';ctx.fillStyle=performance.now()<statusUntil?'#fde68a':'rgba(255,255,255,.58)';ctx.fillText(performance.now()<statusUntil?status:(bestChain>1?'BEST CHAIN ×'+bestChain:'SWIPE OR TAP'),w/2,88);
  ctx.fillStyle='rgba(9,14,31,.72)';roundRect(geom.x-6,geom.y-6,geom.size+12,geom.size+12,18);ctx.fill();ctx.strokeStyle='rgba(255,255,255,.12)';ctx.lineWidth=1.5;ctx.stroke();
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){ctx.fillStyle='rgba(255,255,255,.045)';roundRect(geom.x+c*geom.cell+2,geom.y+r*geom.cell+2,geom.cell-4,geom.cell-4,geom.cell*.14);ctx.fill();if(board[r][c])drawGem(board[r][c],r,c)}
  if(selected){ctx.save();ctx.strokeStyle='#fff';ctx.lineWidth=Math.max(2,geom.cell*.045);ctx.shadowColor='#fff';ctx.shadowBlur=12;roundRect(geom.x+selected.c*geom.cell+4,geom.y+selected.r*geom.cell+4,geom.cell-8,geom.cell-8,geom.cell*.18);ctx.stroke();ctx.restore()}
  particles=particles.filter(p=>p.life>0);for(const p of particles){p.x+=p.vx/60;p.y+=p.vy/60;p.vy+=4;p.life-=1/60;ctx.globalAlpha=Math.max(0,p.life/p.max);ctx.fillStyle=p.color;ctx.beginPath();ctx.arc(p.x,p.y,3.4,0,Math.PI*2);ctx.fill()}ctx.globalAlpha=1;
  requestAnimationFrame(draw);
}
function cellAt(x,y){const rect=canvas.getBoundingClientRect(),c=Math.floor((x-rect.left-geom.x)/geom.cell),r=Math.floor((y-rect.top-geom.y)/geom.cell);return inside(r,c)?{r,c}:null}
canvas.addEventListener('pointerdown',e=>{if(busy)return;canvas.setPointerCapture?.(e.pointerId);pointerStart={x:e.clientX,y:e.clientY,cell:cellAt(e.clientX,e.clientY)};e.preventDefault()});
canvas.addEventListener('pointerup',e=>{if(busy||!pointerStart)return;const s=pointerStart;pointerStart=null;if(!s.cell)return;const dx=e.clientX-s.x,dy=e.clientY-s.y;
  if(Math.hypot(dx,dy)>18){const b={r:s.cell.r+(Math.abs(dy)>Math.abs(dx)?Math.sign(dy):0),c:s.cell.c+(Math.abs(dx)>=Math.abs(dy)?Math.sign(dx):0)};if(inside(b.r,b.c))trySwap(s.cell,b);return}
  const p=cellAt(e.clientX,e.clientY);if(!p)return;if(selected&&adjacent(selected,p))trySwap(selected,p);else if(selected&&selected.r===p.r&&selected.c===p.c)selected=null;else selected=p;e.preventDefault()});
canvas.addEventListener('pointercancel',()=>pointerStart=null);
window.addEventListener('resize',resize);resize();resetBoard();requestAnimationFrame(draw);
})();