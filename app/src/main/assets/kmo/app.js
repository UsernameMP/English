"use strict";
// KMO original tasks, no parametric generation. Offline and deterministic.
const tasks=[
{year:"2025/26",number:1,title:"Разрезание на четыре равные части",kind:"cut",prompt:"Разрежьте клетчатую фигуру на четыре равные части. Равные части должны иметь одинаковую форму и размеры. Резать можно только по линиям клетчатой сетки. Достаточно одного примера.",hint:"У фигуры 24 клетки: на каждую из четырёх частей приходится по 6. Все четыре полученные части должны совпадать при повороте или отражении.",solution:"Оригинал: 15.11.2025, отбор, задача 1. Правильным считается любое разбиение на четыре связные одинаковые фигуры из шести клеток. На экране раскрашивайте целые клетки в четыре цвета: границами разреза станут переходы между цветами."},
{year:"2025/26",number:2,title:"Корзины с эчпочмаками",kind:"baskets",prompt:"У пекаря четыре корзины. Если из №1 переложить 5 эчпочмаков в №2, в этих двух корзинах станет поровну. Если из №2 переложить 4 в №3, во второй станет вдвое больше, чем в третьей. Если из №3 переложить 2 в №4, в третьей и четвёртой будет по 3. Сколько всего эчпочмаков?",hint:"Каждое «если» — отдельный эксперимент от исходного состояния! Начните с третьего условия: сколько было в №3 и №4 до переноса?",solution:"Оригинал: 15.11.2025, отбор, задача 2. Три независимых эксперимента. Сначала №3=5, №4=1, затем №2=22, №1=32; всего 60. Кнопки экспериментов позволяют увидеть результат переноса из одних и тех же исходных корзин."},
{year:"2025/26",number:3,title:"Муха и пчела: маршрут по сотам",kind:"hex",prompt:"Пчела начинает в соте МЁД и каждую секунду проходит цикл МЁД → А → В → А → МЁД. Муха начинает в соте М и каждую секунду переходит в соседнюю по стороне соту. Они движутся одновременно. Мухе нельзя оказаться с пчелой в одной соте или поменяться с ней местами одним ходом. За сколько секунд минимум муха достигнет мёда?",hint:"Важен момент занятия соты, а не только клетка назначения. Разрешается заходить в соту, которую пчела как раз покидает, если вы не движетесь навстречу друг другу.",solution:"Оригинал: 15.11.2025, отбор, задача 3. Минимум 7 секунд. Программа проверяет одновременное движение, запрещённый встречный обмен и безопасное достижение соты МЁД."},
{year:"2025/26",number:4,title:"Код мышиного короля",kind:"digits",prompt:"Найдите наименьшее натуральное число, которое оканчивается на 24, делится нацело на 24 и имеет сумму цифр 24.",hint:"Последние две цифры уже известны. Подберите остальные и проверяйте три условия отдельно: окончание, делимость, сумма цифр. Одного подходящего числа недостаточно: нужно минимальное.",solution:"Оригинал: 15.11.2025, отбор, задача 4. Минимальное число — 19824. Для цифр 1, 9, 8, 2, 4 сумма равна 24; 19824 делится на 24. Меньшее подходящее число отсутствует."},
{year:"2025/26",number:5,title:"Переместить одну скобку",kind:"brackets",prompt:"Перед вами равенство (1+5+1+1)×(2+0+2+5)×2=34. Переставьте ровно одну из четырёх скобок, не меняя цифр и знаков, чтобы оно стало верным.",hint:"Выбирайте одну из четырёх существующих скобок, затем новое место. Можно перемещать скобку из второго блока в первый.",solution:"Оригинал: 15.11.2025, отбор, задача 5. Один подходящий результат: (1+5+(1+1)×2+0+2+5)×2=34. Перемещается ровно открывающая скобка второго множителя."},
{year:"2025/26",number:6,title:"Прямоугольники 2×3 без касаний",kind:"packing",prompt:"Разместите 7 (а затем 8) прямоугольников 2×3 в квадратном клетчатом поле так, чтобы любые два не касались друг друга ни сторонами, ни углами. Прямоугольники разрешено поворачивать. Найдите наименьшую сторону квадрата.",hint:"В оригинале минимальная сторона равна 9 клеткам для обоих случаев. Проверьте построением: помните, что даже диагональное соприкосновение запрещено.",solution:"Оригинал: 15.11.2025, отбор, задача 6. Ответ: а) 9; б) 9 клеток. Здесь проверяется построение на поле 9×9. Полное доказательство минимальности отдельно требует обоснования невозможности поля 8×8."},
{year:"2025/26",number:7,title:"Катер, маяк и три буйка",kind:"boat",prompt:"Катер идёт по прямой к маяку. Изначально до маяка 450 м и сумма расстояний до трёх расположенных впереди буйков тоже 450 м. После прохождения всех буйков, но до маяка, сумма расстояний до буйков снова составляет 450 м. Сколько метров осталось до маяка?",hint:"Точные координаты буйков не заданы: показано одно согласованное размещение. После прохождения всех трёх буйков при сдвиге катера на 1 метр сумма расстояний увеличивается на 3 метра.",solution:"Оригинал: 15.11.2025, отбор, задача 7. Катер прошёл 300 м от исходной точки. До маяка осталось 150 м. Демонстрационная схема задаёт буйки на расстояниях 50, 150, 250 м: их сумма равна 450 м."},
{year:"2025/26",number:8,title:"Календарь планеты Мирена",kind:"months",prompt:"На планете Мирена 12 месяцев по три на сезон: Вирень, Ганевик, Дорень, Зевень, Ковень, Ладень, Малярь, Навень, Ружень, Старень, Тарень, Фарень. Ружень не зимний; Тарень не весенний. Вирень — летний; Малярь — осенний. Дорень, Зевень и Ковень относятся к одному сезону. Ганевик и Фарень — к разным сезонам. Навень → Ладень → Тарень → Ружень идут подряд. Старень и Фарень относятся к одному сезону. Разложите месяцы по сезонам.",hint:"Начните с тройки Дорень–Зевень–Ковень и известной принадлежности Виреня и Маля́ря. У каждого сезона ровно три места.",solution:"Оригинал: 15.11.2025, отбор, задача 8. Зима: Дорень, Зевень, Ковень. Весна: Ганевик, Ладень, Навень. Лето: Вирень, Ружень, Тарень. Осень: Малярь, Старень, Фарень. Проверяйте одновременно вместимость групп и отношения."},
{year:"2024/25",number:1,title:"Карточки: самое большое число",kind:"cards",prompt:"На столе карточки с числами 80, 432, 8, 44, 801. Расположите все пять карточек так, чтобы при записи чисел подряд получилось самое большое 11-значное число. Переставляются именно целые карточки.",hint:"Не всегда нужно сортировать карточки по величине самого числа. Чтобы решить, какой блок поставить раньше, сравните два соединения, например 8|80 и 80|8.",solution:"Оригинал: 10.11.2024, отбор, вариант 1, задача 1. Оптимальный порядок карточек: 8, 80, 801, 44, 432."},
{year:"2024/25",number:7,title:"Раскраска: двухцветные соседства",kind:"color",prompt:"В квадрате 4×4 закрасьте некоторые клетки так, чтобы появилось ровно 16 двухцветных прямоугольников 1×2. Каждый такой прямоугольник — две соседние по стороне клетки разных цветов. Достаточно одного подходящего примера.",hint:"Всего в квадрате 4×4 есть 24 горизонтальных и вертикальных соседства. Каждое разноцветное соседство учитывается один раз. Пробуйте чередовать цвета по строкам и столбцам.",solution:"Оригинал: 10.11.2024, отбор, вариант 1, задача 7. Цель — 16 двухцветных соседств в сетке 4×4. Движок принимает любую раскраску, в которой сумма отличающихся по стороне соседей равна 16."}
];
const $=id=>document.getElementById(id);
const baseExpression="(1+5+1+1)×(2+0+2+5)×2";
const shape=[".#.#..",".###..","####.#",".#####","#####.",".##...","..##.."];
const hexP={H:[38,195],A:[94,195],B:[122,243],M:[122,147],U1:[94,99],U2:[122,51],U3:[178,51],U4:[150,99],U5:[206,99],U6:[178,147]};
const months=["Вирень","Ганевик","Дорень","Зевень","Ковень","Ладень","Малярь","Навень","Ружень","Старень","Тарень","Фарень"];
const monthCorrect=[2,1,0,0,0,1,3,1,2,3,2,3];
const seasonNames=["Зима","Весна","Лето","Осень"];
const init=()=>[{paint:1,groups:{}},{v:[0,0,0,0],trial:0},{at:"M",path:[]},{digits:[1,0,0,2,4],sel:1},{select:null,move:null},{rects:[],rotate:false,target:7},{x:0},{assign:Array(12).fill(-1),selected:null},{cards:["80","432","8","44","801"],selected:null},{bits:Array(16).fill(0)}];
let states=init(),current=0,showHint=false;
const started=Date.now(),metricsKey="rift_kmo_original_v1";
let metrics;try{metrics=JSON.parse(localStorage.getItem(metricsKey)||"{}");}catch(_){metrics={};}
function m(i=current){const key=tasks[i].year+"/"+tasks[i].number;return metrics[key]||(metrics[key]={actions:0,invalid:0,checks:0,hints:0,opened:0,solved:false,firstActionMs:null});}
function save(){try{localStorage.setItem(metricsKey,JSON.stringify(metrics));}catch(_){}}
let openedAt=Date.now();
function act(invalid=false){const z=m();z.actions++;if(invalid)z.invalid++;if(z.firstActionMs===null)z.firstActionMs=Math.max(0,Date.now()-openedAt);save();}
function msg(text,good=null){let el=$("message");el.className="message show"+(good===true?" good":good===false?" bad":"");el.textContent=text;}
function clearMsg(){$("message").className="message";$("message").textContent="";}
function idhtml(id,text,cls="chip"){return '<button class="'+cls+'" data-action="'+id+'">'+text+"</button>";}
function pretty(n){return new Intl.NumberFormat("ru-RU").format(n);}
function selectTask(i){current=Math.max(0,Math.min(tasks.length-1,i));openedAt=Date.now();m().opened++;save();showHint=false;$("explanation").open=false;draw();}
function draw(){
 const t=tasks[current];$("source").textContent=t.year+" · отбор · №"+t.number;$("progress").textContent=(current+1)+" / "+tasks.length;
 $("task-title").textContent=t.title;$("task-prompt").textContent=t.prompt;$("solution").textContent=t.solution;
 $("navigation").innerHTML=tasks.map((t,i)=>'<button class="'+(i===current?"active ":m(i).solved?"done":"")+'" data-nav="'+i+'" title="'+t.title+'">'+(i+1)+"</button>").join("");
 $("prev").disabled=current===0;$("next").disabled=current===tasks.length-1;
 let f=[cut,baskets,hex,digits,brackets,packing,boat,calendar,cards,color][current];
 $("workarea").innerHTML=f();clearMsg();
 if(showHint)msg(t.hint);
}
function feedback(result){m().checks++;if(result.ok)m().solved=true;else m().invalid++;save();msg(result.text,result.ok);$("navigation").querySelectorAll("button")[current].classList.toggle("done",result.ok);}

