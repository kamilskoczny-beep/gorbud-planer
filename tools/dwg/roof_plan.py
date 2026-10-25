"""Rzut dachu z DWG projektu remontu dachu (stan istniejący) → podkład + model inwentaryzacyjny dachu.

Użycie: python3 roof_plan.py roof.json OUT_DIR [dx dy]
  roof.json – zrzut DWG (dump.mjs), OUT_DIR – zapis dach_geo.json (podkład) i dach_items.json (model),
  dx dy – przesunięcie DWG → układ lokalny parteru (dopasowanie obrysu ścian, fit2.py): domyślnie -42118.7 -16369.
Rodzaje linii modelu (iroofl.k): kalenica, naroze, kosz, okap, krawedz (dachu płaskiego), sciana (obrys ścian zewn., przerywana), wieza.
"""
import json, math, sys

src, out = sys.argv[1], sys.argv[2]
DX, DY = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (-42118.7, -16369.0)
X0, X1, Y0, Y1 = 40000, 72000, 14000, 42000  # okno rysunku „Rzut dachu – stan istniejący”
E = json.load(open(src))['entities']
T = lambda p: [int(round((p['x'] + DX) / 10.0)) * 10, int(round((p['y'] + DY) / 10.0)) * 10]
inb = lambda p: X0 < p['x'] < X1 and Y0 < p['y'] < Y1

lines = []  # (a, b, layer, dashed)
for e in E:
    if e['type'] == 'LINE' and inb(e['startPoint']) and inb(e['endPoint']):
        lines.append((T(e['startPoint']), T(e['endPoint']), e['layer'], e.get('lineType') == 'Przerywana'))
    elif e['type'] == 'LWPOLYLINE':
        v = [p for p in e['vertices'] if inb(p)]
        if len(v) == len(e['vertices']):
            v = [T(p) for p in v]
            for i in range(len(v) - 1):
                lines.append((v[i], v[i + 1], e['layer'], e.get('lineType') == 'Przerywana'))
            if e.get('flag', 0) & 1:
                lines.append((v[-1], v[0], e['layer'], False))

geo = {'fixtures': [{'k': 'l', 'p': [a, b]} for a, b, _, _ in lines]}
texts = []
for e in E:
    if e['type'] == 'MTEXT' and inb(e['insertionPoint']):
        t = e['text']
        if '46' in t:
            p = T(e['insertionPoint']); texts.append({'x': p[0], 'y': p[1], 't': '46°', 'h': 180, 'r': 0})
xs = [q[0] for a, b, _, _ in lines for q in (a, b)]; ys = [q[1] for a, b, _, _ in lines for q in (a, b)]
bbox = [min(xs), min(ys), max(xs), max(ys)]

TOWER = (23415, 2369)  # środek wieżyczki (układ parteru)

def kind(a, b, layer, dashed):
    L = math.dist(a, b)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if math.dist(mid, TOWER) < 1900 and L < 3200:
        return 'wieza'
    if dashed:
        return 'sciana'
    if layer.endswith('__20'):
        return 'wieza'
    if layer.endswith('__1'):
        return 'naroze' if L > 800 else None
    if layer.endswith('__7'):
        if L < 400:
            return None
        dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
        return 'naroze' if min(dx, dy) > 0.5 * max(dx, dy) else 'okap'
    if layer.endswith('__21'):
        if L < 1200:
            return None  # zarysy kominów/okien – osobne elementy
        dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
        diag = min(dx, dy) > 0.5 * max(dx, dy)
        return 'diag' if diag else 'prosta'
    return None

items = []
n = 0
for a, b, layer, dashed in lines:
    k = kind(a, b, layer, dashed)
    if not k:
        continue
    items.append({'id': f'inw-dach-l{n:03d}', 'type': 'iroofl', 'k': k, 'pts': [a, b]}); n += 1

# doprecyzowanie: kalenice, kosze, naroża, krawędzie dachu płaskiego (geometria dachu – patrz rys. 05 projektu remontu)
def near(p, q, t=250):
    return math.dist(p, q) < t
for it in items:
    a, b = it['pts']
    if it['k'] == 'prosta':
        L = math.dist(a, b)
        horiz = abs(b[1] - a[1]) < abs(b[0] - a[0])
        # kalenice: skrzydło zach. (x≈4790), skrzydło płd. (y≈4880), szczyty-wystawki (krótkie poziome od lica ściany zach.)
        if (not horiz and 4600 < a[0] < 5000 and L > 10000) or (horiz and 4700 < a[1] < 5100 and L > 10000) or (horiz and L < 3600 and min(a[0], b[0]) < 600):
            it['k'] = 'kalenica'
        elif min(a[1], b[1]) > -200 and max(a[1], b[1]) < 3800 and 5900 < min(a[0], b[0]) and max(a[0], b[0]) < 21800:
            it['k'] = 'krawedz'  # dach płaski (taras/papa) od ul. Pocztowej
        else:
            it['k'] = 'okap'
    elif it['k'] == 'diag':
        # kosze: od kalenicy do naroża wklęsłego (wewnętrzny narożnik L) i przy wystawkach; naroża: do narożników wypukłych
        if any(near(p, q, 400) for p in (a, b) for q in ((9444, 9389), (6443, 6469), (6709, 6728), (2803, 17779), (3518, 6164))) and not any(near(p, q, 400) for p in (a, b) for q in ((-514, -293),)):
            it['k'] = 'kosz'
        else:
            it['k'] = 'naroze'

