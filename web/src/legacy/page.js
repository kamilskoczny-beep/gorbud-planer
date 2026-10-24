
(function(){
const KEYP=(window.PLANER&&window.PLANER.key)||'p11';
const MODEL = JSON.parse(document.getElementById('modelData').textContent);
const VARIANTS = JSON.parse(document.getElementById('variantData').textContent);
const FLOORS = ['piwnica','parter','pietro1','poddasze'];
const UNITS = VARIANTS.units; // {id:{name,color}}
const svg = document.getElementById('svg');
const NS = 'http://www.w3.org/2000/svg';
let floor = 'pietro1';
const sel = {}; FLOORS.forEach(f=>{ const vs=VARIANTS.floors[f]||[]; sel[f]=vs.length?vs[0].id:null; });
try{ const h=location.hash.replace('#',''); if(FLOORS.includes(h)) floor=h; const sv=JSON.parse(localStorage.getItem(KEYP+'.variants')||'{}'); FLOORS.forEach(f=>{ if(sv[f] && (VARIANTS.floors[f]||[]).some(x=>x.id===sv[f])) sel[f]=sv[f]; }); }catch(e){}
function curVariant(f){ const vs=VARIANTS.floors[f]||[]; return vs.find(v=>v.id===sel[f])||null; }
function visibleItems(f){ return project[f].items.filter(it=>!it.v || it.v===sel[f]); }
const layerDefs = [
  ['walls','Ściany','var(--ink)',true],['windows','Okna','var(--win)',true],['doors','Drzwi','var(--door)',true],
  ['stairs','Schody','var(--stair)',true],['fixtures','Wyposażenie','var(--fix)',false],['sills','Parapety','var(--fix)',false],
  ['rooms','Pomieszczenia (etykiety + strefy)','var(--accent)',true],['dwgtext','Opisy z inwentaryzacji','var(--dim)',false],
  ['dims','Linie wymiarowe','var(--dim)',false],['skosy','Skosy poddasza (załamanie sufitu, h = 1,90 / 2,20)','var(--demo)',true],['project','Projekt (nowe elementy: ściany, drzwi)','var(--new)',true],['rfill','Pomieszczenia projektowane – kolor (podkład)','var(--new)',true],['rline','Pomieszczenia projektowane – obrys przerywany','var(--new)',false],['rlbl','Pomieszczenia projektowane – nazwa i powierzchnia','var(--new)',true],['furn','Meble (projekt)','var(--muted)',true],['sketch','Szkic i uwagi (dla Claude)','var(--mark)',true],['autodim','Wymiary automatyczne (pomieszczenia, przejścia)','var(--accent)',true]
];
const layerOn = {}; layerDefs.forEach(l=>layerOn[l[0]]=l[3]);
try{ const s=JSON.parse(localStorage.getItem(KEYP+'.layers')||'{}'); Object.keys(s).forEach(k=>{ if(k in layerOn) layerOn[k]=s[k]; }); }catch(e){}

// ---------- project state (per floor) ----------
const project = {}; FLOORS.forEach(f=>project[f]={items:[]});
const hist = {}; FLOORS.forEach(f=>hist[f]=[]);
let db=null, dbReady=false, saveTimer=null, remoteApplying=false;
let selectedId=null, tool='select', draft=null, hoverPt=null, roomIdx=0;

// ---------- view ----------
let view = {x:0,y:0,w:30000,h:25000}; // in mm, y-up; svg viewBox uses flipped coords
function fitFloor(){
  const b = MODEL.floors[floor].bbox; const m=1500;
  const W=svg.clientWidth||800, H=svg.clientHeight||600;
  let w=b[2]-b[0]+2*m, h=b[3]-b[1]+2*m;
  if (w/h < W/H) w = h*W/H; else h = w*H/W;
  const cx=(b[0]+b[2])/2, cy=(b[1]+b[3])/2;
  view={x:cx-w/2,y:cy-h/2,w,h}; applyView();
}
function applyView(){ svg.setAttribute('viewBox', `${view.x} ${-(view.y+view.h)} ${view.w} ${view.h}`); updateScaleText(); }
function updateScaleText(){ const pxPerM = (svg.clientWidth||1)/ (view.w/1000); document.getElementById('coord').dataset.scale = pxPerM.toFixed(0); }
function svgPoint(evt){ const pt=svg.createSVGPoint(); pt.x=evt.clientX; pt.y=evt.clientY; const p=pt.matrixTransform(svg.getScreenCTM().inverse()); return {x:p.x, y:-p.y}; }
function mmPerPx(){ return view.w/(svg.clientWidth||1); }

// ---------- build static layers ----------
const root = document.createElementNS(NS,'g'); root.setAttribute('transform','scale(1,-1)'); svg.appendChild(root);
const gl = {}; // layer groups
['grid','zones','rfill','walls','windows','doors','stairs','sills','fixtures','dims','skosy','dwgtext','roomlbl','project','rline','rlbl','furn','rhit','sketch','autodim','draft','ui'].forEach(k=>{ const g=document.createElementNS(NS,'g'); g.dataset.layer=k; root.appendChild(g); gl[k]=g; });

function el(tag, attrs, parent){ const e=document.createElementNS(NS,tag); for(const k in attrs) e.setAttribute(k, attrs[k]); (parent||root).appendChild(e); return e; }
function segPath(s){
  if (s.k==='l') return 'M'+s.p.map(q=>q[0]+' '+q[1]).join('L');
  if (s.k==='a'){ let a0=s.a0, a1=s.a1; if(a1<a0) a1+=Math.PI*2; const x0=s.c[0]+s.r*Math.cos(a0), y0=s.c[1]+s.r*Math.sin(a0), x1=s.c[0]+s.r*Math.cos(a1), y1=s.c[1]+s.r*Math.sin(a1); const large=(a1-a0)>Math.PI?1:0; return `M${x0} ${y0}A${s.r} ${s.r} 0 ${large} 1 ${x1} ${y1}`; }
  if (s.k==='c') return `M${s.c[0]-s.r} ${s.c[1]}a${s.r} ${s.r} 0 1 0 ${2*s.r} 0a${s.r} ${s.r} 0 1 0 ${-2*s.r} 0`;
  return '';
}
// ---------- poddasze: model wysokości (skosy) ----------
const ATTIC=VARIANTS.attic||null;
function parseH(t){ if(!t) return null; const m=/=\s*(\d+)\s*cm/.exec(t); return m?parseInt(m[1])*10:null; }
function pointInPoly(p,poly){ let c=false; for(let i=0,j=poly.length-1;i<poly.length;j=i++){ const a=poly[i],b=poly[j]; if(((a[1]>p[1])!==(b[1]>p[1])) && (p[0] < (b[0]-a[0])*(p[1]-a[1])/((b[1]-a[1])||1e-9)+a[0])) c=!c; } return c; }
function flatH(x,y){ const F=MODEL.floors[floor]; for (const r of (F.rooms||[])) if(r.poly && pointInPoly([x,y],r.poly)){ const h=parseH(r.h); if(h) return h; } return FLOOR_H[floor]||2780; }
function heightAt(x,y){ if(!ATTIC||floor!==ATTIC.floor) return null; let h=flatH(x,y);
  for (const pl of ATTIC.planes){ const [a,b]=pl.line; const vx=b[0]-a[0], vy=b[1]-a[1]; const L2=vx*vx+vy*vy||1; const u=((x-a[0])*vx+(y-a[1])*vy)/L2; if(u<0||u>1) continue; const d=(x-a[0])*pl.dir[0]+(y-a[1])*pl.dir[1]; if(d<=0 || d>(pl.h0-(ATTIC.hmin||900))/pl.tan+450) continue; const hh=pl.h0-pl.tan*d; if(hh<h) h=hh; }
  return Math.max(0,Math.round(h)); }
function roomHeightStats(it){ // próbkowanie co 150 mm: h min/max, pow. użytkowa wg PN-ISO 9836 (100% h≥2,20; 50% 1,40–2,20; 0 poniżej)
  if(!ATTIC||floor!==ATTIC.floor) return null; const xs=it.pts.map(q=>q[0]), ys=it.pts.map(q=>q[1]); const st=150; let n=0, use=0, hmin=1e9, hmax=0;
  for (let x=Math.min(...xs)+st/2; x<Math.max(...xs); x+=st) for (let y=Math.min(...ys)+st/2; y<Math.max(...ys); y+=st){ if(!pointInPoly([x,y],it.pts)) continue; if((it.holes||[]).some(h=>pointInPoly([x,y],h))) continue; const h=heightAt(x,y); n++; if(h<hmin) hmin=h; if(h>hmax) hmax=h; use+=h>=2200?1:(h>=1400?0.5:0); }
  if(!n) return null; return {hmin,hmax,area:n*st*st,use:use*st*st}; }
function drawSlopes(){ gl.skosy.innerHTML=''; if(!ATTIC||floor!==ATTIC.floor) return;
  for (const pl of ATTIC.planes){ const [a,b]=pl.line; const L=Math.hypot(b[0]-a[0],b[1]-a[1]); const m=[(a[0]+b[0])/2,(a[1]+b[1])/2]; const horiz=Math.abs(b[1]-a[1])<Math.abs(b[0]-a[0]);
    el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'var(--demo)','stroke-width':28,'stroke-dasharray':'300 150'},gl.skosy);
    for (const [hh,col,dash] of [[2200,'var(--accent)','120 120'],[1900,'#e07a1f','200 100']]){ if(pl.h0<=hh) continue; const d=(pl.h0-hh)/pl.tan; const a2=[a[0]+pl.dir[0]*d,a[1]+pl.dir[1]*d], b2=[b[0]+pl.dir[0]*d,b[1]+pl.dir[1]*d]; el('line',{x1:a2[0],y1:a2[1],x2:b2[0],y2:b2[1],stroke:col,'stroke-width':22,'stroke-dasharray':dash},gl.skosy); if(L>1500){ const mm2=[(a2[0]+b2[0])/2,(a2[1]+b2[1])/2]; const g=el('g',{transform:`translate(${mm2[0]+(horiz?0:140)} ${mm2[1]+(horiz?140:0)}) ${horiz?'':'rotate(90)'} scale(1,-1)`},gl.skosy); const t=el('text',{x:0,y:0,'text-anchor':'middle','font-size':130,fill:col,class:'lbl-ar'},g); t.textContent='h = '+(hh/1000).toFixed(2).replace('.',','); } }
    if(L>1200){ const g=el('g',{transform:`translate(${m[0]-pl.dir[0]*200} ${m[1]-pl.dir[1]*200}) ${horiz?'':'rotate(90)'} scale(1,-1)`},gl.skosy); const t=el('text',{x:0,y:0,'text-anchor':'middle','font-size':140,fill:'var(--demo)',class:'lbl-ar','font-weight':'600'},g); t.textContent='załamanie sufitu h = '+(pl.h0/1000).toFixed(2).replace('.',',')+' → spadek 1:'+(1/pl.tan).toFixed(2).replace('.',',')+' ('+Math.round(Math.atan(pl.tan)*180/Math.PI)+'°)'; }
  }
}
function drawGeo(){
  drawSlopes();
  const F = MODEL.floors[floor];
  const style = {walls:['var(--ink)',45],windows:['var(--win)',30],doors:['var(--door)',25],stairs:['var(--stair)',25],sills:['var(--fix)',18],fixtures:['var(--fix)',18],dims:['var(--dim)',12]};
  for (const k in style){
    gl[k].innerHTML='';
    const segs = (F.geo[k]||[]).concat(k==='fixtures'?(F.geo.misc||[]).concat(F.geo.hatch||[],F.geo.ceiling||[],F.geo.beams||[]):[]);
    const d = segs.map(segPath).join('');
    el('path',{d, fill:'none', stroke:style[k][0], 'stroke-width':style[k][1], 'stroke-linecap':'round','stroke-linejoin':'round'}, gl[k]);
  }
  // DWG texts
  gl.dwgtext.innerHTML='';
  for (const t of F.texts){
    const h = Math.max(t.h||160, 120);
    const tx = el('text',{x:0,y:0,'font-size':h*1.1,class:'dwgtext',transform:`translate(${t.x} ${t.y}) rotate(${(t.r||0)*180/Math.PI}) scale(1,-1)`}, gl.dwgtext);
    tx.textContent = t.t;
  }
  drawRooms();
}
function polyCentroid(p){ let a=0,cx=0,cy=0; for(let i=0;i<p.length;i++){ const j=(i+1)%p.length; const f=p[i][0]*p[j][1]-p[j][0]*p[i][1]; a+=f; cx+=(p[i][0]+p[j][0])*f; cy+=(p[i][1]+p[j][1])*f; } a*=0.5; if(Math.abs(a)<1) return p[0]; return [cx/(6*a), cy/(6*a)]; }
function polyArea(p){ let a=0; for(let i=0;i<p.length;i++){ const j=(i+1)%p.length; a+=p[i][0]*p[j][1]-p[j][0]*p[i][1]; } return Math.abs(a)/2; }
function unitOf(nr){ const v=curVariant(floor); const m=v?(v.assign||{}):{}; return m[nr]||null; }
function drawRooms(){
  const F = MODEL.floors[floor];
  gl.zones.innerHTML=''; gl.roomlbl.innerHTML='';
  const hide=new Set((curVariant(floor)||{}).hide||[]);
  for (const r of F.rooms){
    const u = unitOf(r.nr); const col = u ? UNITS[u].color : 'transparent';
    if (r.poly){
      const pg = el('polygon',{points:r.poly.map(q=>q.join(',')).join(' '), class:'roompoly', fill:u?col:'var(--accent)', 'fill-opacity': u?0.28:0.001}, gl.zones);
      pg.dataset.nr=r.nr;
      pg.addEventListener('pointerenter',()=>{ if(tool==='select'){ pg.classList.add('hover'); hiRow(r.nr,true);} });
      pg.addEventListener('pointerleave',()=>{ pg.classList.remove('hover'); hiRow(r.nr,false); });
      pg.addEventListener('click',(e)=>{ if(tool==='select'){ selectRoom(r.nr); e.stopPropagation(); } });
    }
    if (hide.has(r.nr)) continue;
    // label at centroid if poly else at dwg label position
    const c = r.poly ? polyCentroid(r.poly) : [r.lx+400, r.ly];
    const g = el('g',{transform:`translate(${c[0]} ${c[1]}) scale(1,-1)`, 'pointer-events':'none'}, gl.roomlbl);
    const small = (r.area||r.parea||0) < 6;
    const t1 = el('text',{x:0,y:small?-60:-120,'text-anchor':'middle','font-size':small?170:230,class:'lbl-nr'},g); t1.textContent=r.nr;
    if(!small){ const t2=el('text',{x:0,y:110,'text-anchor':'middle','font-size':150,class:'lbl-nm'},g); t2.textContent=(r.name||'').slice(0,26); }
    const t3 = el('text',{x:0,y:small?130:320,'text-anchor':'middle','font-size':small?140:170,class:'lbl-ar'},g); t3.textContent = r.area? r.area.toFixed(2).replace('.',',')+' m²' : (r.parea? '~'+r.parea.toFixed(1).replace('.',',')+' m²':'');
  }
  renderLegend(); renderRoomTable();
}
function hiRow(nr,on){ const tr=document.querySelector(`#roomTable tr[data-nr="${nr}"]`); if(tr) tr.classList.toggle('active',on); }
function selectRoom(nr){ const F=MODEL.floors[floor]; const r=F.rooms.find(x=>x.nr===nr); if(!r||!r.poly) return; document.querySelectorAll('.roompoly.active').forEach(p=>p.classList.remove('active')); const pg=gl.zones.querySelector(`[data-nr="${nr}"]`); if(pg) pg.classList.add('active'); const xs=r.poly.map(q=>q[0]), ys=r.poly.map(q=>q[1]); const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys); const pad=2500; const W=svg.clientWidth,H=svg.clientHeight; let w=x1-x0+2*pad,h=y1-y0+2*pad; if(w/h<W/H) w=h*W/H; else h=w*H/W; view={x:(x0+x1)/2-w/2,y:(y0+y1)/2-h/2,w,h}; applyView(); }

function renderRoomTable(){
  const F = MODEL.floors[floor]; const tb=document.getElementById('roomTable');
  if (!F.rooms.length){ tb.innerHTML = '<tr><td class="hint">Na tej kondygnacji inwentaryzacja nie numeruje pomieszczeń (lokal Poczty Polskiej). Włącz warstwę „Opisy z inwentaryzacji”, aby zobaczyć nazwy i powierzchnie.</td></tr>'; return; }
  let sum=0; const rows = F.rooms.slice().sort((a,b)=>a.nr.localeCompare(b.nr,'pl',{numeric:true})).map(r=>{ sum+=r.area||0; const u=unitOf(r.nr); return `<tr class="room" data-nr="${r.nr}"><td>${u?`<span class="unitdot" style="background:${UNITS[u].color}"></span>`:''}<b>${r.nr}</b></td><td>${r.name||'—'}</td><td class="num">${r.area?r.area.toFixed(2).replace('.',','):'—'}</td></tr>`; }).join('');
  tb.innerHTML = `<tr><th>Nr</th><th>Nazwa</th><th class="num">m²</th></tr>${rows}<tr><th>Razem</th><th></th><th class="num">${sum.toFixed(2).replace('.',',')}</th></tr>`;
  tb.querySelectorAll('tr.room').forEach(tr=>{ tr.addEventListener('click',()=>selectRoom(tr.dataset.nr)); tr.addEventListener('pointerenter',()=>{const pg=gl.zones.querySelector(`[data-nr="${tr.dataset.nr}"]`); if(pg) pg.classList.add('hover');}); tr.addEventListener('pointerleave',()=>{const pg=gl.zones.querySelector(`[data-nr="${tr.dataset.nr}"]`); if(pg) pg.classList.remove('hover');}); });
}
function renderLegend(){
  const v=curVariant(floor); document.getElementById('variantDesc').textContent=v?v.desc:'Ta kondygnacja nie ma wariantów koncepcji.';
  const lg=document.getElementById('legend'); const sums={};
  // existing rooms assigned
  for (const f of FLOORS){ const vf=curVariant(f); const m=vf?(vf.assign||{}):{}; const hid=new Set(vf&&vf.hide||[]); for (const r of MODEL.floors[f].rooms){ const u=m[r.nr]; if(u && !hid.has(r.nr)){ /* pomieszczenia ukryte (zastąpione projektem) liczą się z obrysów projektowych */ sums[u]=sums[u]||{a:0,fl:new Set()}; sums[u].a+=r.area||r.parea||0; sums[u].fl.add(f);} } }
  // drawn rooms (project) with unit
  for (const f of FLOORS){ for (const it of visibleItems(f)){ if(it.type==='room'&&it.unit){ sums[it.unit]=sums[it.unit]||{a:0,fl:new Set()}; sums[it.unit].a+=roomArea(it)/1e6; sums[it.unit].fl.add(f);} } }
  const names={piwnica:'piwnica',parter:'parter',pietro1:'I p.',poddasze:'poddasze'};
  lg.innerHTML = Object.keys(UNITS).filter(u=>sums[u]).map(u=>`<div class="l"><span class="unitdot" style="background:${UNITS[u].color}"></span>${UNITS[u].name} <span class="hint">(${[...sums[u].fl].map(f=>names[f]).join(', ')})</span><b>${sums[u].a.toFixed(1).replace('.',',')} m²</b></div>`).join('') || '<p class="hint">Brak przypisań w tym wariancie.</p>';
  updateLayerVisibility();
}

