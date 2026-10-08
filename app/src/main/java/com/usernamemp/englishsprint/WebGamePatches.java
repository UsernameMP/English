package com.usernamemp.englishsprint;

/** Host-side, non-destructive mobile adaptations for pinned third-party HTML5 games. */
final class WebGamePatches {
    private WebGamePatches() {}

    static final String COMMON = """
        (function(){
          if(window.__englishSprintMobileHost)return;
          window.__englishSprintMobileHost=true;
          var meta=document.querySelector('meta[name="viewport"]');
          if(!meta){meta=document.createElement('meta');meta.name='viewport';document.head.appendChild(meta);}
          meta.content='width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover';
          document.documentElement.style.overscrollBehavior='none';
          document.body.style.overscrollBehavior='none';
          document.documentElement.style.webkitTextSizeAdjust='100%';
          document.addEventListener('contextmenu',function(e){e.preventDefault();},true);
        })();
        """;

    static final String GAME_2048 = """
        (function(){
          if(window.__englishSprint2048)return;
          window.__englishSprint2048=true;
          var style=document.createElement('style');
          style.textContent=
            'html,body{height:100%!important;overflow:hidden!important;}'+
            'body{margin:0!important;padding:0!important;display:flex!important;align-items:center!important;justify-content:center!important;}'+
            '.game-explanation,.container>hr,.container>p,.game-intro,h1.title{display:none!important;}'+
            '.container{margin:0 auto!important;}'+
            '.heading{display:flex!important;justify-content:center!important;margin:0 0 4px!important;}'+
            '.scores-container{float:none!important;text-align:center!important;}'+
            '.above-game{display:flex!important;justify-content:center!important;margin:0!important;}'+
            '.restart-button{float:none!important;width:100%!important;box-sizing:border-box!important;margin:4px 0 6px!important;}'+
            '.game-container{margin-top:4px!important;}';
          document.head.appendChild(style);
          function fit(){
            var c=document.querySelector('.container');if(!c)return;
            c.style.zoom='1';
            var w=Math.max(1,c.offsetWidth),h=Math.max(1,c.scrollHeight);
            var s=Math.min((window.innerWidth-12)/w,(window.innerHeight-12)/h);
            c.style.zoom=String(Math.max(0.72,Math.min(1.7,s)));
          }
          fit();setTimeout(fit,80);window.addEventListener('resize',fit);
        })();
        """;

    static final String TOWER = """
        (function(){
          if(window.__englishSprintTower)return;
          window.__englishSprintTower=true;
          var style=document.createElement('style');
          style.textContent=
            '.landing{opacity:0!important;pointer-events:none!important;}'+
            '#es-tower-motion{position:fixed;right:10px;bottom:12px;z-index:9999;border:0;border-radius:18px;'+
            'padding:9px 13px;background:rgba(17,24,39,.84);color:#fff;font:700 13px sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.25);}';
          document.head.appendChild(style);

          var motion='slow';
          function installMotion(){
            try{
              if(!window.game||!game.getVariable)return false;
              var opt=game.getVariable('GAME_USER_OPTION');
              if(!opt)return false;
              opt.hookSpeed=function(successCount){
                if(Number(successCount)<1)return 0;
                var divisor;
                if(motion==='fast') divisor=Number(successCount)<10?235:(Number(successCount)<20?205:180);
                else divisor=Number(successCount)<10?520:(Number(successCount)<20?465:410);
                return Math.sin(performance.now()/divisor);
              };
              return true;
            }catch(e){return false;}
          }

          var button=document.createElement('button');
          button.id='es-tower-motion';
          button.textContent='Swing: slow';
          function toggle(e){
            if(e){e.preventDefault();e.stopPropagation();}
            motion=motion==='slow'?'fast':'slow';
            button.textContent=motion==='slow'?'Swing: slow':'Swing: fast';
            installMotion();
          }
          button.addEventListener('click',toggle);
          button.addEventListener('touchstart',function(e){e.stopPropagation();},{passive:true});
          document.body.appendChild(button);

          var attempts=0;
          function enterGame(){
            attempts++;
            installMotion();
            var landing=document.querySelector('.landing');
            var start=document.getElementById('start');
            if(start&&landing&&getComputedStyle(landing).display!=='none'){
              try{start.click();}catch(e){}
            }
            if((window.gameStart&&installMotion())||attempts>120)clearInterval(timer);
          }
          var timer=setInterval(enterGame,50);
          enterGame();
        })();
        """;

