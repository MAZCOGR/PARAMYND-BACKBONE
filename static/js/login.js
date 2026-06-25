/* ════════════════════════════════════════════════
     1. SOUMISSION DU FORMULAIRE ET VALIDATION
     ════════════════════════════════════════════════ */
  const form = document.getElementById('login-form');
  const inputs = form.querySelectorAll('input[required]');

  function validateInput(input) {
    let isValid = true;
    const val = input.value.trim();

    if (!val) {
      isValid = false;
    } else if (input.type === 'email') {
      isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
    }

    if (!isValid) {
      input.classList.add('invalid');
    } else {
      input.classList.remove('invalid');
    }
    return isValid;
  }

  inputs.forEach(input => {
    input.addEventListener('input', () => {
      if (input.classList.contains('invalid')) {
        validateInput(input);
      }
    });
    input.addEventListener('blur', () => {
      validateInput(input);
    });
  });

  form.addEventListener('submit', function(e) {
    let formValid = true;
    inputs.forEach(input => {
      if(!validateInput(input)) formValid = false;
    });

    if (!formValid) {
      e.preventDefault();
      return;
    }
    
    const btn = document.getElementById('login-btn');
    btn.disabled = true;
    btn.innerHTML = `<span style="display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;margin-right:8px;animation: spin 1s linear infinite;vertical-align:middle;"></span> Connexion...`;
  });

  /* ════════════════════════════════════════════════
     2. ANIMATION BRAIN CANVAS (ARRIÈRE-PLAN)
     ════════════════════════════════════════════════ */
  (function () {
    const canvas = document.getElementById('brainCanvas');
    if(!canvas) return;
    const ctx = canvas.getContext('2d');

    const P  = [124, 92, 252];
    const T  = [6, 214, 160];

    function rgb(c,a)    { return \`rgba(\${c[0]},\${c[1]},\${c[2]},\${+a.toFixed(3)})\`; }
    function mix(a,b,t)  { return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]; }
    function lp(a,b,t)   { return a+(b-a)*t; }
    function eo(t,e=3)   { return 1-Math.pow(1-Math.min(t,1),e); }
    function clamp(v,lo,hi){ return Math.max(lo,Math.min(hi,v)); }
    function rand(a,b)   { return a+Math.random()*(b-a); }

    let W, H;
    function resize() {
      W = canvas.width  = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }

    const PH_BANG   = 0;
    const PH_FLY    = 1000;
    const PH_SETTLE = 2000;

    let nodes=[], rings=[], startT=null, raf;
    let mouse = {x:-9999,y:-9999};

    function connR() { return Math.hypot(W,H)*0.15; }

    function mkNode() {
      const pad=50;
      const tx=rand(pad,W-pad), ty=rand(pad,H-pad);
      const cx=W*.5, cy=H*.5;
      const ang=Math.atan2(ty-cy,tx-cx)+rand(-0.35,0.35);
      const spd=rand(5,14);
      return {
        x:cx, y:cy,
        vx:Math.cos(ang)*spd, vy:Math.sin(ang)*spd,
        tx, ty,
        r:rand(1.4,3.8), hue:Math.random(),
        ph:rand(0,Math.PI*2), phSpd:rand(0.007,0.022),
        bright:rand(0.5,1.0),
        wAng:rand(0,Math.PI*2), wSpd:rand(0.0003,0.0008),
        trail:[], isPlanet:false,
      };
    }

    function init(){
      nodes=Array.from({length:140},mkNode);
      startT=null;
      const pCount=7;
      const pIdx=[...Array(nodes.length).keys()].sort(()=>Math.random()-.5).slice(0,pCount);
      pIdx.forEach((i,k)=>{
        const n=nodes[i];
        n.isPlanet=true;
        n.r=rand(4.5,8.5);
        n.bright=1.0;
        const ang2=(k/pCount)*Math.PI*2+rand(-.3,.3);
        const dist=Math.min(W,H)*0.32;
        n.tx=W*.5+Math.cos(ang2)*dist;
        n.ty=H*.5+Math.sin(ang2)*dist;
      });
      for(const n of nodes) { n.x = n.tx; n.y = n.ty; }
    }

    function draw(ts){
      if(!startT)startT=ts;
      const t=ts-startT + 5000;
      const cx=W*.5,cy=H*.5;
      ctx.clearRect(0,0,W,H);

      const tE=t-PH_BANG;
      const fly=clamp(tE/(PH_FLY-PH_BANG),0,1);
      const setP=clamp((t-PH_FLY)/(PH_SETTLE-PH_FLY),0,1);

      for(const n of nodes){
        n.ph+=n.phSpd;
        
        if(n.trail.length>0) n.trail.shift();
        n.wAng+=n.wSpd*(1+.3*Math.sin(n.ph));
        const wF = n.isPlanet ? 0.003 : 0.005;
        n.vx+=Math.cos(n.wAng)*wF;
        n.vy+=Math.sin(n.wAng)*wF;
        
        if(!n.isPlanet){
          let nearP=null,nearD2=Infinity;
          for(const p of nodes){
            if(!p.isPlanet)continue;
            const gx=p.x-n.x,gy=p.y-n.y,gd2=gx*gx+gy*gy;
            if(gd2<nearD2){nearD2=gd2;nearP=p;}
          }
          if(nearP){
            const gd=Math.sqrt(nearD2)||1;
            const gravStr=0.003;
            n.vx+=(nearP.x-n.x)/gd*gravStr;
            n.vy+=(nearP.y-n.y)/gd*gravStr;
            n.vx += -(nearP.y-n.y)/gd * 0.006;
            n.vy += (nearP.x-n.x)/gd * 0.006;
          }
        } else {
          const cdx = cx - n.x, cdy = cy - n.y, cd = Math.hypot(cdx, cdy) || 1;
          if (cd > Math.min(W,H)*0.3) {
            n.vx += (cdx/cd) * 0.002;
            n.vy += (cdy/cd) * 0.002;
          }
        }
        
        const mdx=n.x-mouse.x,mdy=n.y-mouse.y,md2=mdx*mdx+mdy*mdy;
        if(md2<22000){const f=.6/Math.max(md2,1);n.vx+=mdx*f;n.vy+=mdy*f;}
        
        const pad=40;
        if(n.x<pad)n.vx+=(pad-n.x)*.01;
        if(n.x>W-pad)n.vx-=(n.x-(W-pad))*.01;
        if(n.y<pad)n.vy+=(pad-n.y)*.01;
        if(n.y>H-pad)n.vy-=(n.y-(H-pad))*.01;
        
        n.vx*=.991;n.vy*=.991;
        n.x+=n.vx;n.y+=n.vy;
      }

      for(const n of nodes){
        if(!n.trail.length)continue;
        const col=mix(P,T,n.hue);
        for(let i=0;i<n.trail.length;i++){
          const tp=i/n.trail.length;
          ctx.beginPath();
          ctx.arc(n.trail[i].x,n.trail[i].y,n.r*tp*.55,0,Math.PI*2);
          ctx.fillStyle=rgb(col,tp*.45*(1-fly*.4));
          ctx.fill();
        }
      }

      const cA=lp(0,0.13,eo(setP,3));
      const cR=connR();
      for(let i=0;i<nodes.length;i++){
        const a=nodes[i];
        for(let j=i+1;j<nodes.length;j++){
          const b=nodes[j];
          const dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy;
          if(d2>cR*cR)continue;
          const d=Math.sqrt(d2);
          ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
          ctx.strokeStyle=rgb(mix(P,T,(a.hue+b.hue)*.5),cA*(1-d/cR));
          ctx.lineWidth=.7;ctx.stroke();
        }
      }

      for(const n of nodes){
        const col=mix(P,T,n.hue);
        const pul=.55+.45*Math.sin(n.ph);
        const r=n.r*(.88+.12*pul);
        const al=n.bright*pul*.9;
        if(n.isPlanet){
          const g2=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*18);
          g2.addColorStop(0,rgb(col,al*.35));g2.addColorStop(.5,rgb(col,al*.1));g2.addColorStop(1,rgb(col,0));
          ctx.beginPath();ctx.arc(n.x,n.y,r*18,0,Math.PI*2);
          ctx.fillStyle=g2;ctx.fill();
          ctx.beginPath();ctx.arc(n.x,n.y,r*1.6,0,Math.PI*2);
          ctx.fillStyle=rgb(col,al*.9);ctx.fill();
          ctx.beginPath();ctx.arc(n.x,n.y,r*1.6,0,Math.PI*2);
          ctx.strokeStyle=rgb(col,.25);ctx.lineWidth=r*.6;ctx.stroke();
        }else{
          const g=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*6);
          g.addColorStop(0,rgb(col,al*.4));g.addColorStop(1,rgb(col,0));
          ctx.beginPath();ctx.arc(n.x,n.y,r*6,0,Math.PI*2);
          ctx.fillStyle=g;ctx.fill();
          ctx.beginPath();ctx.arc(n.x,n.y,r,0,Math.PI*2);
          ctx.fillStyle=rgb(col,al);ctx.fill();
        }
      }
      
      raf=requestAnimationFrame(draw);
    }

    document.addEventListener('mousemove',e=>{
      mouse.x=e.clientX;mouse.y=e.clientY;
    },{passive:true});
    document.addEventListener('mouseleave',()=>{mouse.x=-9999;mouse.y=-9999;});

    function start(){resize();init();raf=requestAnimationFrame(draw);}
    window.addEventListener('resize',()=>{cancelAnimationFrame(raf);start();});
    document.addEventListener('visibilitychange',()=>{
      if(document.hidden)cancelAnimationFrame(raf);
      else{startT=null;raf=requestAnimationFrame(draw);}
    });
    start();
  })();