// ---------- project items ----------
function uid(){ return Math.random().toString(36).slice(2,9); }
function pushHistory(){ if(Object.isFrozen(project[floor].items)) project[floor].items=JSON.parse(JSON.stringify(project[floor].items)); hist[floor].push(JSON.stringify(project[floor].items)); if(hist[floor].length>60) hist[floor].shift(); }
function commit(){ obstStamp++; try{ drawProject(); }catch(err){ diag('drawProject',err); } if(is3D){ try{ build3D(); }catch(err){ diag('3d',err); } } try{ renderItems(); }catch(err){ diag('renderItems',err); } try{ renderLegend(); }catch(err){ diag('renderLegend',err); } scheduleSave(); }
// ---------- diagnostics: on-screen + saved to db so Claude can read them ----------
const DIAG={log:[], ua:navigator.userAgent, touch:('ontouchstart' in window), pointer:!!window.PointerEvent, started:new Date().toISOString(), events:0, lastEvent:''};
function hintToast(msg){ try{ const t=document.getElementById('errToast'); t.textContent=msg; t.hidden=false; clearTimeout(t._tm); t._tm=setTimeout(()=>{t.hidden=true;},4000); }catch(e){} }
function diag(where, err){
  const msg=where+': '+(err&&err.message||err)+(err&&err.stack?' | '+String(err.stack).split('\n').slice(0,2).join(' / '):'');
  DIAG.log.push(new Date().toISOString()+' '+msg); if(DIAG.log.length>40) DIAG.log.shift();
  try{ const t=document.getElementById('errToast'); t.textContent='Błąd: '+msg.slice(0,220); t.hidden=false; clearTimeout(t._tm); t._tm=setTimeout(()=>{t.hidden=true;},8000); }catch(e){}
  scheduleDiagSave();
}
let diagTimer=null;
function scheduleDiagSave(){ clearTimeout(diagTimer); diagTimer=setTimeout(saveDiag, 1500); }
async function saveDiag(){ if(!db) return; try{ await db.doc('diag/'+DIAG.started.replace(/[^0-9]/g,'').slice(0,14)).set({...DIAG, floor, tool, draftPts: draft?draft.pts.length:0, savedAt:new Date().toISOString()}); }catch(e){} }
window.addEventListener('error', e=>diag('window', e.error||e.message));
window.addEventListener('unhandledrejection', e=>diag('promise', e.reason));
const FURN={
  bed:{n:'łóżko 160×200',w:1600,h:2000},bed1:{n:'łóżko 90×200',w:900,h:2000},night:{n:'szafka nocna',w:450,h:400},wardrobe:{n:'PAX 200×58',w:2000,h:580},pax150:{n:'PAX 150×58',w:1500,h:580},pax175:{n:'PAX 175×58',w:1750,h:580},pax250:{n:'PAX 250×58',w:2500,h:580},pax275:{n:'PAX 275×58',w:2750,h:580},pax300:{n:'PAX 300×58',w:3000,h:580},pax150s:{n:'PAX 150×35 (płytki)',w:1500,h:350},pax200s:{n:'PAX 200×35 (płytki)',w:2000,h:350},
  sofa:{n:'sofa 220',w:2200,h:900},armchair:{n:'fotel',w:800,h:800},coffee:{n:'ława',w:1000,h:600},tv:{n:'szafka RTV',w:1600,h:400},
  table:{n:'stół 140×80',w:1400,h:800},table4:{n:'stół 120×80',w:1200,h:800},chair:{n:'krzesło',w:450,h:450},desk:{n:'biurko 120×60',w:1200,h:600},
  counter:{n:'blat kuchenny 60',w:1800,h:600},sink:{n:'zlew',w:600,h:600},hob:{n:'płyta grzewcza',w:600,h:600},fridge:{n:'lodówka',w:600,h:650},
  shower:{n:'prysznic 90×90',w:900,h:900},bath:{n:'wanna 170×75',w:1700,h:750},wc:{n:'WC',w:400,h:650},basin:{n:'umywalka',w:500,h:400},washer:{n:'pralka',w:600,h:600},
  shoe:{n:'szafka na buty',w:1000,h:350},box:{n:'inne (prostokąt)',w:1000,h:1000}
};
function drawFurn(it){
  const [a,b]=it.pts; const x0=Math.min(a[0],b[0]),y0=Math.min(a[1],b[1]),x1=Math.max(a[0],b[0]),y1=Math.max(a[1],b[1]); const w=x1-x0,h=y1-y0; const k=it.kind||'box';
  const e=el('g',{},gl.furn);
  const kitchen=['counter','sink','hob','fridge'].includes(k), wet=['shower','bath','wc','basin','washer'].includes(k);
  const lowRoof = tooLowFor(it); const collide = !rectFree(rectOf(it), wallSegsAll()) || !!lowRoof;
  el('rect',{x:x0,y:y0,width:w,height:h,fill:wet?'var(--win)':kitchen?'var(--demo)':'var(--fix)','fill-opacity':0.22,stroke:'var(--muted)','stroke-width':18,rx:k==='basin'||k==='wc'?Math.min(w,h)/3:40,class:collide?'furn-collide':''},e);
  const cx=(x0+x1)/2, cy=(y0+y1)/2;
  if(k==='bed'||k==='bed1'){ const hb=it.rot?w:h; el('line',{x1:x0+80,y1:y1-350,x2:x1-80,y2:y1-350,stroke:'var(--muted)','stroke-width':14},e); el('rect',{x:x0+120,y:y1-320,width:w-240,height:240,fill:'none',stroke:'var(--muted)','stroke-width':12,rx:60},e); }
  if(k==='sofa'||k==='armchair'){ el('rect',{x:x0,y:y1-220,width:w,height:220,fill:'var(--muted)','fill-opacity':0.25,stroke:'none'},e); }
  if(k==='wardrobe'||k==='shoe'||k.startsWith('pax')){ el('line',{x1:x0,y1:y0,x2:x1,y2:y1,stroke:'var(--muted)','stroke-width':12},e); el('line',{x1:x0,y1:y1,x2:x1,y2:y0,stroke:'var(--muted)','stroke-width':12},e); }
  if(k==='sink'||k==='basin'||k==='washer'){ el('circle',{cx,cy,r:Math.min(w,h)*0.3,fill:'none',stroke:'var(--muted)','stroke-width':14},e); }
  if(k==='hob'){ [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(d=>el('circle',{cx:cx+d[0]*w*0.22,cy:cy+d[1]*h*0.22,r:w*0.13,fill:'none',stroke:'var(--muted)','stroke-width':12},e)); }
  if(k==='shower'){ el('line',{x1:x0,y1:y0,x2:x1,y2:y1,stroke:'var(--muted)','stroke-width':12},e); el('circle',{cx,cy,r:60,fill:'var(--muted)'},e); }
  if(k==='bath'){ el('rect',{x:x0+90,y:y0+90,width:w-180,height:h-180,fill:'none',stroke:'var(--muted)','stroke-width':12,rx:200},e); }
  if(k==='wc'){ el('ellipse',{cx,cy:cy+h*0.1,rx:w*0.38,ry:h*0.3,fill:'none',stroke:'var(--muted)','stroke-width':12},e); }
  if(k==='fridge'){ el('line',{x1:x0+100,y1:y0,x2:x0+100,y2:y1,stroke:'var(--muted)','stroke-width':12},e); }
  if(k==='chair'){ el('line',{x1:x0+60,y1:y0+60,x2:x1-60,y2:y0+60,stroke:'var(--muted)','stroke-width':40},e); }
  if(k==='tv'){ el('rect',{x:x0+200,y:y1-80,width:w-400,height:80,fill:'var(--muted)'},e); }
  const lbl=it.label||(FURN[k]?FURN[k].n:k); if(Math.min(w,h)>=380 && !['chair','night'].includes(k)){ const g=el('g',{transform:`translate(${cx} ${cy}) ${h>w*1.6?'rotate(90)':''} scale(1,-1)`,'pointer-events':'none'},e); const t=el('text',{x:0,y:40,'text-anchor':'middle','font-size':Math.min(130,Math.max(w,h)/9),fill:'var(--muted)'},g); t.textContent=lbl; }
  return e;
}
function wallNormal(it){ const [a,b]=it.pts; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; return [-(b[1]-a[1])/L,(b[0]-a[0])/L]; } // lewa normalna (patrząc od początku do końca)
function shiftWall(it, off){ // przesunięcie osi o off w lewo (off>0) z drzwiami; prostopadłe sąsiady dociągane
  const n=wallNormal(it); const [a0,b0]=it.pts.map(q=>q.slice()); const hw=(it.w||120)/2;
  const doors=visibleItems(floor).filter(o=>o.type==='door'&&o.pts.every(p=>distPtSeg(p,a0,b0)<=hw+100));
  it.pts=it.pts.map(q=>[Math.round(q[0]+n[0]*off),Math.round(q[1]+n[1]*off)]);
  for (const d of doors) d.pts=d.pts.map(q=>[Math.round(q[0]+n[0]*off),Math.round(q[1]+n[1]*off)]);
  rejoinNeighbours(it,a0,b0,hw); }
function rejoinNeighbours(it,a0,b0,hw){ for (const o of visibleItems(floor)){ if(o.id===it.id||(o.type!=='wall'&&o.type!=='demo')) continue; for (const i of [0,o.pts.length-1]){ if (distPtSeg(o.pts[i],a0,b0)<=hw+120){ try{ snapWallEnds(o, Math.max(400,hw*2+200)); }catch(e){} break; } } } try{ snapWallEnds(it,200); }catch(e){} obstStamp++; }
function setWallThickness(it, w, keep){ // keep: 0 symetrycznie, 1 zostaje lewe lico, -1 zostaje prawe lico
  const w0=it.w||120; const n=wallNormal(it); const [a0,b0]=it.pts.map(q=>q.slice()); const dw=w-w0; it.w=w;
  if (keep){ const off=-keep*dw/2; it.pts=it.pts.map(q=>[Math.round(q[0]+n[0]*off),Math.round(q[1]+n[1]*off)]); const doors=visibleItems(floor).filter(o=>o.type==='door'&&o.pts.every(p=>distPtSeg(p,a0,b0)<=w0/2+100)); for (const d of doors) d.pts=d.pts.map(q=>[Math.round(q[0]+n[0]*off),Math.round(q[1]+n[1]*off)]); }
  rejoinNeighbours(it,a0,b0,Math.max(w0,w)/2); }
function setDoorWidth(it, w){ const [a,b]=it.pts; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const d=[(b[0]-a[0])/L,(b[1]-a[1])/L]; it.pts=[a,[Math.round(a[0]+d[0]*w),Math.round(a[1]+d[1]*w)]]; }
function swapHinge(it){ const [a,b]=it.pts; it.pts=[b,a]; it.flip=!it.flip; } // zamiana końców odwraca normalną – flip przywraca stronę otwierania
function doorSide(it){ return it.flip?'L':'P'; } // zawias po prawej patrząc od strony, na którą drzwi się otwierają = prawe
// ---------- obrysy pomieszczeń podążają za ścianami: raster + flood fill od punktu etykiety ----------
const ROOM_PALETTE=['#f4a261','#2a9d8f','#e9c46a','#8ab17d','#e76f51','#6d9dc5','#c77dff','#f28482','#84a59d','#b5838d','#ffd166','#06d6a0','#f9844a','#4d908e'];
function roomColor(it, idx){ return it.color || ROOM_PALETTE[idx % ROOM_PALETTE.length]; }
const RES=40; let rasterCache=null;
function wallsHash(){ let h=''; for (const it of visibleItems(floor)) if(it.type==='wall'||it.type==='demo') h+=it.type+(it.w||0)+JSON.stringify(it.pts)+';'; return h; }
function buildRaster(){
  const F=MODEL.floors[floor]; const b=F.bbox; const ox=b[0]-1000, oy=b[1]-1000; const W=Math.ceil((b[2]-b[0]+2000)/RES), H=Math.ceil((b[3]-b[1]+2000)/RES);
  const g=new Uint8Array(W*H);
  const px=(x)=>Math.round((x-ox)/RES), py=(y)=>Math.round((y-oy)/RES);
  function line(x0,y0,x1,y1,val,rad){ x0=px(x0); y0=py(y0); x1=px(x1); y1=py(y1); const dx=Math.abs(x1-x0), dy=Math.abs(y1-y0), sx=x0<x1?1:-1, sy=y0<y1?1:-1; let err=dx-dy; for(;;){ for(let a=-rad;a<=rad;a++) for(let c=-rad;c<=rad;c++){ const X=x0+a,Y=y0+c; if(X>=0&&Y>=0&&X<W&&Y<H) g[Y*W+X]=val; } if(x0===x1&&y0===y1) break; const e2=2*err; if(e2>-dy){ err-=dy; x0+=sx; } if(e2<dx){ err+=dx; y0+=sy; } } }
  const dwgSegs=[]; for (const sg of (F.geo.walls||[])) if(sg.k==='l') for(let i=1;i<sg.p.length;i++) dwgSegs.push({a:sg.p[i-1],b:sg.p[i],t:0});
  for (const lay of ['walls','windows','doors']) for (const sg of (F.geo[lay]||[])){ if(sg.k==='l'){ if(lay!=='doors') for(let i=1;i<sg.p.length;i++) line(sg.p[i-1][0],sg.p[i-1][1],sg.p[i][0],sg.p[i][1],1,0); } else if(sg.k==='a'){ let a0=sg.a0,a1=sg.a1; if(a1<a0) a1+=2*Math.PI; if(lay==='doors'){ /* łuk skrzydła nie jest przeszkodą – tylko domknięcie otworu w licach ściany */ const D=[[Math.cos(a0),Math.sin(a0)],[Math.cos(a1),Math.sin(a1)]]; for (let i=0;i<2;i++){ const di=D[i], dj=D[1-i]; line(sg.c[0],sg.c[1],sg.c[0]+sg.r*di[0],sg.c[1]+sg.r*di[1],1,0); let tt=null; for (const w of dwgSegs){ for (const [e0,e1] of [[w.a,w.b],[w.b,w.a]]){ if (Math.hypot(e0[0]-sg.c[0],e0[1]-sg.c[1])>150) continue; const vx=e1[0]-e0[0], vy=e1[1]-e0[1]; const Lw=Math.hypot(vx,vy)||1; if (Math.abs((vx*di[0]+vy*di[1])/Lw)>0.3) continue; const depth=-(vx*dj[0]+vy*dj[1]); if (depth>60 && depth<800 && (tt===null||depth<tt)) tt=depth; } }
            if (tt===null){ const rh=rayHit([sg.c[0]-dj[0]*5,sg.c[1]-dj[1]*5],[-dj[0],-dj[1]],dwgSegs,1); if(rh!==null && rh<700) tt=rh+5; }
            if (tt!==null){ const o=[sg.c[0]-dj[0]*tt,sg.c[1]-dj[1]*tt]; line(o[0]-di[0]*80,o[1]-di[1]*80,o[0]+(sg.r+80)*di[0],o[1]+(sg.r+80)*di[1],1,0); } } } if(lay==='doors') continue; const n=16; let prev=null; for(let k=0;k<=n;k++){ const t=a0+(a1-a0)*k/n; const q=[sg.c[0]+sg.r*Math.cos(t),sg.c[1]+sg.r*Math.sin(t)]; if(prev) line(prev[0],prev[1],q[0],q[1],1,0); prev=q; } } }
  const items=visibleItems(floor);
  for (const it of items) if(it.type==='demo'){ const r=Math.max(1,Math.round(((it.w||160)/2+60)/RES)); for(let i=1;i<it.pts.length;i++) line(it.pts[i-1][0],it.pts[i-1][1],it.pts[i][0],it.pts[i][1],0,r); }
  for (const it of items) if(it.type==='wall'){ const r=Math.max(1,Math.round((it.w||120)/2/RES)); for(let i=1;i<it.pts.length;i++) line(it.pts[i-1][0],it.pts[i-1][1],it.pts[i][0],it.pts[i][1],1,r); }
  // domknięcie morfologiczne (zamyka wnęki drzwiowe/ościeża i szczeliny < ~0,45 m)
  const K=6; const t=new Uint8Array(W*H); const pass=(src,dst,fn)=>{ for(let y=0;y<H;y++){ for(let x=0;x<W;x++){ let v=fn===1?0:1; for(let a=-K;a<=K;a++){ const X=x+a; if(X<0||X>=W) continue; const q=src[y*W+X]; if(fn===1){ if(q){ v=1; break; } } else { if(!q){ v=0; break; } } } dst[y*W+x]=v; } } const tmp=new Uint8Array(W*H); for(let x=0;x<W;x++){ for(let y=0;y<H;y++){ let v=fn===1?0:1; for(let a=-K;a<=K;a++){ const Y=y+a; if(Y<0||Y>=H) continue; const q=dst[Y*W+x]; if(fn===1){ if(q){ v=1; break; } } else { if(!q){ v=0; break; } } } tmp[y*W+x]=v; } } dst.set(tmp); };
  pass(g,t,1); const g2=new Uint8Array(W*H); pass(t,g2,0); for(let i=0;i<g.length;i++) if(g[i]) g2[i]=1;
  return {g:g2,W,H,ox,oy};
}
function getRaster(){ const key=floor+'|'+sel[floor]+'|'+wallsHash(); if(rasterCache&&rasterCache.key===key) return rasterCache.r; const r=buildRaster(); rasterCache={key,r}; return r; }
function floodRoom(R, ax, ay){
  const {g,W,H,ox,oy}=R; let sx=Math.round((ax-ox)/RES), sy=Math.round((ay-oy)/RES);
  if (sx<1||sy<1||sx>=W-1||sy>=H-1) return null;
  if (g[sy*W+sx]){ let found=null; for(let r=1;r<=12&&!found;r++){ for(let a=-r;a<=r&&!found;a++) for(let c=-r;c<=r;c++){ if(Math.max(Math.abs(a),Math.abs(c))!==r) continue; const X=sx+a,Y=sy+c; if(X>0&&Y>0&&X<W-1&&Y<H-1&&!g[Y*W+X]){ found=[X,Y]; break; } } } if(!found) return null; sx=found[0]; sy=found[1]; }
  const m=new Uint8Array(W*H); const st=[sy*W+sx]; m[st[0]]=1; let cnt=0, leak=false; const MAX=Math.round(250e6/(RES*RES));
  while(st.length){ const i=st.pop(); cnt++; if(cnt>MAX){ leak=true; break; } const x=i%W, y=(i-x)/W; if(x===0||y===0||x===W-1||y===H-1){ leak=true; break; }
    const nb=[i-1,i+1,i-W,i+W]; for(const j of nb){ if(!m[j]&&!g[j]){ m[j]=1; st.push(j); } } }
  if (leak) return null;
  // krawędzie brzegowe (wypełnienie po lewej) -> pętle
  const edges=new Map(); const key=(x,y)=>y*(W+1)+x;
  for (let y=0;y<H;y++) for (let x=0;x<W;x++){ if(!m[y*W+x]) continue; const i=y*W+x;
    if(!m[i-W]) add(key(x,y),key(x+1,y)); if(!m[i+1]) add(key(x+1,y),key(x+1,y+1)); if(!m[i+W]) add(key(x+1,y+1),key(x,y+1)); if(!m[i-1]) add(key(x,y+1),key(x,y)); }
  function add(a,b){ let l=edges.get(a); if(!l){ l=[]; edges.set(a,l); } l.push(b); }
  const loops=[];
  for (const [start,lst] of edges){ while(lst.length){ const loop=[start]; let cur=start, nxt=lst.pop(); let guard=0; while(nxt!==start && guard++<W*H){ loop.push(nxt); const l2=edges.get(nxt); if(!l2||!l2.length) break; nxt=l2.pop(); } loops.push(loop); } }
  const toPt=(k)=>{ const x=k%(W+1), y=(k-x)/(W+1); return [ox+(x-0.5)*RES, oy+(y-0.5)*RES]; };
  const polys=loops.map(l=>simplify(l.map(toPt),RES*1.2)).filter(p=>p.length>=3);
  polys.sort((p,q)=>Math.abs(polyArea(q))-Math.abs(polyArea(p)));
  if (!polys.length) return null;
  const outer=polys[0].map(q=>[Math.round(q[0]/10)*10,Math.round(q[1]/10)*10]);
  const holes=polys.slice(1).filter(p=>Math.abs(polyArea(p))>0.08e6).map(p=>p.map(q=>[Math.round(q[0]/10)*10,Math.round(q[1]/10)*10]));
  return {outer,holes,area:(Math.abs(polyArea(outer))-holes.reduce((a,h)=>a+Math.abs(polyArea(h)),0))};
}
function simplify(pts, eps){ // Douglas–Peucker na pętli zamkniętej
  if (pts.length<4) return pts; let far=0, fi=0; for(let i=1;i<pts.length;i++){ const d=Math.hypot(pts[i][0]-pts[0][0],pts[i][1]-pts[0][1]); if(d>far){ far=d; fi=i; } }
  const a=dp(pts.slice(0,fi+1),eps), b=dp(pts.slice(fi).concat([pts[0]]),eps); return a.slice(0,-1).concat(b.slice(0,-1));
  function dp(p,e){ if(p.length<3) return p; const A=p[0],B=p[p.length-1]; let md=0,mi=0; for(let i=1;i<p.length-1;i++){ const d=distPtSeg(p[i],A,B); if(d>md){ md=d; mi=i; } } if(md>e){ const l=dp(p.slice(0,mi+1),e), r=dp(p.slice(mi),e); return l.slice(0,-1).concat(r); } return [A,B]; }
}
function roomAnchor(it){ if(!it.anchor){ it.anchor=polyCentroid(it.pts).map(v=>Math.round(v)); } return it.anchor; }
let roomsStampKey=null;
function recomputeRooms(force){
  const key=floor+'|'+sel[floor]+'|'+wallsHash(); if(!force && roomsStampKey===key) return false; roomsStampKey=key;
  let changed=false; let R=null;
  for (const it of visibleItems(floor)){ if(it.type!=='room'||it.auto===false) continue; try{ R=R||getRaster(); const an=roomAnchor(it); const res=floodRoom(R,an[0],an[1]); if(res && res.area>1.5e6 && res.area<400e6){ const prev=JSON.stringify(it.pts)+JSON.stringify(it.holes||[]); it.pts=res.outer; if(res.holes.length) it.holes=res.holes; else delete it.holes; if(prev!==JSON.stringify(it.pts)+JSON.stringify(it.holes||[])) changed=true; } }catch(err){ diag('room outline',err); } }
  return changed;
}
function roomPath(it){ let d='M'+it.pts.map(q=>q.join(' ')).join('L')+'Z'; for (const h of (it.holes||[])) d+='M'+h.map(q=>q.join(' ')).join('L')+'Z'; return d; }
function roomArea(it){ return Math.abs(polyArea(it.pts))-(it.holes||[]).reduce((a,h)=>a+Math.abs(polyArea(h)),0); }
function drawProject(){
  try{ recomputeRooms(); }catch(err){ diag('rooms',err); }
  gl.project.innerHTML=''; gl.rfill.innerHTML=''; gl.rline.innerHTML=''; gl.rlbl.innerHTML=''; gl.rhit.innerHTML=''; gl.furn.innerHTML=''; gl.sketch.innerHTML=''; let markN=0; roomIdx=0;
  for (const it of visibleItems(floor)){
    try { drawOneItem(it, markN); if(it.type==='mark') markN++; } catch(err){ diag('render '+it.type, err); }
  }
  try { drawAutoDims(); } catch(err){ diag('autodim', err); }
}
// ---------- wymiary automatyczne: światło pomieszczeń przez środek + przejścia wokół zaznaczonego mebla ----------
function rayPoly(o, d, poly){ // odległość od o wzdłuż d do krawędzi wielokąta
  let best=null;
  for (let i=0;i<poly.length;i++){ const a=poly[i], b=poly[(i+1)%poly.length]; const ex=b[0]-a[0], ey=b[1]-a[1]; const den=d[0]*ey-d[1]*ex; if(Math.abs(den)<1e-9) continue; const wx=a[0]-o[0], wy=a[1]-o[1]; const t=(wx*ey-wy*ex)/den, u=(wx*d[1]-wy*d[0])/den; if(u<-0.001||u>1.001||t<=0) continue; if(best===null||t<best) best=t; }
  return best;
}
function dimLine(g, a, b, txt, color, side){ // a→b wymiar z kreskami końcowymi i opisem
  const dx=b[0]-a[0], dy=b[1]-a[1]; const L=Math.hypot(dx,dy)||1; const nx=-dy/L, ny=dx/L; const col=color||'var(--accent)';
  el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:col,'stroke-width':14,opacity:0.9},g);
  for (const p of [a,b]) el('line',{x1:p[0]-nx*90,y1:p[1]-ny*90,x2:p[0]+nx*90,y2:p[1]+ny*90,stroke:col,'stroke-width':14},g);
  const off=side||1; const t=el('g',{transform:`translate(${(a[0]+b[0])/2+nx*off*170} ${(a[1]+b[1])/2+ny*off*170}) rotate(${Math.abs(dx)>Math.abs(dy)?0:90}) scale(1,-1)`},g);
  const tx=el('text',{x:0,y:50,'text-anchor':'middle','font-size':150,fill:col,class:'lbl-ar','font-weight':'600',stroke:'var(--canvas)','stroke-width':40,'paint-order':'stroke'},t); tx.textContent=txt;
}
function fm(v){ return (v/1000).toFixed(2).replace('.',','); }
function drawAutoDims(){
  gl.autodim.innerHTML=''; if(!layerOn.autodim) return;
  const g=el('g',{'pointer-events':'none'},gl.autodim);
  // 1) pomieszczenia projektowe (i istniejące bez przykrycia) – światło przez środek
  const F=MODEL.floors[floor]; const hide=new Set((curVariant(floor)||{}).hide||[]);
  const polys=[]; for (const it of visibleItems(floor)) if(it.type==='room'&&it.pts.length>=3) polys.push(it.pts);
  for (const r of F.rooms) if(r.poly && !hide.has(r.nr)) polys.push(r.poly);
  for (const poly of polys){
    const c=polyCentroid(poly); const L=rayPoly(c,[-1,0],poly), R=rayPoly(c,[1,0],poly), D=rayPoly(c,[0,-1],poly), U=rayPoly(c,[0,1],poly);
    if ([L,R,D,U].some(v=>v===null)) continue;
    const yw=c[1]-Math.min(650,D*0.55), xd=c[0]-Math.min(650,L*0.55);
    const Lw=rayPoly([c[0],yw],[-1,0],poly), Rw=rayPoly([c[0],yw],[1,0],poly), Dd=rayPoly([xd,c[1]],[0,-1],poly), Ud=rayPoly([xd,c[1]],[0,1],poly);
    if (Lw!==null&&Rw!==null) dimLine(g,[c[0]-Lw,yw],[c[0]+Rw,yw],fm(Lw+Rw),'var(--accent)',-1);
    if (Dd!==null&&Ud!==null) dimLine(g,[xd,c[1]-Dd],[xd,c[1]+Ud],fm(Dd+Ud),'var(--accent)',1);
  }
  // 2) przejścia wokół zaznaczonego / przeciąganego mebla: odległości do ścian i innych mebli z 4 stron
  const selIt=project[floor].items.find(i=>i.id===selectedId);
  if (selIt && selIt.type==='furn'){
    const r=rectOf(selIt); const segs=wallSegsAll().map(sg=>({a:sg[0],b:sg[1],t:0}));
    for (const o of visibleItems(floor)) if(o.type==='furn'&&o.id!==selIt.id){ const q=rectOf(o); segs.push({a:[q.x0,q.y0],b:[q.x1,q.y0],t:0},{a:[q.x1,q.y0],b:[q.x1,q.y1],t:0},{a:[q.x1,q.y1],b:[q.x0,q.y1],t:0},{a:[q.x0,q.y1],b:[q.x0,q.y0],t:0}); }
    const mx=(r.x0+r.x1)/2, my=(r.y0+r.y1)/2;
    const probes=[[[r.x0,my],[-1,0]],[[r.x1,my],[1,0]],[[mx,r.y0],[0,-1]],[[mx,r.y1],[0,1]]];
    for (const [o,d] of probes){ const t=rayHit(o,d,segs,1); if(t!==null&&t<4000){ const p2=[o[0]+d[0]*t,o[1]+d[1]*t]; dimLine(g,o,p2,fm(t),t<800?'var(--new)':'var(--door)', d[0]?1:-1); } }
  }
}
function drawOneItem(it, markN){
  {
    const isSel = it.id===selectedId;
    let e;
    if (it.type==='wall'||it.type==='demo'){ e=el('g',{},gl.project); const dd='M'+it.pts.map(q=>q.join(' ')).join('L'); if(it.type==='wall'){ el('path',{d:dd, fill:'none', stroke:'var(--new)', 'stroke-width':it.w||120, 'stroke-linecap':'butt','stroke-linejoin':'miter'},e); try{ wallJoinPatches(it,e); }catch(err){} } else el('path',{d:dd, fill:'none', stroke:'var(--demo)', 'stroke-width':it.w||160, 'stroke-dasharray':'250 150','stroke-linecap':'butt'},e); el('path',{d:dd, fill:'none', stroke:'transparent', 'stroke-width':Math.max(it.w||120, 12*mmPerPx()), 'stroke-linecap':'square','pointer-events':'stroke',class:'hit'},e); }
    else if (it.type==='room'){ const col=roomColor(it, roomIdx++); const dpath=roomPath(it); el('path',{d:dpath, fill:col,'fill-opacity':0.32, stroke:'none','fill-rule':'evenodd','pointer-events':'none'}, gl.rfill); el('path',{d:dpath, fill:'none', stroke:col,'stroke-width':45,'stroke-dasharray':'220 130','pointer-events':'none'}, gl.rline); const c=roomAnchor(it); const lblW=Math.max(1800, Math.max((it.label||'pomieszczenie').length*125, 9*95)+300); e=el('rect',{x:c[0]-lblW/2, y:c[1]-320, width:lblW, height:680, fill:'transparent', stroke:'none','stroke-width':40, rx:120}, gl.rhit); e.setAttribute('class','roomhit'); e.style.cursor='text'; const g=el('g',{transform:`translate(${c[0]} ${c[1]}) scale(1,-1)`,'pointer-events':'none'},gl.rlbl); const t=el('text',{x:0,y:-60,'text-anchor':'middle','font-size':220,fill:'var(--new)','font-weight':'600'},g); t.textContent=it.label||'pomieszczenie'; const t2=el('text',{x:0,y:200,'text-anchor':'middle','font-size':170,fill:'var(--new)',class:'lbl-ar'},g); t2.textContent=(roomArea(it)/1e6).toFixed(2).replace('.',',')+' m²'; const hs=roomHeightStats(it); if(hs){ t2.textContent+=' · użytk. '+(hs.use/1e6).toFixed(2).replace('.',',')+' m²'; const t3=el('text',{x:0,y:400,'text-anchor':'middle','font-size':150,fill:'var(--new)',class:'lbl-ar'},g); t3.textContent='h '+(hs.hmin/1000).toFixed(2).replace('.',',')+'–'+(hs.hmax/1000).toFixed(2).replace('.',',')+' m'; } }
    else if (it.type==='door'){ e=el('g',{},gl.project); drawDoor2D(it,e,'var(--new)'); }
    else if (it.type==='furn'){ e=drawFurn(it); }
    else if (it.type==='ink'){ e=el('g',{},gl.sketch); const dd='M'+it.pts.map(q=>q.join(' ')).join('L'); el('path',{d:dd,fill:'none',stroke:'var(--mark)','stroke-width':70,'stroke-linecap':'round','stroke-linejoin':'round',opacity:0.85},e); el('path',{d:dd,fill:'none',stroke:'transparent','stroke-width':Math.max(200,12*mmPerPx()),'stroke-linecap':'round','pointer-events':'stroke',class:'hit'},e); }
    else if (it.type==='arrow'){ const [a,b]=it.pts; e=el('g',{},gl.sketch); const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const ux=(b[0]-a[0])/L, uy=(b[1]-a[1])/L; const hx=b[0]-ux*350, hy=b[1]-uy*350; el('line',{x1:a[0],y1:a[1],x2:hx,y2:hy,stroke:'var(--mark)','stroke-width':60,'stroke-linecap':'round'},e); el('polygon',{points:`${b[0]},${b[1]} ${hx-uy*180},${hy+ux*180} ${hx+uy*180},${hy-ux*180}`,fill:'var(--mark)'},e); el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'transparent','stroke-width':Math.max(200,12*mmPerPx()),'pointer-events':'stroke',class:'hit'},e); if(it.label){ const g=el('g',{transform:`translate(${a[0]-ux*150} ${a[1]-uy*150}) scale(1,-1)`,'pointer-events':'none'},e); const t=el('text',{x:0,y:60,'text-anchor':ux>0?'end':'start','font-size':220,fill:'var(--mark)','font-weight':'600'},g); t.textContent=it.label; } }
    else if (it.type==='mark'){ const [a]=it.pts; const n=it.n||(markN+1); e=el('g',{},gl.sketch); el('circle',{cx:a[0],cy:a[1],r:280,fill:'var(--mark)',opacity:0.95},e); const g=el('g',{transform:`translate(${a[0]} ${a[1]}) scale(1,-1)`,'pointer-events':'none'},e); const t=el('text',{x:0,y:95,'text-anchor':'middle','font-size':300,fill:'#fff','font-weight':'700'},g); t.textContent=n; if(it.label){ const g2=el('g',{transform:`translate(${a[0]+360} ${a[1]-80}) scale(1,-1)`,'pointer-events':'none'},e); const bg=el('text',{x:0,y:0,'font-size':220,fill:'var(--mark)','font-weight':'600',stroke:'var(--canvas)','stroke-width':60,'paint-order':'stroke'},g2); bg.textContent=it.label; } }
    else if (it.type==='dim'){ const [a,b]=it.pts; e=el('g',{},gl.project); el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'var(--accent)','stroke-width':20},e); [a,b].forEach(p=>el('circle',{cx:p[0],cy:p[1],r:60,fill:'var(--accent)'},e)); const L=Math.hypot(b[0]-a[0],b[1]-a[1]); const g=el('g',{transform:`translate(${(a[0]+b[0])/2} ${(a[1]+b[1])/2+150}) scale(1,-1)`,'pointer-events':'none'},e); const t=el('text',{x:0,y:0,'text-anchor':'middle','font-size':180,fill:'var(--accent)',class:'lbl-ar','font-weight':'500'},g); t.textContent=(L/1000).toFixed(2).replace('.',',')+' m'; }
    else if (it.type==='note'){ const [a]=it.pts; e=el('g',{},gl.project); el('circle',{cx:a[0],cy:a[1],r:160,fill:'var(--note)'},e); const g=el('g',{transform:`translate(${a[0]+220} ${a[1]-60}) scale(1,-1)`},e); const t=el('text',{x:0,y:0,'font-size':200,fill:'var(--note)','font-weight':'500'},g); t.textContent=it.label||''; }
    if (!e) return;
    e.dataset.id=it.id; e.style.cursor='pointer';
    if (isSel && (it.type==='wall'||it.type==='demo') && it.pts.length===2){ const [pa,pb]=it.pts; const Lw=Math.hypot(pb[0]-pa[0],pb[1]-pa[1])||1; const ux=(pb[0]-pa[0])/Lw, uy=(pb[1]-pa[1])/Lw; const s3=6*mmPerPx(); const tipx=pb[0]-ux*s3*1.8, tipy=pb[1]-uy*s3*1.8; el('path',{d:`M${tipx+ux*s3} ${tipy+uy*s3}L${tipx-uy*s3*0.8} ${tipy+ux*s3*0.8}L${tipx+uy*s3*0.8} ${tipy-ux*s3*0.8}Z`,fill:'var(--sel)',opacity:0.9},e); const gL=el('g',{transform:`translate(${(pa[0]+pb[0])/2-uy*(it.w||120)*0.5-uy*s3*2.2} ${(pa[1]+pb[1])/2+ux*(it.w||120)*0.5+ux*s3*2.2}) scale(1,-1)`,'pointer-events':'none'},e); const tL=el('text',{x:0,y:0,'text-anchor':'middle','font-size':2.2*mmPerPx(),fill:'var(--sel)',class:'lbl-ar'},gL); tL.textContent='L'; const gR=el('g',{transform:`translate(${(pa[0]+pb[0])/2+uy*(it.w||120)*0.5+uy*s3*2.2} ${(pa[1]+pb[1])/2-ux*(it.w||120)*0.5-ux*s3*2.2}) scale(1,-1)`,'pointer-events':'none'},e); const tR=el('text',{x:0,y:0,'text-anchor':'middle','font-size':2.2*mmPerPx(),fill:'var(--sel)',class:'lbl-ar'},gR); tR.textContent='P'; for (const pp of it.pts) el('circle',{cx:pp[0],cy:pp[1],r:7*mmPerPx(),fill:'var(--canvas)',stroke:'var(--sel)','stroke-width':2.5*mmPerPx(),style:'cursor:ew-resize'},e); }
    if (isSel){ const hl=e.cloneNode(true); hl.querySelectorAll('.hit').forEach(x=>x.remove()); hl.setAttribute('stroke','var(--sel)'); hl.setAttribute('fill','none'); hl.setAttribute('opacity','0.6'); hl.querySelectorAll('*').forEach(c=>{c.setAttribute('stroke','var(--sel)');}); hl.style.pointerEvents='none'; e.parentNode.insertBefore(hl,e); if(hl.tagName==='path'||hl.tagName==='polygon') hl.setAttribute('stroke-width', (parseFloat(e.getAttribute('stroke-width'))||40)+120); }
    e.addEventListener('click',(ev)=>{ if(suppressClick){ suppressClick=false; ev.stopPropagation(); return; } if(tool==='select'){ selectedId=it.id; drawProject(); renderItems(); showInlineEdit(it, ev); ev.stopPropagation(); } });
  }
}
function renderItems(){
  const box=document.getElementById('items'); const names={wall:'Ściana',demo:'Wyburzenie',room:'Pomieszczenie',door:'Otwór/drzwi',dim:'Pomiar',note:'Notatka',furn:'Mebel',ink:'Szkic',arrow:'Strzałka',mark:'Uwaga'};
  box.innerHTML = visibleItems(floor).map(it=>{ let a=''; if(it.type==='room') a=(roomArea(it)/1e6).toFixed(2)+' m²'; if(it.type==='wall'||it.type==='demo'){ let L=0; for(let i=1;i<it.pts.length;i++) L+=Math.hypot(it.pts[i][0]-it.pts[i-1][0],it.pts[i][1]-it.pts[i-1][1]); a=(L/1000).toFixed(2)+' m'; } if(it.type==='dim'||it.type==='door'){ a=(Math.hypot(it.pts[1][0]-it.pts[0][0],it.pts[1][1]-it.pts[0][1])/1000).toFixed(2)+' m'; } if(it.type==='furn'){ a=(Math.abs(it.pts[1][0]-it.pts[0][0])/10).toFixed(0)+'×'+(Math.abs(it.pts[1][1]-it.pts[0][1])/10).toFixed(0)+' cm'; } return `<div class="it ${it.id===selectedId?'active':''}" data-id="${it.id}"><span class="unitdot" style="background:${it.type==='room'&&it.unit?UNITS[it.unit].color:(it.type==='demo'?'var(--demo)':it.type==='dim'?'var(--accent)':it.type==='note'?'var(--note)':['ink','arrow','mark'].includes(it.type)?'var(--mark)':'var(--new)')}"></span>${names[it.type]}<span class="t">${it.type==='mark'?('#'+(it.n||'')+' '):''}${it.label||(it.type==='furn'&&FURN[it.kind]?FURN[it.kind].n:'')}</span><span class="a">${a.replace('.',',')}</span></div>`; }).join('') || '<p class="hint">Brak elementów projektu na tej kondygnacji. Narysuj ściany, wyburzenia i nowe pomieszczenia — zapisują się automatycznie.</p>';
  box.querySelectorAll('.it').forEach(d=>d.addEventListener('click',()=>{ selectedId=d.dataset.id; drawProject(); renderItems(); }));
  document.getElementById('jsonBox').value = JSON.stringify(visibleItems(floor));
}
function deleteSelected(){ if(!selectedId) return; pushHistory(); project[floor].items=project[floor].items.filter(i=>i.id!==selectedId); selectedId=null; hideInlineEdit(); commit(); }
function undo(){ const h=hist[floor].pop(); if(h===undefined) return; project[floor].items=JSON.parse(h); selectedId=null; commit(); }

