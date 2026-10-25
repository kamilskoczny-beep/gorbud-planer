"""Analiza konstrukcyjna modelu inwentaryzacyjnego (zasady 40–42): ściany nośne biegną w liniach, łączą się w narożnikach
i niosą stropy; inwentaryzacja ma błędy pomiaru (± kilka cm, tynki) – kawałki jednej ściany prostujemy na wspólną oś.
Przerwa w linii ściany nośnej bez otworu = podciąg. Ściana nośna wyżej bez ściany pod spodem = podciąg na kondygnacji niżej.

lines(walls)                       -> grupy współliniowych ścian nośnych [{u, n0, segs:[(t0,t1,w)], walls}]
straighten(items, max_off=150)     -> lista zmian (ściany nośne jednej linii na wspólnej osi)
gap_beams(items, floor)            -> nowe elementy 'beam' w przerwach linii ścian nośnych
support_beams(upper, lower, du, dl, floor) -> 'beam' pod nośnymi ścianami kondygnacji wyżej bez podparcia
Element: {"type":"beam","pts":[a,b],"w":szer.,"src":"gap"|"support","q":...}
"""
import math

R10 = lambda v: int(round(v / 10.0)) * 10

def _frame(w):
    (ax, ay), (bx, by) = w['pts']; L = math.hypot(bx - ax, by - ay) or 1
    return (ax, ay), ((bx - ax) / L, (by - ay) / L), L

def _canon(u):
    # kierunek kanoniczny (kąt w [0,180))
    if u[0] < -1e-9 or (abs(u[0]) < 1e-9 and u[1] < 0):
        return (-u[0], -u[1])
    return u

def lines(walls, ang_tol=0.05, off_tol=150, gap_max=7500):
    N = [w for w in walls if w.get('type') == 'iwall' and w.get('inv') != 'D' and 'filar' not in (w.get('q') or '')]
    groups = []
    for w in N:
        a, u, L = _frame(w); u = _canon(u)
        n = (-u[1], u[0]); off = a[0] * n[0] + a[1] * n[1]
        t0 = a[0] * u[0] + a[1] * u[1]; t1 = t0 + L * (1 if _canon(_frame(w)[1]) == _frame(w)[1] else -1)
        t0, t1 = min(t0, t1), max(t0, t1)
        placed = False
        for G in groups:
            if abs(G['u'][0] * u[1] - G['u'][1] * u[0]) > ang_tol: continue
            gn = (-G['u'][1], G['u'][0])
            # odległość osi liczona w środku odcinka
            mx, my = a[0] + _frame(w)[1][0] * L / 2, a[1] + _frame(w)[1][1] * L / 2
            if abs(mx * gn[0] + my * gn[1] - G['off']) > off_tol: continue
            tt0 = mx * G['u'][0] + my * G['u'][1] - L / 2; tt1 = tt0 + L
            if tt0 > G['t1'] + gap_max or tt1 < G['t0'] - gap_max: continue
            G['walls'].append(w); G['segs'].append((tt0, tt1, w.get('w', 300), w['id']))
            G['t0'] = min(G['t0'], tt0); G['t1'] = max(G['t1'], tt1)
            Ls = sum(s[1] - s[0] for s in G['segs'])
            G['off'] = sum((s[1] - s[0]) * _off_of(x, gn) for s, x in zip(G['segs'], G['walls'])) / Ls
            placed = True; break
        if not placed:
            groups.append({'u': u, 'off': off, 't0': t0, 't1': t1, 'segs': [(t0, t1, w.get('w', 300), w['id'])], 'walls': [w]})
    return groups

def _off_of(w, n):
    (ax, ay), (bx, by) = w['pts']
    return ((ax + bx) / 2) * n[0] + ((ay + by) / 2) * n[1]

def straighten(items, max_off=150):
    walls = [i for i in items if i.get('type') == 'iwall']
    ch = []
    for G in lines(walls, off_tol=max_off):
        if len(G['walls']) < 2: continue
        n = (-G['u'][1], G['u'][0])
        for w in G['walls']:
            d = G['off'] - _off_of(w, n)
            if abs(d) < 15 or abs(d) > max_off: continue
            w['pts'] = [[R10(p[0] + n[0] * d), R10(p[1] + n[1] * d)] for p in w['pts']]
            ch.append((w['id'], round(d)))
    return ch

def _covered(t0, t1, ivals):
    """odcinki [t0,t1] nie pokryte przedziałami ivals"""
    free = [(t0, t1)]
    for a, b in sorted(ivals):
        nf = []
        for x, y in free:
            if b <= x or a >= y: nf.append((x, y)); continue
            if a > x: nf.append((x, a))
            if b < y: nf.append((b, y))
        free = nf
    return free

