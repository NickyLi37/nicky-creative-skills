"""Thematic layers for the chapters that are not the Pingjiang Map.

Usage: python prep/film_layers.py <layers_dir> <raw_osm_dir>
Writes:
  film.json  — moat/wall rings, gates, bridges, Shantang, painting route, gardens, towers, field header
  field.bin  — Float32 RGBA grid (row-major, y up from y0):
               R geodesic distance through water from the Grand Canal's NW entry (m)
               G distance to the moat centreline (m)
               B Shantang fire corridor parameter 0..1, -1 outside
               A water mask (1 = water)
"""
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge, substring

sys.path.insert(0, str(Path(__file__).parent))
from common import to_local  # noqa: E402

EXTENT = dict(x0=-12200, x1=20200, y0=-8420, y1=12660)
CELL = 25.0

# historic land gates (吴越春秋: 阊 胥 盘 蛇 娄 匠 齐 平); positions are today's gates, 蛇门 at 人民路 south — 示意
LAND_GATES = [
    ("阊门", -2056, 700), ("胥门", -1735, -1190), ("盘门", -1110, -2420), ("蛇门", -190, -2290),
    ("匠门", 1076, 94), ("娄门", 1167, 1806), ("齐门", -139, 2050), ("平门", -890, 1760),
]
CHANG, HUQIU, PAN = (-2056, 700), (-4439, 2993), (-1110, -2420)
GARDENS = ["拙政园", "留园", "网师园", "环秀山庄", "沧浪亭", "狮子林", "艺圃", "耦园"]


def ring_from_moat(water):
    parts = [LineString(l["pts"]) for l in water["lines"] if l["moat"]]
    merged = linemerge(parts)
    if merged.geom_type == "MultiLineString":
        coords = []
        for g in merged.geoms:
            coords.extend(g.coords)
    else:
        coords = list(merged.coords)
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return Polygon(coords)


def nearest_on(line, x, y):
    return line.project(Point(x, y))


