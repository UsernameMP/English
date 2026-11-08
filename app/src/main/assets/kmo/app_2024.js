"use strict";
// КМО 2024/25, 5 класс, отбор 10.11.2024, вариант 1.
// Original problems are preserved; each renderer is a distinct offline interaction.
// Loaded after app.js; pre-existing 2025/26 mechanics and saved metrics are unchanged.
(function () {
  const additional = [
    {
      year:"2024/25",number:2,title:"Мыльные пузыри",
      kind:"k24_bubbles",
      prompt:"Для того чтобы получилось 3 больших пузыря, должны столкнуться 4 средних и 7 маленьких. Из 15 маленьких пузырей получается 4 средних. Сейчас в воздухе 4 средних пузыря. Сколько ещё маленьких пузырей нужно выдуть, чтобы в результате получить 12 больших?",
      hint:"Обе операции разрешены несколько раз. Попробуй собрать 12 больших пузырей, учитывая, сколько маленьких пришлось добавить.",
      solution:"10.11.2024, отбор, вариант 1, №2. Четыре группы по 3 больших требуют 16 средних и 28 маленьких. Средних уже 4, остальные 12 получаются из 45 маленьких. Всего нужно 73 маленьких."
    },
    {
      year:"2024/25",number:3,title:"Сырный квадрат Шапокляк",
      kind:"k24_cheese",
      prompt:"Шапокляк сложила квадрат 6×6 из сырных кубиков. Лариска съела отмеченный кубик. Разделите оставшиеся 35 клеток на фигурки формы, показанной в задании: три клетки в верхнем ряду и две слева в нижнем. Фигурки можно поворачивать и переворачивать. Достаточно одного разбиения.",
      hint:"Семь фигурок должны содержать по пять клеток. Поворот или отражение допускаются, но менять форму фигурки нельзя.",
      solution:"10.11.2024, отбор, вариант 1, №3. В оригинальном рисунке отсутствует клетка (столбец 2, строка 3). Форма каждой из семи фигурок — ###/##. Проверяются все 35 клеток, связность, повороты и отражения."
    },
    {
      year:"2024/25",number:4,title:"Лифт с двумя кнопками",
      kind:"k24_elevator",
      prompt:"В лифте 50-этажного небоскрёба работают только две кнопки: «подняться на 5 этажей» и «спуститься на 7 этажей». Сколько существует этажей, с которых можно уехать только в одном направлении?",
      hint:"Отметь на панели те этажи, на которых одна из двух кнопок выводила бы лифт за пределы здания.",
      solution:"10.11.2024, отбор, вариант 1, №4. Таких этажей 12: на 1–7 нельзя спуститься на семь; на 46–50 нельзя подняться на пять. На остальных этажах доступны оба направления."
    },
    {
      year:"2024/25",number:5,title:"Три пловца",
      kind:"k24_swim",
      prompt:"Петя, Вася и Толя одновременно начали плыть от одного бортика с постоянными, но разными скоростями. Достигнув другого бортика, каждый сразу поплыл обратно. Петя доплыл до другого бортика на 10 секунд раньше Васи, а Вася — на 15 секунд раньше Толи. На сколько секунд раньше Пети вернулся бы Толя к первоначальному бортику?",
      hint:"Расстояние обратно равно расстоянию туда. Каждый мальчик тратит на оба отрезка одинаковое время.",
      solution:"10.11.2024, отбор, вариант 1, №5. Разница времени на пути в одну сторону между Петей и Толей — 25 секунд; в обе стороны — 50 секунд. Ответ: Петя вернулся на 50 секунд раньше Толи."
    },
    {
      year:"2024/25",number:6,title:"Недостающее число на доске",
      kind:"k24_pairs",
      prompt:"Трое мальчиков написали каждый по два натуральных числа, отличающихся на 1. Из шести написанных чисел известны пять: 2, 3, 3, 4, 5. Каким могло быть шестое? Укажите все варианты.",
      hint:"Каждое из трёх числовых соседств должно состоять из двух отдельных карточек. Одинаковые цифры на доске — разные карточки.",
      solution:"10.11.2024, отбор, вариант 1, №6. Полный набор возможных шестых чисел: 2, 4, 6. Проверка выполняется перебором трёх пар с разностью 1, без повторного использования карточек."
    },
    {
      year:"2024/25",number:8,title:"Палочки и прямоугольники",
      kind:"k24_sticks",
      prompt:"На столе шесть палочек длиной 2, 3, 4, 4, 5, 6. Выберите три палочки и сломайте ровно одну из них на две части так, чтобы из четырёх получившихся палочек можно было составить прямоугольник. Укажите как можно больше различных наборов из трёх палочек.",
      hint:"В прямоугольнике противоположные стороны равны. Одна сломанная палочка должна дать недостающие стороны; одинаковые палочки длиной 4 существуют в двух экземплярах.",
      solution:"10.11.2024, отбор, вариант 1, №8. Шесть допустимых наборов: (2,4,4), (3,4,4), (4,4,5), (4,4,6), (2,3,5), (2,4,6). Ломаная палочка может дать две равные половины либо дополнить две другие до двух равных пар."
    }
  ];

  // Keep existing 2024 cards and colouring instances/metrics; place missing problems
  // before #7 and #8, preserving canonical task order 1..8 for the year.
  const originalColor = tasks.splice(9, 1)[0];
  tasks.push(...additional.slice(0,5), originalColor, additional[5]);

  const stickerColors = ["#f2f5ff","#47b8e6","#f1b95e","#9ad572","#c49ce8","#ee91a8","#70c8b5","#d7a47c"];
  const missingCell = 2 * 6 + 1;
  const tileShape = [[0,0],[1,0],[2,0],[0,1],[1,1]];
  const sticks = [2,3,4,4,5,6];
  const expectedSticks = ["2,3,5","2,4,4","2,4,6","3,4,4","4,4,5","4,4,6"];
  const initial = {
    k24_bubbles:()=>({small:0,medium:4,big:0,added:0}),
    k24_cheese:()=>({paint:1,groups:Array(36).fill(0)}),
    k24_elevator:()=>({marked:[]}),
    k24_swim:()=>({seconds:0}),
    k24_pairs:()=>({selected:[]}),
    k24_sticks:()=>({selected:[],found:[]})
  };
  const state = Object.fromEntries(Object.entries(initial).map(([key,make])=>[key,make()]));
  function reset(kind){if(!initial[kind])throw Error("Unknown KMO24 kind");state[kind]=initial[kind]();}
  function htmlEsc(value){return String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
  function btn(label,action,cls="chip"){return '<button class="'+cls+'" data-k24="'+htmlEsc(action)+'">'+htmlEsc(label)+'</button>';}
  function render(kind){
    const s=state[kind];
    if(kind==="k24_bubbles"){
      return '<p class="muted">Добавляй маленькие пузыри и запускай только разрешённые столкновения.</p>'+
      '<div class="k24-ledger"><div><small>Добавлено маленьких</small><strong>'+s.added+'</strong></div><div><small>Маленьких осталось</small><strong>'+s.small+'</strong></div><div><small>Средних</small><strong>'+s.medium+'</strong></div><div><small>Больших</small><strong>'+s.big+'</strong></div></div>'+
      '<div class="chip-row">'+[1,5,10].map(n=>btn("Добавить +"+n,"bubble:add:"+n)).join("")+'</div>'+
      '<div class="chip-row">'+btn("15 маленьких → 4 средних","bubble:medium","neutral")+btn("4 средних + 7 маленьких → 3 больших","bubble:big","neutral")+'</div>';
    }
    if(kind==="k24_cheese"){
      const counts=Array.from({length:7},(_,i)=>s.groups.filter(g=>g===i+1).length);
      return '<p class="muted">Выбери цвет фигурки и закрась её пять клеток. Заштрихованная клетка съедена. Пальцем можно проводить по нескольким клеткам.</p>'+
      '<div class="k24-palette">'+counts.map((n,i)=>'<button data-k24="cheese:paint:'+(i+1)+'" class="'+(s.paint===i+1?'k24-picked':'')+'" style="background:'+stickerColors[i+1]+'">'+(i+1)+' · '+n+'/5</button>').join("")+'</div>'+
      '<div class="k24-board" style="grid-template-columns:repeat(6,1fr)">'+s.groups.map((g,i)=>
        '<button class="k24-cell '+(i===missingCell?'k24-missing':'')+'" style="'+(i===missingCell?'':'background:'+stickerColors[g])+'" '+(i===missingCell?'disabled':'data-k24="cheese:cell:'+i+'"')+' aria-label="Клетка '+((i%6)+1)+', '+(Math.floor(i/6)+1)+'"></button>').join("")+'</div>'+
      '<p class="muted">Форма фигурки из условия: <strong>■■■ / ■■□</strong>. Разрешены повороты и отражения.</p>';
    }
    if(kind==="k24_elevator"){
      const marked=new Set(s.marked);
      return '<p class="muted">Нажми этаж, с которого можно уехать только в одном направлении. Можно снять отметку повторным нажатием.</p>'+
      '<div class="k24-floors">'+Array.from({length:50},(_,i)=>50-i).map(f=>'<button class="'+(marked.has(f)?'k24-picked':'')+'" data-k24="elevator:'+f+'">'+f+'</button>').join("")+'</div>'+
      '<p class="metric">Отмечено этажей: '+marked.size+'</p>';
    }
    if(kind==="k24_swim"){
      return '<p class="muted">Перемещай маркер по шкале, чтобы указать разницу времени возвращения Пети и Толи.</p>'+
      '<div class="k24-swim-lanes"><div><strong>Петя</strong><span>туда → обратно ←</span></div><div><strong>Вася</strong><span>туда → обратно ←</span></div><div><strong>Толя</strong><span>туда → обратно ←</span></div></div>'+
      '<input class="track" id="k24-swim-slider" type="range" min="0" max="100" step="1" value="'+s.seconds+'">'+
      '<p class="metric">Твой ответ: <strong>'+s.seconds+' секунд</strong></p>'+
      '<div class="chip-row">'+[-10,-1,1,10].map(n=>btn((n>0?"+":"")+n+" с","swim:"+n)).join("")+'</div>';
    }
    if(kind==="k24_pairs"){
      const pick=new Set(s.selected);
      return '<p class="muted">На доске уже есть пять карточек. Выбери ВСЕ возможные значения шестой карточки.</p>'+
      '<div class="k24-number-row">'+[2,3,3,4,5].map(n=>'<span class="k24-fixed">'+n+'</span>').join("")+'<span class="k24-unknown">?</span></div>'+
      '<div class="chip-row">'+Array.from({length:9},(_,i)=>i+1).map(n=>btn(String(n),"pairs:"+n,pick.has(n)?"chip on":"chip")).join("")+'</div>'+
      '<p class="metric">Выбрано возможных значений: '+pick.size+'</p>';
    }
    if(kind==="k24_sticks"){
      const selected=new Set(s.selected);
      return '<p class="muted">Выбери три палочки, нажми «Добавить набор». Удалить найденный набор можно нажатием на него. Одинаковые длины 4 — отдельные палочки.</p>'+
      '<div class="k24-sticks">'+sticks.map((n,i)=>'<button data-k24="sticks:pick:'+i+'" class="'+(selected.has(i)?'k24-picked':'')+'"><span style="width:'+(n*12)+'px"></span><small>'+n+'</small></button>').join("")+'</div>'+
      '<div class="chip-row">'+btn("Добавить выбранную тройку","sticks:add","neutral")+'</div>'+
      '<p class="metric">Наборов записано: '+s.found.length+'</p>'+
      '<div class="chip-row">'+s.found.map(v=>btn("("+v.replaceAll(",",", ")+") ×","sticks:remove:"+v)).join("")+'</div>';
    }
    throw Error("Unknown renderer "+kind);
  }
  function pairPossible(values) {
    if (!values.length) return true;
    const first=values[0];
    for(let j=1;j<values.length;j++){
      if(Math.abs(first-values[j])===1 && pairPossible(values.slice(1,j).concat(values.slice(j+1)))) return true;
    }
    return false;
  }
  function validTriple(numbers){
    const [a,b,c]=numbers.slice().sort((x,y)=>x-y);
    return a===b || b===c || a+b===c;
  }
  function check(kind){
    const s=state[kind];
    if(kind==="k24_bubbles")return s.big===12&&s.medium===0&&s.small===0&&s.added===73?
      {ok:true,text:"Получены 12 больших пузырей, лишних нет. Число добавленных маленьких указано верно."}:
      {ok:false,text:"Нужно получить ровно 12 больших пузырей без оставшихся маленьких и средних. Проверь количество добавленных."};
    if(kind==="k24_cheese"){
      const base=canon(tileShape);
      for(let g=1;g<=7;g++){
        const pieces=s.groups.flatMap((v,i)=>v===g?[[i%6,Math.floor(i/6)]]:[]);
        if(pieces.length!==5)return{ok:false,text:"Каждую из семи фигурок нужно составить ровно из пяти клеток."};
        if(!connected(pieces)||canon(pieces)!==base)return{ok:false,text:"Проверь форму и связность фигурки №"+g+". Она должна совпадать с фигуркой из условия."};
      }
      return {ok:true,text:"Все 35 клеток разбиты на семь одинаковых фигурок. Разрезание верно."};
    }
    if(kind==="k24_elevator"){
      const expected=new Set(Array.from({length:50},(_,i)=>i+1).filter(i=>(i+5>50)!==(i-7<1)));
      return s.marked.length===expected.size&&s.marked.every(i=>expected.has(i))?
        {ok:true,text:"Верно! Отмечены все этажи, с которых работает только одно направление."}:
        {ok:false,text:"Есть пропущенные или лишние этажи. Перепроверь работу обеих кнопок у границ здания."};
    }
    if(kind==="k24_swim")return s.seconds===50?
      {ok:true,text:"Верно. Разница на пути туда и обратно вдвое больше разницы на пути в одну сторону."}:
      {ok:false,text:"Учитывай оба отрезка пути: туда и обратно."};
    if(kind==="k24_pairs"){
      const expected=Array.from({length:9},(_,i)=>i+1).filter(n=>pairPossible([2,3,3,4,5,n]));
      return s.selected.length===expected.length&&s.selected.every(n=>expected.includes(n))?
        {ok:true,text:"Все возможные шестые числа найдены."}:
        {ok:false,text:"Набор неполон или содержит невозможные варианты. Каждую карточку можно использовать лишь в одной паре."};
    }
    if(kind==="k24_sticks"){
      const valid=s.found.every(v=>validTriple(v.split(",").map(Number)));
      return valid&&s.found.length===expectedSticks.length&&expectedSticks.every(v=>s.found.includes(v))?
        {ok:true,text:"Все допустимые наборы найдены; прямоугольник можно составить в каждом случае."}:
        {ok:false,text:"Не все наборы найдены либо в списке есть невозможная тройка. Ищи одинаковые пары сторон."};
    }
    throw Error("Unknown checker "+kind);
  }
  function handle(action){
    const [name,verb,payload]=action.split(":");
    const kind="k24_"+({bubble:"bubbles",cheese:"cheese",elevator:"elevator",swim:"swim",pairs:"pairs",sticks:"sticks"}[name]||"");
    if (!state[kind] || tasks[current].kind!==kind) return;
    const s=state[kind];
    if(name==="bubble"){
      if(verb==="add"){const n=Number(payload);s.small+=n;s.added+=n;act();}
      if(verb==="medium"){if(s.small<15){act(true);msg("Для этого столкновения нужно 15 маленьких пузырей.",false);return;}s.small-=15;s.medium+=4;act();}
      if(verb==="big"){if(s.medium<4||s.small<7){act(true);msg("Для этого столкновения не хватает средних или маленьких пузырей.",false);return;}s.medium-=4;s.small-=7;s.big+=3;act();}
    }else if(name==="cheese"){
      if(verb==="paint"){s.paint=Number(payload);}
      if(verb==="cell"){const i=Number(payload);if(i!==missingCell){s.groups[i]=s.groups[i]===s.paint?0:s.paint;act();}}
    }else if(name==="elevator"){
      const floor=Number(verb),i=s.marked.indexOf(floor);
      if(i>=0)s.marked.splice(i,1);else s.marked.push(floor);
      act();
    }else if(name==="swim"){
      s.seconds=Math.max(0,Math.min(100,s.seconds+Number(verb)));act();
    }else if(name==="pairs"){
      const n=Number(verb),i=s.selected.indexOf(n);
      if(i>=0)s.selected.splice(i,1);else s.selected.push(n);
      act();
    }else if(name==="sticks"){
      if(verb==="pick"){const i=Number(payload),at=s.selected.indexOf(i);if(at>=0)s.selected.splice(at,1);else if(s.selected.length<3)s.selected.push(i);act();}
      if(verb==="add"){
        if(s.selected.length!==3){act(true);msg("Выбери ровно три палочки.",false);return;}
        const values=s.selected.map(i=>sticks[i]).sort((a,b)=>a-b);
        const key=values.join(",");
        if(!validTriple(values)){act(true);msg("Эта тройка не даёт прямоугольник после одного разлома.",false);return;}
        if(!s.found.includes(key))s.found.push(key);
        s.selected=[];act();
      }
      if(verb==="remove"){s.found=s.found.filter(v=>v!==payload);act();}
    }
    draw();
  }

  $("workarea").addEventListener("click",e=>{
    const el=e.target.closest("[data-k24]");
    if(!el||!$("workarea").contains(el))return;
    if(Date.now()<cheeseSuppressClickUntil&&el.dataset.k24.startsWith("cheese:cell:"))return;
    handle(el.dataset.k24);
  });
  $("workarea").addEventListener("input",e=>{
    if(e.target.id!=="k24-swim-slider"||tasks[current].kind!=="k24_swim")return;
    state.k24_swim.seconds=Number(e.target.value);
    const node=$("workarea").querySelector(".metric strong");
    if(node)node.textContent=state.k24_swim.seconds+" секунд";
  });
  $("workarea").addEventListener("change",e=>{
    if(e.target.id==="k24-swim-slider"&&tasks[current].kind==="k24_swim"){act();draw();}
  });

  let cheeseBrush=false,cheeseLast=-1,cheeseSuppressClickUntil=0;
  function paintCheeseAt(clientX,clientY){
    const el=document.elementFromPoint(clientX,clientY);
    const button=el&&el.closest("[data-k24^='cheese:cell:']");
    if(!button||!$("workarea").contains(button))return;
    const i=Number(button.dataset.k24.split(":")[2]);
    if(i===missingCell||i===cheeseLast)return;
    cheeseLast=i;
    state.k24_cheese.groups[i]=state.k24_cheese.paint;
    button.style.background=stickerColors[state.k24_cheese.paint];act();
  }
  $("workarea").addEventListener("pointerdown",e=>{
    if(tasks[current].kind!=="k24_cheese"||!e.target.closest("[data-k24^='cheese:cell:']"))return;
    cheeseBrush=true;cheeseLast=-1;e.preventDefault();paintCheeseAt(e.clientX,e.clientY);
  });
  $("workarea").addEventListener("pointermove",e=>{
    if(!cheeseBrush||tasks[current].kind!=="k24_cheese")return;
    e.preventDefault();paintCheeseAt(e.clientX,e.clientY);
  });
  const cheeseFinish=()=>{if(cheeseBrush){cheeseBrush=false;cheeseLast=-1;cheeseSuppressClickUntil=Date.now()+500;draw();}};
  window.addEventListener("pointerup",cheeseFinish);
  window.addEventListener("pointercancel",cheeseFinish);

  window.KMO24={render,check,reset,state,expectedSticks,pairPossible,validTriple,tileShape,missingCell};
  selectTask(0);
})();