def gap_beams(items, floor, min_gap=250, max_gap=7500):
    walls = [i for i in items if i.get('type') == 'iwall']
    out = []
    for G in lines(walls):
        if len(G['segs']) < 2: continue
        u = G['u']; n = (-u[1], u[0]); segs = sorted(G['segs'])
        wmean = sorted(s[2] for s in segs)[len(segs) // 2]
        for k in range(len(segs) - 1):
            g0 = max(s[1] for s in segs[:k + 1]); g1 = segs[k + 1][0]
            if g1 - g0 < min_gap or g1 - g0 > max_gap: continue
            # co zajmuje przerwę: ściany poprzeczne, otwory, kominy, schody
            iv = []
            for o in items:
                if o.get('type') not in ('iwall', 'idoor', 'iwin', 'chimney', 'istair') or len(o.get('pts', [])) != 2: continue
                if o.get('type') == 'iwall' and o['id'] in [s[3] for s in segs]: continue
                (ax, ay), (bx, by) = o['pts']
                if o['type'] in ('chimney', 'istair'):
                    xs = sorted([ax, bx]); ys = sorted([ay, by]); pts = [(xs[0], ys[0]), (xs[1], ys[0]), (xs[0], ys[1]), (xs[1], ys[1])]
                    offs = [p[0] * n[0] + p[1] * n[1] for p in pts]
                    if min(offs) > G['off'] + wmean / 2 or max(offs) < G['off'] - wmean / 2: continue
                    ts = [p[0] * u[0] + p[1] * u[1] for p in pts]; iv.append((min(ts), max(ts))); continue
                ow = o.get('w', 300) if o['type'] != 'idoor' else max(o.get('w', 300) - 40, 100)
                oL = math.hypot(bx - ax, by - ay) or 1; ou = ((bx - ax) / oL, (by - ay) / oL)
                para = abs(ou[0] * u[1] - ou[1] * u[0]) < 0.2
                if para:
                    oo = ((ax + bx) / 2) * n[0] + ((ay + by) / 2) * n[1]
                    if abs(oo - G['off']) > (wmean + ow) / 2: continue
                    ta, tb = ax * u[0] + ay * u[1], bx * u[0] + by * u[1]; iv.append((min(ta, tb), max(ta, tb)))
                elif o['type'] == 'iwall':
                    # ściana poprzeczna przechodzi przez linię?
                    oa, ob = ax * n[0] + ay * n[1], bx * n[0] + by * n[1]
                    if min(oa, ob) - ow / 2 > G['off'] + wmean / 2 or max(oa, ob) + ow / 2 < G['off'] - wmean / 2: continue
                    # punkt przecięcia osi
                    den = ou[0] * n[0] + ou[1] * n[1]
                    if abs(den) < 1e-6: continue
                    s = (G['off'] - (ax * n[0] + ay * n[1])) / den
                    X = (ax + ou[0] * s, ay + ou[1] * s); tx = X[0] * u[0] + X[1] * u[1]
                    sin = abs(ou[0] * u[1] - ou[1] * u[0]) or 1
                    iv.append((tx - ow / 2 / sin, tx + ow / 2 / sin))
            for f0, f1 in _covered(g0, g1, iv):
                if f1 - f0 < min_gap: continue
                A = (u[0] * f0 + n[0] * G['off'], u[1] * f0 + n[1] * G['off']); B = (u[0] * f1 + n[0] * G['off'], u[1] * f1 + n[1] * G['off'])
                out.append({'id': f'bm-{floor}-g{len(out):02d}', 'type': 'beam', 'src': 'gap', 'w': R10(wmean),
                            'pts': [[R10(A[0]), R10(A[1])], [R10(B[0]), R10(B[1])]],
                            'q': f'przerwa {round((f1 - f0) / 10)} cm w linii ściany nośnej (bez drzwi/okna) – strop musi być tu podparty: podciąg (wg mnie istniejący). Potwierdź albo napisz, co tu jest.'})
    return out

def support_beams(upper, lower, du, dl, floor, min_len=600, off_tol=350):
    """du, dl – przesunięcia lokal→wspólny (align) kondygnacji wyżej i niżej. Zwraca belki w układzie kondygnacji niżej."""
    UP = [w for w in upper if w.get('type') == 'iwall' and w.get('inv') != 'D' and w.get('w', 0) >= 240]
    LO = [w for w in lower if (w.get('type') == 'iwall' and w.get('inv') != 'D') or w.get('type') == 'beam']
    LOO = [w for w in lower if w.get('type') in ('idoor', 'iwin', 'chimney', 'istair')]
    out = []
    for w in UP:
        a = (w['pts'][0][0] + du[0] - dl[0], w['pts'][0][1] + du[1] - dl[1]); b = (w['pts'][1][0] + du[0] - dl[0], w['pts'][1][1] + du[1] - dl[1])
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1; u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L); n = (-u[1], u[0])
        off = a[0] * n[0] + a[1] * n[1]; t0 = a[0] * u[0] + a[1] * u[1]; t1 = t0 + L
        iv = []
        for o in LO + LOO:
            (ax, ay), (bx, by) = o['pts']
            if o['type'] in ('chimney', 'istair'):
                continue
            oL = math.hypot(bx - ax, by - ay) or 1; ou = ((bx - ax) / oL, (by - ay) / oL)
            if abs(ou[0] * u[1] - ou[1] * u[0]) > 0.1: continue
            oo = ((ax + bx) / 2) * n[0] + ((ay + by) / 2) * n[1]
            if abs(oo - off) > off_tol: continue
            ta, tb = ax * u[0] + ay * u[1], bx * u[0] + by * u[1]; iv.append((min(ta, tb) - 150, max(ta, tb) + 150))
        # ściany poprzeczne niżej też podpierają (na szerokość swojej grubości) – pomijamy, bo podparcie punktowe
        for f0, f1 in _covered(t0, t1, iv):
            if f1 - f0 < min_len: continue
            A = (u[0] * f0 + n[0] * off, u[1] * f0 + n[1] * off); B = (u[0] * f1 + n[0] * off, u[1] * f1 + n[1] * off)
            out.append({'id': f'bm-{floor}-s{len(out):02d}', 'type': 'beam', 'src': 'support', 'w': R10(w.get('w', 300)), 'above': w['id'],
                        'pts': [[R10(A[0]), R10(A[1])], [R10(B[0]), R10(B[1])]],
                        'q': f'nad tym miejscem stoi ściana nośna kondygnacji wyżej ({round(w.get("w", 0) / 10)} cm), a tu nie ma pod nią ściany na długości {round((f1 - f0) / 10)} cm – musi być podciąg (albo ściana, której brak w inwentaryzacji). Potwierdź albo napisz, co jest.'})
    return out