// inline editor for label/unit
const ie=document.getElementById('inlineEdit');
function showInlineEdit(it, ev){
  ie.innerHTML='';
  if (it.type==='room'||it.type==='note'||it.type==='wall'||it.type==='demo'||it.type==='furn'||it.type==='door'||it.type==='arrow'||it.type==='mark'||it.type==='ink'){
    const inp=document.createElement('input'); inp.type='text'; inp.id='ieLabel'; inp.placeholder='nazwa / opis'; inp.value=it.label||''; ie.appendChild(inp);
    if (sel[floor]){ const sv=document.createElement('select'); sv.id='ieVar'; sv.innerHTML=`<option value="${sel[floor]}" ${it.v?'selected':''}>tylko ten wariant</option><option value="" ${!it.v?'selected':''}>wszystkie warianty</option>`; ie.appendChild(sv); }
    if (it.type==='door'){ const so=document.createElement('select'); so.id='ieOpen'; so.innerHTML=`<option value="0" ${!it.open?'selected':''}>drzwi</option><option value="1" ${it.open?'selected':''}>otwór bez drzwi</option>`; ie.appendChild(so);
      const sw=document.createElement('select'); sw.id='ieDoorW'; const curW=Math.round(Math.hypot(it.pts[1][0]-it.pts[0][0],it.pts[1][1]-it.pts[0][1])/10); sw.innerHTML=[70,80,90,100,120,150,180].map(w=>`<option value="${w}" ${w===curW?'selected':''}>${w} cm</option>`).join('')+(([70,80,90,100,120,150,180].includes(curW))?'':`<option value="${curW}" selected>${curW} cm</option>`); sw.addEventListener('change',()=>{ pushHistory(); setDoorWidth(it, parseInt(sw.value)*10); commit(); }); ie.appendChild(sw);
      const sf=document.createElement('button'); sf.className='btn'; sf.textContent='↔ Kierunek (do/na zewnątrz)'; sf.addEventListener('click',()=>{ pushHistory(); it.flip=!it.flip; commit(); }); ie.appendChild(sf);
      const sh=document.createElement('button'); sh.className='btn'; sh.textContent='L/P zawias'; sh.addEventListener('click',()=>{ pushHistory(); swapHinge(it); commit(); }); ie.appendChild(sh);
      const hint=document.createElement('span'); hint.className='hint'; hint.textContent='Przeciągnij drzwi wzdłuż ściany. Klawisze: R kierunek, L zawias.'; ie.appendChild(hint); }
    if ((it.type==='wall'||it.type==='demo') && it.pts.length===2){
      const tw=document.createElement('input'); tw.type='number'; tw.id='ieWallW'; tw.min='3'; tw.max='100'; tw.step='0.5'; tw.style.width='64px'; tw.title='Grubość ściany [cm]'; tw.value=String((it.w||120)/10); ie.appendChild(tw);
      const ks=document.createElement('select'); ks.id='ieWallKeep'; ks.title='Przy zmianie grubości: które lico zostaje na miejscu'; ks.innerHTML='<option value="0">grubość symetrycznie od osi</option><option value="1">zostaje lewe lico</option><option value="-1">zostaje prawe lico</option>'; ie.appendChild(ks);
      tw.addEventListener('change',()=>{ const v=parseFloat((tw.value||'').replace(',','.')); if(!(v>0)) return; pushHistory(); setWallThickness(it, Math.round(v*10), +ks.value); commit(); });
      const mk=(txt,title,fn)=>{ const bt=document.createElement('button'); bt.className='btn'; bt.textContent=txt; bt.title=title; bt.addEventListener('click',()=>{ pushHistory(); fn(); commit(); }); ie.appendChild(bt); };
      mk('⇤ o grubość w lewo','Przesuń ścianę o jej grubość w lewo (patrząc w kierunku rysowania) – lewe lico staje się prawym',()=>shiftWall(it, (it.w||120)));
      mk('⇥ o grubość w prawo','Przesuń ścianę o jej grubość w prawo (patrząc w kierunku rysowania)',()=>shiftWall(it, -(it.w||120)));
      mk('↺ odwróć kierunek','Zamień początek z końcem (zmienia, co jest lewą/prawą stroną)',()=>{ it.pts.reverse(); });
    }
    if (it.type==='furn'){ const sz=document.createElement('input'); sz.type='text'; sz.id='ieSize'; sz.style.width='110px'; sz.placeholder='szer×gł cm'; sz.value=(Math.abs(it.pts[1][0]-it.pts[0][0])/10).toFixed(0)+'×'+(Math.abs(it.pts[1][1]-it.pts[0][1])/10).toFixed(0); ie.appendChild(sz); }
    if (it.type==='room'){ const ci=document.createElement('input'); ci.type='color'; ci.id='ieColor'; ci.title='Kolor pomieszczenia'; ci.value=roomColor(it, visibleItems(floor).filter(r=>r.type==='room').indexOf(it)); ci.style.width='34px'; ci.addEventListener('input',()=>{ it.color=ci.value; drawProject(); renderLegend(); }); ci.addEventListener('change',()=>{ pushHistory(); it.color=ci.value; commit(); }); ie.appendChild(ci);
      const la=document.createElement('label'); la.className='hint'; la.style.whiteSpace='nowrap'; la.innerHTML=`<input type="checkbox" id="ieAuto" ${it.auto===false?'':'checked'}> obrys za ścianami`; ie.appendChild(la); la.querySelector('input').addEventListener('change',(ev)=>{ pushHistory(); it.auto=ev.target.checked?undefined:false; if(it.auto===undefined) delete it.auto; recomputeRooms(true); commit(); });
      const mv=document.createElement('button'); mv.className='btn'; mv.textContent='⌖ Przestaw etykietę'; mv.title='Kliknij, a potem kliknij nowe miejsce etykiety (punkt startowy obrysu)'; mv.addEventListener('click',()=>{ hideInlineEdit(); anchorMove=it; hintToast('Kliknij nowe miejsce etykiety pomieszczenia „'+(it.label||'')+'”.'); }); ie.appendChild(mv);
      const s=document.createElement('select'); s.id='ieUnit'; s.innerHTML='<option value="">— lokal —</option>'+Object.keys(UNITS).map(u=>`<option value="${u}" ${it.unit===u?'selected':''}>${UNITS[u].name}</option>`).join(''); ie.appendChild(s); }
    const ok=document.createElement('button'); ok.className='btn primary'; ok.textContent='OK'; ie.appendChild(ok);
    const del=document.createElement('button'); del.className='btn danger'; del.textContent='Usuń'; del.addEventListener('click',()=>{ selectedId=it.id; deleteSelected(); }); ie.appendChild(del);
    const go=()=>{ pushHistory(); it.label=inp.value.trim(); const s=document.getElementById('ieUnit'); if(s) it.unit=s.value||null; const sv=document.getElementById('ieVar'); if(sv){ if(sv.value) it.v=sv.value; else delete it.v; } const so=document.getElementById('ieOpen'); if(so) it.open=so.value==='1'; const sz=document.getElementById('ieSize'); if(sz){ const mm=sz.value.split(/[x×]/).map(v=>parseFloat(v)*10); if(mm.length===2&&mm.every(v=>v>0)){ const x0=Math.min(it.pts[0][0],it.pts[1][0]), y0=Math.min(it.pts[0][1],it.pts[1][1]); it.pts=[[x0,y0],[x0+mm[0],y0+mm[1]]]; } } hideInlineEdit(); if(it.type==='furn') afterFurnChange(it); else commit(); };
    ok.addEventListener('click',go); inp.addEventListener('keydown',e=>{ if(e.key==='Enter') go(); if(e.key==='Escape') hideInlineEdit(); });
    const wrap=document.getElementById('canvasWrap').getBoundingClientRect();
    ie.style.left=Math.min(ev.clientX-wrap.left+8, wrap.width-260)+'px'; ie.style.top=Math.min(ev.clientY-wrap.top+8, wrap.height-80)+'px'; ie.classList.add('show'); inp.focus();
  }
}
function hideInlineEdit(){ ie.classList.remove('show'); ie.innerHTML=''; }