function canon(points){
 let forms=[];for(let flip=0;flip<2;flip++)for(let rot=0;rot<4;rot++){
 let v=points.map(([x,y])=>{if(flip)x=-x;for(let r=0;r<rot;r++){let a=x;x=-y;y=a;}return[x,y];});
 let minx=Math.min(...v.map(p=>p[0])),miny=Math.min(...v.map(p=>p[1]));
 forms.push(v.map(([x,y])=>(x-minx)+","+(y-miny)).sort().join(";"));
 }return forms.sort()[0];
}
function connected(points){
 if(!points.length)return false;let found=new Set([points[0].join(",")]),todo=[points[0]],all=new Set(points.map(p=>p.join(",")));
 while(todo.length){let [x,y]=todo.pop();for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){let k=(x+dx)+","+(y+dy);if(all.has(k)&&!found.has(k)){found.add(k);todo.push([x+dx,y+dy]);}}}
 return found.size===points.length;
}
function shapePoints(){let out=[];shape.forEach((line,y)=>[...line].forEach((v,x)=>{if(v==="#")out.push([x,y]);}));return out;}
function cut(){
 const st=states[0],colors=["#ffffff","#4bc0e8","#fac25b","#a8db80","#d19fe9"];
 const row=shape.map((line,y)=>[...line].map((v,x)=>{if(v===".")return '<div class="cell blank"></div>';let key=x+","+y,g=st.groups[key]||0;return '<button class="cell g'+g+'" data-cell="'+key+'" aria-label="Клетка '+(x+1)+', '+(y+1)+'; группа '+g+'"></button>';}).join("")).join("");
 const amount=[1,2,3,4].map(k=>Object.values(st.groups).filter(z=>z===k).length);
 return '<p class="muted">Выбери цвет части, затем проведи пальцем по её клеткам. Каждая часть должна содержать 6 клеток. Повторное нажатие выбранным цветом убирает закраску.</p>'+
 '<div class="palette">'+[1,2,3,4].map((k,i)=>'<button class="chip '+(st.paint===k?"picked":"")+'" style="background:'+colors[k]+'" data-paint="'+k+'">Часть '+k+" · "+amount[i]+"/6</button>").join("")+"</div>"+
 '<div class="gridShape" style="grid-template-columns:repeat(6,max-content)" id="shapeGrid">'+row+"</div>";
}
function setCell(key){const st=states[0];st.groups[key]=(st.groups[key]===st.paint?0:st.paint);act();draw();}
function checkCut(){
 const st=states[0],forms=[];for(let k=1;k<=4;k++){
 const p=Object.entries(st.groups).filter(([_,n])=>n===k).map(([key])=>key.split(",").map(Number));
 if(p.length!==6)return {ok:false,text:"У каждой части должно быть ровно 6 клеток. Проверь количества по цветам."};
 if(!connected(p))return {ok:false,text:"Часть "+k+" распалась на несвязанные клетки. Исправь границы."};
 forms.push(canon(p));
 }
 return forms.every(x=>x===forms[0])?{ok:true,text:"Разрезание верное: четыре одинаковые связные фигуры!"}:{ok:false,text:"Площади равны, но формы частей не совпадают при наложении."};
}
function baskets(){
 const s=states[1],after=[s.v.slice(),s.v.slice(),s.v.slice()];
 after[0][0]-=5;after[0][1]+=5;after[1][1]-=4;after[1][2]+=4;after[2][2]-=2;after[2][3]+=2;
 const badges=["Из №1 → №2: 5, затем поровну","Из №2 → №3: 4, затем 2:1","Из №3 → №4: 2, затем по 3"];
 return '<p class="muted">Подбирай начальное распределение кнопками. Перекладывание в каждом условии независимо от двух других.</p>'+
 '<div class="basketbox">'+s.v.map((n,i)=>'<div class="basket"><small>Корзина '+(i+1)+'</small><strong>'+n+'</strong><div class="dots">'+(n?"◆".repeat(Math.min(6,n)):"пусто")+'</div><div class="num-actions"><button data-basket="'+i+'" data-delta="-1">−</button><button data-basket="'+i+'" data-delta="1">+</button></div></div>').join("")+"</div>"+
 '<p class="metric">Всего в исходных корзинах: <strong>'+s.v.reduce((a,b)=>a+b,0)+"</strong></p>"+
 '<div class="chip-row">'+badges.map((x,i)=>idhtml("trial:"+i,"Опыт "+(i+1),s.trial===i?"chip on":"chip")).join("")+"</div>"+
 '<div class="stageNote">'+badges[s.trial]+'<br>После переноса: '+after[s.trial].map((v,i)=>"№"+(i+1)+" = "+v).join(", ")+"</div>";
}
function basketConditions(v){return[v[0]-5===v[1]+5,v[1]-4===2*(v[2]+4),v[2]-2===3&&v[3]+2===3];}
function checkBaskets(){const v=states[1].v,a=basketConditions(v);return a.every(Boolean)?{ok:true,text:"Все три независимых опыта выполняются! Сумма = "+v.reduce((x,y)=>x+y,0)+". Верно."}:{ok:false,text:"Подходят "+a.filter(Boolean).length+" из 3 условий. Перепроверь исходное состояние."};}