def main():
    layers, raw = Path(sys.argv[1]), Path(sys.argv[2])
    water = json.loads((layers / "water.json").read_text())
    bridges = json.loads((layers / "bridges.json").read_text())
    out = {}

    # ---- moat ring and wall ring (wall sits just inside the moat)
    moat = ring_from_moat(water)
    moat_line = moat.exterior
    wall_poly = moat.buffer(-48, join_style=2).simplify(4)
    if wall_poly.geom_type == "MultiPolygon":
        wall_poly = max(wall_poly.geoms, key=lambda g: g.area)
    wall = wall_poly.exterior
    # start the ring at 阊门 so "u" runs clockwise from the west gate
    s0 = wall.project(Point(*CHANG))
    L = wall.length
    ring = [wall.interpolate((s0 + d) % L) for d in np.arange(0, L, 20.0)]
    ring_xy = [(round(p.x, 1), round(p.y, 1)) for p in ring]
    cw = json.loads((raw / "citywall.json").read_text())
    survive = []
    for e in cw["elements"]:
        g = e.get("geometry")
        if g:
            survive.append([[round(v, 1) for v in to_local(p["lon"], p["lat"])] for p in g])
    surv_union = shapely.union_all([LineString(s).buffer(70) for s in survive])
    keep = [1 if surv_union.contains(Point(p)) else 0 for p in ring_xy]
    out["moat"] = [[round(x, 1), round(y, 1)] for x, y in moat_line.coords]
    out["wall"] = {"pts": ring_xy, "keep": keep, "length_m": round(L), "survive": survive,
                   "survive_m": round(sum(LineString(s).length for s in survive))}
    out["old_city_km2"] = round(moat.area / 1e6, 2)

    # ---- gates: land gate on the wall ring, water gate 150 m clockwise along it
    gates = []
    for name, x, y in LAND_GATES:
        s = wall.project(Point(x, y))
        p = wall.interpolate(s)
        q = wall.interpolate((s + 150) % L)
        gates.append({"name": name, "land": [round(p.x, 1), round(p.y, 1)], "water": [round(q.x, 1), round(q.y, 1)]})
    out["gates"] = gates

    # ---- Shantang canal, oriented from 阊门 to 虎丘
    st = [l for l in water["lines"] if l["name"] == "山塘河"][0]["pts"]
    if math.dist(st[0], CHANG) > math.dist(st[-1], CHANG):
        st = st[::-1]
    shantang = LineString(st)
    out["shantang"] = [[round(x, 1), round(y, 1)] for x, y in st]

    # ---- 姑苏繁华图 route (示意): 盘门 -> west moat -> 阊门 -> 山塘 -> 虎丘
    sp, sc = moat_line.project(Point(*PAN)), moat_line.project(Point(*CHANG))
    a = substring(moat_line, sp, sc)
    b = substring(moat_line, sc, sp)
    xu = (-1735, -1190)  # pick the half that passes 胥门
    west = a if a.distance(Point(xu)) < b.distance(Point(xu)) else LineString(list(b.coords)[::-1])
    wc = list(west.coords)
    if math.dist(wc[0], PAN) > math.dist(wc[-1], PAN):
        wc = wc[::-1]
    route = LineString(wc + st).simplify(6)
    out["route"] = [[round(x, 1), round(y, 1)] for x, y in route.coords]

    # ---- bridges: old city (+ moat) and the Shantang corridor
    zone = moat.buffer(120)
    st_zone = shantang.buffer(160)
    sel = []
    for b_ in bridges:
        p = Point(b_["x"], b_["y"])
        if (zone.contains(p) or st_zone.contains(p)) and b_["len"] < 160:
            sel.append([round(b_["x"], 1), round(b_["y"], 1), round(b_["dx"], 1), round(b_["dy"], 1), round(b_["len"], 1)])
    out["bridges"] = sel

    # ---- gardens (OSM polygons)
    her = json.loads((raw / "heritage.json").read_text())
    gardens = []
    for e in her["elements"]:
        n = e.get("tags", {}).get("name", "")
        if e["type"] == "way" and n in GARDENS and e.get("geometry"):
            pts = [[round(v, 1) for v in to_local(p["lon"], p["lat"])] for p in e["geometry"]]
            c = Polygon(pts).centroid
            gardens.append({"name": n, "pts": pts, "c": [round(c.x), round(c.y)], "area": round(Polygon(pts).area)})
    out["gardens"] = gardens

    # ---- towers: OSM buildings with an explicit height (CMAB compresses supertall heights)
    tall = json.loads((raw / "tall.json").read_text())
    towers = []
    for e in tall["elements"]:
        t = e.get("tags", {})
        g = e.get("geometry")
        if e["type"] != "way" or not g:
            continue
        h = t.get("height")
        try:
            h = float(str(h).replace("m", "").split()[0])
        except (TypeError, ValueError):
            continue
        if h < 100:
            continue
        pts = [[round(v, 1) for v in to_local(p["lon"], p["lat"])] for p in g]
        towers.append({"name": t.get("name", ""), "h": h, "pts": pts,
                       "lattice": t.get("man_made") == "tower" or t.get("tower:construction") == "lattice"})
    gp = raw / "gate_orient.json"
    if gp.exists():
        for e in json.loads(gp.read_text())["elements"]:
            t = e.get("tags", {})
            if "东方之门" in t.get("name", "") and e.get("geometry"):
                pts = [[round(v, 1) for v in to_local(p["lon"], p["lat"])] for p in e["geometry"]]
                towers.append({"name": "东方之门", "h": 301.8, "pts": pts, "lattice": False, "arch": True})
    out["towers"] = towers
    out["caoxieshan"] = [16208, 7100]

    # ---- raster field
    nx = int(math.ceil((EXTENT["x1"] - EXTENT["x0"]) / CELL))
    ny = int(math.ceil((EXTENT["y1"] - EXTENT["y0"]) / CELL))
    to_px = lambda x, y: ((x - EXTENT["x0"]) / CELL, (EXTENT["y1"] - y) / CELL)  # image rows go down
    img = Image.new("L", (nx, ny), 0)
    dr = ImageDraw.Draw(img)
    for a_ in water["areas"]:
        for k, r in enumerate(a_["rings"]):
            if len(r) >= 3:
                dr.polygon([to_px(*p) for p in r], fill=0 if k else 255)
    for l in water["lines"]:
        dr.line([to_px(*p) for p in l["pts"]], fill=255, width=2)
    wmask = np.array(img)[::-1] > 0  # row 0 = y0 (south)
    ys, xs = np.nonzero(wmask)
    idx = -np.ones(wmask.shape, np.int64)
    idx[ys, xs] = np.arange(len(xs))
    rows, cols, wts = [], [], []
    for dy, dx, w in [(0, 1, 1.0), (1, 0, 1.0), (1, 1, 1.4142), (1, -1, 1.4142)]:
        y2, x2 = ys + dy, xs + dx
        ok = (y2 >= 0) & (y2 < ny) & (x2 >= 0) & (x2 < nx)
        y2, x2, a0 = y2[ok], x2[ok], idx[ys[ok], xs[ok]]
        b0 = idx[y2, x2]
        m = b0 >= 0
        rows.append(a0[m]); cols.append(b0[m]); wts.append(np.full(m.sum(), w * CELL))
    G = coo_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(len(xs), len(xs))).tocsr()
    src_xy = water["lines"][[i for i, l in enumerate(water["lines"]) if l["name"] == "京杭大运河"][0]]["pts"][0]
    sx, sy = int((src_xy[0] - EXTENT["x0"]) / CELL), int((src_xy[1] - EXTENT["y0"]) / CELL)
    cand = np.argsort((xs - sx) ** 2 + (ys - sy) ** 2)[:6]
    dist = dijkstra(G, directed=False, indices=cand, min_only=True)
    geo = np.full(wmask.shape, np.inf, np.float32)
    geo[ys, xs] = dist
    reached = np.isfinite(geo)
    # unreached water (isolated ponds) lights after its nearest reached neighbour
    d_e, (iy, ix) = ndimage.distance_transform_edt(~reached, return_indices=True)
    geo = np.where(reached, geo, geo[iy, ix] + d_e * CELL * 1.5).astype(np.float32)
    # every cell takes its nearest water cell's value (so thin canals sample cleanly)
    _, (jy, jx) = ndimage.distance_transform_edt(~wmask, return_indices=True)
    geo = geo[jy, jx]

    # moat distance
    mimg = Image.new("L", (nx, ny), 0)
    ImageDraw.Draw(mimg).line([to_px(*p) for p in moat_line.coords], fill=255, width=2)
    mm = np.array(mimg)[::-1] > 0
    mdist = (ndimage.distance_transform_edt(~mm) * CELL).astype(np.float32)

    # Shantang corridor: within 170 m of the canal, parameter along it; 阊门外 within 420 m gets 0
    gx = EXTENT["x0"] + (np.arange(nx) + 0.5) * CELL
    gy = EXTENT["y0"] + (np.arange(ny) + 0.5) * CELL
    X, Y = np.meshgrid(gx, gy)
    corr = np.full(X.shape, -1.0, np.float32)
    box = (X > -5200) & (X < -1700) & (Y > 300) & (Y < 3200)
    pts = shapely.points(X[box], Y[box])
    d = shapely.distance(shantang, pts)
    par = shapely.line_locate_point(shantang, pts) / shantang.length
    near_chang = (np.hypot(X[box] - CHANG[0], Y[box] - CHANG[1]) < 420) & ~shapely.contains(moat, pts)
    v = np.where(d < 170, par, -1.0)
    v = np.where(near_chang & (v < 0), 0.0, v)
    corr[box] = v

    field = np.stack([geo, mdist, corr, wmask.astype(np.float32)], axis=-1).astype(np.float32)
    (layers / "field.bin").write_bytes(field.tobytes())
    reach = geo[wmask]
    oc = shapely.contains(moat, shapely.points(X, Y)) & wmask
    out["field"] = {"x0": EXTENT["x0"], "y0": EXTENT["y0"], "cell": CELL, "nx": nx, "ny": ny,
                    "wave_max": float(np.percentile(reach, 99.5)),
                    "wave_moat": float(np.median(geo[(mdist < 40) & wmask])),
                    "wave_oldcity_p90": float(np.percentile(geo[oc], 90)) if oc.any() else None}
    (layers / "film.json").write_text(json.dumps(out, ensure_ascii=False))
    print(json.dumps({"old_city_km2": out["old_city_km2"], "wall_m": out["wall"]["length_m"],
                      "survive_m": out["wall"]["survive_m"], "keep_share": round(sum(keep) / len(keep), 3),
                      "bridges": len(sel), "gardens": [g["name"] for g in gardens],
                      "towers": [(t["name"], t["h"]) for t in towers], "route_m": round(route.length),
                      "field": out["field"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
