/**
 * Planer GORBUD – powłoka aplikacji (etap 0).
 * Zarządza projektami w IndexedDB i uruchamia edytor rzutów (src/legacy/page.js – kod przeniesiony
 * z modelu roboczego Pocztowa 11; stopniowo przepisywany na moduły TypeScript w src/engine i src/ui).
 */
import './shell.css';
import './legacy/page.css';
import legacyBody from './legacy/page.body.html?raw';
import { store, slug, download, pickFile, type PlanerProject } from './store';
import seedModel from '../../projects/drawsko-pocztowa11/model.json';
import seedVariants from '../../projects/drawsko-pocztowa11/variants.json';
import seedItems from '../../projects/drawsko-pocztowa11/items_pietro1.json';
import seedAttic from '../../projects/drawsko-pocztowa11/items_poddasze.json';
import seedParter from '../../projects/drawsko-pocztowa11/items_parter.json';
import seedPiwnica from '../../projects/drawsko-pocztowa11/items_piwnica.json';

declare global { interface Window { PLANER?: PlanerAdapter } }
interface PlanerAdapter { key: string; name: string; loadItems(floor: string): Promise<unknown[] | null>; saveItems(floor: string, items: unknown[]): Promise<void>; }

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const LAST = 'planer.lastProject';
let current: PlanerProject | null = null;

async function seedIfEmpty() {
  const all = await store.list();
  if (all.length) return;
  const now = new Date().toISOString();
  const p: PlanerProject = {
    id: 'drawsko-pocztowa11', schema: 1, name: 'Pocztowa 11',
    subtitle: 'Drawsko Pomorskie · model roboczy zmiany sposobu użytkowania',
    createdAt: now, updatedAt: now, model: seedModel, variants: seedVariants,
    items: { pietro1: (seedItems as { items: unknown[] }).items, poddasze: (seedAttic as { items: unknown[] }).items, parter: (seedParter as { items: unknown[] }).items, piwnica: (seedPiwnica as { items: unknown[] }).items },
  };
  await store.put(p);
}

async function refreshList() {
  const all = (await store.list()).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  const sel = $<HTMLSelectElement>('projSel');
  sel.innerHTML = all.map(p => `<option value="${p.id}">${p.name}${p.subtitle ? ' — ' + p.subtitle : ''}</option>`).join('');
  if (current) sel.value = current.id;
  return all;
}

function mountEditor(p: PlanerProject) {
  current = p; localStorage.setItem(LAST, p.id);
  $('modelData').textContent = JSON.stringify(p.model);
  $('variantData').textContent = JSON.stringify(p.variants);
  window.PLANER = {
    key: 'planer.' + p.id, name: p.name,
    async loadItems(floor) { const fresh = await store.get(p.id); return (fresh?.items?.[floor] as unknown[]) ?? null; },
    async saveItems(floor, items) { const fresh = (await store.get(p.id)) ?? p; fresh.items = { ...fresh.items, [floor]: items }; await store.put(fresh); current = fresh; $('projInfo').textContent = 'zapisano ' + new Date().toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' }); },
  };
  const app = $('app'); app.innerHTML = legacyBody;
  const h1 = app.querySelector('header h1');
  if (h1) h1.innerHTML = `${escapeHtml(p.name)}<small>${escapeHtml(p.subtitle || '')}</small>`;
  document.title = `${p.name} – Planer GORBUD`;
  // edytor jest skryptem klasycznym (IIFE) – ładujemy go raz na otwarcie projektu
  const s = document.createElement('script'); s.src = new URL('./legacy/page.js', import.meta.url).href; s.dataset.editor = '1';
  app.appendChild(s);
  $('projInfo').textContent = `${Object.values(p.items).reduce((n, a) => n + (a?.length || 0), 0)} elementów · zapis automatyczny w tej przeglądarce`;
}

function openProject(id: string) { // edytor nie umie się jeszcze przeładować w miejscu – odświeżamy stronę
  localStorage.setItem(LAST, id); location.hash = ''; location.reload();
}

function escapeHtml(s: string) { return s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c] as string)); }

async function main() {
  await seedIfEmpty();
  const all = await refreshList();
  const want = localStorage.getItem(LAST);
  const p = all.find(x => x.id === want) || all[0];
  if (p) mountEditor(p);
  await refreshList();

  $('projOpen').onclick = () => openProject($<HTMLSelectElement>('projSel').value);
  $<HTMLSelectElement>('projSel').ondblclick = () => openProject($<HTMLSelectElement>('projSel').value);
  $('projNew').onclick = async () => {
    const txt = await pickFile($<HTMLInputElement>('fileModel')); if (!txt) return;
    let model: { floors?: Record<string, { name?: string }> };
    try { model = JSON.parse(txt); } catch { alert('To nie jest poprawny JSON.'); return; }
    if (!model.floors) { alert('Plik nie wygląda na model.json (brak "floors"). Użyj narzędzia tools/dwg, żeby zrobić model z DWG.'); return; }
    const name = prompt('Nazwa projektu (np. adres budynku):', 'Nowy budynek'); if (!name) return;
    const subtitle = prompt('Podtytuł (miejscowość · zakres):', '') || '';
    const id = slug(name) + '-' + Date.now().toString(36).slice(-4);
    const now = new Date().toISOString();
    const items: Record<string, unknown[]> = {}; Object.keys(model.floors).forEach(f => items[f] = []);
    const variants = { units: {}, floors: Object.fromEntries(Object.keys(model.floors).map(f => [f, []])) };
    await store.put({ id, schema: 1, name, subtitle, createdAt: now, updatedAt: now, model, variants, items });
    openProject(id);
  };
  $('projImport').onclick = async () => {
    const txt = await pickFile($<HTMLInputElement>('fileProject')); if (!txt) return;
    let p: PlanerProject; try { p = JSON.parse(txt); } catch { alert('To nie jest poprawny JSON.'); return; }
    if (p.schema !== 1 || !p.id || !p.model) { alert('To nie jest plik .planer.json.'); return; }
    const ex = await store.get(p.id);
    if (ex && !confirm(`Projekt „${ex.name}” już istnieje w tej przeglądarce. Nadpisać?`)) return;
    await store.put(p); openProject(p.id);
  };
  $('projExport').onclick = async () => {
    if (!current) return; const fresh = (await store.get(current.id)) ?? current;
    const d = new Date().toISOString().slice(0, 10);
    download(`${slug(fresh.name)}_${d}.planer.json`, JSON.stringify(fresh));
  };
  $('projDelete').onclick = async () => {
    if (!current) return; if (!confirm(`Usunąć projekt „${current.name}” z tej przeglądarki? Zrób wcześniej Eksport.`)) return;
    await store.del(current.id); localStorage.removeItem(LAST); location.reload();
  };
}

main().catch(err => { console.error(err); $('projInfo').textContent = 'Błąd uruchomienia: ' + (err?.message || err); });