    static final String SUIKA = """
        (function(){
          if(window.__englishSprintSuika)return;
          window.__englishSprintSuika=true;
          var style=document.createElement('style');
          style.textContent=
            'html,body{width:100%!important;height:100%!important;overflow:hidden!important;}'+
            'body{margin:0!important;display:flex!important;align-items:center!important;justify-content:center!important;}'+
            '.container{width:400px!important;height:600px!important;max-width:none!important;margin:0!important;gap:4px!important;}'+
            '#app{width:400px!important;height:500px!important;}'+
            '#fruit-info{width:80px!important;height:80px!important;}'+
            '.title{font-size:1rem!important;}';
          document.head.appendChild(style);
          function fit(){
            var c=document.querySelector('.container');if(!c)return;
            c.style.zoom='1';
            var s=Math.min((window.innerWidth-8)/400,(window.innerHeight-8)/600);
            c.style.zoom=String(Math.max(0.55,Math.min(1.35,s)));
          }
          fit();setTimeout(fit,80);window.addEventListener('resize',fit);
        })();
        """;

    static final String COZY_CAFE = """
        (function(){
          if(window.__englishSprintCozyFit)return;
          window.__englishSprintCozyFit=true;
          var c=document.getElementById('gameCanvas');if(!c)return;
          document.documentElement.style.overflow='hidden';
          document.body.style.cssText+=';display:block!important;position:relative!important;width:100vw!important;height:100vh!important;overflow:hidden!important;background:#151515!important;';
          c.style.position='absolute';
          c.style.margin='0';
          c.style.maxWidth='none';
          function fit(){
            var vw=window.innerWidth,vh=window.innerHeight;
            var scale=vw/1024;
            var renderedW=1024*scale;
            var renderedH=768*scale;
            c.style.width=renderedW+'px';
            c.style.height=renderedH+'px';
            c.style.left=Math.max(0,(vw-renderedW)/2)+'px';
            c.style.top=Math.max(0,(vh-renderedH)/2)+'px';
          }
          fit();setTimeout(fit,80);window.addEventListener('resize',fit);
        })();
        """;

    static final String BUBBLE_SHOOTER = """
        (function(){
          if(window.__englishSprintBubble)return;
          window.__englishSprintBubble=true;

          var style=document.createElement('style');
          style.textContent=
            'html,body{width:100%!important;height:100%!important;margin:0!important;overflow:hidden!important;background:#070b14!important;}'+
            'body{position:relative!important;}'+
            '#viewport{position:absolute!important;left:50%!important;bottom:4px!important;top:auto!important;'+
            'width:106vw!important;height:auto!important;max-width:none!important;margin:0!important;transform:translateX(-50%)!important;}';
          document.head.appendChild(style);

          var proto=CanvasRenderingContext2D.prototype;
          if(!proto.__englishSprintFillText){
            proto.__englishSprintFillText=proto.fillText;
            proto.fillText=function(text){
              var value=String(text||'');
              if(value.indexOf('Bubble Shooter Example')===0||value.indexOf('Fps:')===0)return;
              return proto.__englishSprintFillText.apply(this,arguments);
            };
          }
          if(!proto.__englishSprintDrawImage){
            proto.__englishSprintDrawImage=proto.drawImage;
            var palette=['#ff4f87','#45d7e8','#7c6cff','#ffd447','#45d483','#3987ff','#ff934d'];
            proto.drawImage=function(img){
              var src='';
              try{src=String(img&&img.src||'');}catch(e){}
              if(src.indexOf('bubble-sprites.png')>=0&&arguments.length===9){
                var sx=Number(arguments[1])||0;
                var dx=Number(arguments[5])||0,dy=Number(arguments[6])||0;
                var dw=Number(arguments[7])||40,dh=Number(arguments[8])||40;
                var idx=Math.max(0,Math.min(palette.length-1,Math.round(sx/40)));
                var cx=dx+dw/2,cy=dy+dh/2,r=Math.min(dw,dh)*.45;
                this.save();
                this.shadowColor='rgba(15,23,42,.28)';
                this.shadowBlur=Math.max(2,r*.18);
                this.shadowOffsetY=Math.max(1,r*.08);
                var g=this.createRadialGradient(cx-r*.32,cy-r*.38,r*.08,cx,cy,r);
                g.addColorStop(0,'#ffffff');
                g.addColorStop(.16,palette[idx]);
                g.addColorStop(1,palette[idx]);
                this.fillStyle=g;
                this.beginPath();this.arc(cx,cy,r,0,Math.PI*2);this.fill();
                this.shadowColor='transparent';
                this.lineWidth=Math.max(1.5,r*.08);
                this.strokeStyle='rgba(255,255,255,.72)';
                this.stroke();
                this.fillStyle='rgba(255,255,255,.65)';
                this.beginPath();this.arc(cx-r*.28,cy-r*.30,r*.15,0,Math.PI*2);this.fill();
                this.restore();
                return;
              }
              return proto.__englishSprintDrawImage.apply(this,arguments);
            };
          }
        })();
        """;


}
