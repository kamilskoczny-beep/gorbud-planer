"""Jednorazowy skrypt z 2026-10-25 (Pocztowa 11): ponowne przerysowanie piwnicy, ściany na obrysie → nośne, pytania o grubość
(qFix = propozycja wprowadzana przy „potwierdzam”). Ścieżki S/… wskazują katalog roboczy – do ponownego użycia podmień je."""
import json, sys, math, copy
sys.path.insert(0, '/home/claude/gorbud-planer/tools/dwg')
from exterior_walls import exterior, footprint_dwg
import join_corners
from shapely.geometry import LineString, Point
from shapely.affinity import translate

S = '/tmp/claude-0/-home-claude/cb81abd0-51f0-55bb-946c-6f7d15844280/scratchpad'
ALIGN = {'piwnica': [20, 300], 'parter': [180, 220], 'pietro1': [0, 0], 'poddasze': [-20, 140]}
FL = ['piwnica', 'parter', 'pietro1', 'poddasze']
m = json.load(open('/home/claude/drawsko/model_final.json'))
_P = m['floors']['piwnica']['geo']
for s in list(_P.get('dims', [])):
    if s.get('k') == 'l' and any(tuple(p) in {(3100, 20621), (3100, 23701), (290, 20621), (18710, 17607), (9703, 17607), (9703, 24253)} for p in map(tuple, s['p'])):
        _P['dims'].remove(s); _P['walls'].append(s)

items = {f: json.load(open(f'{S}/live49/projekt/{f}.json'))['items'] for f in FL}
log = []

# ---------- 1) piwnica: ponowne przerysowanie ścian/okien/drzwi z poprawionym obrysem (lica z warstwy wymiarów) ----------
new = json.load(open(f'{S}/piw/items_inw_piwnica.json'))['items']
TM = {'wall': 'iwall', 'window': 'iwin', 'door': 'idoor'}
keep = [i for i in items['piwnica'] if i['type'] not in ('iwall', 'iwin', 'idoor')]
conv = []
for i in new:
    if i['type'] in TM:
        j = dict(i); j['type'] = TM[i['type']]; conv.append(j)
old_n = {t: sum(1 for i in items['piwnica'] if i['type'] == t) for t in ('iwall', 'iwin', 'idoor')}
nj = join_corners.join(conv)
items['piwnica'] = keep + conv
log.append(f"piwnica: przerysowane ściany {old_n['iwall']}→{sum(1 for i in conv if i['type']=='iwall')}, okna {old_n['iwin']}→{sum(1 for i in conv if i['type']=='iwin')}, drzwi {old_n['idoor']}→{sum(1 for i in conv if i['type']=='idoor')}, domknięte narożniki {nj}")

# ---------- 2) obrysy kondygnacji (poddasze ∪ I piętro – skosy wycinają lico) ----------
FP = {f: footprint_dwg(m['floors'][f]['geo']) for f in FL}
d = (ALIGN['pietro1'][0] - ALIGN['poddasze'][0], ALIGN['pietro1'][1] - ALIGN['poddasze'][1])
FP['poddasze'] = FP['poddasze'].union(translate(FP['pietro1'], d[0], d[1]))

def ext_ids(f):
    walls = [i for i in items[f] if i['type'] == 'iwall']
    F = FP[f]; out = set()
    for w in walls:
        (ax, ay), (bx, by) = w['pts']; L = math.hypot(bx - ax, by - ay)
        if L < 300: continue
        ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = -uy, ux; off = w.get('w', 100) / 2 + 250
        n = max(3, int(L / 400)); hit = [0, 0]
        for k in range(1, n):
            t = L * k / n; px, py = ax + ux * t, ay + uy * t
            for s_, sg in enumerate((1, -1)):
                if not F.contains(Point(px + sg * nx * off, py + sg * ny * off)): hit[s_] += 1
        if max(hit) >= 0.6 * (n - 1): out.add(w['id'])
    return out

EXT = {f: ext_ids(f) for f in FL}

def G(p, f):
    return (p[0] + ALIGN[f][0], p[1] + ALIGN[f][1])

def counterpart(w, f, g, ext_only=False):
    """ściana na kondygnacji g w tym samym miejscu (równoległa, oś ≤ 450 mm, nakład ≥ 50 %)."""
    a, b = G(w['pts'][0], f), G(w['pts'][1], f); L = math.dist(a, b) or 1
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L); best = None
    for o in items[g]:
        if o['type'] != 'iwall' or (ext_only and o['id'] not in EXT[g]): continue
        oa, ob = G(o['pts'][0], g), G(o['pts'][1], g); oL = math.dist(oa, ob) or 1
        v = ((ob[0] - oa[0]) / oL, (ob[1] - oa[1]) / oL)
        if abs(u[0] * v[1] - u[1] * v[0]) > 0.08: continue
        dist = abs((oa[0] - a[0]) * (-u[1]) + (oa[1] - a[1]) * u[0])
        if dist > 450: continue
        t0 = (oa[0] - a[0]) * u[0] + (oa[1] - a[1]) * u[1]; t1 = (ob[0] - a[0]) * u[0] + (ob[1] - a[1]) * u[1]
        ov = min(L, max(t0, t1)) - max(0, min(t0, t1))
        if ov < 0.5 * min(L, oL): continue
        if best is None or ov > best[0]: best = (ov, o)
    return best[1] if best else None