const bees=["H","A","B","A"];
function neighbour(a,b){let x=hexP[a],y=hexP[b];return x&&y&&Math.hypot(x[0]-y[0],x[1]-y[1])<61&&a!==b;}
function hexSvg(){
 const s=states[2],t=s.path.length,be=bees[t%4];
 let hexes=Object.entries(hexP).map(([id,[x,y]])=>{
 const points=Array.from({length:6},(_,i)=>{let a=Math.PI/180*(60*i-90);return (x+32*Math.cos(a)).toFixed(1)+","+(y+32*Math.sin(a)).toFixed(1);}).join(" ");
 let label=id==="H"?"МЁД":id==="M"?"М":id==="A"?"А":id==="B"?"В":"";
 return '<g data-hex="'+id+'"><polygon class="'+(s.at===id?"fly ":be===id?"bee ":"")+(s.path.includes(id)?"path":"")+'" points="'+points+'"></polygon><text x="'+x+'" y="'+(y+5)+'" text-anchor="middle">'+(label||(id==="U"+2?"":""))+'</text>'+(s.at===id?'<circle cx="'+(x-12)+'" cy="'+(y-13)+'" r="7" fill="#0f856c" />':"")+(be===id?'<circle cx="'+(x+12)+'" cy="'+(y+14)+'" r="7" fill="#d48b11" />':"")+"</g>";
 }).join("");
 return '<p class="muted">Нажимай соседнюю соту. Маленькие кружки: зелёный — муха, жёлтый — пчела. Каждый ход идёт одновременно.</p>'+
 '<svg viewBox="0 0 260 290" class="hex-svg" aria-label="Сотовое поле с мухой и пчелой">'+hexes+'</svg>'+
 '<div class="metric">Прошло <strong>'+t+'</strong> секунд. Муха: '+(s.at==="M"?"М":s.at==="H"?"МЁД":s.at==="A"?"А":s.at==="B"?"В":"сота без названия")+'. Пчела: '+(be==="H"?"МЁД":be==="A"?"А":"В")+". Оптимально: 7 секунд.</div>";
}
function stepHex(to){
 let s=states[2],t=s.path.length,be=bees[t%4],next=bees[(t+1)%4];
 if(!neighbour(s.at,to)||to===next||(to===be&&s.at===next)){act(true);msg("Такой переход запрещён: нет общего ребра или происходит столкновение.",false);return;}
 s.at=to;s.path.push(to);act();draw();
 if(to==="H")msg("Муха добралась до мёда за "+s.path.length+" секунд. Нажми «Проверить», чтобы узнать, оптимален ли маршрут.",true);
}
function checkHex(){const s=states[2];return s.at==="H"&&s.path.length===7?{ok:true,text:"Правильно: достигли мёда за минимальные 7 секунд!"}:{ok:false,text:s.at!=="H"?"Ещё не достигнута сота МЁД.":"Маршрут безопасный, но не минимальный: "+s.path.length+" секунд вместо 7."};}

