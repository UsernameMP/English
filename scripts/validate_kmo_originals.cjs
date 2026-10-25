#!/usr/bin/env node
"use strict";
// Execute the bundled KMO WebView activity without network or external libraries.
const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const path="app/src/main/assets/kmo/app.js";
const src=fs.readFileSync(path,"utf8");
new vm.Script(src,{filename:path});
const elements=new Map(),listeners={};
function element(id){if(!elements.has(id))elements.set(id,{
  textContent:"",innerHTML:"",className:"",open:false,disabled:false,style:{},
  addEventListener(type,fn){listeners[id+":"+type]=fn;},
  querySelectorAll(){return Array.from({length:10},()=>({classList:{toggle(){}}}));},
  showModal(){},close(){},contains(){return true;}
});return elements.get(id);}
const ls={getItem(){return null;},setItem(){}};
const ctx=vm.createContext({document:{getElementById:element,elementFromPoint(){return null;}},window:{addEventListener(){}},localStorage:ls,Intl,Date,Math,console});
vm.runInContext(src,ctx);
function run(source){return vm.runInContext(source,ctx);}
assert.equal(run("tasks.length"),10);
assert.deepEqual(Array.from(run("tasks.map(t=>t.year)")),["2025/26","2025/26","2025/26","2025/26","2025/26","2025/26","2025/26","2025/26","2024/25","2024/25"]);
assert.equal(run("shapePoints().length"),24);
const cutting=[".2.2..",".222..","1124.4",".11444","11334.",".33...","..33.."];
for(let y=0;y<cutting.length;y++)for(let x=0;x<cutting[y].length;x++){
 let g=Number(cutting[y][x]);if(g)run("states[0].groups["+JSON.stringify(x+","+y)+"]="+g);
}
assert.equal(run("checkCut().ok"),true,"Original figure must admit four congruent pieces");
run("states[0].groups['0,2']=4");
assert.equal(run("checkCut().ok"),false,"Invalid cut must fail");
run("states[1].v=[32,22,5,1]");
assert.equal(run("checkBaskets().ok"),true);
assert.equal(run("states[1].v.reduce((a,b)=>a+b,0)"),60);
run("states[1].v[1]++");assert.equal(run("checkBaskets().ok"),false);
// Do not allow collisions or opposite-direction exchanges on the bee's route.
const hex=run("Object.keys(hexP)");
let frontier=[["M",0]],seen=new Set(["M/0"]),best=-1;
for(let idx=0;idx<frontier.length;idx++){
 const [at,steps]=frontier[idx];if(at==="H"){best=steps;break;}
 const now=run("bees["+steps+"%4]"),next=run("bees["+(steps+1)+"%4]");
 for(const to of hex){
 if(!run("neighbour("+JSON.stringify(at)+","+JSON.stringify(to)+")"))continue;
 if(to===next||(at===next&&to===now))continue;
 const key=to+"/"+((steps+1)%4);
 if(!seen.has(key)){seen.add(key);frontier.push([to,steps+1]);}
 }
}
assert.equal(best,7,"Original bee/fly graph must have a minimum of seven seconds");
run("states[2].at='H';states[2].path=['U1','M','U1','U4','M','A','H']");
assert.equal(run("checkHex().ok"),true);
run("states[3].digits=[1,9,8,2,4]");
assert.equal(run("checkDigits().ok"),true);
for(let n=1;n<19824;n++)if(n%100===24&&n%24===0&&String(n).split("").reduce((s,d)=>s+Number(d),0)===24)assert.fail("smaller code exists: "+n);
run("states[4].move={from:10,to:5}");
assert.equal(run("expressionFor(states[4])"),"(1+5+(1+1)×2+0+2+5)×2");
assert.equal(run("evaluate(expressionFor(states[4]))"),34);
assert.equal(run("checkBrackets().ok"),true);
// Explicit arrangement of eight 2×3 rectangles with no shared corners or edges.
const places=[[0,0,false],[4,0,true],[7,0,true],[0,3,false],[6,4,false],[0,6,true],[3,6,true],[6,7,false]];
for(let [x,y,turn] of places) {
 const good=run("canPlace({x:"+x+",y:"+y+",turn:"+turn+"},states[5].rects)");
 assert.equal(good,true,"Packing at "+x+","+y);
 run("states[5].rects.push({x:"+x+",y:"+y+",turn:"+turn+"})");
}
run("states[5].target=8");assert.equal(run("checkPacking().ok"),true);
run("states[6].x=300");assert.equal(run("checkBoat().ok"),true);
run("states[7].assign=monthCorrect.slice()");assert.equal(run("checkCalendar().ok"),true);
run("states[8].cards=['8','80','801','44','432']");assert.equal(run("checkCards().ok"),true);
assert.equal(run("states[8].cards.join('')"),"88080144432");
run("states[9].bits=[0,1,0,1,1,0,1,0,0,1,0,0,0,0,0,0]");
assert.equal(run("checkColor().ok"),true);
// Each original interactive screen must render offline without DOM exceptions.
for(let i=0;i<10;i++){
 run("selectTask("+i+")");
 assert.ok(element("workarea").innerHTML.length>150,"empty renderer #"+(i+1));
}
assert.equal(src.includes("Math.random("),false,"No generated task conditions in original KMO exercise");
assert.ok(fs.readFileSync("app/src/main/assets/kmo/index.html","utf8").includes("app.js"));
console.log("KMO OK: 10 authentic selection exercises, 10 interactive renderers, all golden answers, no generators");