// ---------- snapping ----------
let snapPts=[];
function buildSnap(){ const F=MODEL.floors[floor]; snapPts=[]; for (const k of ['walls','windows','doors']){ for (const s of (F.geo[k]||[])){ if(s.k==='l') for(const q of s.p) snapPts.push(q); } } }
function snap(p){
  const tol = 10*mmPerPx(); let best=null, bd=tol;
  for (const q of snapPts){ const d=Math.hypot(q[0]-p.x,q[1]-p.y); if(d<bd){bd=d;best=q;} }
  for (const it of project[floor].items){ for(const q of it.pts){ const d=Math.hypot(q[0]-p.x,q[1]-p.y); if(d<bd){bd=d;best=q;} } }
  // ściany i wyburzenia: tylko pod kątem 90° – zawsze blokada do osi względem poprzedniego punktu (przyciągnięty punkt rzutowany na oś)
  if (draft && draft.pts.length && (draft.type==='wall'||draft.type==='demo')){ const l=draft.pts[draft.pts.length-1]; const q=best?{x:best[0],y:best[1]}:{x:Math.round(p.x/10)*10,y:Math.round(p.y/10)*10}; const dx=Math.abs(p.x-l[0]), dy=Math.abs(p.y-l[1]); if (dx<=dy) return {x:l[0],y:q.y,snapped:!!best}; return {x:q.x,y:l[1],snapped:!!best}; }
  if (best) return {x:best[0],y:best[1],snapped:true};
  // orthogonal lock relative to last draft point
  if (draft && draft.pts.length){ const l=draft.pts[draft.pts.length-1]; const dx=Math.abs(p.x-l[0]), dy=Math.abs(p.y-l[1]); if (dx<tol*1.5) return {x:l[0],y:Math.round(p.y/10)*10,snapped:false}; if (dy<tol*1.5) return {x:Math.round(p.x/10)*10,y:l[1],snapped:false}; }
  return {x:Math.round(p.x/50)*50,y:Math.round(p.y/50)*50,snapped:false};
}
function updateDraftBar(){ const bar=document.getElementById('draftBar'); const on=!!(draft&&draft.pts.length); bar.hidden=!on; if(on){ const n=draft.pts.length; const need=draft.type==='room'?3:2; document.getElementById('dbInfo').textContent=(draft.type==='room'?'Obrys: ':draft.type==='wall'?'Ściana '+(wallW()/10)+' cm, grubość '+(['w prawo od linii','na osi','w lewo od linii'][wallSide()+1])+' (Tab zmienia): ':draft.type==='demo'?'Wyburzenie: ':'')+n+' pkt'+(n<need?' – potrzeba '+need:''); document.getElementById('dbFinish').disabled=n<need; } }
function drawDraft(){
  updateDraftBar();
  gl.draft.innerHTML='';
  if (hoverPt){ el('circle',{cx:hoverPt.x,cy:hoverPt.y,r:hoverPt.snapped?90:50,fill:hoverPt.snapped?'var(--sel)':'none',stroke:'var(--sel)','stroke-width':20},gl.draft); const g=el('g',{transform:`translate(${hoverPt.x+150} ${hoverPt.y+150}) scale(1,-1)`},gl.draft); }
  if (tool==='door' && hoverPt){ if (hoverPt.door) drawDoorPreview(hoverPt.door, gl.draft); else { el('circle',{cx:hoverPt.x,cy:hoverPt.y,r:9*mmPerPx(),fill:'none',stroke:'var(--new)','stroke-width':2*mmPerPx(),'stroke-dasharray':`${4*mmPerPx()} ${3*mmPerPx()}`},gl.draft); } return; }
  if (tool==='furn' && hoverPt){ const f=FURN[document.getElementById('furnSel').value]; const w=furnRot?f.h:f.w, h=furnRot?f.w:f.h; el('rect',{x:hoverPt.x-w/2,y:hoverPt.y-h/2,width:w,height:h,fill:'var(--sel)','fill-opacity':0.2,stroke:'var(--sel)','stroke-width':20},gl.draft); }
  if (!draft) return;
  const pts = draft.pts.concat(hoverPt?[[hoverPt.x,hoverPt.y]]:[]);
  if (pts.length<2) return;
  const d='M'+pts.map(q=>q.join(' ')).join('L');
  const col = draft.type==='demo'?'var(--demo)':draft.type==='dim'?'var(--accent)':draft.type==='arrow'?'var(--mark)':'var(--new)';
  if (draft.type==='wall'){ const w=wallW(); const side=wallSide(); const body=offsetPolyline(pts, side*w/2); el('path',{d:'M'+body.map(q=>q.join(' ')).join('L'), fill:'none', stroke:col,'stroke-width':w,'stroke-linejoin':'miter','opacity':0.75},gl.draft); if (side) el('path',{d, fill:'none', stroke:'var(--sel)','stroke-width':14,'stroke-dasharray':'80 60'},gl.draft); }
  else el('path',{d:d+(draft.type==='room'&&pts.length>2?'Z':''), fill:draft.type==='room'?col:'none','fill-opacity':0.15, stroke:col,'stroke-width':40,'stroke-dasharray':'150 100','opacity':0.8},gl.draft);
  // live length of last segment
  const a=pts[pts.length-2], b=pts[pts.length-1]; const L=Math.hypot(b[0]-a[0],b[1]-a[1]);
  const g=el('g',{transform:`translate(${(a[0]+b[0])/2} ${(a[1]+b[1])/2+200}) scale(1,-1)`},gl.draft); const t=el('text',{x:0,y:0,'text-anchor':'middle','font-size':180,fill:col,class:'lbl-ar','font-weight':'500'},g); t.textContent=(L/1000).toFixed(2).replace('.',',')+' m';
  if (draft.type==='room' && pts.length>2){ const c=polyCentroid(pts); const g2=el('g',{transform:`translate(${c[0]} ${c[1]}) scale(1,-1)`},gl.draft); const t2=el('text',{x:0,y:0,'text-anchor':'middle','font-size':200,fill:col,class:'lbl-ar'},g2); t2.textContent=(polyArea(pts)/1e6).toFixed(2).replace('.',',')+' m²'; }
}
// ---------- łączenie ścian: końce nowych ścian wpinają się w oś innej ściany projektowej lub w lico ściany istniejącej ----------
function projOnSeg(p,a,b){ const vx=b[0]-a[0], vy=b[1]-a[1]; const L2=vx*vx+vy*vy||1; const u=((p[0]-a[0])*vx+(p[1]-a[1])*vy)/L2; return {u, L:Math.sqrt(L2), q:[a[0]+u*vx,a[1]+u*vy]}; }
function lineX(a,b,c,d){ const r=[b[0]-a[0],b[1]-a[1]], q=[d[0]-c[0],d[1]-c[1]]; const den=r[0]*q[1]-r[1]*q[0]; if (Math.abs(den)<1e-6) return null; const t=((c[0]-a[0])*q[1]-(c[1]-a[1])*q[0])/den; return [a[0]+t*r[0],a[1]+t*r[1]]; }
function snapWallEnds(it, tol){
  tol=tol||300; const w=it.w||120; const joined=[false,false];
  const others=visibleItems(floor).filter(o=>o.type==='wall'&&o.id!==it.id);
  [0,it.pts.length-1].forEach((idx,k)=>{
    const p=it.pts[idx]; const nb=it.pts[idx===0?1:idx-1]; let best=null;
    // 1) oś innej ściany projektowej – wzdłuż WŁASNEJ osi (kierunek ściany zostaje), do przecięcia z osią sąsiada
    for (const o of others){ for(let i=1;i<o.pts.length;i++){ const a=o.pts[i-1], b=o.pts[i]; const ow=(o.w||120); const x=lineX(nb,p,a,b); if(!x) continue; const pr=projOnSeg(x,a,b); if (pr.u*pr.L < -ow/2-tol || (pr.u-1)*pr.L > ow/2+tol) continue; const d=Math.hypot(p[0]-x[0],p[1]-x[1]); if (d<=tol && (!best||d<best.d)){ best={d,q:[Math.round(x[0]),Math.round(x[1])],o,a,b}; } } } // zawsze punkt przecięcia osi – ściana zostaje prosta; koniec sąsiada dociągamy niżej
    if (best){ it.pts[idx]=best.q; joined[k]=true;
      // narożnik L: jeśli koniec drugiej ściany jest blisko naszej osi – dociągnij go do naszej osi
      const ours=[it.pts[idx], nb]; for (const endIdx of [0,best.o.pts.length-1]){ const pe=best.o.pts[endIdx]; const pr2=projOnSeg(pe,ours[0],ours[1]); const d2=Math.hypot(pe[0]-pr2.q[0],pe[1]-pr2.q[1]); if (d2<=tol && d2>1 && Math.hypot(pe[0]-best.q[0],pe[1]-best.q[1])<=tol+w){ best.o.pts[endIdx]=[Math.round(pr2.q[0]),Math.round(pr2.q[1])]; } }
      return; }
    // 2) lico ściany istniejącej (lub projektowej dalej) – dotnij/wydłuż wzdłuż własnej osi
    const L=Math.hypot(p[0]-nb[0],p[1]-nb[1])||1; const d=[(p[0]-nb[0])/L,(p[1]-nb[1])/L]; const segs=obstacleSegs(it.id);
    const tOut=rayHit([p[0]-d[0]*60,p[1]-d[1]*60],d,segs,1); // przed nami
    if (tOut!==null && tOut-60<=tol){ it.pts[idx]=[Math.round(p[0]+d[0]*(tOut-60)),Math.round(p[1]+d[1]*(tOut-60))]; joined[k]=true; return; }
    const tBack=rayHit([p[0]+d[0]*60,p[1]+d[1]*60],[-d[0],-d[1]],segs,1); // przestrzeliliśmy – cofnij do lica
    if (tBack!==null && tBack-60<=tol && tBack-60<L-100){ it.pts[idx]=[Math.round(p[0]-d[0]*(tBack-60)),Math.round(p[1]-d[1]*(tBack-60))]; joined[k]=true; }
  });
  return joined;
}
function wallW(){ const sel=document.getElementById('wallW'); if (sel.value==='custom'){ const v=parseFloat((document.getElementById('wallWin').value||'').replace(',','.')); return (v>0?Math.round(v*10):120); } return +sel.value||120; }
function wallSide(){ return +document.getElementById('wallSide').value||0; }
function offsetPolyline(pts, off){ // przesunięcie linii o off w lewo (off>0) / prawo (off<0) – narożniki 90° domykane sumą normalnych
  if (!off || pts.length<2) return pts.map(q=>q.slice()); const n=[]; for(let i=1;i<pts.length;i++){ const L=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])||1; n.push([-(pts[i][1]-pts[i-1][1])/L,(pts[i][0]-pts[i-1][0])/L]); }
  return pts.map((q,i)=>{ const n1=n[Math.max(0,i-1)], n2=n[Math.min(n.length-1,i)]; let ox=n1[0], oy=n1[1]; if (i>0 && i<pts.length-1){ ox=n1[0]+n2[0]; oy=n1[1]+n2[1]; const dot=n1[0]*n2[0]+n1[1]*n2[1]; if (dot<-0.99){ ox=n1[0]; oy=n1[1]; } } return [Math.round(q[0]+ox*off), Math.round(q[1]+oy*off)]; }); }
