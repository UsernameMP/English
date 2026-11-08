#!/usr/bin/env node
"use strict";
// 2024/25 official variant-1 answer-key regression, plus WebView render smoke tests.
const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const scripts=["app/src/main/assets/kmo/app.js","app/src/main/assets/kmo/app_2024.js"];
const elements=new Map(),listeners={};
function element(id){
  if(!elements.has(id))elements.set(id,{
    textContent:"",innerHTML:"",className:"",open:false,disabled:false,style:{},
    addEventListener(type,fn){(listeners[id+":"+type]||(listeners[id+":"+type]=[])).push(fn);},
    querySelectorAll(){return Array.from({length:16},()=>({classList:{toggle(){}}}));},
    querySelector(){return {textContent:"",style:{}};},
    showModal(){},close(){},contains(){return true;}
  });
  return elements.get(id);
}
const ctx=vm.createContext({
  document:{getElementById:element,elementFromPoint(){return null;}},
  window:{addEventListener(){}},
  localStorage:{getItem(){return null;},setItem(){}},
  Intl,Date,Math,console
});
for(const path of scripts){
  const code=fs.readFileSync(path,"utf8");
  new vm.Script(code,{filename:path});
  vm.runInContext(code,ctx);
}
const run=s=>vm.runInContext(s,ctx);
assert.equal(run("tasks.length"),16,"8 tasks per each year");
assert.deepEqual(Array.from(run("tasks.filter(t=>t.year==='2024/25').map(t=>t.number)")),[1,2,3,4,5,6,7,8]);
assert.equal(run("tasks.filter(t=>t.year==='2025/26').length"),8);
for(let i=0;i<16;i++){
  run("selectTask("+i+")");
  assert.ok(element("workarea").innerHTML.length>160,"Renderer missing at index "+i);
}
assert.deepEqual(Array.from(run("Object.keys(window.KMO24.state)")).sort(),[
  "k24_bubbles","k24_cheese","k24_elevator","k24_pairs","k24_sticks","k24_swim"
].sort());
// Bubble transformations: 73 -> 3 times 15 small to 4 medium, 4 times 4 medium+7 small to 3 big.
run("window.KMO24.state.k24_bubbles={small:0,medium:4,big:0,added:73}");
assert.equal(run("window.KMO24.check('k24_bubbles').ok"),false);
run("window.KMO24.state.k24_bubbles={small:0,medium:0,big:12,added:73}");
assert.equal(run("window.KMO24.check('k24_bubbles').ok"),true);
run("window.KMO24.state.k24_bubbles.added=74");
assert.equal(run("window.KMO24.check('k24_bubbles').ok"),false);
// Original cheese diagram: 6x6 minus x=1,y=2 and seven identical 5-cell pentominoes.
const solved=["116667","116677","1X3377","233355","224455","224445"];
run("window.KMO24.state.k24_cheese.groups="+JSON.stringify(
  solved.join("").split("").map(c=>c==="X"?0:Number(c))
));
assert.equal(run("window.KMO24.missingCell"),13);
assert.equal(run("window.KMO24.check('k24_cheese').ok"),true,"Known exact tiling should pass");
run("window.KMO24.state.k24_cheese.groups[0]=7");
assert.equal(run("window.KMO24.check('k24_cheese').ok"),false);
// Elevator: upward five, downward seven; 12 floors allow exactly one button.
run("window.KMO24.state.k24_elevator.marked=[1,2,3,4,5,6,7,46,47,48,49,50]");
assert.equal(run("window.KMO24.check('k24_elevator').ok"),true);
run("window.KMO24.state.k24_elevator.marked.pop()");
assert.equal(run("window.KMO24.check('k24_elevator').ok"),false);
// Swim leg differences 10+15 doubled -> 50 seconds.
run("window.KMO24.state.k24_swim.seconds=50");
assert.equal(run("window.KMO24.check('k24_swim').ok"),true);
run("window.KMO24.state.k24_swim.seconds=25");
assert.equal(run("window.KMO24.check('k24_swim').ok"),false);
// Pairing all six cards using three disjoint consecutive pairs.
const pairOptions=Array.from({length:9},(_,i)=>i+1).filter(n=>run("window.KMO24.pairPossible([2,3,3,4,5,"+n+"])"));
assert.deepEqual(pairOptions,[2,4,6]);
run("window.KMO24.state.k24_pairs.selected=[2,4,6]");
assert.equal(run("window.KMO24.check('k24_pairs').ok"),true);
run("window.KMO24.state.k24_pairs.selected=[2,4]");
assert.equal(run("window.KMO24.check('k24_pairs').ok"),false);
// Six original stick triples, no duplicates; invalid triples must not pass.
const found=Array.from(new Set(run("window.KMO24.expectedSticks")));
assert.equal(found.length,6);
for(const key of found)assert.equal(run("window.KMO24.validTriple("+JSON.stringify(key.split(",").map(Number))+")"),true);
assert.equal(run("window.KMO24.validTriple([2,3,4])"),false);
run("window.KMO24.state.k24_sticks.found="+JSON.stringify(found));
assert.equal(run("window.KMO24.check('k24_sticks').ok"),true);
run("window.KMO24.state.k24_sticks.found=['2,3,4']");
assert.equal(run("window.KMO24.check('k24_sticks').ok"),false);
// Original 2024 cards and colouring still work after repositioning.
run("states[8].cards=['8','80','801','44','432'];selectTask(8)");
assert.equal(run("checkCards().ok"),true);
run("states[9].bits=[0,1,0,1,1,0,1,0,0,1,0,0,0,0,0,0];selectTask(14)");
assert.equal(run("checkColor().ok"),true);
assert.equal(run("tasks[14].number"),7);
assert.ok(fs.readFileSync("app/src/main/assets/kmo/index.html","utf8").includes('src="app_2024.js"'));
console.log("KMO 2024/25 OK: full eight original variant-1 tasks; 16 screens total; six new validators pass official golden answers.");