function digits(){
 const s=states[3],v=Number(s.digits.join("")),sum=s.digits.reduce((a,b)=>a+b,0);
 return '<p class="muted">Нажми на одну из первых трёх цифр, затем выбери цифру ниже. Последние две цифры закреплены.</p>'+
 '<div class="pad">'+s.digits.map((d,i)=>'<button data-digit="'+i+'" class="'+(i===s.sel?"sel ":"")+(i>=3?"fixed":"")+'">'+d+'</button>').join("")+"</div>"+
 '<div class="keypad">'+Array.from({length:10},(_,i)=>'<button data-key="'+i+'">'+i+"</button>").join("")+"</div>"+
 '<div class="metric">Получилось: <strong>'+pretty(v)+'</strong><br>Кончается на 24: ✓<br>Сумма цифр: '+sum+" / 24 "+(sum===24?"✓":"×")+"<br>Делимость на 24: "+(v%24===0?"✓":"×")+"</div>";
}
function checkDigits(){let n=Number(states[3].digits.join(""));return n===19824?{ok:true,text:"Да! Это минимальный код 19824."}:{ok:false,text:n%24===0&&[...String(n)].reduce((a,x)=>a+Number(x),0)===24?"Условия выполняются, но существует меньшее подходящее число.":"Проверь сумму цифр и делимость на 24."};}