function straightenWall(it){ if(it.pts.length!==2) return; const [a,b]=it.pts; const dx=b[0]-a[0], dy=b[1]-a[1]; if (Math.abs(dx)>0 && Math.abs(dy)<=Math.abs(dx)*0.09){ const y=Math.round((a[1]+b[1])/2); it.pts=[[a[0],y],[b[0],y]]; } else if (Math.abs(dy)>0 && Math.abs(dx)<=Math.abs(dy)*0.09){ const x=Math.round((a[0]+b[0])/2); it.pts=[[x,a[1]],[x,b[1]]]; } }
function joinAllWalls(){ pushHistory(); const ws=visibleItems(floor).filter(o=>o.type==='wall'); ws.forEach(straightenWall); ws.forEach(w=>{ try{ snapWallEnds(w,300); }catch(e){} }); ws.forEach(w=>{ try{ snapWallEnds(w,120); }catch(e){} }); commit(); }
function wallJoinPatches(it, g){ // łatki w narożnikach: koniec ściany leżący na osi innej ściany
  const w=it.w||120; const others=visibleItems(floor).filter(o=>o.type==='wall'&&o.id!==it.id);
  for (const idx of [0,it.pts.length-1]){ const p=it.pts[idx];
    for (const o of others){ for(let i=1;i<o.pts.length;i++){ const a=o.pts[i-1], b=o.pts[i]; const pr=projOnSeg(p,a,b); const ow=o.w||120; if (pr.u*pr.L < -ow/2-1 || (pr.u-1)*pr.L > ow/2+1) continue; if (Math.hypot(p[0]-pr.q[0],p[1]-pr.q[1])<=2){ const ang=Math.atan2(b[1]-a[1],b[0]-a[0])*180/Math.PI; el('rect',{x:-Math.max(w,ow)/2,y:-ow/2,width:Math.max(w,ow),height:ow,fill:'var(--new)',transform:`translate(${p[0]} ${p[1]}) rotate(${ang})`},g); } } } }
}
// ---------- drzwi jednym kliknięciem: najedź na ścianę -> podgląd drzwi (domyślnie 80 cm) -> klik = wstaw ----------
function doorAtPoint(p, tol){
  tol=tol||14*mmPerPx(); let best=null; const P=[p.x,p.y];
  for (const it of visibleItems(floor)) if(it.type==='wall') for(let i=1;i<it.pts.length;i++){ const a=it.pts[i-1],b=it.pts[i]; const pr=projOnSeg(P,a,b); if(pr.u<0||pr.u>1) continue; const d=Math.hypot(P[0]-pr.q[0],P[1]-pr.q[1]); const th=(it.w||120); if (d<=th/2+tol && (!best||d<best.d)) best={d,a,b,th,u:pr.u,L:pr.L}; }
  if (!best){ const F=MODEL.floors[floor]; const segs=[]; for (const sg of (F.geo.walls||[])) if(sg.k==='l') for(let i=1;i<sg.p.length;i++) segs.push({a:sg.p[i-1],b:sg.p[i],t:0});
    let nf=null; for (const sg of segs){ const pr=projOnSeg(P,sg.a,sg.b); if(pr.u<0||pr.u>1||pr.L<300) continue; const d=Math.hypot(P[0]-pr.q[0],P[1]-pr.q[1]); if(d<=tol+350 && (!nf||d<nf.d)) nf={d,a:sg.a,b:sg.b,q:pr.q,L:pr.L}; }
    if (nf){ const L=nf.L; const ux=(nf.b[0]-nf.a[0])/L, uy=(nf.b[1]-nf.a[1])/L; const nx=-uy, ny=ux; let th=null, sgn=0;
      for (const sg of [1,-1]){ const t=rayHit([nf.q[0]+nx*sg*5,nf.q[1]+ny*sg*5],[nx*sg,ny*sg],segs,1); if(t!==null && t<700 && (th===null||t<th)){ th=t+5; sgn=sg; } }
      if (th===null){ th=250; sgn=((P[0]-nf.q[0])*nx+(P[1]-nf.q[1])*ny)>=0?1:-1; }
      const a=[nf.a[0]+nx*sgn*th/2,nf.a[1]+ny*sgn*th/2], b=[nf.b[0]+nx*sgn*th/2,nf.b[1]+ny*sgn*th/2]; const pr=projOnSeg(P,a,b);
      if (Math.hypot(P[0]-pr.q[0],P[1]-pr.q[1])<=th/2+tol) best={d:nf.d,a,b,th:Math.round(th),u:pr.u,L}; } }
  if (!best) return null;
  const W=+document.getElementById('doorW').value||800; const L=best.L; if (L<W+100) return null;
  const ux=(best.b[0]-best.a[0])/L, uy=(best.b[1]-best.a[1])/L;
  let t=Math.round(best.u*L/10)*10; t=Math.max(W/2+50, Math.min(L-W/2-50, t));
  const c=[best.a[0]+ux*t, best.a[1]+uy*t];
  const p1=[Math.round(c[0]-ux*W/2),Math.round(c[1]-uy*W/2)], p2=[Math.round(c[0]+ux*W/2),Math.round(c[1]+uy*W/2)];
  const side=(P[0]-c[0])*(-uy)+(P[1]-c[1])*ux; // po której stronie osi jest kursor – drzwi otwierają się w tę stronę
  return {pts:[p1,p2], w:best.th+40, flip: side<0};
}
// ---------- model drzwi: ościeżnica regulowana (stojaki 45 mm + opaski 70 mm nachodzące na ścianę z obu stron), skrzydło 40 mm, 3 zawiasy, klamka ----------
const JAMB=45, ARCH_W=70, ARCH_T=16, LEAF_T=40, LEAF_H=2040;
let dwgSegCache=null;
function dwgWallSegs(){ if(dwgSegCache&&dwgSegCache.floor===floor) return dwgSegCache.segs; const F=MODEL.floors[floor]; const segs=[]; for (const sg of (F.geo.walls||[])) if(sg.k==='l') for(let i=1;i<sg.p.length;i++) segs.push({a:sg.p[i-1],b:sg.p[i],t:0}); dwgSegCache={floor,segs}; return segs; }
function doorWallThick(it){ // grubość ściany, w której siedzą drzwi – ościeżnica regulowana dopasowuje się automatycznie
  const [a,b]=it.pts; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const u=[(b[0]-a[0])/L,(b[1]-a[1])/L]; const nl=[-u[1],u[0]]; const m=[(a[0]+b[0])/2,(a[1]+b[1])/2];
  for (const o of visibleItems(floor)) if(o.type==='wall') for(let i=1;i<o.pts.length;i++){ const pa=o.pts[i-1], pb=o.pts[i]; const Lw=Math.hypot(pb[0]-pa[0],pb[1]-pa[1])||1; const d=[(pb[0]-pa[0])/Lw,(pb[1]-pa[1])/Lw]; if (Math.abs(d[0]*u[0]+d[1]*u[1])<0.95) continue; if (distPtSeg(m,pa,pb)<=(o.w||120)/2+40) return o.w||120; }
  const segs=dwgWallSegs(); let best=null;
  for (const q of [[a[0]-u[0]*120,a[1]-u[1]*120],[b[0]+u[0]*120,b[1]+u[1]*120]]){ const t1=rayHit(q,nl,segs,1), t2=rayHit(q,[-nl[0],-nl[1]],segs,1); if (t1!==null&&t2!==null&&t1+t2<900){ const th=Math.round(t1+t2); if(best===null||th<best) best=th; } }
  return best!==null?best:Math.max(60,(it.w||300)-40);
}
function doorFrame(it){ const [a,b]=it.pts; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const u=[(b[0]-a[0])/L,(b[1]-a[1])/L]; const nl=[-u[1],u[0]]; const sgn=it.flip?-1:1; const n=[nl[0]*sgn,nl[1]*sgn]; let th; try{ th=doorWallThick(it); }catch(e){ th=Math.max(60,(it.w||300)-40); } return {a,b,L,u,nl,n,sgn,th}; }
function drawDoor2D(it, parent, col){
  const {a,b,L,u,nl,n,th}=doorFrame(it); const P=(o,du,dn)=>[o[0]+u[0]*du+nl[0]*dn, o[1]+u[1]*du+nl[1]*dn]; const poly=(pts,attrs)=>el('polygon',Object.assign({points:pts.map(q=>q.join(',')).join(' ')},attrs),parent);
  // otwór w ścianie = światło + stojaki ościeżnicy
  const g0=P(a,-JAMB,0), g1=P(b,JAMB,0); el('line',{x1:g0[0],y1:g0[1],x2:g1[0],y2:g1[1],stroke:'var(--canvas)','stroke-width':th+40},parent);
  if (it.open){ el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:col,'stroke-width':20},parent); }
  else {
    // stojaki ościeżnicy (w grubości ściany)
    poly([P(a,-JAMB,-th/2),P(a,0,-th/2),P(a,0,th/2),P(a,-JAMB,th/2)],{fill:'var(--canvas)',stroke:col,'stroke-width':14});
    poly([P(b,0,-th/2),P(b,JAMB,-th/2),P(b,JAMB,th/2),P(b,0,th/2)],{fill:'var(--canvas)',stroke:col,'stroke-width':14});
    // opaski regulowanej ościeżnicy – nachodzą na lico ściany z obu stron
    for (const sd of [1,-1]){ const z0=sd*th/2, z1=sd*(th/2+ARCH_T);
      poly([P(a,-ARCH_W,z0),P(a,0,z0),P(a,0,z1),P(a,-ARCH_W,z1)],{fill:col,stroke:'none'});
      poly([P(b,0,z0),P(b,ARCH_W,z0),P(b,ARCH_W,z1),P(b,0,z1)],{fill:col,stroke:'none'}); }
    // skrzydło otwarte 90° (grubość 40 mm) + 3 zawiasy
    const tip=[a[0]+n[0]*L,a[1]+n[1]*L];
    poly([a,[a[0]+u[0]*LEAF_T,a[1]+u[1]*LEAF_T],[tip[0]+u[0]*LEAF_T,tip[1]+u[1]*LEAF_T],tip],{fill:'var(--canvas)',stroke:col,'stroke-width':18});
    // łuk otwierania – wypukły, środek w zawiasie
    let d='M'+tip[0]+' '+tip[1]; for(let k=1;k<=16;k++){ const f=k/16*Math.PI/2; d+='L'+(a[0]+(n[0]*Math.cos(f)+u[0]*Math.sin(f))*L)+' '+(a[1]+(n[1]*Math.cos(f)+u[1]*Math.sin(f))*L); }
    el('path',{d,fill:'none',stroke:col,'stroke-width':14,'stroke-dasharray':'none'},parent);
    // klamka
    const h=[a[0]+n[0]*(L-90)+u[0]*(LEAF_T+40), a[1]+n[1]*(L-90)+u[1]*(LEAF_T+40)]; el('circle',{cx:h[0],cy:h[1],r:28,fill:col},parent);
  }
  // etykieta
  const g=el('g',{transform:`translate(${(a[0]+b[0])/2+n[0]*L*0.6} ${(a[1]+b[1])/2+n[1]*L*0.6}) scale(1,-1)`,'pointer-events':'none'},parent); const t=el('text',{x:0,y:0,'text-anchor':'middle','font-size':150,fill:col,class:'lbl-ar'},g); t.textContent=it.open?('otwór '+(L/10).toFixed(0)+' cm'):((L/10).toFixed(0)+' '+doorSide(it));
  // strefa chwytania
  el('line',{x1:g0[0],y1:g0[1],x2:g1[0],y2:g1[1],stroke:'transparent','stroke-width':Math.max(th+40,14*mmPerPx()),'pointer-events':'stroke',class:'hit'},parent);
}
function drawDoorPreview(dd, parent){ drawDoor2D(Object.assign({open:false},dd), parent, 'var(--sel)'); }
// ---------- Wytnij: usuń odcinek ściany między najbliższymi ścianami poprzecznymi ----------
function dwgWallAxisAt(P, tol){
  const segs=dwgWallSegs(); let nf=null; for (const sg of segs){ const pr=projOnSeg(P,sg.a,sg.b); if(pr.u<0||pr.u>1||pr.L<300) continue; const d=Math.hypot(P[0]-pr.q[0],P[1]-pr.q[1]); if(d<=tol+350 && (!nf||d<nf.d)) nf={d,a:sg.a,b:sg.b,q:pr.q,L:pr.L}; }
  if (!nf) return null; const L=nf.L; const ux=(nf.b[0]-nf.a[0])/L, uy=(nf.b[1]-nf.a[1])/L; const nx=-uy, ny=ux; let th=null, sgn=0;
  for (const sg of [1,-1]){ const t=rayHit([nf.q[0]+nx*sg*5,nf.q[1]+ny*sg*5],[nx*sg,ny*sg],segs,1); if(t!==null && t<700 && (th===null||t<th)){ th=t+5; sgn=sg; } }
  if (th===null) return null;
  const a=[nf.a[0]+nx*sgn*th/2,nf.a[1]+ny*sgn*th/2], b=[nf.b[0]+nx*sgn*th/2,nf.b[1]+ny*sgn*th/2]; const pr=projOnSeg(P,a,b); if (Math.hypot(P[0]-pr.q[0],P[1]-pr.q[1])>th/2+tol) return null;
  return {a,b,th:Math.round(th),u:[ux,uy],q:pr.q,L};
}
function nearestCross(q,u,segs,half){ const n=[-u[1],u[0]]; let best=null; for (const off of [0,half-5,-(half-5)]){ const t=rayHit([q[0]+n[0]*off,q[1]+n[1]*off],u,segs,1); if(t!==null && (best===null||t<best)) best=t; } return best; }
function cutWallAt(p){
  const tol=10*mmPerPx(); const P=[p.x,p.y]; let best=null;
  for (const it of visibleItems(floor)) if(it.type==='wall') for(let i=1;i<it.pts.length;i++){ const a=it.pts[i-1],b=it.pts[i]; const pr=projOnSeg(P,a,b); if(pr.u<0||pr.u>1) continue; const d=Math.hypot(P[0]-pr.q[0],P[1]-pr.q[1]); if(d<=(it.w||120)/2+tol && (!best||d<best.d)) best={d,it,i,a,b,q:pr.q}; }
  if (best){ const {it,i,a,b,q}=best; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const u=[(b[0]-a[0])/L,(b[1]-a[1])/L]; const segs=obstacleSegs(it.id); const tq=(q[0]-a[0])*u[0]+(q[1]-a[1])*u[1];
    const hw=(it.w||120)/2; const tR=nearestCross(q,u,segs,hw), tL=nearestCross(q,[-u[0],-u[1]],segs,hw); const endR=(tR!==null && tq+tR<L)?tq+tR:L; const endL=(tL!==null && tq-tL>0)?tq-tL:0;
    const P1=t=>[Math.round(a[0]+u[0]*t),Math.round(a[1]+u[1]*t)]; pushHistory();
    const parts=[]; const left=it.pts.slice(0,i); if(endL>60) left.push(P1(endL)); if(left.length>=2) parts.push(Object.assign({},it,{id:uid(),pts:left}));
    const right=it.pts.slice(i); if(L-endR>60) right.unshift(P1(endR)); if(right.length>=2) parts.push(Object.assign({},it,{id:uid(),pts:right}));
    const idx=project[floor].items.indexOf(it); project[floor].items.splice(idx,1,...parts);
    // drzwi w wyciętym odcinku
    const cutA=P1(endL), cutB=P1(endR); project[floor].items=project[floor].items.filter(o=>{ if(o.type!=='door'||(o.v&&o.v!==sel[floor])) return true; const m=[(o.pts[0][0]+o.pts[1][0])/2,(o.pts[0][1]+o.pts[1][1])/2]; const pr=projOnSeg(m,cutA,cutB); return !(pr.u>0&&pr.u<1&&Math.hypot(m[0]-pr.q[0],m[1]-pr.q[1])<=(it.w||120)/2+40); });
    selectedId=null; commit(); hintToast('Wycięto '+((endR-endL)/1000).toFixed(2).replace('.',',')+' m ściany'+(parts.length?'; zostały '+parts.length+' odcinki.':'.')); return true; }
  const ax=dwgWallAxisAt(P,tol); if (!ax) return false;
  const segs=dwgWallSegs().concat(obstacleSegs(null)); const u=ax.u; const tR=nearestCross(ax.q,u,segs,ax.th/2), tL=nearestCross(ax.q,[-u[0],-u[1]],segs,ax.th/2); if (tR===null||tL===null||tR>20000||tL>20000) return false;
  const pA=[Math.round(ax.q[0]-u[0]*tL),Math.round(ax.q[1]-u[1]*tL)], pB=[Math.round(ax.q[0]+u[0]*tR),Math.round(ax.q[1]+u[1]*tR)];
  pushHistory(); const it={id:uid(),type:'demo',pts:[pA,pB],w:ax.th,v:sel[floor]||undefined,label:'wyburzenie '+((tL+tR)/1000).toFixed(2).replace('.',',')+' m'}; project[floor].items.push(it); selectedId=it.id; commit(); hintToast('Ściana istniejąca: wyburzenie odcinka '+((tL+tR)/1000).toFixed(2).replace('.',',')+' m (gr. '+ax.th+' mm) między ścianami poprzecznymi.'); return true;
}
function finishDraft(){ try{ finishDraftInner(); }catch(err){ diag('finishDraft',err); draft=null; drawDraft(); } }
function finishDraftInner(){
  if (!draft) return;
  const t=draft.type; const n=draft.pts.length;
  const ok = (t==='room'&&n>=3)||((t==='wall'||t==='demo')&&n>=2);
  if (ok){ pushHistory(); const it={id:uid(),type:t,pts:draft.pts,v:sel[floor]||undefined}; if(t==='wall'){ it.w=wallW(); const side=wallSide(); if(side) it.pts=offsetPolyline(it.pts, side*it.w/2); straightenWall(it); snapWallEnds(it); } if(t==='demo') it.w=160; if(t==='room'){ it.unit=document.getElementById('unitSel').value||null; it.label=''; it.anchor=polyCentroid(it.pts).map(v=>Math.round(v)); } project[floor].items.push(it); selectedId=it.id; commit(); if(t==='room'){ showInlineEdit(it,{clientX:lastClient.x,clientY:lastClient.y}); } }
  draft=null; drawDraft();
}
let lastClient={x:0,y:0};

// ---------- pointer handling ----------
let panning=null, dragging=null, wallDrag=null, doorDrag=null, suppressClick=false, inkDraft=null, anchorMove=null, endDrag=null;
// ---- geometry helpers for wall dragging ----
function obstacleSegs(excludeId){
  const F=MODEL.floors[floor]; const out=[];
  for (const s of (F.geo.walls||[])) if(s.k==='l') for(let i=1;i<s.p.length;i++) out.push({a:s.p[i-1],b:s.p[i],t:0});
  for (const it of visibleItems(floor)) if(it.type==='wall'&&it.id!==excludeId) for(let i=1;i<it.pts.length;i++) out.push({a:it.pts[i-1],b:it.pts[i],t:it.w||120});
  return out;
}
function rayHit(o,d,segs,minT){ // nearest intersection of ray o+t*d with segments; returns distance to the obstacle FACE
  let best=null;
  for (const s of segs){
    const ex=s.b[0]-s.a[0], ey=s.b[1]-s.a[1]; const den=d[0]*ey-d[1]*ex; if(Math.abs(den)<1e-9) continue;
    const wx=s.a[0]-o[0], wy=s.a[1]-o[1];
    const t=(wx*ey-wy*ex)/den; const u=(wx*d[1]-wy*d[0])/den;
    if (u<-0.001||u>1.001) continue; const tf=t-s.t/2; if (tf<(minT||1)) continue;
    if (best===null||tf<best) best=tf;
  }
  return best;
}
function distPtSeg(p,a,b){ const vx=b[0]-a[0], vy=b[1]-a[1]; const L2=vx*vx+vy*vy||1; let u=((p[0]-a[0])*vx+(p[1]-a[1])*vy)/L2; u=Math.max(0,Math.min(1,u)); return Math.hypot(p[0]-(a[0]+u*vx), p[1]-(a[1]+u*vy)); }
// ---------- kolizje mebli ze ścianami ----------
let obstCache=null;
function wallSegsAll(){
  if (obstCache && obstCache.floor===floor && obstCache.n===project[floor].items.length && obstCache.v===sel[floor] && obstCache.stamp===obstStamp) return obstCache.segs;
  const F=MODEL.floors[floor]; const segs=[];
  const wsegs=[]; for (const s of (F.geo.walls||[])) if(s.k==='l') for(let i=1;i<s.p.length;i++) wsegs.push([s.p[i-1],s.p[i]]);
  const nearWall=(p)=>wsegs.some(([a,b])=>distPtSeg(p,a,b)<=120);
  // wyburzenia: fragmenty linii inwentaryzacji leżące w pasie wyburzenia nie są przeszkodą (docinamy odcinek)
  const demos=[]; for (const it of visibleItems(floor)) if(it.type==='demo') for(let i=1;i<it.pts.length;i++) demos.push({a:it.pts[i-1],b:it.pts[i],r:(it.w||160)/2+60});
  const clipDemo=(p,q)=>{ let parts=[[p,q]]; for (const d of demos){ const out=[]; for (const [a,b] of parts){ const vx=b[0]-a[0], vy=b[1]-a[1]; const L=Math.hypot(vx,vy)||1; const ux=vx/L, uy=vy/L; const dvx=d.b[0]-d.a[0], dvy=d.b[1]-d.a[1]; const dL=Math.hypot(dvx,dvy)||1; if (Math.abs(ux*dvx/dL+uy*dvy/dL)<0.9){ out.push([a,b]); continue; } const dist=Math.abs((d.a[0]-a[0])*uy-(d.a[1]-a[1])*ux); if (dist>d.r){ out.push([a,b]); continue; } let t0=((d.a[0]-a[0])*ux+(d.a[1]-a[1])*uy), t1=((d.b[0]-a[0])*ux+(d.b[1]-a[1])*uy); if(t0>t1){ const tt=t0; t0=t1; t1=tt; } t0=Math.max(0,t0-d.r); t1=Math.min(L,t1+d.r); if (t1<=0||t0>=L){ out.push([a,b]); continue; } if (t0>30) out.push([a,[a[0]+ux*t0,a[1]+uy*t0]]); if (L-t1>30) out.push([[a[0]+ux*t1,a[1]+uy*t1],b]); } parts=out; } return parts; };
  for (const lay of ['walls','windows','sills']) for (const s of (F.geo[lay]||[])) if(s.k==='l') for(let i=1;i<s.p.length;i++){ if (lay!=='walls' && ATTIC && floor===ATTIC.floor && !(nearWall(s.p[i-1]) && nearWall(s.p[i]))) continue; /* okna połaciowe narysowane w rzucie nie są przeszkodą */ for (const sg of (demos.length?clipDemo(s.p[i-1],s.p[i]):[[s.p[i-1],s.p[i]]])) segs.push(sg); }
  for (const it of visibleItems(floor)) if(it.type==='wall'){ const hw=(it.w||120)/2; for(let i=1;i<it.pts.length;i++){ const a=it.pts[i-1],b=it.pts[i]; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const nx=-(b[1]-a[1])/L*hw, ny=(b[0]-a[0])/L*hw; const ex=(b[0]-a[0])/L*hw, ey=(b[1]-a[1])/L*hw; const a1=[a[0]-ex,a[1]-ey], b1=[b[0]+ex,b[1]+ey]; segs.push([[a1[0]+nx,a1[1]+ny],[b1[0]+nx,b1[1]+ny]]); segs.push([[a1[0]-nx,a1[1]-ny],[b1[0]-nx,b1[1]-ny]]); segs.push([[a1[0]+nx,a1[1]+ny],[a1[0]-nx,a1[1]-ny]]); segs.push([[b1[0]+nx,b1[1]+ny],[b1[0]-nx,b1[1]-ny]]); } }
  obstCache={floor,n:project[floor].items.length,v:sel[floor],stamp:obstStamp,segs}; return segs;
}
let obstStamp=0;
function rectOf(it){ const [a,b]=it.pts; return {x0:Math.min(a[0],b[0]),y0:Math.min(a[1],b[1]),x1:Math.max(a[0],b[0]),y1:Math.max(a[1],b[1])}; }
function segHitsRect(sg,r,eps){ // Liang–Barsky: czy odcinek przechodzi przez wnętrze prostokąta (zmniejszonego o eps)
  const x0=r.x0+eps,y0=r.y0+eps,x1=r.x1-eps,y1=r.y1-eps; if(x1<=x0||y1<=y0) return false;
  const [a,b]=sg; const dx=b[0]-a[0], dy=b[1]-a[1]; let t0=0,t1=1;
  const p=[-dx,dx,-dy,dy], q=[a[0]-x0,x1-a[0],a[1]-y0,y1-a[1]];
  for(let i=0;i<4;i++){ if(p[i]===0){ if(q[i]<0) return false; } else { const t=q[i]/p[i]; if(p[i]<0){ if(t>t1) return false; if(t>t0) t0=t; } else { if(t<t0) return false; if(t<t1) t1=t; } } }
  return (t1-t0)*Math.hypot(dx,dy) > 1;
}
function rectCollisions(r, segs){ return segs.filter(sg=>segHitsRect(sg,r,5)); }
function rectFree(r, segs){ return rectCollisions(r,segs).length===0; }
function translateRect(r,dx,dy){ return {x0:r.x0+dx,y0:r.y0+dy,x1:r.x1+dx,y1:r.y1+dy}; }
function resolveRect(r, segs){ // zwraca przesunięty prostokąt bez kolizji albo null
  if (rectFree(r,segs)) return r;
  const hits=rectCollisions(r,segs); const cands=[];
  for (const [a,b] of hits){
    if (Math.abs(a[0]-b[0])<2){ const x=a[0]; cands.push([x-r.x0,0]); cands.push([x-r.x1,0]); }
    else if (Math.abs(a[1]-b[1])<2){ const y=a[1]; cands.push([0,y-r.y0]); cands.push([0,y-r.y1]); }
    else { const x=(a[0]+b[0])/2, y=(a[1]+b[1])/2; cands.push([x-r.x0,0]);cands.push([x-r.x1,0]);cands.push([0,y-r.y0]);cands.push([0,y-r.y1]); }
  }
  cands.sort((p,q)=>Math.hypot(p[0],p[1])-Math.hypot(q[0],q[1]));
  for (const c of cands){ if(Math.hypot(c[0],c[1])>1500) break; const t=translateRect(r,c[0],c[1]); if(rectFree(t,segs)) return t; }
  for (const c of cands){ for (const d of cands){ if((c[0]&&d[0])||(c[1]&&d[1])) continue; const t=translateRect(r,c[0]+d[0],c[1]+d[1]); if(Math.hypot(c[0]+d[0],c[1]+d[1])<=1500 && rectFree(t,segs)) return t; } }
  return null;
}
function snapFlush(r, segs, maxGap){ // dosunięcie do najbliższych lic (max 2 osie)
  let cur=r;
  for (let pass=0; pass<2; pass++){
    let best=null;
    for (const [a,b] of segs){
      if (Math.abs(a[0]-b[0])<2){ const x=a[0], ylo=Math.min(a[1],b[1]), yhi=Math.max(a[1],b[1]); if(yhi<cur.y0+50||ylo>cur.y1-50) continue;
        const gL=cur.x0-x, gR=x-cur.x1; if(gL>=0&&gL<=maxGap&&(!best||gL<best.g)) best={g:gL,dx:-gL,dy:0}; if(gR>=0&&gR<=maxGap&&(!best||gR<best.g)) best={g:gR,dx:gR,dy:0}; }
      else if (Math.abs(a[1]-b[1])<2){ const y=a[1], xlo=Math.min(a[0],b[0]), xhi=Math.max(a[0],b[0]); if(xhi<cur.x0+50||xlo>cur.x1-50) continue;
        const gB=cur.y0-y, gT=y-cur.y1; if(gB>=0&&gB<=maxGap&&(!best||gB<best.g)) best={g:gB,dx:0,dy:-gB}; if(gT>=0&&gT<=maxGap&&(!best||gT<best.g)) best={g:gT,dx:0,dy:gT}; }
    }
    if (!best || best.g<1){ if(best&&best.g<1){ /* już dosunięte w tej osi – spróbuj drugiej */ segs=segs.filter(sg=>!(best.dx?Math.abs(sg[0][0]-sg[1][0])<2:Math.abs(sg[0][1]-sg[1][1])<2)); continue; } break; }
    const t=translateRect(cur,best.dx,best.dy); if(rectFree(t,segs)) cur=t;
    segs=segs.filter(sg=>!(best.dx?Math.abs(sg[0][0]-sg[1][0])<2:Math.abs(sg[0][1]-sg[1][1])<2)); // druga iteracja: druga oś
  }
  return cur;
}
function applyRect(it,r){ it.pts=[[Math.round(r.x0),Math.round(r.y0)],[Math.round(r.x1),Math.round(r.y1)]]; }
const PAX_W=[1500,1750,2000,2500,2750,3000];
function isPax(it){ return it.kind==='wardrobe'||String(it.kind||'').startsWith('pax'); }
function fitFurn(it){ // po upuszczeniu: wypchnij ze ścian, dosuń do lica; zwraca true gdy OK, false gdy nierozwiązana kolizja
  const segs=wallSegsAll(); let r=rectOf(it);
  const res=resolveRect(r,segs); if(!res) return false;
  r=snapFlush(res,segs,250); applyRect(it,r); return true;
}
function shrinkFurn(it){ // pomniejsz do wolnego pola między ścianami (dla PAX – do modułu)
  const segs=wallSegsAll(); const r=rectOf(it); const cx=(r.x0+r.x1)/2, cy=(r.y0+r.y1)/2;
  const asSeg=segs.map(sg=>({a:sg[0],b:sg[1],t:0}));
  const L=rayHit([cx,cy],[-1,0],asSeg,1), R=rayHit([cx,cy],[1,0],asSeg,1), D=rayHit([cx,cy],[0,-1],asSeg,1), U=rayHit([cx,cy],[0,1],asSeg,1);
  if ([L,R,D,U].some(v=>v===null)) return false;
  const spanX=L+R, spanY=D+U; let w=r.x1-r.x0, h=r.y1-r.y0;
  const horiz = w>=h; // dłuższy bok = szerokość mebla
  if (isPax(it)){ const span=horiz?spanX:spanY; const ok=PAX_W.filter(p=>p<=span-20); if(!ok.length) return false; const nw=ok[ok.length-1]; if(horiz) w=Math.min(w,nw); else h=Math.min(h,nw); if(horiz) h=Math.min(h,spanY-20); else w=Math.min(w,spanX-20); }
  else { w=Math.min(w,spanX-20); h=Math.min(h,spanY-20); }
  if (w<200||h<200) return false;
  const nr={x0:cx-L+10,y0:cy-D+10,x1:cx-L+10+w,y1:cy-D+10+h}; // zakotwicz przy lewej/dolnej ścianie
  applyRect(it,nr); const r2=rectOf(it); const fixed=resolveRect(r2,segs); if(!fixed) return false; applyRect(it,snapFlush(fixed,segs,250)); return true;
}
function collidingFurn(){ const segs=wallSegsAll(); return visibleItems(floor).filter(it=>it.type==='furn' && (!rectFree(rectOf(it),segs) || tooLowFor(it))); }
const cbox=document.getElementById('conflictBox');
function hideConflict(){ cbox.hidden=true; cbox.innerHTML=''; }
function showConflict(items, context){
  if (!items.length){ hideConflict(); return; }
  const names=items.map(it=>{ const l=tooLowFor(it); return (it.label||(FURN[it.kind]?FURN[it.kind].n:it.kind))+(l?` (za nisko pod skosem: sufit ${(l.hmin/1000).toFixed(2).replace('.',',')} m, mebel ${(l.need/1000).toFixed(2).replace('.',',')} m)`:''); }).join(', ');
  cbox.innerHTML=`<div><b>Kolizja ze ścianą lub skosem:</b> ${names}. Co robimy?</div><div class="row"><button class="btn" id="cfMove">Przesuń mebel</button><button class="btn" id="cfShrink">Pomniejsz mebel${items.some(isPax)?' (do modułu PAX)':''}</button><button class="btn" id="cfUndo">Cofnij ${context==='wall'?'ścianę':'zmianę'}</button><button class="btn" id="cfKeep">Zostaw (zaznacz)</button></div><p class="hint" id="cfMsg"></p>`;
  cbox.hidden=false;
  document.getElementById('cfMove').addEventListener('click',()=>{ pushHistory(); const left=[]; for(const it of items){ if(!fitFurn(it)) left.push(it); } commit(); if(left.length){ document.getElementById('cfMsg').textContent='Nie da się przesunąć bez kolizji: '+left.map(i=>i.label||i.kind).join(', ')+' – pomniejsz albo przesuń ścianę.'; } else hideConflict(); });
  document.getElementById('cfShrink').addEventListener('click',()=>{ pushHistory(); const left=[]; for(const it of items){ if(!shrinkFurn(it)) left.push(it); } commit(); if(left.length){ document.getElementById('cfMsg').textContent='Za mało miejsca nawet na najmniejszy moduł (PAX 150) lub mebel: '+left.map(i=>i.label||i.kind).join(', ')+' – zmień lokalizację lub przesuń ścianę.'; } else hideConflict(); });
  document.getElementById('cfUndo').addEventListener('click',()=>{ undo(); hideConflict(); });
  document.getElementById('cfKeep').addEventListener('click',()=>{ hideConflict(); });
}
function afterFurnChange(it){ // wywołać po upuszczeniu / postawieniu / zmianie wymiaru
  if (!fitFurn(it)){ commit(); showConflict([it],'furn'); return; }
  commit(); hideConflict();
}
function startEndDrag(it,e){ // złap koniec ściany: skracanie/wydłużanie wzdłuż osi, wydłużenie maks. do najbliższej ściany
  const q=svgPoint(e); const r=Math.max(14*mmPerPx(), (it.w||120)); let idx=-1; for (const k of [0,1]){ if (Math.hypot(q.x-it.pts[k][0],q.y-it.pts[k][1])<=r) idx=k; } if (idx<0) return false;
  const fix=it.pts[1-idx], end=it.pts[idx]; const L=Math.hypot(end[0]-fix[0],end[1]-fix[1]); if(L<1) return false; const d=[(end[0]-fix[0])/L,(end[1]-fix[1])/L];
  const segs=obstacleSegs(it.id); const hw=(it.w||120)/2;
  let maxT=null; for (const off of [0,hw-5,-(hw-5)]){ const n=[-d[1],d[0]]; const t=rayHit([fix[0]+n[0]*off+d[0]*(hw+5),fix[1]+n[1]*off+d[1]*(hw+5)],d,segs,1); if(t!==null && (maxT===null||t+hw+5<maxT)) maxT=t+hw+5; }
  if (maxT===null) maxT=60000;
  let minT=100; for (const o of visibleItems(floor)) if(o.type==='door'){ const m=[(o.pts[0][0]+o.pts[1][0])/2,(o.pts[0][1]+o.pts[1][1])/2]; if (distPtSeg(m,fix,end)<=hw+40){ for (const pp of o.pts){ const t=(pp[0]-fix[0])*d[0]+(pp[1]-fix[1])*d[1]+JAMB; if(t>minT) minT=t; } } }
  pushHistory(); endDrag={it,idx,fix:fix.slice(),d,L0:L,maxT:Math.max(maxT,minT),minT,moved:false}; selectedId=it.id; svg.setPointerCapture(e.pointerId); return true; }