cm = lambda v: f"{round(v / 10)} cm"
NB = {'piwnica': ['parter'], 'parter': ['piwnica', 'pietro1'], 'pietro1': ['parter', 'poddasze'], 'poddasze': ['pietro1']}
for f in FL:
    nN = 0; nq = 0
    for w in items[f]:
        if w['type'] != 'iwall' or w['id'] not in EXT[f]: continue
        if w.get('inv') == 'D':
            w['inv'] = 'N'; nN += 1
        if w.get('w', 0) < 300:
            sug = None
            for g in NB[f]:
                o = counterpart(w, f, g, ext_only=True)
                if o and o.get('w', 0) >= 300: sug = (g, o['w']); break
            single = w.get('w', 0) <= 100
            base = ('ściana zewnętrzna narysowana w podkładzie jedną linią' if single else f"ściana zewnętrzna o grubości tylko {cm(w['w'])}")
            if sug:
                w['q'] = f"{base} – ściana na obrysie budynku jest nośna; na kondygnacji {({'piwnica':'piwnica','parter':'parter','pietro1':'I piętro','poddasze':'poddasze'})[sug[0]]} w tym miejscu {cm(sug[1])}. Proponuję {cm(sug[1])} (potwierdzam = przyjmij propozycję)."
                w['qFix'] = {'w': sug[1]}
            else:
                w['q'] = f"{base} – ściana na obrysie budynku jest nośna; jaka jest jej grubość? (wpisz w komentarzu)"
            nq += 1
    log.append(f"{f}: ścian na obrysie {len(EXT[f])}, przeniesione z działowych do nośnych {nN}, pytania o grubość ścian zewnętrznych {nq}")

# ---------- 3) piwnica: kontrola grubości ścian nośnych względem parteru i wzdłuż tej samej ściany ----------
sus = []
for w in items['piwnica']:
    if w['type'] != 'iwall' or w.get('inv') != 'N' or w.get('qFix'): continue
    o = counterpart(w, 'piwnica', 'parter')
    if o and o.get('inv') == 'N' and o.get('w', 0) - w.get('w', 0) >= 60:
        w['q'] = (w.get('q', '') + ' · ' if w.get('q') else '') + f"ściana piwnicy ({cm(w['w'])}) cieńsza niż ściana nad nią na parterze ({cm(o['w'])}) – ściana nośna w piwnicy nie powinna być cieńsza. Proponuję {cm(o['w'])} (potwierdzam = przyjmij)."
        w['qFix'] = {'w': o['w']}; sus.append(('cieńsza niż parter', w['id'], w['w'], o['w']))
# ta sama linia ściany, różne grubości kawałków (> 40 mm)
W = [w for w in items['piwnica'] if w['type'] == 'iwall' and w.get('inv') == 'N']
for i, w in enumerate(W):
    a, b = w['pts']; L = math.dist(a, b) or 1; u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    for o in W[i + 1:]:
        oa, ob = o['pts']; oL = math.dist(oa, ob) or 1; v = ((ob[0] - oa[0]) / oL, (ob[1] - oa[1]) / oL)
        if abs(u[0] * v[1] - u[1] * v[0]) > 0.05: continue
        if abs((oa[0] - a[0]) * (-u[1]) + (oa[1] - a[1]) * u[0]) > 150: continue
        gap = min(math.dist(p, q) for p in (a, b) for q in (oa, ob))
        if gap > 1500: continue
        dw = abs(w['w'] - o['w'])
        if 40 < dw < 250:
            thin, thick = (w, o) if w['w'] < o['w'] else (o, w)
            if thin.get('qFix'): continue
            thin['q'] = (thin.get('q', '') + ' · ' if thin.get('q') else '') + f"ta sama ściana ma obok grubość {cm(thick['w'])}, tu {cm(thin['w'])} – błąd rysunku czy faktyczne przewężenie (np. wnęka)? Proponuję {cm(thick['w'])} (potwierdzam = przyjmij)."
            thin['qFix'] = {'w': thick['w']}; sus.append(('różne grubości w jednej linii', thin['id'], thin['w'], thick['w']))
log.append(f"piwnica: podejrzane grubości ścian: {len(sus)}")
for s_ in sus: log.append('   ' + str(s_))

for f in FL:
    json.dump({'items': items[f]}, open(f'{S}/db49_{f}.json', 'w'), ensure_ascii=False)
print('\n'.join(log))
