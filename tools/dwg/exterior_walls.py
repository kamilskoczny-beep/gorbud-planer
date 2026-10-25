"""Ściany na obrysie budynku = zawsze nośne (zasada 32) + kontrola grubości ścian (pytania `q`).

exterior(items) -> zbiór id ścian zewnętrznych (iwall, których jedno lico wychodzi poza obrys budynku).
Obrys budynku = suma wszystkich ścian (iwall) zamknięta (buffer ±400 mm) z wypełnionymi otworami (dziedzińce/pomieszczenia).
"""
import math
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import unary_union

def footprint(walls):
    U = unary_union([LineString(w['pts']).buffer(max(w.get('w', 100), 60) / 2, cap_style=2, join_style=2) for w in walls])
    U = U.buffer(400, join_style=2).buffer(-400, join_style=2)
    geoms = list(U.geoms) if isinstance(U, MultiPolygon) else [U]
    big = max(geoms, key=lambda g: g.area)
    return Polygon(big.exterior)

def footprint_dwg(geo, close=1300):
    """Obrys z podkładu DWG kondygnacji: lica ścian + okna/parapety (mostkują otwory), domknięcie ±close mm."""
    lines = []
    for g in ('walls', 'windows', 'sills', 'doors'):
        for s in geo.get(g, []):
            if s.get('k') == 'l' and len(s['p']) >= 2:
                lines.append(LineString(s['p']).buffer(60))
    U = unary_union(lines).buffer(close, join_style=2).buffer(-close, join_style=2)
    geoms = list(U.geoms) if isinstance(U, MultiPolygon) else [U]
    big = max(geoms, key=lambda g: g.area)
    return Polygon(big.exterior)

def exterior(items, margin=250, geo=None):
    walls = [i for i in items if i.get('type') == 'iwall' and len(i.get('pts', [])) == 2]
    if not walls:
        return set(), None
    F = footprint_dwg(geo) if geo else footprint(walls)
    out = set()
    for w in walls:
        (ax, ay), (bx, by) = w['pts']; L = math.hypot(bx - ax, by - ay)
        if L < 300:
            continue
        ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = -uy, ux; off = w.get('w', 100) / 2 + margin
        n = max(3, int(L / 400)); hit = [0, 0]
        for k in range(1, n):
            t = L * k / n; px, py = ax + ux * t, ay + uy * t
            for s, sg in enumerate((1, -1)):
                if not F.contains(Point(px + sg * nx * off, py + sg * ny * off)):
                    hit[s] += 1
        if max(hit) >= 0.6 * (n - 1):
            out.add(w['id'])
    return out, F
