// ════════════════════════════════════════════════
//  BIG BANG → UNIVERSE — Brain Canvas Animation
// ════════════════════════════════════════════════
(function () {
  const canvas = document.getElementById('brainCanvas');
  const ctx    = canvas.getContext('2d');

  const P  = [124, 92, 252];
  const T  = [6, 214, 160];
  const W2 = [230, 220, 255];

  function rgb(c,a)    { return `rgba(${c[0]},${c[1]},${c[2]},${+a.toFixed(3)})`; }
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

  const PH_BANG   = 900;
  const PH_FLY    = 3400;
  const PH_SETTLE = 5000;

  let nodes=[], signals=[], rings=[], flash=0, startT=null, raf;
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

  function neighbours(i) {
    const n=nodes[i],r2=connR()*connR(),out=[];
    for(let j=0;j<nodes.length;j++){
      if(i===j)continue;
      const m=nodes[j],dx=m.x-n.x,dy=m.y-n.y;
      if(dx*dx+dy*dy<r2)out.push(j);
    }
    return out.slice(0,5);
  }
  function spawnSig(){
    const fi=(Math.random()*nodes.length)|0;
    const nb=neighbours(fi);
    if(!nb.length)return;
    signals.push({fi,ti:nb[(Math.random()*nb.length)|0],t:0,hue:Math.random()});
  }

  function init(){
    nodes=Array.from({length:140},mkNode);
    signals=[];rings=[];flash=0;startT=null;
    /* designate 7 planet nodes — larger, spread evenly around canvas */
    const pCount=7;
    const pIdx=[...Array(nodes.length).keys()].sort(()=>Math.random()-.5).slice(0,pCount);
    pIdx.forEach((i,k)=>{
      const n=nodes[i];
      n.isPlanet=true;
      n.r=rand(4.5,8.5);
      n.bright=1.0;
      /* planet targets: spread around canvas in a ring at ~70% radius */
      const ang2=(k/pCount)*Math.PI*2+rand(-.3,.3);
      const dist=Math.min(W,H)*0.32;
      n.tx=W*.5+Math.cos(ang2)*dist;
      n.ty=H*.5+Math.sin(ang2)*dist;
    });
  }

  function draw(ts){
    if(!startT)startT=ts;
    const t=ts-startT;
    const cx=W*.5,cy=H*.5;
    ctx.clearRect(0,0,W,H);

    /* ── SINGULARITY ── */
    if(t<PH_BANG){
      const p=t/PH_BANG;
      const pul=.5+.5*Math.sin(p*Math.PI*7);
      const r1=3+pul*10,r2=15+pul*60;
      const gO=ctx.createRadialGradient(cx,cy,0,cx,cy,r2);
      gO.addColorStop(0,rgb(P,.5*pul));
      gO.addColorStop(.5,rgb(T,.2*pul));
      gO.addColorStop(1,rgb(P,0));
      ctx.beginPath();ctx.arc(cx,cy,r2,0,Math.PI*2);
      ctx.fillStyle=gO;ctx.fill();
      const gC=ctx.createRadialGradient(cx,cy,0,cx,cy,r1);
      gC.addColorStop(0,rgb(W2,1));
      gC.addColorStop(.4,rgb(P,.95));
      gC.addColorStop(1,rgb(P,0));
      ctx.beginPath();ctx.arc(cx,cy,r1,0,Math.PI*2);
      ctx.fillStyle=gC;ctx.fill();
      if(t>PH_BANG*.82){
        flash=clamp((t-PH_BANG*.82)/(PH_BANG*.18),0,1);
        ctx.fillStyle=`rgba(230,220,255,${(flash*.8).toFixed(3)})`;
        ctx.fillRect(0,0,W,H);
      }
    }

    /* ── EXPANSION + SETTLE + DRIFT ── */
    if(t>=PH_BANG){
      const tE=t-PH_BANG;
      const fly=clamp(tE/(PH_FLY-PH_BANG),0,1);
      const setP=clamp((t-PH_FLY)/(PH_SETTLE-PH_FLY),0,1);
      const done=t>PH_SETTLE;

      flash=clamp(flash-0.018,0,1);
      if(flash>0){
        ctx.fillStyle=`rgba(230,220,255,${(flash*.65).toFixed(3)})`;
        ctx.fillRect(0,0,W,H);
      }

      /* shockwave rings removed */

      /* physics */
      for(const n of nodes){
        n.ph+=n.phSpd;
        if(t < PH_FLY){
          /* fly/expansion phase: smooth ease interpolation from center to target */
          const prevX = n.x, prevY = n.y;
          const E = 1 - Math.pow(1 - fly, 4); // easeOutQuart
          n.x = cx + (n.tx - cx) * E;
          n.y = cy + (n.ty - cy) * E;
          n.vx = n.x - prevX;
          n.vy = n.y - prevY;
          n.trail.push({x:n.x,y:n.y});
          if(n.trail.length>14)n.trail.shift();
        }else{
          /* drift phase */
          if(n.trail.length>0) n.trail.shift();
          /* slow wander */
          n.wAng+=n.wSpd*(1+.3*Math.sin(n.ph));
          const wF = n.isPlanet ? 0.003 : 0.005;
          n.vx+=Math.cos(n.wAng)*wF;
          n.vy+=Math.sin(n.wAng)*wF;
          /* planet gravity: non-planets attracted to nearest planet */
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
              /* orbit effect */
              n.vx += -(nearP.y-n.y)/gd * 0.006;
              n.vy += (nearP.x-n.x)/gd * 0.006;
            }
          } else {
            /* planets gently pulled to center so they don't wander off */
            const cdx = cx - n.x, cdy = cy - n.y, cd = Math.hypot(cdx, cdy) || 1;
            if (cd > Math.min(W,H)*0.3) {
              n.vx += (cdx/cd) * 0.002;
              n.vy += (cdy/cd) * 0.002;
            }
          }
          
          /* mouse repulsion */
          const mdx=n.x-mouse.x,mdy=n.y-mouse.y,md2=mdx*mdx+mdy*mdy;
          if(md2<22000){const f=.6/Math.max(md2,1);n.vx+=mdx*f;n.vy+=mdy*f;}
          
          /* edge boundary — soft bounce */
          const pad=40;
          if(n.x<pad)n.vx+=(pad-n.x)*.01;
          if(n.x>W-pad)n.vx-=(n.x-(W-pad))*.01;
          if(n.y<pad)n.vy+=(pad-n.y)*.01;
          if(n.y>H-pad)n.vy-=(n.y-(H-pad))*.01;
          
          n.vx*=.991;n.vy*=.991;
          n.x+=n.vx;n.y+=n.vy;
        }
      }

      /* comet trails */
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

      /* connections */
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

      /* signals removed — clean cosmic drift */

      /* nodes */
      for(const n of nodes){
        const col=mix(P,T,n.hue);
        const pul=.55+.45*Math.sin(n.ph);
        const r=n.r*(.88+.12*pul);
        const al=n.bright*pul*.9;
        if(n.isPlanet){
          /* planet: large soft halo + bright core + outer ring */
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

// ════════════════════════════════════════════════
//  NAV + REVEAL + SMOOTH SCROLL
// ════════════════════════════════════════════════
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('stuck', window.scrollY > 20);
}, { passive: true });

const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); observer.unobserve(e.target); } });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  });
});