# kominy (zarysy z DWG, układ parteru) + liczba kanałów ze zdjęć z drona 2026-08 (DJI_0375/0379/0404)
CH = [
    ('A', [[18326, 5804], [18734, 6580]], 2, 0, 'skrzydło płd., przy wieżyczce; 2 kanały obok siebie (DJI_0375, DJI_0404)', None),
    ('B', [[14759, 5112], [15292, 6709]], 4, 1, 'skrzydło płd.; trzon z 3 lizen, 4 kanały murowane + element stalowy (wkład/nasada?) (DJI_0375, DJI_0404)',
     'na koronie widać 4 kanały murowane i zardzewiały element stalowy – czy to 5. kanał z wkładem stalowym? potwierdzić (kominiarz)'),
    ('C', [[6443, 5266], [6959, 6728]], 2, 0, 'skrzydło płd. przy narożu wewn.; 2 kanały (DJI_0375, DJI_0404)', None),
    ('D', [[9444, 9389], [10345, 10670]], 2, 1, 'wysoki komin w narożu wewn. (kosz); 2 kanały murowane + wkład stalowy z nasadą – przewód spalinowy kotłowni gazowej (DJI_0375, DJI_0404)', None),
    ('E', [[5905, 8998], [6916, 9395]], 2, 0, 'skrzydło zach. przy narożu; 2 kanały jeden za drugim; to ten sam trzon co „występ” w 108 (I p.) i 211 (poddasze) (DJI_0375, DJI_0404)', None),
    ('F', [[7034, 14893], [8024, 15325]], 2, 0, 'skrzydło zach., komin pom. 217 (poddasze); 2 kanały jeden za drugim (DJI_0375, DJI_0379)', None),
    ('G', [[8300, 23150], [8700, 23550]], 1, 0, 'ściana szczytowa płn. (od strony podwórza), 1 kanał (DJI_0375, DJI_0379)',
     'komin przy ścianie szczytowej płn. widoczny tylko na zdjęciach – brak w rysunkach; położenie przybliżone (±0,5 m), 1 kanał – potwierdzić'),
    ('H', [[4500, 22930], [4900, 23330]], 1, 0, 'ściana szczytowa płn., przy kalenicy, 1 kanał (DJI_0375, DJI_0379)',
     'komin przy kalenicy skrzydła zach. (ściana płn.) widoczny tylko na zdjęciach – brak w rysunkach; położenie przybliżone (±0,5 m), 1 kanał – potwierdzić'),
]
for key, pts, nk, ns, label, q in CH:
    it = {'id': f'inw-dach-k{key}', 'type': 'chimney', 'pts': pts, 'n': nk, 'ns': ns, 'label': f'{nk + ns} kan.' + (f' ({ns} stal.)' if ns else ''), 'note': label}
    if q:
        it['q'] = q
    items.append(it)

# okna połaciowe / wyłaz (z inwentaryzacji poddasza, układ poddasza → parter: (-200,-80)) – potwierdzone zdjęciami
for i, (p0, p1, txt) in enumerate([
    ([7810, 11790], [8970, 12520], 'wyłaz / okno połaciowe 116×73 (DWG dachu: ramka – okno wyłazowe; protokół kominiarski: „okno wyłazowe do wymiany”)'),
    ([7810, 16560], [8970, 17300], 'okno połaciowe 116×73'),
    ([7810, 20500], [8970, 21230], 'okno połaciowe 116×73'),
    ([4550, 930], [5280, 2090], 'okno połaciowe 73×116'),
]):
    it = {'id': f'inw-dach-o{i}', 'type': 'iroof', 'pts': [[p0[0] - 200, p0[1] - 80], [p1[0] - 200, p1[1] - 80]], 'note': txt}
    if i == 3:
        it['q'] = 'okno połaciowe na połaci płd.-zach. (z rzutu poddasza) – na zdjęciach z drona niewidoczne; potwierdzić'
    items.append(it)

# spadki połaci 46° (z rysunku 05 projektu remontu)
for i, (p, d) in enumerate([((3531, 13760), (-1, 0)), ((5481, 13760), (1, 0)), ((12380, 6190), (0, 1)), ((12380, 4380), (0, -1))]):
    items.append({'id': f'inw-dach-s{i}', 'type': 'slope', 'pts': [list(p)], 'dir': list(d), 'deg': 46})

json.dump({'name': 'Dach', 'geo': geo, 'texts': texts, 'rooms': [], 'bbox': bbox}, open(f'{out}/dach_geo.json', 'w'), ensure_ascii=False)
json.dump(items, open(f'{out}/dach_items.json', 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print('podkład linii:', len(lines), 'bbox', bbox)
print(Counter(i.get('k', i['type']) for i in items))