function expressionFor(s){if(!s.move)return baseExpression;let a=[...baseExpression];let c=a.splice(s.move.from,1)[0];a.splice(s.move.to,0,c);return a.join("");}
function evaluate(expression){
 if(!/^[0-9+×()]+$/.test(expression))return null;
 let values=[],ops=[];const prec={"+":1,"×":2};
 const apply=()=>{let op=ops.pop();if(values.length<2||!(op in prec))throw Error("parse");let b=values.pop(),a=values.pop();values.push(op==="+"?a+b:a*b);};
 try{
 for(let ch of expression){if(/[0-9]/.test(ch))values.push(+ch);else if(ch==="(")ops.push(ch);else if(ch===")"){while(ops.length&&ops.at(-1)!=="(")apply();if(ops.pop()!=="(")return null;}else{while(ops.length&&ops.at(-1)!=="("&&prec[ops.at(-1)]>=prec[ch])apply();ops.push(ch);}}
 while(ops.length){if(ops.at(-1)==="(")return null;apply();}
 return values.length===1?values[0]:null;
 }catch(_){return null;}
}
function brackets(){
 const s=states[4],expression=expressionFor(s),value=evaluate(expression),arr=[...baseExpression];
 let rendered='<div class="expr">';
 for(let i=0;i<=arr.length;i++){
 if(s.select!==null)rendered+='<button class="slot" data-gap="'+(i<=s.select?i:i-1)+'" title="Переставить сюда" aria-label="Вставить скобку здесь"></button>';
 if(i<arr.length)rendered+=["(",")"].includes(arr[i])?'<button class="token '+(s.select===i?"selected":"")+'" data-bracket="'+i+'">'+arr[i]+"</button>":'<span class="token">'+arr[i]+"</span>";
 }
 rendered+="</div>";
 return '<p class="muted">Выбери любую существующую скобку. Затем нажми на промежуток между символами, куда её перенести. Перемещается ровно одна скобка исходного выражения.</p>'+
 rendered+'<p class="metric">После перемещения: <strong>'+expression+'</strong> = '+(value===null?"неверная запись":value)+'</p>'+
 idhtml("cancelmove","Отменить перенос","ghost");
}
function checkBrackets(){const s=states[4],v=evaluate(expressionFor(s));return s.move&&v===34?{ok:true,text:"Равенство стало верным, перемещена ровно одна скобка."}:{ok:false,text:v===null?"Скобки пока стоят так, что выражение нельзя вычислить.":"Получилось "+v+", а нужно 34. Перемещай другую скобку или выбери иное место."};}

