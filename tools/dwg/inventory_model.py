"""Model inwentaryzacyjny z podkładu DWG (model.json) – ściany nośne/działowe (oś + grubość), okna, drzwi.

Podkład DWG jest niezmienny; ten skrypt wyprowadza z lic ścian edytowalne elementy:
  wall   {inv:'N'|'D', pts:[a,b], w}        – ściana istniejąca nośna (N, grubość ≥ 240) / działowa (D)
  window {inv:true, pts:[a,b], w}           – okno w ścianie (a,b na osi ściany = światło otworu), w = grubość ściany
  door   {inv:true, pts:[zawias,koniec], w:grubość+40, flip} – drzwi istniejące (szerokość = promień łuku w DWG)
Elementy z polem `q` wymagają potwierdzenia przez użytkownika (pytania).
Użycie: python3 inventory_model.py model.json out_dir  (zapisuje items_inw_<kondygnacja>.json)
Heurystyki: pary równoległych lic (±4°) w odległości 60–1600 mm z nakładem ≥ 300 mm, bez trzeciego lica pomiędzy i bez
pomieszczenia pomiędzy (wąski korytarz to nie ściana); oś = połowa odległości, grubość = średnia (lico skośne → `q`);
łączenie współliniowych kawałków, także przez otwory (okno – odcinek warstwy okien w otworze, drzwi – łuk).
Ścianki narysowane jedną linią → działowa 80 mm z `q`. Wszystko zaokrąglone do 10 mm.
"""
import json, math, sys, os
from collections import defaultdict

R10 = lambda v: int(round(v / 10.0)) * 10

def segs_of(geo, layer, minlen=40):
    out = []
    for s in geo.get(layer, []):
        if s.get('k') != 'l':
            continue
        p = s['p']
        for i in range(1, len(p)):
            a, b = p[i - 1], p[i]
            if math.hypot(b[0] - a[0], b[1] - a[1]) >= minlen:
                out.append((tuple(map(float, a)), tuple(map(float, b))))
    return out

