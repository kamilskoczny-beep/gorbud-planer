import json, re, math, sys
db = json.load(open('zsu.json'))
ents = db['entities']
# block definitions
blocks = {}
for br in db['tables']['BLOCK_RECORD']['entries']:
    blocks[br['name']] = br.get('entities', [])

bands = {'piwnica': (-26000, 13000), 'parter': (13000, 51000), 'pietro1': (51000, 91500), 'poddasze': (91500, 129000)}
XMAX = 1916000
LAYERMAP = {'Sciany': 'walls', 'witryny.okna': 'windows', 'drzwi i wyp.': 'doors', 'schody': 'stairs',
            'PARAPET': 'sills', 'sufit': 'ceiling', 'dach': 'roof', 'kreskowanie': 'hatch', 'PODCIĄG': 'beams',
            'wypos': 'fixtures', '0': 'misc', 'Defpoints': None, 'linie wymiarowe': 'dims', 'wymiary': 'dims',
            '2-OPIS': 'text', '5': None, 'działka': None, '2DA_SYM': None}

def clean(t):
    t = re.sub(r'\\[A-Za-z][^;]*;', '', t)
    t = t.replace('{', '').replace('}', '').replace('\\P', ' ')
    return t.strip()

def seg_entities(e, ox=0, oy=0, sx=1, sy=1, rot=0):
    """yield primitive segments/arcs from entity (with optional block transform)"""
    def tr(p):
        x, y = p['x'] * sx, p['y'] * sy
        if rot:
            c, s = math.cos(rot), math.sin(rot)
            x, y = x * c - y * s, x * s + y * c
        return [x + ox, y + oy]
    t = e['type']
    if t == 'LINE':
        yield {'k': 'l', 'p': [tr(e['startPoint']), tr(e['endPoint'])]}
    elif t == 'LWPOLYLINE':
        v = [tr(p) for p in e['vertices']]
        if e.get('closed') and len(v) > 2: v.append(v[0])
        yield {'k': 'pl', 'p': v}
    elif t == 'ARC':
        c = tr(e['center']); r = e['radius'] * sx
        yield {'k': 'a', 'c': c, 'r': r, 'a0': e['startAngle'] + rot, 'a1': e['endAngle'] + rot}
    elif t == 'CIRCLE':
        c = tr(e['center']); r = e['radius'] * sx
        yield {'k': 'c', 'c': c, 'r': r}
    elif t == 'INSERT':
        name = e.get('name')
        ip = e['insertionPoint']
        for be in blocks.get(name, []):
            yield from seg_entities(be, ox=ip['x'], oy=ip['y'], sx=e.get('xScale', 1) or 1, sy=e.get('yScale', 1) or 1, rot=e.get('rotation', 0) or 0)

out = {}
for fl, (y0, y1) in bands.items():
    geo = {}
    texts = []
    for e in ents:
        lay = e['layer']
        grp = LAYERMAP.get(lay, 'misc')
        if grp is None: continue
        p = e.get('startPoint') or e.get('insertionPoint') or e.get('center')
        if e['type'] == 'LWPOLYLINE': p = e['vertices'][0]
        if e['type'] == 'DIMENSION': continue
        if not p or not (y0 <= p['y'] < y1 and p['x'] < XMAX): continue
        if e['type'] in ('TEXT', 'MTEXT'):
            t = clean(e.get('text', ''))
            if not t: continue
            if lay == '2-OPIS':
                texts.append({'x': p['x'], 'y': p['y'], 't': t, 'h': e.get('textHeight', 160), 'r': e.get('rotation', 0)})
            continue
        if grp == 'text': continue
        for s in seg_entities(e):
            geo.setdefault(grp, []).append(s)
    # bbox of walls
    xs = []; ys = []
    for s in geo['walls']:
        pts = s.get('p') or [s['c']]
        for q in pts: xs.append(q[0]); ys.append(q[1])
    out[fl] = {'geo': geo, 'texts': texts, 'bbox': [min(xs), min(ys), max(xs), max(ys)]}
    print(fl, {k: len(v) for k, v in geo.items()}, 'texts', len(texts), 'bbox', [round(v) for v in out[fl]['bbox']])
json.dump(out, open('floors_raw.json', 'w'), ensure_ascii=False)