function updateEndDrag(e){ const E=endDrag; const q=svgPoint(e); let t=(q.x-E.fix[0])*E.d[0]+(q.y-E.fix[1])*E.d[1]; t=Math.round(t/10)*10; t=Math.max(E.minT,Math.min(E.maxT,t)); const np=[Math.round(E.fix[0]+E.d[0]*t),Math.round(E.fix[1]+E.d[1]*t)]; if(np[0]!==E.it.pts[E.idx][0]||np[1]!==E.it.pts[E.idx][1]){ E.moved=true; E.it.pts[E.idx]=np; drawProject(); }
  gl.draft.innerHTML=''; const g=el('g',{transform:`translate(${np[0]+E.d[0]*250} ${np[1]+E.d[1]*250}) scale(1,-1)`},gl.draft); const tx=el('text',{x:0,y:0,'text-anchor':'middle','font-size':170,fill:'var(--sel)',class:'lbl-ar','font-weight':'600'},g); tx.textContent='L = '+(t/1000).toFixed(2).replace('.',',')+' m'+(t>=E.maxT-1?' (do ściany)':''); }
function startWallDrag(it,e){
  const a=it.pts[0], b=it.pts[1]; const L=Math.hypot(b[0]-a[0],b[1]-a[1]); if(L<1) return false;
  const d=[(b[0]-a[0])/L,(b[1]-a[1])/L], n=[-d[1],d[0]]; const q=svgPoint(e);
  const segs=obstacleSegs(it.id);
  const touchA = rayHit([a[0]+d[0]*60,a[1]+d[1]*60],[-d[0],-d[1]],segs,1)<=300;
  const touchB = rayHit([b[0]-d[0]*60,b[1]-d[1]*60],d,segs,1)<=300;
  // attached items: other walls' endpoints, doors, room vertices lying on this wall
  const att=[];
  for (const o of visibleItems(floor)){
    if (o.id===it.id) continue;
    if (o.type==='wall'||o.type==='demo'){ o.pts.forEach((p,i)=>{ if((i===0||i===o.pts.length-1)&&distPtSeg(p,a,b)<=(it.w||120)/2+100){ // koniec ściany przyległej idzie za nami tylko, gdy ta ściana jest prostopadła (ruch wzdłuż jej osi) – nigdy nie krzywimy ścian
          const nb=o.pts[i===0?1:i-1]; const Lo=Math.hypot(p[0]-nb[0],p[1]-nb[1])||1; const dA=[(p[0]-nb[0])/Lo,(p[1]-nb[1])/Lo]; if (Math.abs(dA[0]*n[0]+dA[1]*n[1])>0.7) att.push({o,i}); } }); }
    else if (o.type==='door'){ if(o.pts.every(p=>distPtSeg(p,a,b)<=(it.w||120)/2+100)) o.pts.forEach((p,i)=>att.push({o,i})); }
    else if (o.type==='room'){ o.pts.forEach((p,i)=>{ if(distPtSeg(p,a,b)<=(it.w||120)/2+100) att.push({o,i}); }); }
  }
  pushHistory();
  wallDrag={it,d,n,sx:q.x,sy:q.y,orig:[a.slice(),b.slice()],touchA,touchB,segs,att:att.map(x=>({o:x.o,i:x.i,p:x.o.pts[x.i].slice()})),off:0,moved:false};
  selectedId=it.id; svg.setPointerCapture(e.pointerId); return true;
}
function updateWallDrag(e){
  const W=wallDrag; const q=svgPoint(e); let off=(q.x-W.sx)*W.n[0]+(q.y-W.sy)*W.n[1]; off=Math.round(off/10)*10; W.off=off; W.moved=W.moved||off!==0;
  let a=[W.orig[0][0]+W.n[0]*off, W.orig[0][1]+W.n[1]*off], b=[W.orig[1][0]+W.n[0]*off, W.orig[1][1]+W.n[1]*off];
  const mid=[(a[0]+b[0])/2,(a[1]+b[1])/2]; const half=(W.it.w||120)/2;
  if (W.touchB){ const t=rayHit(mid,W.d,W.segs,50); if(t!==null&&t<30000) b=[mid[0]+W.d[0]*t, mid[1]+W.d[1]*t]; }
  if (W.touchA){ const t=rayHit(mid,[-W.d[0],-W.d[1]],W.segs,50); if(t!==null&&t<30000) a=[mid[0]-W.d[0]*t, mid[1]-W.d[1]*t]; }
  W.it.pts=[[Math.round(a[0]),Math.round(a[1])],[Math.round(b[0]),Math.round(b[1])]];
  for (const x of W.att){ x.o.pts[x.i]=[Math.round(x.p[0]+W.n[0]*off), Math.round(x.p[1]+W.n[1]*off)]; }
  drawProject();
  // live distances to parallel obstacles on both sides + length
  gl.draft.innerHTML='';
  const segs2=obstacleSegs(W.it.id);
  [[W.n[0],W.n[1]],[-W.n[0],-W.n[1]]].forEach(dir=>{ const t=rayHit(mid,dir,segs2,1); if(t!==null&&t<30000){ const p2=[mid[0]+dir[0]*(t+half),mid[1]+dir[1]*(t+half)]; const p1=[mid[0]+dir[0]*half,mid[1]+dir[1]*half]; el('line',{x1:p1[0],y1:p1[1],x2:p2[0],y2:p2[1],stroke:'var(--accent)','stroke-width':20,'stroke-dasharray':'100 60'},gl.draft); const g=el('g',{transform:`translate(${(p1[0]+p2[0])/2+W.d[0]*250} ${(p1[1]+p2[1])/2+W.d[1]*250}) scale(1,-1)`},gl.draft); const tx=el('text',{x:0,y:0,'text-anchor':'middle','font-size':200,fill:'var(--accent)',class:'lbl-ar','font-weight':'600'},g); tx.textContent=(t/1000).toFixed(2).replace('.',',')+' m'; } });
  const fsegs=[]; for (const o of visibleItems(floor)) if(o.type==='furn'){ const q=rectOf(o); fsegs.push({a:[q.x0,q.y0],b:[q.x1,q.y0],t:0},{a:[q.x1,q.y0],b:[q.x1,q.y1],t:0},{a:[q.x1,q.y1],b:[q.x0,q.y1],t:0},{a:[q.x0,q.y1],b:[q.x0,q.y0],t:0}); }
  [[W.n[0],W.n[1]],[-W.n[0],-W.n[1]]].forEach(dir=>{ const tf=rayHit(mid,dir,fsegs,1); if(tf!==null&&tf<4000){ const p1=[mid[0]+dir[0]*half,mid[1]+dir[1]*half]; const p2=[mid[0]+dir[0]*(tf),mid[1]+dir[1]*(tf)]; const gg=el('g',{transform:`translate(${(p1[0]+p2[0])/2-W.d[0]*350} ${(p1[1]+p2[1])/2-W.d[1]*350}) scale(1,-1)`},gl.draft); const tx=el('text',{x:0,y:0,'text-anchor':'middle','font-size':170,fill:(tf-half)<800?'var(--new)':'var(--door)',class:'lbl-ar','font-weight':'600'},gg); tx.textContent='do mebla '+fm(tf-half)+' m'; } });
  const Lw=Math.hypot(b[0]-a[0],b[1]-a[1]); const g2=el('g',{transform:`translate(${mid[0]-W.n[0]*300} ${mid[1]-W.n[1]*300}) scale(1,-1)`},gl.draft); const t2=el('text',{x:0,y:0,'text-anchor':'middle','font-size':160,fill:'var(--new)',class:'lbl-ar'},g2); t2.textContent='L = '+(Lw/1000).toFixed(2).replace('.',',')+' m';
}
svg.addEventListener('pointerdown',e=>{
  lastClient={x:e.clientX,y:e.clientY}; DIAG.events++; DIAG.lastEvent='down:'+(e.pointerType||'?')+':'+tool;
  if (tool==='select' && e.button===0 && selectedId){ const sw=project[floor].items.find(i=>i.id===selectedId); if (sw && (sw.type==='wall'||sw.type==='demo') && sw.pts.length===2 && startEndDrag(sw,e)) return; }
  if (tool==='select' && e.button===0){ const t=e.target.closest('[data-id]'); if(t){ const it=project[floor].items.find(i=>i.id===t.dataset.id); if(it && (it.type==='furn'||it.type==='note')){ const q=svgPoint(e); pushHistory(); dragging={it,sx:q.x,sy:q.y,orig:it.pts.map(p=>p.slice()),moved:false}; selectedId=it.id; svg.setPointerCapture(e.pointerId); return; }
      if(it && (it.type==='wall'||it.type==='demo') && it.pts.length===2){ if(startEndDrag(it,e)) return; if(startWallDrag(it,e)) return; }
      if(it && it.type==='door'){ const q=svgPoint(e); const [a,b]=it.pts; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; pushHistory(); doorDrag={it,d:[(b[0]-a[0])/L,(b[1]-a[1])/L],sx:q.x,sy:q.y,orig:[a.slice(),b.slice()],moved:false}; selectedId=it.id; svg.setPointerCapture(e.pointerId); return; }
      if(it){ selectedId=it.id; drawProject(); renderItems(); showInlineEdit(it,e); return; } } }
  if (tool==='ink' && e.button===0){ const q=svgPoint(e); inkDraft={pts:[[Math.round(q.x),Math.round(q.y)]]}; svg.setPointerCapture(e.pointerId); return; }
  if (e.button===1 || e.button===2 || tool==='select' || e.shiftKey){ panning={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y}; svg.classList.add('grabbing'); svg.setPointerCapture(e.pointerId); return; }
});
svg.addEventListener('pointermove',e=>{
  lastClient={x:e.clientX,y:e.clientY};
  const p=svgPoint(e); document.getElementById('coord').textContent=`x ${(p.x/1000).toFixed(2)} m · y ${(p.y/1000).toFixed(2)} m · 1 m = ${document.getElementById('coord').dataset.scale||'?'} px · ${tool}${draft?' · pkt '+draft.pts.length:''} · ${e.pointerType||'?'}`;
  try{ const hr=document.getElementById('hRead'); const hh=heightAt(p.x,p.y); if(hh===null){ hr.hidden=true; } else { hr.hidden=false; const rc=svg.getBoundingClientRect(); hr.style.left=(e.clientX-rc.left+14)+'px'; hr.style.top=(e.clientY-rc.top+14)+'px'; hr.style.right='auto'; hr.style.bottom='auto'; hr.textContent='h ≈ '+(hh/1000).toFixed(2).replace('.',',')+' m'; hr.style.color=hh<1900?'var(--new)':hh<2200?'#e07a1f':'var(--ink)'; } }catch(err){}
  if (panning){ const k=mmPerPx(); view.x=panning.vx-(e.clientX-panning.x)*k; view.y=panning.vy+(e.clientY-panning.y)*k; applyView(); return; }
  if (inkDraft){ const q=svgPoint(e); const l=inkDraft.pts[inkDraft.pts.length-1]; if(Math.hypot(q.x-l[0],q.y-l[1])>25){ inkDraft.pts.push([Math.round(q.x),Math.round(q.y)]); gl.draft.innerHTML=''; el('path',{d:'M'+inkDraft.pts.map(p=>p.join(' ')).join('L'),fill:'none',stroke:'var(--mark)','stroke-width':70,'stroke-linecap':'round','stroke-linejoin':'round',opacity:0.85},gl.draft); } return; }
  if (doorDrag){ const q=svgPoint(e); const D=doorDrag; let t=(q.x-D.sx)*D.d[0]+(q.y-D.sy)*D.d[1]; t=Math.round(t/10)*10; if(t!==0) D.moved=true; D.it.pts=[[Math.round(D.orig[0][0]+D.d[0]*t),Math.round(D.orig[0][1]+D.d[1]*t)],[Math.round(D.orig[1][0]+D.d[0]*t),Math.round(D.orig[1][1]+D.d[1]*t)]]; drawProject(); return; }
  if (endDrag){ updateEndDrag(e); return; }
  if (wallDrag){ updateWallDrag(e); return; }
  if (dragging){ const q=svgPoint(e); const dx=Math.round((q.x-dragging.sx)/10)*10, dy=Math.round((q.y-dragging.sy)/10)*10; dragging.it.pts=dragging.orig.map(pt=>[pt[0]+dx,pt[1]+dy]); drawProject(); return; }
  if (tool==='furn'||tool==='arrow'||tool==='mark'){ hoverPt={x:Math.round(p.x/10)*10,y:Math.round(p.y/10)*10,snapped:false}; drawDraft(); return; }
  if (tool==='door'){ const dd=doorAtPoint(p); hoverPt={x:p.x,y:p.y,snapped:!!dd,door:dd}; drawDraft(); return; }
  if (tool==='cut'){ hoverPt=null; drawDraft(); return; }
  if (tool!=='select'){ hoverPt=snap(p); drawDraft(); }
});
svg.addEventListener('pointerup',e=>{ try{ onPointerUp(e); }catch(err){ diag('pointerup/'+tool, err); } });
function onPointerUp(e){
  DIAG.events++; DIAG.lastEvent='up:'+(e.pointerType||'?')+':'+tool;
  if (inkDraft){ const d=inkDraft; inkDraft=null; gl.draft.innerHTML=''; if(d.pts.length>=2){ pushHistory(); const it={id:uid(),type:'ink',pts:d.pts,v:sel[floor]||undefined}; project[floor].items.push(it); commit(); } return; }
  if (doorDrag){ const D=doorDrag; doorDrag=null; if(D.moved){ suppressClick=true; commit(); } else { hist[floor].pop(); drawProject(); renderItems(); showInlineEdit(D.it,e); } return; }
  if (endDrag){ const E=endDrag; endDrag=null; gl.draft.innerHTML=''; if(E.moved){ suppressClick=true; try{ snapWallEnds(E.it, 200); }catch(err){ diag('snapWallEnds',err); } obstStamp++; commit(); } else { hist[floor].pop(); drawProject(); renderItems(); showInlineEdit(E.it,e); } return; }
  if (wallDrag){ const W=wallDrag; wallDrag=null; gl.draft.innerHTML=''; if(W.moved){ suppressClick=true; try{ snapWallEnds(W.it, 200); }catch(err){ diag('snapWallEnds',err); } obstStamp++; commit(); const col=collidingFurn(); if(col.length) showConflict(col,'wall'); else hideConflict(); } else { hist[floor].pop(); drawProject(); renderItems(); showInlineEdit(W.it,e); } return; }
  if (dragging){ const d=dragging; dragging=null; const moved=JSON.stringify(d.it.pts)!==JSON.stringify(d.orig); if(moved){ suppressClick=true; if(d.it.type==='furn') afterFurnChange(d.it); else commit(); } else { hist[floor].pop(); drawProject(); renderItems(); showInlineEdit(d.it,e); } return; }
  if (panning){ const moved=Math.hypot(e.clientX-panning.x,e.clientY-panning.y)>4; panning=null; svg.classList.remove('grabbing'); if(!moved && tool==='select'){ selectedId=null; hideInlineEdit(); drawProject(); renderItems(); document.querySelectorAll('.roompoly.active').forEach(p=>p.classList.remove('active')); } return; }
  if (anchorMove){ const q=svgPoint(e); const it=anchorMove; anchorMove=null; pushHistory(); it.anchor=[Math.round(q.x),Math.round(q.y)]; recomputeRooms(true); commit(); return; }
  if (tool==='select') return;
  const p=snap(svgPoint(e));
  if (tool==='furn'){ const k=document.getElementById('furnSel').value; const f=FURN[k]; const w=furnRot?f.h:f.w, h=furnRot?f.w:f.h; const q=svgPoint(e); const x0=Math.round((q.x-w/2)/10)*10, y0=Math.round((q.y-h/2)/10)*10; pushHistory(); const it={id:uid(),type:'furn',kind:k,pts:[[x0,y0],[x0+w,y0+h]],rot:furnRot?1:0,v:sel[floor]||undefined}; project[floor].items.push(it); selectedId=it.id; afterFurnChange(it); return; }
  if (tool==='note'){ pushHistory(); const it={id:uid(),type:'note',pts:[[p.x,p.y]],label:'',v:sel[floor]||undefined}; project[floor].items.push(it); selectedId=it.id; commit(); showInlineEdit(it,e); return; }
  if (tool==='mark'){ const q=svgPoint(e); pushHistory(); const n=visibleItems(floor).filter(i=>i.type==='mark').length+1; const it={id:uid(),type:'mark',n,pts:[[Math.round(q.x),Math.round(q.y)]],label:'',v:sel[floor]||undefined}; project[floor].items.push(it); selectedId=it.id; commit(); showInlineEdit(it,e); return; }
  if (tool==='arrow'){ const q=svgPoint(e); const pt=[Math.round(q.x),Math.round(q.y)]; if(!draft) draft={type:'arrow',pts:[pt]}; else { pushHistory(); const it={id:uid(),type:'arrow',pts:[draft.pts[0],pt],label:'',v:sel[floor]||undefined}; project[floor].items.push(it); selectedId=it.id; draft=null; commit(); showInlineEdit(it,e); } drawDraft(); return; }
  if (tool==='cut'){ try{ if(!cutWallAt(svgPoint(e))) hintToast('Kliknij w ścianę (projektowaną lub istniejącą), którą chcesz wyciąć.'); }catch(err){ diag('cut',err); } return; }
  if (tool==='door'){ const dd=doorAtPoint(svgPoint(e)); if(!dd){ hintToast('Drzwi wstawia się na ścianie – najedź kursorem na ścianę (projektowaną lub istniejącą) i kliknij.'); return; } pushHistory(); const it={id:uid(),type:'door',pts:dd.pts,w:dd.w,flip:dd.flip,v:sel[floor]||undefined}; project[floor].items.push(it); selectedId=it.id; commit(); drawDraft(); return; }
  if (tool==='dim'){ if(!draft) draft={type:tool,pts:[[p.x,p.y]]}; else { pushHistory(); const it={id:uid(),type:tool,pts:[draft.pts[0],[p.x,p.y]],v:sel[floor]||undefined}; project[floor].items.push(it); selectedId=it.id; draft=null; commit(); } drawDraft(); return; }
  if (!draft) draft={type:tool,pts:[]};
  const last=draft.pts[draft.pts.length-1];
  if (last && Math.hypot(last[0]-p.x,last[1]-p.y)<=12*mmPerPx()){ finishDraft(); return; } // click/tap near last point closes
  if (tool==='room' && draft.pts.length>=3 && Math.hypot(draft.pts[0][0]-p.x,draft.pts[0][1]-p.y)<200){ finishDraft(); return; }
  draft.pts.push([p.x,p.y]); drawDraft();
}
svg.addEventListener('dblclick',e=>{ e.preventDefault(); if(draft){ if(draft.pts.length>1 && Math.hypot(draft.pts[draft.pts.length-1][0]-draft.pts[draft.pts.length-2][0],draft.pts[draft.pts.length-1][1]-draft.pts[draft.pts.length-2][1])<1) draft.pts.pop(); finishDraft(); } });
svg.addEventListener('contextmenu',e=>e.preventDefault());
svg.addEventListener('wheel',e=>{ e.preventDefault(); const p=svgPoint(e); const f=Math.exp(e.deltaY*0.0015); const nw=Math.min(Math.max(view.w*f,2000),200000); const nh=view.h*nw/view.w; view.x=p.x-(p.x-view.x)*nw/view.w; view.y=p.y-(p.y-view.y)*nh/view.h; view.w=nw; view.h=nh; applyView(); },{passive:false});
// touch pinch
let pinch=null;
svg.addEventListener('touchstart',e=>{ if(e.touches.length===2){ pinch={d:Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY),w:view.w,h:view.h,cx:view.x+view.w/2,cy:view.y+view.h/2}; } },{passive:true});
svg.addEventListener('touchmove',e=>{ if(pinch&&e.touches.length===2){ const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY); const f=pinch.d/d; view.w=pinch.w*f; view.h=pinch.h*f; view.x=pinch.cx-view.w/2; view.y=pinch.cy-view.h/2; applyView(); } },{passive:true});
svg.addEventListener('touchend',()=>{pinch=null;});
document.getElementById('zoomIn').addEventListener('click',()=>{ const c={x:view.x+view.w/2,y:view.y+view.h/2}; view.w*=0.7; view.h*=0.7; view.x=c.x-view.w/2; view.y=c.y-view.h/2; applyView(); });
document.getElementById('zoomOut').addEventListener('click',()=>{ const c={x:view.x+view.w/2,y:view.y+view.h/2}; view.w/=0.7; view.h/=0.7; view.x=c.x-view.w/2; view.y=c.y-view.h/2; applyView(); });
document.getElementById('zoomFit').addEventListener('click',fitFloor);
window.addEventListener('keydown',e=>{
  const tg=e.target; if (tg.tagName==='TEXTAREA' || (tg.tagName==='INPUT' && tg.type!=='checkbox') || (tg.tagName==='SELECT' && !(e.key==='Enter'||e.key==='Escape'))) return;
  if (tg.tagName==='BUTTON'||tg.tagName==='SELECT'){ if(e.key==='Enter'||e.key==='Escape'||e.key==='Delete'||e.key==='Backspace'){ e.preventDefault(); tg.blur(); } }
  if (e.key==='Tab' && (tool==='wall')){ e.preventDefault(); const ws=document.getElementById('wallSide'); ws.value=String(({'0':1,'1':-1,'-1':0})[ws.value]); drawDraft(); return; }
  if (e.key==='Escape'){ if(draft){ draft=null; drawDraft(); } else setTool('select'); }
  if (e.key==='Enter'){ finishDraft(); }
  if ((e.key==='l'||e.key==='L') && selectedId){ const it=project[floor].items.find(i=>i.id===selectedId); if(it&&it.type==='door'){ pushHistory(); swapHinge(it); commit(); } }
  if ((e.key==='r'||e.key==='R') && selectedId && tool!=='furn'){ const it=project[floor].items.find(i=>i.id===selectedId); if(it&&it.type==='door'){ pushHistory(); it.flip=!it.flip; commit(); return; } }
  if (e.key==='r'||e.key==='R'){ if(tool==='furn'){ furnRot=!furnRot; document.getElementById('toolHint').textContent='Obrót: '+(furnRot?'90°':'0°')+'. Kliknij, aby postawić mebel.'; } else if(selectedId){ const it=project[floor].items.find(i=>i.id===selectedId); if(it&&it.type==='furn'){ pushHistory(); const [a,b]=it.pts; const cx=(a[0]+b[0])/2, cy=(a[1]+b[1])/2, w=Math.abs(b[0]-a[0]), h=Math.abs(b[1]-a[1]); it.pts=[[Math.round(cx-h/2),Math.round(cy-w/2)],[Math.round(cx+h/2),Math.round(cy+w/2)]]; it.rot=it.rot?0:1; commit(); } } }
  if (e.key==='Delete'||e.key==='Backspace'){ deleteSelected(); }
  if ((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){ e.preventDefault(); undo(); }
});

// ---------- tools UI ----------
const toolDefs=[
  ['select','Wskaż','<svg viewBox="0 0 24 24"><path d="M5 3l14 8-6 2-3 6z"/></svg>'],
  ['wall','Ściana','<svg viewBox="0 0 24 24"><path d="M3 12h18M3 9v6M21 9v6"/></svg>'],
  ['demo','Wyburz','<svg viewBox="0 0 24 24"><path d="M4 12h3M10 12h4M17 12h3M6 6l12 12M18 6L6 18"/></svg>'],
  ['cut','Wytnij','<svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.5 7.5L20 19M8.5 16.5L20 5M3 12h18" /></svg>'],
  ['room','Pomieszcz.','<svg viewBox="0 0 24 24"><path d="M4 4h16v16H4zM4 12h8v8"/></svg>'],
  ['door','Drzwi','<svg viewBox="0 0 24 24"><path d="M3 20h18M7 20V8M7 8a12 12 0 0 1 10 10"/></svg>'],
  ['dim','Pomiar','<svg viewBox="0 0 24 24"><path d="M3 12h18M3 8v8M21 8v8M8 10v4M13 10v4"/></svg>'],
  ['note','Notatka','<svg viewBox="0 0 24 24"><path d="M5 4h14v12H9l-4 4z"/></svg>'],
  ['furn','Meble','<svg viewBox="0 0 24 24"><path d="M4 11h16v7H4zM6 18v2M18 18v2M6 11V7h12v4"/></svg>'],
  ['ink','Ołówek','<svg viewBox="0 0 24 24"><path d="M4 20l4-1 11-11-3-3L5 16zM14 7l3 3"/></svg>'],
  ['arrow','Strzałka','<svg viewBox="0 0 24 24"><path d="M4 20L20 4M12 4h8v8"/></svg>'],
  ['mark','Uwaga nr','<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M10 9l2-1v8"/></svg>']
];
const hints={cut:'Wytnij: kliknij ścianę – usunę jej odcinek między najbliższymi ścianami poprzecznymi (ściana projektowana → podział na dwie; ściana istniejąca → wyburzenie odcinka). Drzwi w wyciętym odcinku znikają. Ctrl+Z cofa.',select:'Kliknij ścianę, drzwi lub mebel, aby zaznaczyć (Del usuwa). Koniec ściany (kółko) przeciągasz wzdłuż osi – skraca lub wydłuża ją, maks. do najbliższej ściany. Przeciągnij nową ścianę – przesuwa się równolegle i sama docina do sąsiednich ścian; ścianki, drzwi i obrysy przyłączone do niej idą razem. Meble przeciągasz, R obraca. Puste pole: przesuwanie widoku.',wall:'Klikaj kolejne punkty nowej ściany – tylko poziomo/pionowo. Grubość wybierasz z listy albo wpisujesz (inna…); „Grubość od linii” mówi, po której stronie rysowanej linii leży mur (Tab przełącza w trakcie). Po zakończeniu końce same wpinają się w oś sąsiedniej ściany projektowej albo w lico ściany istniejącej (do 30 cm) – ściany tworzą całość, nic nie wystaje. Podwójne kliknięcie lub Enter kończy.',demo:'Narysuj linię po ścianie do wyburzenia (żółta, przerywana). Podwójne kliknięcie kończy.',room:'Obrysuj nowe pomieszczenie klikając narożniki; kliknij punkt startowy lub Enter, aby zamknąć. Powierzchnia liczy się na bieżąco.',door:'Najedź na ścianę – pokaże się podgląd drzwi (domyślnie 80 cm, otwierane w stronę kursora) – i kliknij, żeby upuścić. Potem w trybie Wskaż: przeciągnij po ścianie, R – kierunek otwierania, L – zawias lewy/prawy, szerokość w okienku.',dim:'Kliknij dwa punkty — odległość w metrach.',note:'Kliknij, aby postawić notatkę z tekstem.',furn:'Wybierz mebel z listy i kliknij, gdzie ma stanąć (środek). R obraca przed postawieniem. Narzędziem „Wskaż” przeciągasz meble; Del usuwa.',ink:'Rysuj odręcznie po planie (przeciągnij). Szkic zapisuje się i Claude go odczyta.',arrow:'Kliknij początek i koniec strzałki, potem wpisz, co zmienić.',mark:'Kliknij miejsce – pojawi się numer uwagi; wpisz treść. W rozmowie wystarczy podać numer.'};
const tb=document.getElementById('tools');
tb.innerHTML=toolDefs.map(t=>`<button data-tool="${t[0]}" aria-pressed="${t[0]==='select'}" title="${t[1]}">${t[2]}<span>${t[1]}</span></button>`).join('');
tb.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{ if(b.dataset.tool===tool && draft && draft.pts.length){ finishDraft(); return; } setTool(b.dataset.tool); }));
document.getElementById('dbFinish').addEventListener('click',()=>{ finishDraft(); });
document.getElementById('wallW').addEventListener('change',()=>{ const c=document.getElementById('wallW').value==='custom'; const inp=document.getElementById('wallWin'); inp.hidden=!c; if(c){ inp.focus(); } drawDraft(); });
document.getElementById('wallWin').addEventListener('input',()=>drawDraft());
document.getElementById('wallSide').addEventListener('change',()=>drawDraft());
document.getElementById('btnJoin').addEventListener('click',()=>{ try{ joinAllWalls(); }catch(err){ diag('joinAllWalls',err); } });
document.getElementById('dbBack').addEventListener('click',()=>{ if(draft&&draft.pts.length){ draft.pts.pop(); if(!draft.pts.length) draft=null; drawDraft(); } });
document.getElementById('dbCancel').addEventListener('click',()=>{ draft=null; drawDraft(); });
// blur focused controls when drawing starts so keyboard shortcuts reach the canvas
svg.addEventListener('pointerdown',()=>{ if(document.activeElement&&document.activeElement!==document.body) document.activeElement.blur(); },true);
function setTool(t){ tool=t; draft=null; hoverPt=null; drawDraft(); hideInlineEdit(); tb.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.tool===t)); svg.classList.toggle('tool',t!=='select'); document.getElementById('toolHint').textContent=hints[t]; }
document.getElementById('furnSel').innerHTML=Object.keys(FURN).map(k=>`<option value="${k}">${FURN[k].n}</option>`).join('');
let furnRot=false;
document.getElementById('unitSel').innerHTML='<option value="">— lokal —</option>'+Object.keys(UNITS).map(u=>`<option value="${u}">${UNITS[u].name}</option>`).join('');
document.getElementById('undoBtn').addEventListener('click',undo);
document.getElementById('delBtn').addEventListener('click',deleteSelected);
let clearArmed=false;
document.getElementById('clearBtn').addEventListener('click',(e)=>{ if(!clearArmed){ clearArmed=true; e.target.textContent='Na pewno? Kliknij ponownie'; setTimeout(()=>{clearArmed=false; e.target.textContent='Wyczyść kondygnację';},3000); return; } clearArmed=false; e.target.textContent='Wyczyść kondygnację'; pushHistory(); const vis=new Set(visibleItems(floor).map(i=>i.id)); project[floor].items=project[floor].items.filter(i=>!vis.has(i.id)); selectedId=null; commit(); });
document.getElementById('copyBtn').addEventListener('click',(e)=>{ const ta=document.getElementById('jsonBox'); const txt=ta.value; const done=()=>{e.target.textContent='Skopiowano'; setTimeout(()=>e.target.textContent='Kopiuj',1500);}; try{ navigator.clipboard.writeText(txt).then(done).catch(()=>{ta.select(); done();}); }catch(err){ ta.select(); done(); } });
document.getElementById('loadBtn').addEventListener('click',()=>{ try{ const arr=JSON.parse(document.getElementById('jsonBox').value); if(Array.isArray(arr)){ pushHistory(); const vis=new Set(visibleItems(floor).map(i=>i.id)); project[floor].items=project[floor].items.filter(i=>!vis.has(i.id)).concat(arr.filter(i=>i&&i.type&&Array.isArray(i.pts)).map(i=>({...i,id:i.id||uid()}))); commit(); } }catch(err){ document.getElementById('toolHint').textContent='Nie udało się odczytać JSON — sprawdź składnię.'; } });