function cellsOf(r){let v=[];for(let y=0;y<(r.turn?3:2);y++)for(let x=0;x<(r.turn?2:3);x++)v.push([r.x+x,r.y+y]);return v;}
function canPlace(rect,prev){let cur=cellsOf(rect);if(cur.some(([x,y])=>x<0||x>=9||y<0||y>=9))return false;
 for(const r of prev)for(const [x,y] of cellsOf(r))for(const [a,b] of cur)if(Math.abs(x-a)<=1&&Math.abs(y-b)<=1)return false;return true;}
function packing(){
 const s=states[5],occupied={};s.rects.forEach((r,i)=>cellsOf(r).forEach(([x,y])=>occupied[x+","+y]=i));
 return '<p class="muted">Выбери ориентацию прямоугольника и нажми клетку его верхнего левого угла. Нажатие на уже размещённый прямоугольник удаляет его. Касаться углами нельзя.</p>'+
 '<div class="chip-row">'+idhtml("rotate",s.rotate?"Ориентация: 3×2 ↻":"Ориентация: 2×3 ↻","neutral")+
 idhtml("target:7","7 прямоугольников",s.target===7?"chip on":"chip")+idhtml("target:8","8 прямоугольников",s.target===8?"chip on":"chip")+'</div>'+
 '<div class="squareBoard" style="grid-template-columns:repeat(9,max-content)">'+Array.from({length:81},(_,i)=>{let x=i%9,y=Math.floor(i/9),owner=occupied[x+","+y];return '<button data-square="'+x+','+y+'" class="'+(owner!==undefined?"placed "+(owner%2?"second":""):"")+'" aria-label="Клетка '+(x+1)+', '+(y+1)+'">'+(owner!==undefined?(owner+1):"")+"</button>";}).join("")+'</div>'+
 '<div class="metric">Размещено <strong>'+s.rects.length+" из "+s.target+"</strong> прямоугольников. Поле 9×9.</div>";
}
function stepPacking(key){let s=states[5],p=key.split(",").map(Number),x=p[0],y=p[1];let owned=s.rects.findIndex(r=>cellsOf(r).some(([a,b])=>a===x&&b===y));
 if(owned>=0){s.rects.splice(owned,1);act();draw();return;}
 let r={x,y,turn:s.rotate};if(s.rects.length>=s.target||!canPlace(r,s.rects)){act(true);msg("Поставить здесь нельзя: выход за поле, касание другой фигуры или достигнут лимит.",false);return;}
 s.rects.push(r);act();draw();
}
function checkPacking(){let s=states[5];return s.rects.length===s.target?{ok:true,text:"На поле 9×9 размещено "+s.target+" прямоугольников без касания! Для доказательства минимальности отдельно докажите, что 8×8 не подходит."}:{ok:false,text:"Пока размещено "+s.rects.length+" из "+s.target+". Продолжайте построение."};}

function boat(){
 let s=states[6],x=s.x,buoys=[50,150,250],sum=buoys.reduce((a,b)=>a+Math.abs(x-b),0);
 return '<p class="muted">Перемещай катер по линии. Буйки на схеме стоят на 50, 150 и 250 м от старта — это допустимый пример исходных условий, а не заданные оригиналом координаты.</p>'+
 '<div class="line">'+[...buoys,450].map((v,i)=>'<div class="point" style="left:'+(v/450*100)+'%;background:'+(i===3?"#008e7d":"#e3a949")+'"><small>'+(i===3?"МАЯК":"буй")+'</small></div>').join("")+'</div>'+
 '<input type="range" class="track" id="boatRange" min="0" max="450" step="5" value="'+x+'" aria-label="Положение катера">'+
 '<div class="metric">Катер прошёл <strong>'+x+' м</strong><br>До маяка: '+(450-x)+' м<br>До трёх буйков: '+buoys.map(b=>Math.abs(x-b)).join(" + ")+" = <strong>"+sum+" м</strong><br>"+(x>250&&x<450?"Все три буйка уже позади.":"Нужно пройти все буйки, но не достигать маяка.")+"</div>";
}
function checkBoat(){const x=states[6].x;return x===300?{ok:true,text:"Верно: катер в 300 м от старта, до маяка 150 м, сумма расстояний до буйков снова 450."}:{ok:false,text:"Нужно быть за всеми тремя буйками, ещё не у маяка, и иметь сумму расстояний до буйков 450 м."};}