def unit(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

def proj(p, o, u):
    return (p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1]

def perp(p, o, u):
    return (p[0] - o[0]) * (-u[1]) + (p[1] - o[1]) * u[0]

def parallel(u, v, tol_deg=4.0):
    return abs(u[0] * v[1] - u[1] * v[0]) <= math.sin(math.radians(tol_deg))

def point_in_poly(p, poly):
    c = False; n = len(poly)
    for i in range(n):
        a = poly[i]; b = poly[i - 1]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < (b[0] - a[0]) * (p[1] - a[1]) / ((b[1] - a[1]) or 1e-9) + a[0]:
            c = not c
    return c

class Piece:
    __slots__ = ('a', 'b', 't', 'q')
    def __init__(self, a, b, t, q=None):
        self.a = a; self.b = b; self.t = t; self.q = q
    def frame(self):
        u = unit(self.a, self.b); return self.a, u, math.hypot(self.b[0] - self.a[0], self.b[1] - self.a[1])

def extract_walls(wsegs, rooms, log, labels=()):
    pieces = []
    n = len(wsegs)
    us = [unit(a, b) for a, b in wsegs]
    for i in range(n):
        A0, A1 = wsegs[i]; uA = us[i]; LA = math.hypot(A1[0] - A0[0], A1[1] - A0[1])
        for j in range(i + 1, n):
            if not parallel(uA, us[j]):
                continue
            B0, B1 = wsegs[j]
            d0, d1 = perp(B0, A0, uA), perp(B1, A0, uA)
            if d0 * d1 <= 0:
                continue
            ad0, ad1 = abs(d0), abs(d1)
            if min(ad0, ad1) < 60 or max(ad0, ad1) > 950 or abs(ad0 - ad1) > 400:
                continue
            tb0, tb1 = proj(B0, A0, uA), proj(B1, A0, uA)
            ov0, ov1 = max(0.0, min(tb0, tb1)), min(LA, max(tb0, tb1))
            if ov1 - ov0 < 300:
                continue
            sgn = 1 if d0 > 0 else -1
            dmax = max(ad0, ad1)
            # trzecie lico pomiędzy?
            between = False
            for k in range(n):
                if k == i or k == j or not parallel(uA, us[k]):
                    continue
                C0, C1 = wsegs[k]
                e0, e1 = perp(C0, A0, uA) * sgn, perp(C1, A0, uA) * sgn
                if not (30 < (e0 + e1) / 2 < dmax - 30):
                    continue
                tc0, tc1 = sorted((proj(C0, A0, uA), proj(C1, A0, uA)))
                if min(tc1, ov1) - max(tc0, ov0) > 150:
                    between = True; break
            if between:
                continue
            def dist_at(t):
                if abs(tb1 - tb0) < 1e-6:
                    return (ad0 + ad1) / 2
                return ad0 + (ad1 - ad0) * (t - tb0) / (tb1 - tb0)
            nA = (-uA[1] * sgn, uA[0] * sgn)
            def mid(t):
                d = dist_at(t)
                return (A0[0] + uA[0] * t + nA[0] * d / 2, A0[1] + uA[1] * t + nA[1] * d / 2)
            inroom = 0
            for k in range(5):
                tt = ov0 + (ov1 - ov0) * (k + 0.5) / 5
                if any(point_in_poly(mid(tt), poly) for poly in rooms):
                    inroom += 1
            if inroom >= 2:
                continue
            # etykieta pomieszczenia albo łuk drzwi w pasie → to przestrzeń, nie ściana
            dm = max(ad0, ad1)
            if any(0 < perp(L_, A0, uA) * sgn < dm and ov0 - 100 < proj(L_, A0, uA) < ov1 + 100 for L_ in labels):
                continue
            t = (dist_at(ov0) + dist_at(ov1)) / 2
            q = None
            if abs(dist_at(ov0) - dist_at(ov1)) > 60:
                q = f'lico skośne – grubość {R10(dist_at(ov0))}–{R10(dist_at(ov1))} mm, przyjęto średnią'
            pieces.append(Piece(mid(ov0), mid(ov1), t, q))
    merged = []
    for p in sorted(pieces, key=lambda p: -math.hypot(p.b[0] - p.a[0], p.b[1] - p.a[1])):
        for q in merged:
            o, u, L = q.frame()
            if not parallel(u, unit(p.a, p.b), 1.5) or abs(q.t - p.t) > 30:
                continue
            if abs(perp(p.a, o, u)) > 25 or abs(perp(p.b, o, u)) > 25:
                continue
            ta, tb = sorted((proj(p.a, o, u), proj(p.b, o, u)))
            if ta > L + 60 or tb < -60:
                continue
            t0, t1 = min(0.0, ta), max(L, tb)
            q.a, q.b = (o[0] + u[0] * t0, o[1] + u[1] * t0), (o[0] + u[0] * t1, o[1] + u[1] * t1)
            q.q = q.q or p.q
            break
        else:
            merged.append(Piece(p.a, p.b, p.t, p.q))
    return merged

def bridge_openings(walls, winsegs, arcs, log):
    """Łączy współliniowe kawałki tej samej ściany przez otwory (okno/drzwi) albo małe przerwy (≤ 1300)."""
    changed = True
    while changed:
        changed = False
        for i in range(len(walls)):
            w = walls[i]; o, u, L = w.frame()
            for j in range(len(walls)):
                if i == j:
                    continue
                q = walls[j]
                if not parallel(u, unit(q.a, q.b), 1.5) or abs(q.t - w.t) > 40:
                    continue
                if abs(perp(q.a, o, u)) > 40 or abs(perp(q.b, o, u)) > 40:
                    continue
                ta, tb = sorted((proj(q.a, o, u), proj(q.b, o, u)))
                if ta >= L:
                    gap = ta - L; g0, g1 = L, ta
                elif tb <= 0:
                    gap = -tb; g0, g1 = tb, 0.0
                else:
                    continue
                if gap > 2700:
                    continue
                ok = gap <= 1300
                if not ok:
                    for a, b in winsegs:
                        if not parallel(u, unit(a, b), 4) or abs(perp(a, o, u)) > w.t / 2 + 150:
                            continue
                        s0, s1 = sorted((proj(a, o, u), proj(b, o, u)))
                        if min(s1, g1) - max(s0, g0) >= gap * 0.5:
                            ok = True; break
                if not ok:
                    for c, r in arcs:
                        if abs(perp(c, o, u)) <= w.t / 2 + 150 and g0 - 150 <= proj(c, o, u) <= g1 + 150 and r <= gap + 250:
                            ok = True; break
                if ok:
                    t0, t1 = min(0.0, ta), max(L, tb)
                    w.a, w.b = (o[0] + u[0] * t0, o[1] + u[1] * t0), (o[0] + u[0] * t1, o[1] + u[1] * t1)
                    w.q = w.q or q.q
                    walls.pop(j); changed = True; break
            if changed:
                break
    return walls

def extract_openings(walls, winsegs, arcs, log):
    windows = []; doors = []
    for wi, w in enumerate(walls):
        o, u, L = w.frame(); spans = []
        for a, b in winsegs:
            if not parallel(u, unit(a, b), 4) or abs(perp(a, o, u)) > w.t / 2 + 60:
                continue
            ta, tb = sorted((proj(a, o, u), proj(b, o, u)))
            if tb < -50 or ta > L + 50 or tb - ta < 300:
                continue
            spans.append([max(ta, 0.0), min(tb, L)])
        spans.sort(); ms = []
        for s in spans:
            if ms and s[0] <= ms[-1][1] + 120:
                ms[-1][1] = max(ms[-1][1], s[1])
            else:
                ms.append(s)
        for s in ms:
            if s[1] - s[0] >= 400:
                windows.append(dict(wall=wi, t0=s[0], t1=s[1]))
    for (c, r, a0, a1) in arcs:
        E = [(c[0] + r * math.cos(a0), c[1] + r * math.sin(a0)), (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1))]
        best = None
        for wi, w in enumerate(walls):
            o, u, L = w.frame(); nc = perp(c, o, u); tc = proj(c, o, u)
            if abs(nc) > w.t / 2 + 120 or tc < -150 or tc > L + 150:
                continue
            for k, e in enumerate(E):
                ue = unit(c, e)
                if abs(ue[0] * u[0] + ue[1] * u[1]) > 0.97:
                    other = E[1 - k]
                    side = (other[0] - c[0]) * (-ue[1]) + (other[1] - c[1]) * ue[0]
                    if best is None or abs(nc) < best[0]:
                        best = (abs(nc), wi, ue, side)
        if best is None:
            k = min((0, 1), key=lambda k: min(abs(abs(math.cos(a0 if k == 0 else a1)) - 1), abs(abs(math.sin(a0 if k == 0 else a1)) - 1)))
            ue = unit(c, E[k]); other = E[1 - k]
            side = (other[0] - c[0]) * (-ue[1]) + (other[1] - c[1]) * ue[0]
            doors.append(dict(wall=None, hinge=c, u=ue, r=r, flip=side < 0, q='drzwi bez rozpoznanych lic ściany (ściana jednoliniowa?) – przyjęto 100 mm, potwierdzić'))
            continue
        _, wi, ue, side = best
        doors.append(dict(wall=wi, hinge=c, u=ue, r=r, flip=side < 0))
    return windows, doors

