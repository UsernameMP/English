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
          style.textContent='.landing{opacity:0!important;pointer-events:none!important;}';
          document.head.appendChild(style);
          var attempts=0;
          function enterGame(){
            attempts++;
            var landing=document.querySelector('.landing');
            var start=document.getElementById('start');
            if(start && landing && getComputedStyle(landing).display!=='none'){
              try{start.click();}catch(e){}
            }
            if(window.gameStart || attempts>100){clearInterval(timer);}
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
          if(window.__englishSprintCozyCamera)return;
          window.__englishSprintCozyCamera=true;
          var c=document.getElementById('gameCanvas');if(!c)return;
          document.documentElement.style.overflow='hidden';
          document.body.style.cssText+=';display:block!important;position:relative!important;width:100vw!important;height:100vh!important;overflow:hidden!important;';
          c.style.position='absolute';
          c.style.margin='0';
          c.style.maxWidth='none';
          function currentState(){
            try{return Number(gameState)||0;}catch(e){return 0;}
          }
          function fit(){
            var vw=window.innerWidth,vh=window.innerHeight;
            var scale=vh/768;
            var renderedW=1024*scale;
            var state=currentState();
            var focus=state===0?160:(state===1?770:(state===2?330:512));
            var left=vw/2-focus*scale;
            var minLeft=vw-renderedW;
            left=Math.min(0,Math.max(minLeft,left));
            c.style.width=renderedW+'px';
            c.style.height=(768*scale)+'px';
            c.style.left=left+'px';
            c.style.top='0px';
          }
          fit();window.addEventListener('resize',fit);setInterval(fit,120);
        })();
        """;

    static final String BUBBLE_SHOOTER = """
        (function(){
          if(window.__englishSprintBubble)return;
          window.__englishSprintBubble=true;
          var proto=CanvasRenderingContext2D.prototype;
          if(!proto.__englishSprintFillText){
            proto.__englishSprintFillText=proto.fillText;
            proto.fillText=function(text){
              var value=String(text||'');
              if(value.indexOf('Bubble Shooter Example')===0 || value.indexOf('Fps:')===0)return;
              return proto.__englishSprintFillText.apply(this,arguments);
            };
          }
        })();
        """;
}