function calendar(){
 const s=states[7],buckets=seasonNames.map((name,i)=>'<div class="season" data-season="'+i+'"><h3>'+name+' · '+s.assign.filter(v=>v===i).length+'/3</h3>'+months.map((v,j)=>s.assign[j]===i?'<button class="month '+(s.selected===j?"selected":"")+'" data-month="'+j+'">'+v+'</button>':"").join("")+"</div>").join("");
 return '<p class="muted">Выбери месяц внизу, затем коснись нужного сезона. Переносить карточку можно и повторно. Можно вернуть её в «Не распределены».</p>'+
 '<div class="monthgrid">'+buckets+'</div>'+
 '<div class="season" data-season="-1"><h3>Не распределены</h3>'+months.map((v,j)=>s.assign[j]===-1?'<button class="month '+(s.selected===j?"selected":"")+'" data-month="'+j+'">'+v+'</button>':"").join("")+"</div>"+
 '<p class="muted">Сначала распределите 12 карточек, затем нажмите «Проверить». Можно выбрать месяц, а потом нажать название сезона.</p>';
}
function checkCalendar(){
 const s=states[7],counts=seasonNames.map((_,i)=>s.assign.filter(v=>v===i).length);
 if(counts.some(n=>n!==3))return {ok:false,text:"В каждом сезоне должно быть ровно три месяца."};
 let diff=months.filter((_,i)=>s.assign[i]!==monthCorrect[i]);
 return diff.length===0?{ok:true,text:"Верно! Все 12 месяцев распределены по сезонам согласно условиям."}:{ok:false,text:"Несколько ограничений пока нарушаются: проверь состав трёхмесячных групп и последовательность Навень–Ладень–Тарень–Ружень."};
}
function cards(){
 const s=states[8],v=s.cards.join("");return '<p class="muted">Выбери карточку, затем другую позицию для переноса. На компьютере карточки также можно перетаскивать.</p>'+
 '<div class="tiles">'+s.cards.map((c,i)=>'<button draggable="true" class="tile '+(s.selected===i?"active":"")+'" data-card="'+i+'">'+c+"</button>").join("")+'</div>'+
 '<div class="metric">Получилось 11-значное число: <strong>'+v+"</strong></div>";
}
function stepCards(i){let s=states[8];if(s.selected===null){s.selected=i;draw();return;}let from=s.selected;if(from!==i){let x=s.cards.splice(from,1)[0];s.cards.splice(i,0,x);act();}s.selected=null;draw();}
function checkCards(){return states[8].cards.join("")==="88080144432"?{ok:true,text:"Максимальное число собрано! Карточки: 8 | 80 | 801 | 44 | 432."}:{ok:false,text:"Пока последовательность не максимальна. Попробуйте переставить карточки с похожими первыми цифрами."};}

function color(){
 const s=states[9],count=colorCount(s.bits);
 return '<p class="muted">Нажми клетку для смены цвета. Считаются соседние пары с разным цветом по горизонтали и вертикали.</p>'+
 '<div class="colorBoard">'+s.bits.map((v,i)=>'<button class="'+(v?"on":"")+'" data-color="'+i+'" aria-label="Клетка '+(i+1)+', цвет '+(v?"синий":"белый")+'"></button>').join("")+"</div>"+
 '<div class="metric">Двухцветных соседств: <strong>'+count+' / 16</strong>. Всего соседних пар на поле: 24.</div>';
}
function colorCount(bits){let n=0;for(let y=0;y<4;y++)for(let x=0;x<4;x++){let i=y*4+x;if(x<3&&bits[i]!==bits[i+1])n++;if(y<3&&bits[i]!==bits[i+4])n++;}return n;}
function checkColor(){let c=colorCount(states[9].bits);return c===16?{ok:true,text:"Получилась допустимая раскраска: ровно 16 разноцветных соседств!"}:{ok:false,text:"Сейчас "+c+" разноцветных соседств, требуется ровно 16."};}

