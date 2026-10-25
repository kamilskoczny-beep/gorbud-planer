"""Uzupełnia okna, które model inwentaryzacyjny pominął.

Bierze odcinki warstw okien i parapetów z podkładu, których nie pokrywa żadne `iwin`, grupuje je i tworzy:
  - okno w ścianie (iwin) – pary równoległych linii (szyba/parapety): zakres = suma odcinków, oś = ściana iwall,
    jeśli leży w jej pasie, inaczej środek pary (np. witryna w ściance działowej), w = rozstaw linii;
  - okno połaciowe (iroof) – zamknięty prostokąt z warstwy okien z przekątnymi (symbol okna dachowego).
Każde dodane okno ma `q` do potwierdzenia.
"""
import math

def _segs(geo, lay, minlen=300):
    out = []
    for s in geo.get(lay, []):
        if s.get('k') != 'l':
            continue
        p = s['p']
        for k in range(1, len(p)):
            a, b = p[k - 1], p[k]
            if math.hypot(b[0] - a[0], b[1] - a[1]) >= minlen:
                out.append((tuple(a), tuple(b), lay))
    return out

def _unit(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L), L

def add_missing(F, items, floor):
    wins = [i for i in items if i.get('type') == 'iwin']
    walls = [i for i in items if i.get('type') == 'iwall']
    def covered(p):
        for w in wins:
            u, L = _unit(*w['pts']); a = w['pts'][0]
            t = (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1]; n = abs(-(p[0] - a[0]) * u[1] + (p[1] - a[1]) * u[0])
            if -150 < t < L + 150 and n < w['w'] / 2 + 200:
                return True
        for r in [i for i in items if i.get('type') == 'iroof']:
            (x0, y0), (x1, y1) = r['pts']
            if min(x0, x1) - 100 <= p[0] <= max(x0, x1) + 100 and min(y0, y1) - 100 <= p[1] <= max(y0, y1) + 100:
                return True
        return False
    segs = [s for s in _segs(F['geo'], 'windows') + _segs(F['geo'], 'sills') if not covered(((s[0][0] + s[1][0]) / 2, (s[0][1] + s[1][1]) / 2))]
    R = lambda v: int(round(v / 10.0)) * 10
    added = []
    # 1) okna połaciowe: zamknięte prostokąty z przekątnymi na warstwie okien (grupy z odcinkami prostopadłymi)
    W = [s for s in segs if s[2] == 'windows']
    bb = [(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])) for a, b, _ in W]
    par = list(range(len(W)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(W)):
        for j in range(i + 1, len(W)):
            A, B = bb[i], bb[j]
            if A[0] - 30 <= B[2] and B[0] - 30 <= A[2] and A[1] - 30 <= B[3] and B[1] - 30 <= A[3]:
                par[f(i)] = f(j)
    used = set()
    groups = {}
    for i in range(len(W)):
        groups.setdefault(f(i), []).append(i)
    for g in groups.values():
        if len(g) < 4:
            continue
        angs = [math.degrees(math.atan2(W[i][1][1] - W[i][0][1], W[i][1][0] - W[i][0][0])) % 180 for i in g]
        nh = sum(1 for a in angs if a < 10 or a > 170); nv = sum(1 for a in angs if 80 < a < 100); nd = len(angs) - nh - nv
        if nh >= 2 and nv >= 2 and nd >= 1:
            xs = [p[0] for i in g for p in W[i][:2]]; ys = [p[1] for i in g for p in W[i][:2]]
            added.append({'id': f'inw-r-{floor}-{len(added):02d}', 'type': 'iroof', 'pts': [[R(min(xs)), R(min(ys))], [R(max(xs)), R(max(ys))]],
                          'q': f'okno połaciowe {R(max(xs)-min(xs))/10:.0f}×{R(max(ys)-min(ys))/10:.0f} cm (symbol z inwentaryzacji) – potwierdzić'})
            used.update(id(W[i]) for i in g)
    rest = [s for s in segs if id(s) not in used and math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]) >= 450]
    # 2) okna w ścianach: wiązki równoległych linii (szyba, parapety) w odległości ≤ 900 mm i z nakładem ≥ 50 %
    par = list(range(len(rest)))
    def f2(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    U = [_unit(a, b) for a, b, _ in rest]
    for i in range(len(rest)):
        (ui, Li) = U[i]; a = rest[i][0]
        for j in range(i + 1, len(rest)):
            (uj, Lj) = U[j]
            if abs(ui[0] * uj[1] - ui[1] * uj[0]) > 0.09:
                continue
            b0, b1 = rest[j][0], rest[j][1]
            n = abs(-(b0[0] - a[0]) * ui[1] + (b0[1] - a[1]) * ui[0])
            if n > 900:
                continue
            t0, t1 = sorted(((b0[0] - a[0]) * ui[0] + (b0[1] - a[1]) * ui[1], (b1[0] - a[0]) * ui[0] + (b1[1] - a[1]) * ui[1]))
            ov = min(Li, t1) - max(0, t0)
            if ov >= 0.5 * min(Li, Lj):
                par[f2(i)] = f2(j)
    groups = {}
    for i in range(len(rest)):
        groups.setdefault(f2(i), []).append(rest[i])
    for g in groups.values():
        if len(g) < 2:
            continue
        a0, b0, _ = max(g, key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
        u, _L = _unit(a0, b0); nl = (-u[1], u[0])
        ts = [(p[0] * u[0] + p[1] * u[1]) for a, b, _ in g for p in (a, b)]
        ns = [(p[0] * nl[0] + p[1] * nl[1]) for a, b, _ in g for p in (a, b)]
        t0, t1 = min(ts), max(ts)
        if t1 - t0 < 450:
            continue
        nc = (min(ns) + max(ns)) / 2; wth = max(120, min(900, max(ns) - min(ns)))
        host = None
        for w in walls:
            wu, WL = _unit(*w['pts'])
            if abs(wu[0] * u[1] - wu[1] * u[0]) > 0.1:
                continue
            a = w['pts'][0]; c = (u[0] * (t0 + t1) / 2 + nl[0] * nc, u[1] * (t0 + t1) / 2 + nl[1] * nc)
            n = abs(-(c[0] - a[0]) * wu[1] + (c[1] - a[1]) * wu[0]); t = (c[0] - a[0]) * wu[0] + (c[1] - a[1]) * wu[1]
            if n <= w['w'] / 2 + 150 and -300 < t < WL + 300:
                host = w; break
        if host:
            a = host['pts'][0]; nc = a[0] * nl[0] + a[1] * nl[1]; wth = host['w']
        p0 = (u[0] * t0 + nl[0] * nc, u[1] * t0 + nl[1] * nc); p1 = (u[0] * t1 + nl[0] * nc, u[1] * t1 + nl[1] * nc)
        has_sill = any(l == 'sills' for _, _, l in g)
        q = f'okno uzupełnione z podkładu, szer. {R(t1 - t0)/10:.0f} cm' + ('' if host else (' – witryna / przeszklenie w ściance działowej' if wth <= 150 else (' – w otworze ściany zewnętrznej (ściana w modelu przerwana)' if has_sill else ' – w ściance bez lic (witryna?)'))) + ' – potwierdzić'
        added.append({'id': f'inw-o2-{floor}-{len(added):02d}', 'type': 'iwin', 'pts': [[R(p0[0]), R(p0[1])], [R(p1[0]), R(p1[1])]], 'w': R(wth), 'q': q})
    return added