// ---------- layers UI ----------
const lw=document.getElementById('layers');
lw.innerHTML=layerDefs.map(l=>`<label><input type="checkbox" id="ly_${l[0]}" ${layerOn[l[0]]?'checked':''}><span class="sw" style="background:${l[2]}"></span>${l[1]}</label>`).join('');
lw.querySelectorAll('input').forEach(i=>i.addEventListener('change',()=>{ layerOn[i.id.slice(3)]=i.checked; try{localStorage.setItem(KEYP+'.layers',JSON.stringify(layerOn));}catch(e){} updateLayerVisibility(); if(i.id==='ly_autodim') drawProject(); }));
function updateLayerVisibility(){ for (const k of ['walls','windows','doors','stairs','sills','fixtures','dims','skosy','dwgtext','project','rfill','rline','rlbl','furn','sketch','autodim']) gl[k].style.display=layerOn[k]?'':'none'; gl.zones.style.display=gl.roomlbl.style.display=layerOn.rooms?'':'none'; gl.rhit.style.display=layerOn.rlbl?'':'none'; }

// ---------- floors UI ----------
const ft=document.getElementById('floorTabs');
ft.innerHTML=FLOORS.map(f=>`<button role="tab" data-f="${f}" aria-selected="${f===floor}">${MODEL.floors[f].name}</button>`).join('');
ft.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>setFloor(b.dataset.f)));
function setFloor(f){ floor=f; selectedId=null; draft=null; hideInlineEdit(); ft.querySelectorAll('button').forEach(b=>b.setAttribute('aria-selected',b.dataset.f===f)); try{ history.replaceState(null,'','#'+f); }catch(e){} renderVariantSel(); buildSnap(); drawGeo(); drawProject(); renderItems(); fitFloor(); if(is3D){ focus3D(); build3D(); } }

// ---------- variants UI ----------
const vs=document.getElementById('variantSel');
function renderVariantSel(){ const list=VARIANTS.floors[floor]||[]; vs.innerHTML=list.length?list.map(v=>`<option value="${v.id}" ${v.id===sel[floor]?'selected':''}>${v.name}</option>`).join(''):'<option value="">— brak wariantów —</option>'; vs.disabled=!list.length; }
vs.addEventListener('change',()=>{ sel[floor]=vs.value||null; try{localStorage.setItem(KEYP+'.variants',JSON.stringify(sel));}catch(e){} selectedId=null; drawRooms(); drawProject(); renderItems(); if(is3D) build3D(); });

// ---------- persistence ----------
const saveDot=document.getElementById('saveDot'), saveTxt=document.getElementById('saveTxt');
function setStatus(cls,txt){ saveDot.className='dot '+cls; saveTxt.textContent=txt; }
function scheduleSave(){ clearTimeout(saveTimer); saveTimer=setTimeout(saveNow,700); }
async function saveNow(){
  const f=floor; const items=project[f].items;
  try{ localStorage.setItem(KEYP+'.proj.'+f, JSON.stringify(items)); }catch(e){}
  if (window.PLANER && window.PLANER.saveItems){ try{ setStatus('','zapisywanie…'); await window.PLANER.saveItems(f, items); setStatus('ok','zapisano '+new Date().toLocaleTimeString('pl-PL',{hour:'2-digit',minute:'2-digit'})); }catch(err){ setStatus('warn','brak zapisu: '+(err&&err.message||'błąd')); } return; }
  if (!db){ setStatus('warn','zapis tylko w tej przeglądarce'); return; }
  try{ setStatus('','zapisywanie…'); await db.doc('projekt/'+f).set({items, updatedAt:new Date().toISOString(), floor:f}); setStatus('ok','zapisano '+new Date().toLocaleTimeString('pl-PL',{hour:'2-digit',minute:'2-digit'})); }
  catch(err){ setStatus('warn','brak zapisu: '+(err&&err.code||'błąd')); }
}
async function initDb(){
  try{
    for (const f of FLOORS){ try{ const s=localStorage.getItem(KEYP+'.proj.'+f); if(s) project[f].items=JSON.parse(s); }catch(e){} }
    if (window.PLANER && window.PLANER.loadItems){ for (const f of FLOORS){ try{ const it=await window.PLANER.loadItems(f); if(Array.isArray(it)) project[f].items=JSON.parse(JSON.stringify(it)); }catch(e){} } drawProject(); renderItems(); renderLegend(); setStatus('ok','projekt: '+(window.PLANER.name||'')); return; }
    drawProject(); renderItems(); renderLegend();
    db = window.claude && window.claude.use ? await window.claude.use('db') : null;
    if (!db){ setStatus('warn','zapis tylko w tej przeglądarce'); return; }
    setStatus('ok','połączono z bazą'); scheduleDiagSave();
    for (const f of FLOORS){
      db.doc('projekt/'+f).onSnapshot(snap=>{
        if (!snap.exists) return;
        if (snap.metadata && snap.metadata.hasPendingWrites) return;
        const d=snap.data(); if(!d||!Array.isArray(d.items)) return;
        const cur=JSON.stringify(project[f].items); const inc=JSON.stringify(d.items);
        if (cur===inc) return;
        project[f].items=JSON.parse(JSON.stringify(d.items)); /* kopia: snapshot z bazy jest zamrożony */ if(f===floor){ drawProject(); renderItems(); } renderLegend();
        setStatus('ok','wczytano '+(d.updatedAt?new Date(d.updatedAt).toLocaleString('pl-PL',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):''));
      }, err=>{ setStatus('warn','baza niedostępna ('+err.code+')'); });
    }
  }catch(e){ setStatus('warn','zapis tylko w tej przeglądarce'); }
}

// ---------- 3D ----------
let is3D=false, R3=null;
const FLOOR_H={piwnica:2290,parter:3330,pietro1:3440,poddasze:2780};
const SILL=850, WIN_TOP=2750, DOOR_H=2100;
const FURN_H={bed:500,bed1:500,night:500,wardrobe:2360,pax150:2360,pax175:2360,pax250:2360,pax275:2360,pax300:2360,pax150s:2360,pax200s:2360,sofa:850,armchair:850,coffee:450,tv:500,table:750,table4:750,chair:450,desk:750,counter:900,sink:900,hob:900,fridge:1800,shower:2000,bath:600,wc:400,basin:850,washer:850,shoe:900,box:900};
function mm(v){ return v/1000; }
function tooLowFor(it){ // poddasze: czy mebel mieści się pod skosem (najniższy punkt sufitu nad obrysem mebla)
  if(!ATTIC||floor!==ATTIC.floor||it.type!=='furn') return null; const r=rectOf(it); const hF=FURN_H[it.kind]||900; let hmin=1e9; for (const x of [r.x0+30,(r.x0+r.x1)/2,r.x1-30]) for (const y of [r.y0+30,(r.y0+r.y1)/2,r.y1-30]){ const h=heightAt(x,y); if(h!==null&&h<hmin) hmin=h; } if (hmin<1e9 && hmin<hF) return {hmin,need:hF}; return null; }
