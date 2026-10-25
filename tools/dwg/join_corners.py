"""Domyka narożniki i styki ścian modelu inwentaryzacyjnego (iwall).

Koniec ściany A, który leży blisko osi innej, nierównoległej ściany B, jest przenoszony na przecięcie osi
i przedłużany o pół grubości B (do zewnętrznego lica B) – narożnik L i styk T są wypełnione w całości.
Rysowanie: końce ścian bez czapek (butt). Użycie jako moduł: join(items) -> liczba zmienionych końców.
"""
import math

def _int(a, u, b, v):
    d = u[0] * v[1] - u[1] * v[0]
    if abs(d) < 1e-9:
        return None
    t = ((b[0] - a[0]) * v[1] - (b[1] - a[1]) * v[0]) / d
    return (a[0] + u[0] * t, a[1] + u[1] * t)

def join(items, tol=900):
    walls = [i for i in items if i.get('type') == 'iwall' and len(i.get('pts', [])) == 2]
    fr = []
    for w in walls:
        a, b = w['pts']; L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        fr.append((tuple(a), tuple(b), ((b[0] - a[0]) / L, (b[1] - a[1]) / L), L))
    changed = 0
    for i, w in enumerate(walls):
        a, b, u, L = fr[i]
        for end in (0, 1):
            E = a if end == 0 else b
            d_out = (-u[0], -u[1]) if end == 0 else u   # kierunek na zewnątrz od końca
            best = None
            for j, o in enumerate(walls):
                if j == i:
                    continue
                oa, ob, ov, oL = fr[j]
                if abs(u[0] * ov[1] - u[1] * ov[0]) < math.sin(math.radians(30)):
                    continue
                X = _int(E, u, oa, ov)
                if X is None:
                    continue
                dist = math.hypot(X[0] - E[0], X[1] - E[1])
                if dist > tol + o['w'] / 2:
                    continue
                to = (X[0] - oa[0]) * ov[0] + (X[1] - oa[1]) * ov[1]
                if to < -w['w'] - 600 or to > oL + w['w'] + 600:
                    continue
                # nie przedłużać „w głąb” ściany A przez całą jej długość: przecięcie musi być blisko końca
                s = (X[0] - E[0]) * d_out[0] + (X[1] - E[1]) * d_out[1]
                if s < -min(tol, L * 0.45):
                    continue
                if best is None or dist < best[0]:
                    best = (dist, X, o['w'])
            if best:
                _, X, ow = best
                # do zewnętrznego lica ściany B
                N = (X[0] + d_out[0] * ow / 2, X[1] + d_out[1] * ow / 2)
                newp = [int(round(N[0] / 10.0)) * 10, int(round(N[1] / 10.0)) * 10]
                if newp != list(w['pts'][end]):
                    w['pts'][end] = newp; changed += 1
    return changed