function applyCheck(){const result=[checkCut,checkBaskets,checkHex,checkDigits,checkBrackets,checkPacking,checkBoat,checkCalendar,checkCards,checkColor][current]();feedback(result);}
$("navigation").addEventListener("click",e=>{let el=e.target.closest("[data-nav]");if(el)selectTask(+el.dataset.nav);});
$("prev").addEventListener("click",()=>selectTask(current-1));$("next").addEventListener("click",()=>selectTask(current+1));
$("check").addEventListener("click",applyCheck);
$("reset").addEventListener("click",()=>{states[current]=init()[current];act();draw();});
$("hint").addEventListener("click",()=>{m().hints++;save();msg(tasks[current].hint);});
$("workarea").addEventListener("click",event=>{
 let el=event.target.closest("[data-paint],[data-cell],[data-basket],[data-action],[data-hex],[data-digit],[data-key],[data-bracket],[data-gap],[data-square],[data-season],[data-month],[data-card],[data-color]");
 if(!el)return;
 if(el.hasAttribute("data-paint")){states[0].paint=+el.dataset.paint;draw();return;}
 if(el.hasAttribute("data-cell")){setCell(el.dataset.cell);return;}
 if(el.hasAttribute("data-basket")){let i=+el.dataset.basket,delta=+el.dataset.delta,s=states[1];s.v[i]=Math.max(0,Math.min(100,s.v[i]+delta));act();draw();return;}
 if(el.hasAttribute("data-hex")){stepHex(el.dataset.hex);return;}
 if(el.hasAttribute("data-digit")){let i=+el.dataset.digit;if(i<3){states[3].sel=i;draw();}return;}
 if(el.hasAttribute("data-key")){let s=states[3];s.digits[s.sel]=+el.dataset.key;act();draw();return;}
 if(el.hasAttribute("data-bracket")){states[4].select=+el.dataset.bracket;states[4].move=null;draw();return;}
 if(el.hasAttribute("data-gap")){const s=states[4];if(s.select!==null){s.move={from:s.select,to:+el.dataset.gap};s.select=null;act();draw();}return;}
 if(el.hasAttribute("data-square")){stepPacking(el.dataset.square);return;}
 if(el.hasAttribute("data-month")){states[7].selected=+el.dataset.month;draw();return;}
 if(el.hasAttribute("data-season")){let s=states[7];if(s.selected!==null){s.assign[s.selected]=+el.dataset.season;s.selected=null;act();draw();}return;}
 if(el.hasAttribute("data-card")){stepCards(+el.dataset.card);return;}
 if(el.hasAttribute("data-color")){let i=+el.dataset.color;states[9].bits[i]^=1;act();draw();return;}
 if(el.hasAttribute("data-action")){
 const a=el.dataset.action;
 if(a.startsWith("trial:")){states[1].trial=+a.split(":")[1];draw();}
 if(a==="cancelmove"){states[4].move=null;states[4].select=null;act();draw();}
 if(a==="rotate"){states[5].rotate=!states[5].rotate;draw();}
 if(a.startsWith("target:")){states[5].target=+a.split(":")[1];states[5].rects=[];draw();}
 }
});
$("workarea").addEventListener("input",event=>{if(event.target.id==="boatRange"){states[6].x=+event.target.value;act();draw();}});
let dragged=null;
$("workarea").addEventListener("dragstart",e=>{let card=e.target.closest("[data-card]");if(card)dragged=+card.dataset.card;});
$("workarea").addEventListener("dragover",e=>{if(e.target.closest("[data-card]"))e.preventDefault();});
$("workarea").addEventListener("drop",e=>{let target=e.target.closest("[data-card]");if(target&&dragged!==null){e.preventDefault();states[8].selected=dragged;stepCards(+target.dataset.card);dragged=null;}});
$("stats").addEventListener("click",()=>{
 $("statsTable").innerHTML=tasks.map((t,i)=>{let x=m(i);return '<div class="statrow"><strong>'+(i+1)+'. '+t.title+'</strong> · '+(x.solved?"решено":"не завершено")+'<br>Действия: '+x.actions+'; неудачные попытки: '+x.invalid+'; проверки: '+x.checks+'; подсказки: '+x.hints+'; до первого действия: '+(x.firstActionMs===null?"—":(x.firstActionMs/1000).toFixed(1)+" с")+"</div>";}).join("");
 $("statsDialog").showModal();
});
$("closeStats").addEventListener("click",()=>$("statsDialog").close());
selectTask(0);