def _pip(p, poly):
    x, y = p; ins = False; j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi: ins = not ins
        j = i
    return ins

def check_doors(items, rooms, footprint=None, snap=220):
    """Drzwi muszą prowadzić z jednego pomieszczenia do drugiego (albo na zewnątrz).
    rooms – [{nr, poly}] z inwentaryzacji; footprint – shapely Polygon obrysu (opcjonalnie).
    Zwraca (poprawione, pytania): drzwi przesunięte na oś ściany (≤ snap mm), drzwi bez sensu → q."""
    from shapely.geometry import Point
    walls = [w for w in items if w.get('type') in ('iwall', 'wall')]
    fixed, asked = [], []
    def where(p):
        for w in walls:
            (ax, ay), (bx, by) = w['pts']; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy or 1
            t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
            if math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy) < w.get('w', 100) / 2 - 20: return 'ściana'
        for r in rooms:
            if r.get('poly') and _pip(p, r['poly']): return r['nr']
        if footprint is not None and not footprint.contains(Point(p)): return 'zewnątrz'
        return '?'
    for d in items:
        if d.get('type') != 'idoor' or len(d.get('pts', [])) != 2: continue  # drzwi projektowe to decyzja projektanta
        (ax, ay), (bx, by) = d['pts']; L = math.hypot(bx - ax, by - ay) or 1; u = ((bx - ax) / L, (by - ay) / L); n = (-u[1], u[0])
        m = ((ax + bx) / 2, (ay + by) / 2)
        # najbliższa ściana równoległa (oś)
        best = None
        for w in walls:
            (wa, wb) = w['pts']; wL = math.hypot(wb[0] - wa[0], wb[1] - wa[1]) or 1; wu = ((wb[0] - wa[0]) / wL, (wb[1] - wa[1]) / wL)
            if abs(wu[0] * u[1] - wu[1] * u[0]) > 0.15: continue
            wn = (-wu[1], wu[0]); off = (m[0] - wa[0]) * wn[0] + (m[1] - wa[1]) * wn[1]
            t = (m[0] - wa[0]) * wu[0] + (m[1] - wa[1]) * wu[1]
            if t < -L or t > wL + L: continue
            if best is None or abs(off) < abs(best[0]): best = (off, w, wn)
        wt = max((d.get('w', 300) - 40), 100) if d['type'] == 'idoor' else 300
        if best: snap_w = max(snap, best[1].get('w', 100) / 2 + 40)
        if best and 25 < abs(best[0]) <= snap_w and d['type'] == 'idoor':
            off, w, wn = best
            d['pts'] = [[R10(p[0] - wn[0] * off), R10(p[1] - wn[1] * off)] for p in d['pts']]
            fixed.append((d['id'], round(off))); (ax, ay), (bx, by) = d['pts']; m = ((ax + bx) / 2, (ay + by) / 2)
        if not best or abs(best[0]) > max(snap, best[1].get('w', 100) / 2 + 40):
            msg = 'drzwi nie stoją w żadnej ścianie – gdzie mają być? (popraw albo usuń)'
            asked.append((d['id'], msg)); d.setdefault('q', msg); continue
        wt = max(best[1].get('w', 100), 100)
        s1 = where((m[0] + n[0] * (wt / 2 + 300), m[1] + n[1] * (wt / 2 + 300)))
        s2 = where((m[0] - n[0] * (wt / 2 + 300), m[1] - n[1] * (wt / 2 + 300)))
        bad = None
        if 'ściana' in (s1, s2): bad = f'drzwi prowadzą w ścianę (po jednej stronie mur) – strony: {s1} / {s2}'
        elif s1 == s2 and s1 not in ('?',): bad = f'po obu stronach drzwi to samo pomieszczenie ({s1}) – drzwi do nikąd?'
        if bad:
            msg = bad + ' – popraw położenie albo usuń; potwierdź, jeśli tak ma być.'
            if d['type'] == 'idoor': d['q'] = (d['q'] + ' · ' if d.get('q') and msg not in d['q'] else '') + msg if msg not in (d.get('q') or '') else d['q']
            asked.append((d['id'], msg))
    return fixed, asked