function init3D(){
  if (R3 || !window.THREE) return;
  const canvas=document.getElementById('gl3d');
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true}); renderer.setPixelRatio(Math.min(2,window.devicePixelRatio||1));
  const scene=new THREE.Scene(); const camera=new THREE.PerspectiveCamera(50,1,0.05,400);
  scene.add(new THREE.HemisphereLight(0xffffff,0x8899aa,0.95)); const dl=new THREE.DirectionalLight(0xffffff,0.55); dl.position.set(8,20,6); scene.add(dl);
  R3={renderer,scene,camera,group:null,orbit:{theta:2.2,phi:0.95,r:20,target:new THREE.Vector3(3.5,0,-7.5)},ray:new THREE.Raycaster(),pick:[],drag:null,orb:null,ptr:new THREE.Vector2()};
  canvas.addEventListener('pointerdown',on3dDown); canvas.addEventListener('pointermove',on3dMove); canvas.addEventListener('pointerup',on3dUp); canvas.addEventListener('pointercancel',on3dUp);
  canvas.addEventListener('wheel',e=>{ e.preventDefault(); R3.orbit.r=Math.min(80,Math.max(2,R3.orbit.r*Math.exp(e.deltaY*0.0015))); render3D(); },{passive:false});
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
}
function cam3D(){ const o=R3.orbit; const c=R3.camera; c.position.set(o.target.x+o.r*Math.sin(o.phi)*Math.cos(o.theta), o.target.y+o.r*Math.cos(o.phi), o.target.z+o.r*Math.sin(o.phi)*Math.sin(o.theta)); c.lookAt(o.target); }
function size3D(){ const cv=document.getElementById('gl3d'); const w=cv.clientWidth||800, h=cv.clientHeight||600; R3.renderer.setSize(w,h,false); R3.camera.aspect=w/h; R3.camera.updateProjectionMatrix(); }
function render3D(){ if(!R3||!is3D) return; cam3D(); R3.renderer.render(R3.scene,R3.camera); }
function wallPlane(a,b,z0,z1,mat,group){ const L=Math.hypot(b[0]-a[0],b[1]-a[1]); if(L<1) return; const g=new THREE.PlaneGeometry(mm(L),mm(z1-z0)); const m=new THREE.Mesh(g,mat); m.position.set(mm((a[0]+b[0])/2),mm((z0+z1)/2),-mm((a[1]+b[1])/2)); m.rotation.y=Math.atan2((b[1]-a[1]),(b[0]-a[0])); group.add(m); return m; }
// ---- ściany docinane pod skos (poddasze): góra ściany = min(H, wysokość sufitu w danym punkcie) ----
function topProfile(a,b,z1){ if(!ATTIC||floor!==ATTIC.floor) return null; const L=Math.hypot(b[0]-a[0],b[1]-a[1]); const n=Math.max(2,Math.ceil(L/250)+1); const zs=[]; let cut=false; for(let i=0;i<n;i++){ const t=i/(n-1); const x=a[0]+(b[0]-a[0])*t, y=a[1]+(b[1]-a[1])*t; let h=heightAt(x,y); if(h===null) h=z1; h=Math.min(z1,Math.max(60,h)); if(h<z1-1) cut=true; zs.push(h); } return cut?zs:null; }
function wallPlaneSloped(a,b,z0,z1,mat,group){ const zs=topProfile(a,b,z1); if(!zs) return wallPlane(a,b,z0,z1,mat,group); const n=zs.length; const v=[]; const P=(t,z)=>[mm(a[0]+(b[0]-a[0])*t),mm(z),-mm(a[1]+(b[1]-a[1])*t)]; for(let i=0;i<n-1;i++){ const t0=i/(n-1), t1=(i+1)/(n-1); const p00=P(t0,z0),p01=P(t0,zs[i]),p10=P(t1,z0),p11=P(t1,zs[i+1]); v.push(...p00,...p10,...p11, ...p00,...p11,...p01); } const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(v),3)); g.computeVertexNormals(); const m=new THREE.Mesh(g,mat); group.add(m); return m; }
function boxSegSloped(a,b,thick,z0,z1,mat,group,ud){ const zs=topProfile(a,b,z1); if(!zs) return boxSeg(a,b,thick,z0,z1,mat,group,ud); const n=zs.length; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const nx=-(b[1]-a[1])/L*thick/2, ny=(b[0]-a[0])/L*thick/2; const v=[]; const P=(t,side,z)=>[mm(a[0]+(b[0]-a[0])*t+nx*side),mm(z),-mm(a[1]+(b[1]-a[1])*t+ny*side)]; const quad=(p0,p1,p2,p3)=>{ v.push(...p0,...p1,...p2, ...p0,...p2,...p3); };
  for(let i=0;i<n-1;i++){ const t0=i/(n-1), t1=(i+1)/(n-1); const hz0=zs[i], hz1=zs[i+1];
    quad(P(t0,1,z0),P(t1,1,z0),P(t1,1,hz1),P(t0,1,hz0));        // lewe lico
    quad(P(t1,-1,z0),P(t0,-1,z0),P(t0,-1,hz0),P(t1,-1,hz1));    // prawe lico
    quad(P(t0,1,hz0),P(t1,1,hz1),P(t1,-1,hz1),P(t0,-1,hz0)); }  // góra (skośna)
  quad(P(0,-1,z0),P(0,1,z0),P(0,1,zs[0]),P(0,-1,zs[0])); quad(P(1,1,z0),P(1,-1,z0),P(1,-1,zs[n-1]),P(1,1,zs[n-1]));
  const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(v),3)); g.computeVertexNormals(); const mat2=mat.clone(); mat2.side=THREE.DoubleSide; const m=new THREE.Mesh(g,mat2); if(ud) m.userData=ud; group.add(m); return m; }
function boxSeg(a,b,thick,z0,z1,mat,group,ud){ const L=Math.hypot(b[0]-a[0],b[1]-a[1]); if(L<1) return; const g=new THREE.BoxGeometry(mm(L),mm(z1-z0),mm(thick)); const m=new THREE.Mesh(g,mat); m.position.set(mm((a[0]+b[0])/2),mm((z0+z1)/2),-mm((a[1]+b[1])/2)); m.rotation.y=Math.atan2((b[1]-a[1]),(b[0]-a[0])); if(ud) m.userData=ud; group.add(m); return m; }
function labelPlane(text, cx, cy, w, group){ const c=document.createElement('canvas'); c.width=512; c.height=128; const x=c.getContext('2d'); x.fillStyle='rgba(255,255,255,0.0)'; x.fillRect(0,0,512,128); x.font='bold 44px IBM Plex Sans, sans-serif'; x.fillStyle='#8a1f2f'; x.textAlign='center'; x.fillText(text.slice(0,28),256,70); const t=new THREE.CanvasTexture(c); const m=new THREE.Mesh(new THREE.PlaneGeometry(mm(w),mm(w)/4),new THREE.MeshBasicMaterial({map:t,transparent:true,depthWrite:false})); m.rotation.x=-Math.PI/2; m.position.set(mm(cx),0.02,-mm(cy)); group.add(m); }
function slopes3D(G){ if(!ATTIC||floor!==ATTIC.floor) return; const mat=new THREE.MeshLambertMaterial({color:0x8d99a6,transparent:true,opacity:0.45,side:THREE.DoubleSide});
  for (const pl of ATTIC.planes){ const [a,b]=pl.line; const D=(pl.h0-ATTIC.hmin)/pl.tan; const a2=[a[0]+pl.dir[0]*D,a[1]+pl.dir[1]*D], b2=[b[0]+pl.dir[0]*D,b[1]+pl.dir[1]*D];
    const g=new THREE.BufferGeometry(); const v=new Float32Array([mm(a[0]),mm(pl.h0),-mm(a[1]), mm(b[0]),mm(pl.h0),-mm(b[1]), mm(b2[0]),mm(ATTIC.hmin),-mm(b2[1]), mm(a[0]),mm(pl.h0),-mm(a[1]), mm(b2[0]),mm(ATTIC.hmin),-mm(b2[1]), mm(a2[0]),mm(ATTIC.hmin),-mm(a2[1])]); g.setAttribute('position',new THREE.BufferAttribute(v,3)); g.computeVertexNormals(); G.add(new THREE.Mesh(g,mat)); } }
function door3D(it,G,matDoor,matFrame,matMetal){
  const [a,b]=it.pts; const W=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const ang=Math.atan2(b[1]-a[1],b[0]-a[0]); const sgn=it.flip?-1:1; const th=doorFrame(it).th; const zo=-sgn; // lokalne -Z = lewa normalna
  const grp=new THREE.Group(); grp.position.set(mm(a[0]),0,-mm(a[1])); grp.rotation.y=ang; G.add(grp);
  const box=(par,x,y,z,sx,sy,sz,mat,ud)=>{ const m=new THREE.Mesh(new THREE.BoxGeometry(mm(sx),mm(sy),mm(sz)),mat); m.position.set(mm(x),mm(y),mm(z)); if(ud) m.userData=ud; par.add(m); return m; };
  const cyl=(par,x,y,z,r,h,mat,axis)=>{ const m=new THREE.Mesh(new THREE.CylinderGeometry(mm(r),mm(r),mm(h),16),mat); m.position.set(mm(x),mm(y),mm(z)); if(axis==='z') m.rotation.x=Math.PI/2; if(axis==='x') m.rotation.z=Math.PI/2; par.add(m); return m; };
  // ościeżnica: stojaki + nadproże (w grubości ściany)
  box(grp,-JAMB/2,DOOR_H/2,0,JAMB,DOOR_H,th,matFrame); box(grp,W+JAMB/2,DOOR_H/2,0,JAMB,DOOR_H,th,matFrame); box(grp,W/2,DOOR_H-JAMB/2,0,W+2*JAMB,JAMB,th,matFrame);
  // opaski ościeżnicy regulowanej – nachodzą na ścianę z obu stron
  for (const zs of [1,-1]){ const z=zs*(th/2+ARCH_T/2); const Ht=DOOR_H+ARCH_W-JAMB;
    box(grp,-ARCH_W/2,Ht/2,z,ARCH_W,Ht,ARCH_T,matFrame); box(grp,W+ARCH_W/2,Ht/2,z,ARCH_W,Ht,ARCH_T,matFrame); box(grp,W/2,Ht-ARCH_W/2,z,W+2*ARCH_W,ARCH_W,ARCH_T,matFrame); }
  // skrzydło na zawiasach – otwarte ~75°
  const leaf=new THREE.Group(); leaf.position.set(mm(-10),0,mm(zo*(th/2-LEAF_T/2-4))); leaf.rotation.y=-zo*0.75*Math.PI/2; grp.add(leaf);
  const LW=W+20; const m=box(leaf,LW/2,LEAF_H/2+10,0,LW,LEAF_H,LEAF_T,matDoor,{id:it.id,type:'door'}); R3.pick.push(m);
  for (const y of [300,1020,1740]) cyl(leaf,0,y,zo*(LEAF_T/2+8),7,90,matMetal,'y');
  // klamka z obu stron (rozeta + szyjka + dźwignia)
  for (const zs of [1,-1]){ const zb=zs*LEAF_T/2; cyl(leaf,LW-60,1020,zb+zs*4,26,8,matMetal,'z'); cyl(leaf,LW-60,1020,zb+zs*28,9,48,matMetal,'z'); box(leaf,LW-60-55,1020,zb+zs*52,125,20,14,matMetal); }
}
function build3D(){
  if (!R3) init3D(); if(!R3) return;
  if (R3.group){ R3.scene.remove(R3.group); R3.group.traverse(o=>{ if(o.geometry) o.geometry.dispose(); }); }
  const G=new THREE.Group(); R3.group=G; R3.pick=[];
  const F=MODEL.floors[floor]; const H=FLOOR_H[floor]||3000; const b=F.bbox;
  const dark=document.documentElement.getAttribute('data-theme')==='dark'||(matchMedia('(prefers-color-scheme: dark)').matches&&document.documentElement.getAttribute('data-theme')!=='light');
  const matWall=new THREE.MeshLambertMaterial({color:dark?0x5a6470:0xe6e2dc,side:THREE.DoubleSide}); const matNew=new THREE.MeshLambertMaterial({color:0xd96a6a}); const matGlass=new THREE.MeshLambertMaterial({color:0x7fb3e0,transparent:true,opacity:0.35,side:THREE.DoubleSide}); const matDoor=new THREE.MeshLambertMaterial({color:0xc69c6d}); const matFrame=new THREE.MeshLambertMaterial({color:0xf2eee7}); const matMetal=new THREE.MeshPhongMaterial({color:0x9ea3a8,shininess:80}); const matFloor=new THREE.MeshLambertMaterial({color:dark?0x1c242c:0xf3efe8});
  // podłoga
  const fl=new THREE.Mesh(new THREE.PlaneGeometry(mm(b[2]-b[0]+4000),mm(b[3]-b[1]+4000)),matFloor); fl.rotation.x=-Math.PI/2; fl.position.set(mm((b[0]+b[2])/2),-0.005,-mm((b[1]+b[3])/2)); G.add(fl);
  // ściany istniejące (lica z inwentaryzacji) + okna
  for (const s of (F.geo.walls||[])) if(s.k==='l') for(let i=1;i<s.p.length;i++) wallPlaneSloped(s.p[i-1],s.p[i],0,H,matWall,G);
  for (const s of (F.geo.windows||[])) if(s.k==='l') for(let i=1;i<s.p.length;i++) wallPlane(s.p[i-1],s.p[i],SILL,WIN_TOP,matGlass,G);
  // elementy projektu
  try{ slopes3D(G); }catch(err){ diag('slopes3D',err); }
  const items=visibleItems(floor); const doors=items.filter(i=>i.type==='door');
  for (const it of items){
    if (it.type==='wall'){ const w=it.w||120; for(let i=1;i<it.pts.length;i++){ const a=it.pts[i-1], bb=it.pts[i]; const L=Math.hypot(bb[0]-a[0],bb[1]-a[1])||1; const d=[(bb[0]-a[0])/L,(bb[1]-a[1])/L];
        // otwory drzwiowe na tym odcinku
        const cuts=[]; for (const dr of doors){ let t0=((dr.pts[0][0]-a[0])*d[0]+(dr.pts[0][1]-a[1])*d[1]), t1=((dr.pts[1][0]-a[0])*d[0]+(dr.pts[1][1]-a[1])*d[1]); if(t0>t1){ const tt=t0; t0=t1; t1=tt; } if(!dr.open){ t0-=JAMB; t1+=JAMB; } const off=Math.abs((dr.pts[0][0]-a[0])*d[1]-(dr.pts[0][1]-a[1])*d[0]); if(off<=w/2+60 && Math.max(t0,t1)>0 && Math.min(t0,t1)<L) cuts.push([Math.max(0,Math.min(t0,t1)),Math.min(L,Math.max(t0,t1))]); }
        cuts.sort((p,q)=>p[0]-q[0]); let cur=0; const P=t=>[a[0]+d[0]*t,a[1]+d[1]*t];
        for (const [c0,c1] of cuts){ if(c0>cur) boxSegSloped(P(cur),P(c0),w,0,H,matNew,G); boxSegSloped(P(c0),P(c1),w,DOOR_H,H,matNew,G); cur=Math.max(cur,c1); }
        if (cur<L) boxSegSloped(P(cur),P(L),w,0,H,matNew,G); } }
    else if (it.type==='door' && !it.open){ const [a,bb]=it.pts; const L=Math.hypot(bb[0]-a[0],bb[1]-a[1])||1; const ang=Math.atan2(bb[1]-a[1],bb[0]-a[0]); const sgn=it.flip?-1:1; const nx=-Math.sin(ang)*sgn, ny=Math.cos(ang)*sgn; const open=0.75; // skrzydło otwarte ~75%
        const ex=[a[0]+((bb[0]-a[0])/L)*Math.cos(open*Math.PI/2)*L+nx*Math.sin(open*Math.PI/2)*L, a[1]+((bb[1]-a[1])/L)*Math.cos(open*Math.PI/2)*L+ny*Math.sin(open*Math.PI/2)*L];
        door3D(it,G,matDoor,matFrame,matMetal); }
    else if (it.type==='furn'){ const r=rectOf(it); const k=it.kind||'box'; const h=FURN_H[k]||900; const wet=['shower','bath','wc','basin','washer'].includes(k), kit=['counter','sink','hob','fridge'].includes(k);
        const mat=new THREE.MeshLambertMaterial({color:k==='shower'?0x7fb3e0:wet?0xb9d7ea:kit?0xe9c46a:(k.startsWith('pax')||k==='wardrobe')?0xb08968:0xc9bfb2,transparent:k==='shower',opacity:k==='shower'?0.4:1});
        const g=new THREE.BoxGeometry(mm(r.x1-r.x0),mm(h),mm(r.y1-r.y0)); const m=new THREE.Mesh(g,mat); m.position.set(mm((r.x0+r.x1)/2),mm(h/2),-mm((r.y0+r.y1)/2)); m.userData={id:it.id,type:'furn'}; if(it.id===selectedId){ m.material.emissive=new THREE.Color(0x664400); } G.add(m); R3.pick.push(m); }
    else if (it.type==='room' && it.pts.length>=3){ const c=roomAnchor(it); labelPlane((it.label||'')+' '+(roomArea(it)/1e6).toFixed(1).replace('.',',')+' m²', c[0], c[1], 2600, G); }
  }
  // istniejące pokoje (etykiety) poza ukrytymi
  const hide=new Set((curVariant(floor)||{}).hide||[]); for (const r of F.rooms) if(r.poly && !hide.has(r.nr)){ const c=polyCentroid(r.poly); labelPlane(r.nr+' '+(r.name||''), c[0], c[1], 2400, G); }
  R3.scene.add(G); size3D(); render3D();
}
function floorHit(e){ const cv=document.getElementById('gl3d'); const rc=cv.getBoundingClientRect(); R3.ptr.set(((e.clientX-rc.left)/rc.width)*2-1, -((e.clientY-rc.top)/rc.height)*2+1); R3.ray.setFromCamera(R3.ptr,R3.camera); const pl=new THREE.Plane(new THREE.Vector3(0,1,0),0); const p=new THREE.Vector3(); return R3.ray.ray.intersectPlane(pl,p)?p:null; }
function on3dDown(e){
  const cv=document.getElementById('gl3d'); cv.setPointerCapture(e.pointerId); cv.classList.add('drag');
  const rc=cv.getBoundingClientRect(); R3.ptr.set(((e.clientX-rc.left)/rc.width)*2-1, -((e.clientY-rc.top)/rc.height)*2+1); R3.ray.setFromCamera(R3.ptr,R3.camera);
  const hits=e.button===0&&!e.shiftKey?R3.ray.intersectObjects(R3.pick,false):[];
  if (hits.length){ const ud=hits[0].object.userData; const it=project[floor].items.find(i=>i.id===ud.id); if(it){ const p=floorHit(e); pushHistory(); R3.drag={it,mesh:hits[0].object,p0:p,orig:it.pts.map(q=>q.slice()),moved:false}; selectedId=it.id; drawProject(); renderItems(); return; } }
  R3.orb={x:e.clientX,y:e.clientY,theta:R3.orbit.theta,phi:R3.orbit.phi,target:R3.orbit.target.clone(),pan:e.shiftKey||e.button===2||e.button===1};
}
function on3dMove(e){
  if (!R3) return;
  if (R3.drag){ const p=floorHit(e); if(!p||!R3.drag.p0) return; let dx=Math.round((p.x-R3.drag.p0.x)*100)*10, dy=Math.round((-(p.z-R3.drag.p0.z))*100)*10; const it=R3.drag.it;
    if (it.type==='door'){ const [a,b]=R3.drag.orig; const L=Math.hypot(b[0]-a[0],b[1]-a[1])||1; const d=[(b[0]-a[0])/L,(b[1]-a[1])/L]; const t=Math.round((dx*d[0]+dy*d[1])/10)*10; it.pts=[[Math.round(a[0]+d[0]*t),Math.round(a[1]+d[1]*t)],[Math.round(b[0]+d[0]*t),Math.round(b[1]+d[1]*t)]]; }
    else { it.pts=R3.drag.orig.map(q=>[q[0]+dx,q[1]+dy]); }
    if (dx||dy) R3.drag.moved=true; build3D(); return; }
  if (R3.orb){ const o=R3.orb; const dx=e.clientX-o.x, dy=e.clientY-o.y;
    if (o.pan){ const s=R3.orbit.r*0.0018; const right=new THREE.Vector3(Math.cos(R3.orbit.theta+Math.PI/2),0,Math.sin(R3.orbit.theta+Math.PI/2)); const fwd=new THREE.Vector3(-Math.cos(R3.orbit.theta),0,-Math.sin(R3.orbit.theta)); R3.orbit.target.copy(o.target).addScaledVector(right,-dx*s).addScaledVector(fwd,-dy*s); }
    else { R3.orbit.theta=o.theta+dx*0.008; R3.orbit.phi=Math.min(1.5,Math.max(0.15,o.phi-dy*0.008)); }
    render3D(); }
}
function on3dUp(e){
  const cv=document.getElementById('gl3d'); cv.classList.remove('drag');
  if (R3&&R3.drag){ const d=R3.drag; R3.drag=null; if(d.moved){ if(d.it.type==='furn') afterFurnChange(d.it); else commit(); } else { hist[floor].pop(); build3D(); } return; }
  if (R3) R3.orb=null;
}
function focus3D(){ let b=MODEL.floors[floor].bbox; const pts=[]; for(const it of visibleItems(floor)) if(it.type==='wall'||it.type==='room'||it.type==='furn') for(const q of it.pts) pts.push(q); if(pts.length>4){ b=[Math.min(...pts.map(q=>q[0])),Math.min(...pts.map(q=>q[1])),Math.max(...pts.map(q=>q[0])),Math.max(...pts.map(q=>q[1]))]; } R3.orbit.target.set(mm((b[0]+b[2])/2),0,-mm((b[1]+b[3])/2)); R3.orbit.r=Math.max(b[2]-b[0],b[3]-b[1])/1000*1.15; }
function toggle3D(on){ try{ document.getElementById('hRead').hidden=true; }catch(e){}
  is3D=on; const btn=document.getElementById('btn3d'); btn.setAttribute('aria-pressed',on); const cv=document.getElementById('gl3d'); document.getElementById('hint3d').hidden=!on; cv.hidden=!on; svg.style.display=on?'none':''; document.getElementById('coord').hidden=on;
  if (on){ if(!window.THREE){ diag('3d','biblioteka 3D nie wczytała się (brak połączenia z CDN)'); toggle3D(false); return; } init3D(); focus3D(); build3D(); }
}
document.getElementById('btn3d').addEventListener('click',()=>toggle3D(!is3D));
window.__p11dbg={ get R3(){ return R3; }, get items(){ return project[floor].items; }, get sel(){ return selectedId; }, addWall(pts,w,side){ draft={type:'wall',pts:pts.map(q=>q.slice())}; if(w==='custom'){ document.getElementById('wallW').value='custom'; } else document.getElementById('wallW').value=String(w||120); document.getElementById('wallSide').value=String(side||0); finishDraft(); return project[floor].items[project[floor].items.length-1]; }, layer(k,on){ layerOn[k]=on; updateLayerVisibility(); drawProject(); }, raster(){ return getRaster(); }, snapEnds(it,tol){ return snapWallEnds(it,tol); }, hits(it){ return rectCollisions(rectOf(it),wallSegsAll()); }, low(it){ return tooLowFor(it); }, get wallDrag(){ return wallDrag; } };
window.addEventListener('resize',()=>{ if(is3D&&R3){ size3D(); render3D(); } });
// ---------- boot ----------
setFloor(floor);
setTool('select');
window.addEventListener('resize',()=>{ applyView(); });
initDb();
})();
