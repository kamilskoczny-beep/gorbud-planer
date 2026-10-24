/**
 * Magazyn projektów w przeglądarce (IndexedDB).
 * Jeden rekord = jeden projekt (plik .planer.json w pamięci). Format: docs/FORMAT_PROJEKTU.md
 */
export interface PlanerProject {
  id: string;                 // slug, np. "drawsko-pocztowa11"
  schema: 1;
  name: string;               // "Pocztowa 11"
  subtitle?: string;          // "Drawsko Pomorskie · model roboczy …"
  createdAt: string;
  updatedAt: string;
  model: unknown;             // wynik tools/dwg (geometria kondygnacji, pomieszczenia, teksty)
  variants: unknown;          // warianty koncepcji, lokale, skosy poddasza
  items: Record<string, unknown[]>; // elementy projektowane per kondygnacja
  ui?: { layers?: Record<string, boolean>; variants?: Record<string, string | null> };
}

const DB = 'planer-gorbud';
const STORE = 'projects';

function openDb(): Promise<IDBDatabase> {
  return new Promise((res, rej) => {
    const r = indexedDB.open(DB, 1);
    r.onupgradeneeded = () => { r.result.createObjectStore(STORE, { keyPath: 'id' }); };
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}

function tx<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return openDb().then(db => new Promise<T>((res, rej) => {
    const t = db.transaction(STORE, mode); const req = fn(t.objectStore(STORE));
    req.onsuccess = () => res(req.result); req.onerror = () => rej(req.error);
  }));
}

export const store = {
  list: () => tx<PlanerProject[]>('readonly', s => s.getAll() as IDBRequest<PlanerProject[]>),
  get: (id: string) => tx<PlanerProject | undefined>('readonly', s => s.get(id) as IDBRequest<PlanerProject | undefined>),
  put: (p: PlanerProject) => { p.updatedAt = new Date().toISOString(); return tx('readwrite', s => s.put(p)); },
  del: (id: string) => tx('readwrite', s => s.delete(id)),
};

export function slug(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l').replace(/Ł/g, 'L')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48) || 'projekt';
}

export function download(name: string, data: string, type = 'application/json') {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([data], { type })); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

export function pickFile(input: HTMLInputElement): Promise<string | null> {
  return new Promise(res => {
    input.value = '';
    input.onchange = () => { const f = input.files && input.files[0]; if (!f) return res(null); f.text().then(res); };
    input.click();
  });
}
