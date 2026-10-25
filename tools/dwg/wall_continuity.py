"""Ciągłość ścian modelu inwentaryzacyjnego (zasada 37): każdy koniec ściany musi stykać się z inną ścianą
(albo z otworem – drzwi/okno – który leży w linii ściany). Wyjątek: filary (q zawiera „filar”).

fix(items, max_ext=2500) -> (zmienione, nierozwiązane)
  koniec bez styku → przedłużenie wzdłuż osi do pierwszej ściany na drodze (≤ max_ext):
  styk T – do osi ściany poprzecznej, narożnik L (koniec tamtej ściany blisko) – do jej zewnętrznego lica.
  Gdy po drodze jest otwór (drzwi/okno) – koniec zostaje (ściana kończy się na ościeżu).
"""
import math

def _seg_dist(p, a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)

def _ray_hit(E, d, a, b):
    """parametr s ≥ 0 przecięcia promienia E + s·d z odcinkiem a-b (lub None) oraz t na odcinku."""
    ex, ey = E; vx, vy = b[0] - a[0], b[1] - a[1]
    den = d[0] * vy - d[1] * vx
    if abs(den) < 1e-9:
        return None
    s = ((a[0] - ex) * vy - (a[1] - ey) * vx) / den
    t = ((a[0] - ex) * d[1] - (a[1] - ey) * d[0]) / den
    return (s, t)

def fix(items, max_ext=2500, tol=40):
    walls = [i for i in items if i.get('type') == 'iwall' and len(i.get('pts', [])) == 2]
    opens = [i for i in items if i.get('type') in ('idoor', 'iwin') and len(i.get('pts', [])) == 2]
    blocks = [i for i in items if i.get('type') in ('chimney', 'istair') and len(i.get('pts', [])) == 2]
    changed, unresolved = [], []
    def touching(w, E):
        for o in walls:
            if o is w: continue
            if _seg_dist(E, o['pts'][0], o['pts'][1]) <= o.get('w', 100) / 2 + tol:
                return True
        for o in opens:
            ow = (o.get('w', 300) - 40) if o['type'] == 'idoor' else o.get('w', 300)
            if _seg_dist(E, o['pts'][0], o['pts'][1]) <= max(ow, w.get('w', 100)) / 2 + 120:
                return True
        for o in blocks:  # koniec przy kominie / biegu schodów
            (x0, y0), (x1, y1) = o['pts']; m = w.get('w', 100) / 2 + 60
            if min(x0, x1) - m <= E[0] <= max(x0, x1) + m and min(y0, y1) - m <= E[1] <= max(y0, y1) + m:
                return True
        return False
    for w in walls:
        if 'filar' in (w.get('q') or ''):
            continue
        for end in (0, 1):
            a, b = w['pts']; E = w['pts'][end]; O = w['pts'][1 - end]
            L = math.hypot(E[0] - O[0], E[1] - O[1]) or 1
            d = ((E[0] - O[0]) / L, (E[1] - O[1]) / L)
            if touching(w, E):
                continue
            best = None
            for o in walls + opens:
                if o is w: continue
                oa, ob = o['pts']
                h = _ray_hit(E, d, oa, ob)
                if not h: continue
                s, t = h
                ow = o.get('w', 100) if o['type'] == 'iwall' else 300
                oL = math.hypot(ob[0] - oa[0], ob[1] - oa[1]) or 1
                if s < -10 or s > max_ext: continue
                if t < -(ow / 2 + 50) / oL or t > 1 + (ow / 2 + 50) / oL: continue
                if best is None or s < best[0]:
                    best = (s, o, t)
            if not best or best[1]['type'] != 'iwall':
                # druga próba: ściana poprzeczna jest za krótka – przedłuż obie do wspólnego narożnika (L)
                cand = None
                if not best:
                    for o in walls:
                        if o is w: continue
                        oa, ob = o['pts']; oL = math.hypot(ob[0] - oa[0], ob[1] - oa[1]) or 1
                        u = ((ob[0] - oa[0]) / oL, (ob[1] - oa[1]) / oL)
                        if abs(d[0] * u[1] - d[1] * u[0]) < 0.5: continue  # tylko poprzeczne
                        h = _ray_hit(E, d, oa, ob)
                        if not h: continue
                        s_, t_ = h
                        if s_ < -10 or s_ > max_ext: continue
                        gap = (-t_ if t_ < 0 else t_ - 1) * oL
                        if gap <= 0 or gap > max_ext: continue
                        if cand is None or s_ + gap < cand[0]:
                            cand = (s_ + gap, s_, o, 0 if t_ < 0 else 1)
                if cand:
                    _, s_, o, oend = cand
                    X = (E[0] + d[0] * s_, E[1] + d[1] * s_)
                    ow = o.get('w', 100); ww = w.get('w', 100)
                    oo = o['pts'][1 - oend]; od = (X[0] - oo[0], X[1] - oo[1]); odl = math.hypot(*od) or 1
                    w['pts'][end] = [int(round((X[0] + d[0] * ow / 2) / 10.0)) * 10, int(round((X[1] + d[1] * ow / 2) / 10.0)) * 10]
                    o['pts'][oend] = [int(round((X[0] + od[0] / odl * ww / 2) / 10.0)) * 10, int(round((X[1] + od[1] / odl * ww / 2) / 10.0)) * 10]
                    changed.append((w['id'], end, round(s_))); changed.append((o['id'], oend, -1))
                    continue
                unresolved.append((w['id'], end, E))
                continue
            s, o, t = best; ow = o.get('w', 100); oL = math.hypot(o['pts'][1][0] - o['pts'][0][0], o['pts'][1][1] - o['pts'][0][1]) or 1
            near_end = min(abs(t), abs(1 - t)) * oL < ow
            s2 = s + (ow / 2 if near_end else 0)
            N = [int(round((E[0] + d[0] * s2) / 10.0)) * 10, int(round((E[1] + d[1] * s2) / 10.0)) * 10]
            if N != list(E):
                w['pts'][end] = N; changed.append((w['id'], end, round(s2)))
    return changed, unresolved
