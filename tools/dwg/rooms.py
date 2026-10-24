"""Flood-fill rooms from wall geometry; produce room polygons + model JSON in local mm coords."""
import json, math, re
import numpy as np, cv2

d = json.load(open('floors_raw.json'))
PX = 20.0  # mm per pixel

# alignment: shift each floor so that the staircase east wall x and south-west wall corner align
# use the walls bbox min as origin for piwnica/pietro1/poddasze; parter has different horizontal offset
ORIGIN = {}
for fl, f in d.items():
    b = f['bbox']
    ORIGIN[fl] = (b[0], b[1])
# parter: align stairs east edge to the other floors (1901473 vs 1903587 -> dx 2114) and ymin (16209)
ORIGIN['parter'] = (1878317 + (2114 - (1878317 - 1876365)), 16209)  # => x shift so stair aligns

def tr(fl, p):
    ox, oy = ORIGIN[fl]
    return [round(p[0] - ox), round(p[1] - oy)]

def arc_pts(c, r, a0, a1, n=12):
    if a1 < a0: a1 += 2 * math.pi
    return [[c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)] for i in range(n + 1)]

model = {'floors': {}, 'px': PX}
FLNAMES = {'piwnica': 'Piwnica', 'parter': 'Parter (Poczta)', 'pietro1': 'I piętro', 'poddasze': 'Poddasze'}
for fl, f in d.items():
    geo = {}
    for grp, segs in f['geo'].items():
        out = []
        for s in segs:
            if s['k'] in ('l', 'pl'):
                out.append({'k': 'l', 'p': [tr(fl, q) for q in s['p']]})
            elif s['k'] == 'a':
                out.append({'k': 'a', 'c': tr(fl, s['c']), 'r': round(s['r']), 'a0': round(s['a0'], 4), 'a1': round(s['a1'], 4)})
            elif s['k'] == 'c':
                out.append({'k': 'c', 'c': tr(fl, s['c']), 'r': round(s['r'])})
        geo[grp] = out
    texts = [{'x': tr(fl, [t['x'], t['y']])[0], 'y': tr(fl, [t['x'], t['y']])[1], 't': t['t'], 'h': t['h'], 'r': t['r']} for t in f['texts']]
    # ---- raster for flood fill
    allpts = [q for s in geo['walls'] if s['k']=='l' for q in s['p']]
    W = int(max(q[0] for q in allpts) / PX) + 40
    H = int(max(q[1] for q in allpts) / PX) + 40
    minx = min(q[0] for q in allpts); miny = min(q[1] for q in allpts)
    OFF = 20
    def px(q): return (int(round((q[0] - minx) / PX)) + OFF, int(round((q[1] - miny) / PX)) + OFF)
    img = np.zeros((H + 2 * OFF, W + 2 * OFF), np.uint8)
    for grp in ('walls', 'windows', 'doors', 'stairs' if fl == 'xx' else 'walls'):
        for s in geo[grp]:
            if s['k'] == 'l':
                for a, b in zip(s['p'][:-1], s['p'][1:]):
                    cv2.line(img, px(a), px(b), 255, 1)
            elif s['k'] == 'a':
                pts = arc_pts(s['c'], s['r'], s['a0'], s['a1'])
                for a, b in zip(pts[:-1], pts[1:]):
                    cv2.line(img, px(a), px(b), 255, 1)
    img0 = img.copy()
    imgs = []
    for ks in (53, 37, 25):
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
        imgs.append(cv2.morphologyEx(img0, cv2.MORPH_CLOSE, k))
    img = imgs[0]
    # ---- rooms from labels
    nums = [t for t in texts if re.fullmatch(r'\d{3}[aA]?', t['t']) and t['h'] >= 145]
    rooms = []
    seen = set()
    for t in nums:
        if t['t'] in seen: continue
        # name: nearest text to the right on same line; area: text with m² below-left
        name = None; area = None; hgt = None
        for u in texts:
            dx = u['x'] - t['x']; dy = u['y'] - t['y']
            if abs(dy) < 120 and 0 < dx < 2500 and not re.fullmatch(r'[\d.,]+ m²', u['t']) and name is None:
                name = u['t']
            if 'm²' in u['t'] and -600 < dy < 0 and abs(dx) < 1200:
                area = float(u['t'].replace('m²', '').replace(',', '.').strip())
            if u['t'].startswith('h') and '=' in u['t'] and -1000 < dy < 0 and abs(dx) < 2500 and hgt is None:
                hgt = u['t']
        # candidate seeds: number label, area text, name text, height text
        cands = [[t['x'] + 300, t['y'] + 60]]
        alts = [u for u in nums if u['t'] == t['t'] and u is not t]
        for u in alts: cands.insert(0, [u['x'] + 300, u['y'] + 60])
        if alts and (t['h'] or 0) >= 160:  # leader label; prefer the in-room one for label position
            t = {**t, 'x': alts[0]['x'], 'y': alts[0]['y']}
        for u in texts:
            dx = u['x'] - t['x']; dy = u['y'] - t['y']
            if abs(dx) < 2500 and -1200 < dy < 200 and u is not t:
                cands.append([u['x'] + 200, u['y'] + 60])
        best = None
        for img in imgs:
          if best: break
          for sp in cands:
              seed = px(sp)
              if not (0 <= seed[1] < img.shape[0] and 0 <= seed[0] < img.shape[1]): continue
              if img[seed[1], seed[0]] != 0: continue
              mask = np.zeros((img.shape[0] + 2, img.shape[1] + 2), np.uint8)
              fill = img.copy()
              cv2.floodFill(fill, mask, seed, 128)
              region = (fill == 128).astype(np.uint8)
              cnt = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
              if not cnt: continue
              c = max(cnt, key=cv2.contourArea)
              c = cv2.approxPolyDP(c, 1.5, True)
              pa = cv2.contourArea(c) * PX * PX / 1e6
              if area and not (0.7 * area < pa < 1.3 * area + 3): continue
              if not area and pa > 150: continue
              pl = [[round((p[0][0] - OFF) * PX + minx), round((p[0][1] - OFF) * PX + miny)] for p in c]
              score = abs(pa - area) if area else pa
              if best is None or score < best[0]: best = (score, pa, pl)
        poly = best[2] if best else None; parea = best[1] if best else None
        seen.add(t['t'])
        rooms.append({'nr': t['t'], 'name': name, 'area': area, 'h': hgt, 'lx': t['x'], 'ly': t['y'], 'poly': poly, 'parea': round(parea, 2) if parea else None})
    print(fl, 'rooms:')
    for r in rooms:
        print('  ', r['nr'], r['name'], r['area'], '->', r['parea'], 'poly' if r['poly'] else 'NOPOLY', r['h'])
    model['floors'][fl] = {'name': FLNAMES[fl], 'geo': geo, 'texts': texts, 'rooms': rooms,
                           'bbox': [0, 0, round(f['bbox'][2] - ORIGIN[fl][0]), round(f['bbox'][3] - ORIGIN[fl][1])]}
json.dump(model, open('model.json', 'w'), ensure_ascii=False, separators=(',', ':'))
import os; print('model.json', os.path.getsize('model.json'))
