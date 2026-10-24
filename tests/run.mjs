// Test dymny: buduje aplikację, uruchamia podgląd i sprawdza, że edytor startuje, zapisuje i odczytuje projekt.
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
const sh=(cmd,args,opts={})=>new Promise((res,rej)=>{ const p=spawn(cmd,args,{stdio:'inherit',shell:process.platform==='win32',...opts}); p.on('exit',c=>c===0?res():rej(new Error(cmd+' exit '+c))); });
await sh('npx',['vite','build'],{cwd:new URL('../web',import.meta.url)});
const srv=spawn('npx',['vite','preview','--port','4199','--strictPort'],{cwd:new URL('../web',import.meta.url),stdio:'ignore',shell:process.platform==='win32'});
await new Promise(r=>setTimeout(r,2500));
let fail=0; const check=(ok,msg)=>{ console.log((ok?'OK  ':'FAIL')+' '+msg); if(!ok) fail++; };
try{
  const b=await chromium.launch(); const pg=await b.newPage({viewport:{width:1400,height:900}});
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  await pg.goto('http://localhost:4199/'); await pg.waitForTimeout(2500);
  check(await pg.evaluate(()=>!!window.__p11dbg),'edytor uruchomiony');
  const n0=await pg.evaluate(()=>window.__p11dbg.items.length);
  await pg.evaluate(()=>window.__p11dbg.addWall([[1000,9000],[2500,9000]],120,0)); await pg.waitForTimeout(1500);
  await pg.reload(); await pg.waitForTimeout(2500);
  const n1=await pg.evaluate(()=>window.__p11dbg.items.length);
  check(n1===n0+1,'zapis i odczyt projektu (IndexedDB): '+n0+' -> '+n1);
  check(errs.length===0,'brak błędów JS'+(errs.length?': '+errs.join(' | '):''));
  await b.close();
} finally { srv.kill(); }
process.exit(fail?1:0);