def build_floor(name, F, log):
    geo = F['geo']
    wsegs = segs_of(geo, 'walls')
    winsegs = segs_of(geo, 'windows')
    arcs = [(tuple(d['c']), d['r'], d['a0'], d['a1']) for d in geo.get('doors', []) if d.get('k') == 'a' and 500 <= d.get('r', 0) <= 1500]
    rooms = [r['poly'] for r in F.get('rooms', []) if r.get('poly')]
    labels = [(r['lx'] + 300, r['ly'] + 60) for r in F.get('rooms', []) if r.get('lx') is not None]
    walls = extract_walls(wsegs, rooms, log, labels)
    walls = bridge_openings(walls, winsegs, [(c, r) for c, r, _, _ in arcs], log)
    walls = [w for w in walls if math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1]) >= 250]
    singles = []
    for a, b in wsegs:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 800:
            continue
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); covered = False
        for w in walls:
            o, u, WL = w.frame()
            if abs(perp(mid, o, u)) <= w.t / 2 + 60 and -60 <= proj(mid, o, u) <= WL + 60:
                covered = True; break
        if not covered:
            singles.append(Piece(a, b, 80, 'ściana narysowana jedną linią – przyjęto 80 mm, potwierdzić grubość'))
    walls += singles
    windows, doors = extract_openings(walls, winsegs, arcs, log)
    items = []
    for i, w in enumerate(walls):
        cls = 'N' if w.t >= 240 else 'D'
        it = {'id': f'inw-s-{name}-{i:03d}', 'type': 'wall', 'inv': cls, 'pts': [[R10(w.a[0]), R10(w.a[1])], [R10(w.b[0]), R10(w.b[1])]], 'w': R10(w.t)}
        if w.q: it['q'] = w.q
        items.append(it)
    for i, win in enumerate(windows):
        w = walls[win['wall']]; o, u, L = w.frame()
        a = (o[0] + u[0] * win['t0'], o[1] + u[1] * win['t0']); b = (o[0] + u[0] * win['t1'], o[1] + u[1] * win['t1'])
        items.append({'id': f'inw-o-{name}-{i:03d}', 'type': 'window', 'inv': True, 'pts': [[R10(a[0]), R10(a[1])], [R10(b[0]), R10(b[1])]], 'w': R10(w.t)})
    for i, d in enumerate(doors):
        if d['wall'] is None:
            a = d['hinge']; b = (a[0] + d['u'][0] * d['r'], a[1] + d['u'][1] * d['r'])
            items.append({'id': f'inw-d-{name}-{i:03d}', 'type': 'door', 'inv': True, 'pts': [[R10(a[0]), R10(a[1])], [R10(b[0]), R10(b[1])]], 'w': 140, 'flip': bool(d['flip']), 'q': d['q']})
            continue
        w = walls[d['wall']]; o, u, L = w.frame(); tc = proj(d['hinge'], o, u)
        a = (o[0] + u[0] * tc, o[1] + u[1] * tc)
        sgn = 1 if (d['u'][0] * u[0] + d['u'][1] * u[1]) > 0 else -1
        b = (a[0] + u[0] * sgn * d['r'], a[1] + u[1] * sgn * d['r'])
        items.append({'id': f'inw-d-{name}-{i:03d}', 'type': 'door', 'inv': True, 'pts': [[R10(a[0]), R10(a[1])], [R10(b[0]), R10(b[1])]], 'w': R10(w.t) + 40, 'flip': bool(d['flip'])})
    thick = defaultdict(float)
    for w in walls:
        thick[R10(w.t)] += math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1])
    log.append(f'{name}: ściany {len(walls)} (nośne {sum(1 for w in walls if w.t>=240)}, działowe {sum(1 for w in walls if w.t<240)}, jednoliniowe {len(singles)}), okna {len(windows)}, drzwi {len(doors)}/{len(arcs)} łuków (bez ściany {sum(1 for d in doors if d["wall"] is None)}); grubości [mm: m.b.] ' + ', '.join(f'{k}:{v/1000:.1f}' for k, v in sorted(thick.items())))
    return items

if __name__ == '__main__':
    model = json.load(open(sys.argv[1], encoding='utf-8'))
    out = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(out, exist_ok=True)
    log = []
    for name, F in model['floors'].items():
        items = build_floor(name, F, log)
        json.dump({'items': items}, open(os.path.join(out, f'items_inw_{name}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('\n'.join(log), file=sys.stderr)