def fix_short_fat(items, maxL=750):
    """„Ściany” krótsze niż grube (w ≥ 1,1·L) to błąd rozpoznania: para lic ościeży otworu albo filarek między oknami
    odczytany w poprzek. Obracamy: oś wzdłuż linii ściany, długość = w, grubość = L. Jeśli w tym miejscu są drzwi/okno –
    to sam otwór (ościeża) → usuwamy fałszywą ścianę."""
    opens = [o for o in items if o.get('type') in ('idoor', 'iwin', 'door') and len(o.get('pts', [])) == 2]
    out, rot, rem = [], [], []
    for w in items:
        if w.get('type') != 'iwall' or len(w.get('pts', [])) != 2:
            out.append(w); continue
        (ax, ay), (bx, by) = w['pts']; L = math.hypot(bx - ax, by - ay) or 1
        if not (w.get('w', 0) >= 1.1 * L and L <= maxL) or 'filar' in (w.get('q') or ''):
            out.append(w); continue
        c = ((ax + bx) / 2, (ay + by) / 2); u = ((bx - ax) / L, (by - ay) / L); v = (-u[1], u[0]); H = w['w'] / 2
        A = (c[0] - v[0] * H, c[1] - v[1] * H); B = (c[0] + v[0] * H, c[1] + v[1] * H)
        hit = False
        for o in opens:
            (oa, ob) = o['pts']; oL = math.hypot(ob[0] - oa[0], ob[1] - oa[1]) or 1; ou = ((ob[0] - oa[0]) / oL, (ob[1] - oa[1]) / oL)
            if abs(ou[0] * v[1] - ou[1] * v[0]) > 0.2: continue
            om = ((oa[0] + ob[0]) / 2, (oa[1] + ob[1]) / 2)
            if abs((om[0] - c[0]) * u[0] + (om[1] - c[1]) * u[1]) > L: continue
            t0, t1 = sorted([(oa[0] - c[0]) * v[0] + (oa[1] - c[1]) * v[1], (ob[0] - c[0]) * v[0] + (ob[1] - c[1]) * v[1]])
            if min(t1, H) - max(t0, -H) > 0.5 * min(2 * H, t1 - t0): hit = True; break
        if hit:
            rem.append(w['id']); continue
        w['pts'] = [[R10(A[0]), R10(A[1])], [R10(B[0]), R10(B[1])]]; w['w'] = R10(L)
        rot.append(w['id']); out.append(w)
    items[:] = out
    return rot, rem
