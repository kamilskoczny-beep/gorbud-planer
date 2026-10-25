"""Dzieli page_template.html (model roboczy) na web/src/legacy/{page.css,page.body.html,page.js}.
Użycie: python3 tools/split_legacy.py <ścieżka do page_template.html>
Klucze localStorage 'p11.' → KEYP (adapter PLANER), zapis/odczyt elementów przez window.PLANER."""
import re, sys, pathlib
src=pathlib.Path(sys.argv[1]); out=pathlib.Path(__file__).resolve().parent.parent/'web/src/legacy'
t=src.read_text(encoding='utf-8')
css=max(re.findall(r'<style>(.*?)</style>',t,re.S),key=len)
body=t[t.index('</style>')+8:]
body=body[:body.index('</main>')+7]
body=re.sub(r'<script(?: [^>]*)?>.*?</script>','',body,flags=re.S).strip()
js=max(re.findall(r'<script(?: [^>]*)?>(.*?)</script>',t,re.S),key=len)
lines=js.split('\n'); lines.insert(2,"const KEYP=(window.PLANER&&window.PLANER.key)||'p11';"); js='\n'.join(lines)
js=js.replace("'p11.variants'","KEYP+'.variants'").replace("'p11.layers'","KEYP+'.layers'").replace("'p11.proj.'","KEYP+'.proj.'").replace("'p11.under'","KEYP+'.under'").replace("'p11.alignAdj'","KEYP+'.alignAdj'")
a="  try{ localStorage.setItem(KEYP+'.proj.'+f, JSON.stringify(items)); }catch(e){}"
assert js.count(a)==1, 'save hook'
js=js.replace(a,a+"\n  if (window.PLANER && window.PLANER.saveItems){ try{ setStatus('','zapisywanie…'); await window.PLANER.saveItems(f, items); setStatus('ok','zapisano '+new Date().toLocaleTimeString('pl-PL',{hour:'2-digit',minute:'2-digit'})); }catch(err){ setStatus('warn','brak zapisu: '+(err&&err.message||'błąd')); } return; }")
b="    for (const f of FLOORS){ try{ const s=localStorage.getItem(KEYP+'.proj.'+f); if(s) project[f].items=JSON.parse(s); }catch(e){} }"
assert js.count(b)==1, 'load hook'
js=js.replace(b,b+"\n    if (window.PLANER && window.PLANER.loadItems){ for (const f of FLOORS){ try{ const it=await window.PLANER.loadItems(f); if(Array.isArray(it)) project[f].items=JSON.parse(JSON.stringify(it)); }catch(e){} } drawProject(); renderItems(); renderLegend(); setStatus('ok','projekt: '+(window.PLANER.name||'')); return; }")
(out/'page.css').write_text(css.strip()+'\n',encoding='utf-8'); (out/'page.body.html').write_text(body+'\n',encoding='utf-8'); (out/'page.js').write_text(js,encoding='utf-8'); (out/'page_template.html').write_text(t,encoding='utf-8')
print('ok', len(css), len(body), len(js))
