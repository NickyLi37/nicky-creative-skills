"""Georeference the traced Pingjiang lines (stele px) onto the local metre frame with a
least-squares affine through hand-picked control points (the stele is schematic, so a TPS
bends its straight lines into nonsense), flag which canals still match today's water,
then export renderer layers.

Usage: pj_georef.py <lines.json> <water.json> <out_layer.json> <check.png>
Control points: stele px (read off gridded crops of the Siyuwj photo) -> local metres (OSM).
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# name: (stele_x, stele_y, local_x, local_y)
CONTROL = {
    "齐门": (2540, 2085, -143, 2052),
    "娄门": (3105, 2520, 1167, 1806),
    "葑门": (3105, 4880, 1560, -1000),
    "盘门": (1420, 5420, -1052, -2378),
    "阊门": (1110, 2700, -2056, 700),
    "东北角": (3100, 2085, 1090, 2340),
    "东南角": (3105, 5320, 1640, -1960),
    "西北角": (1120, 2085, -2040, 1940),
    "西南角": (1100, 5400, -1250, -2350),
    # interior: canals still running today, matched by eye on the OSM water render
    "北横河西端": (1150, 2500, -2000, 1020),
    "北横河×临顿河": (2540, 2500, 0, 1450),
    "干将河西端": (1370, 3570, -1460, -440),
    "干将河×临顿河": (2540, 3570, 520, 20),
    "干将河东端": (2970, 3570, 1180, 260),
    "子城中心": (2275, 4073, 420, -690),
}
# city wall centre line on the stele (closed), px
WALL = [(1130, 2250), (1290, 2085), (2960, 2085), (3100, 2230), (3105, 5250), (3060, 5330),
        (1300, 5420), (1250, 5420), (1090, 5180), (1130, 2250)]


def _basis(P, order):
    P = np.asarray(P, float)
    x, y = (P[:, 0] - 2100) / 1000, (P[:, 1] - 3750) / 1000          # centred stele px (k)
    cols = [np.ones(len(P)), x, y]
    if order >= 2:
        cols += [x * x, x * y, y * y]
    return np.stack(cols, 1)


def fit_affine(names=None, order=1, ridge=0.0):
    """order 1 = affine; order 2 = gentle quadratic warp (keeps lines smooth). ridge damps the
    quadratic terms so the stele grid is not bent more than the control points demand."""
    names = names or list(CONTROL)
    src = _basis([[CONTROL[n][0], CONTROL[n][1]] for n in names], order)
    dst = np.array([[CONTROL[n][2], CONTROL[n][3]] for n in names])
    reg = np.diag([0, 0, 0] + [ridge] * (src.shape[1] - 3))
    M = np.linalg.solve(src.T @ src + reg, src.T @ dst)
    lin = M[:3].copy()
    lin[1:] /= 1000.0
    return (lambda P: _basis(P, order) @ M), lin


def densify(p0, p1, step=12):
    n = max(2, int(np.hypot(p1[0] - p0[0], p1[1] - p0[1]) / step) + 1)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) * np.array(p0, float) + t * np.array(p1, float)


def main():
    lines = json.load(open(sys.argv[1]))
    order = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    ridge = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
    tps, M = fit_affine(order=order, ridge=ridge)
    a, b, c, d = M[1, 0], M[1, 1], M[2, 0], M[2, 1]
    print("affine: rotation of stele x-axis %.1f deg, scale %.3f m/px x, %.3f m/px y"
          % (np.degrees(np.arctan2(b, a)), np.hypot(a, b), np.hypot(c, d)))
    out = {"canals": [], "streets": [], "wall": None, "control": {}}
    for key, kind, horiz in (("canal_h", "canals", True), ("canal_v", "canals", False),
                             ("street_h", "streets", True), ("street_v", "streets", False)):
        for o, a, b in lines[key]:
            p0, p1 = ((a, o), (b, o)) if horiz else ((o, a), (o, b))
            pts = tps(densify(p0, p1))
            spx = densify(p0, p1)
            out[kind].append({"axis": "h" if horiz else "v", "len_px": int(abs(b - a)),
                              "pts": [[round(x, 1), round(y, 1)] for x, y in pts],
                              "spx": [[round(x), round(y)] for x, y in spx]})
    wall = np.vstack([densify(WALL[i], WALL[i + 1]) for i in range(len(WALL) - 1)])
    out["wall"] = [[round(x, 1), round(y, 1)] for x, y in tps(wall)]
    out["wall_spx"] = [[round(x), round(y)] for x, y in wall]
    out["affine"] = M.tolist()
    for k, v in CONTROL.items():
        out["control"][k] = {"stele": [v[0], v[1]], "local": [v[2], v[3]]}
    # residuals so the report can say how schematic the stele is
    res = {}
    for n, v in CONTROL.items():
        px = tps([[v[0], v[1]]])[0]
        res[n] = round(float(np.hypot(px[0] - v[2], px[1] - v[3])))
    out["residual_m"] = res
    # which stele canals still coincide with a canal today (mean distance to today's water)
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    W = json.load(open(sys.argv[2]))
    today = unary_union([LineString(l["pts"]) for l in W["lines"] if len(l["pts"]) > 1] +
                        [Polygon(a["rings"][0]).exterior for a in W["areas"] if len(a["rings"][0]) > 3])
    for c in out["canals"]:
        pts = c["pts"]
        dist = [today.distance(__import__("shapely").geometry.Point(p)) for p in pts]
        c["d_today"] = round(float(np.mean(dist)), 1)
        c["match"] = bool(np.mean(np.array(dist) < 70) > 0.6)
    n_match = sum(c["match"] for c in out["canals"])
    L_all = sum(LineString(c["pts"]).length for c in out["canals"])
    L_match = sum(LineString(c["pts"]).length for c in out["canals"] if c["match"])
    out["match_stats"] = {"canals": len(out["canals"]), "matched": n_match,
                          "len_km": round(L_all / 1000, 2), "matched_len_km": round(L_match / 1000, 2)}
    json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False)
    print("canals", len(out["canals"]), "streets", len(out["streets"]), "residual m:", out["residual_m"])
    print("match:", out["match_stats"])

    # overlay check against real water
    X0, X1, Y0, Y1, s = -2600, 2200, -2800, 2700, 0.28
    im = Image.new("RGB", (int((X1 - X0) * s), int((Y1 - Y0) * s)), (16, 16, 20))
    d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - X0) * s, (Y1 - y) * s)
    for a in W["areas"]:
        d.polygon([P(*p) for p in a["rings"][0]], fill=(30, 90, 130))
    for l in W["lines"]:
        d.line([P(*p) for p in l["pts"]], fill=(70, 160, 210), width=3)
    for c in out["streets"]:
        d.line([P(*p) for p in c["pts"]], fill=(230, 180, 70), width=1)
    for c in out["canals"]:
        d.line([P(*p) for p in c["pts"]], fill=(120, 255, 140) if c["match"] else (255, 255, 255), width=2 if c["match"] else 1)
    d.line([P(*p) for p in out["wall"]], fill=(255, 90, 90), width=2)
    f = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 14)
    for k, v in CONTROL.items():
        x, y = P(v[2], v[3]); d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(255, 255, 0)); d.text((x + 5, y - 8), k, fill=(255, 255, 0), font=f)
    im.save(sys.argv[4])


if __name__ == "__main__":
    main()
