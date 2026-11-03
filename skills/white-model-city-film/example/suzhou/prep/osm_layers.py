"""Turn raw Overpass JSON into compact local-metre layers for the renderer.

Usage: python prep/osm_layers.py <raw_osm_dir> <out_dir>
Local frame: transverse Mercator centred on the old city (see common.py); x east, y north, metres.
"""
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, Polygon, MultiPolygon, Point, shape
from shapely.ops import unary_union, linemerge, polygonize

sys.path.insert(0, str(Path(__file__).parent))
from common import to_local, EXTENT_LOCAL  # noqa: E402

OLD_CITY_WATER_NAMES = {"外城河", "护城河", "环城河"}


def way_coords(e):
    return [to_local(p["lon"], p["lat"]) for p in e.get("geometry", []) if p]


def rel_polygons(e):
    """Assemble a multipolygon relation from member ways (outer/inner)."""
    outers, inners = [], []
    for m in e.get("members", []):
        g = m.get("geometry")
        if not g:
            continue
        line = LineString([to_local(p["lon"], p["lat"]) for p in g if p])
        (inners if m.get("role") == "inner" else outers).append(line)
    polys = list(polygonize(linemerge(outers))) if outers else []
    holes = list(polygonize(linemerge(inners))) if inners else []
    out = []
    for p in polys:
        for h in holes:
            if p.contains(h):
                p = p.difference(h)
        out.append(p)
    return out


def rnd(coords, nd=1):
    return [[round(x, nd), round(y, nd)] for x, y in coords]


def poly_to_rings(p):
    polys = list(p.geoms) if isinstance(p, MultiPolygon) else [p]
    res = []
    for q in polys:
        if q.is_empty or q.area < 50:
            continue
        q = q.simplify(0.8)
        res.append([rnd(q.exterior.coords)] + [rnd(i.coords) for i in q.interiors])
    return res


def main():
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    load = lambda n: json.loads((raw / f"{n}.json").read_text())["elements"]
    clip = Polygon(EXTENT_LOCAL)

    # --- water areas + centre lines
    areas, lines = [], []
    for e in load("water"):
        t = e.get("tags", {})
        name = t.get("name", "")
        if e["type"] == "way":
            c = way_coords(e)
            if len(c) < 2:
                continue
            closed = c[0] == c[-1] and len(c) >= 4
            if closed and (t.get("natural") == "water" or t.get("water") or t.get("landuse") == "reservoir"):
                areas.append((Polygon(c).buffer(0), name, t.get("water", "")))
            elif t.get("waterway"):
                lines.append((LineString(c), name, t["waterway"]))
        elif e["type"] == "relation":
            for p in rel_polygons(e):
                areas.append((p.buffer(0), name, t.get("water", "")))
    water_areas = []
    for p, name, kind in areas:
        p = p.intersection(clip)
        for rings in poly_to_rings(p):
            water_areas.append({"name": name, "kind": kind, "moat": name in OLD_CITY_WATER_NAMES, "rings": rings})
    water_lines = []
    for l, name, kind in lines:
        l = l.intersection(clip)
        for g in getattr(l, "geoms", [l]):
            if g.length > 5:
                water_lines.append({"name": name, "kind": kind, "moat": name in OLD_CITY_WATER_NAMES,
                                    "pts": rnd(g.simplify(0.8).coords)})
    (out / "water.json").write_text(json.dumps({"areas": water_areas, "lines": water_lines}, ensure_ascii=False))
    print("water areas", len(water_areas), "lines", len(water_lines))

    # --- roads (major) + old-city streets
    rank = {"motorway": 5, "trunk": 4, "primary": 3, "secondary": 2, "tertiary": 1,
            "motorway_link": 4, "trunk_link": 3}
    roads = []
    for e in load("roads"):
        t = e.get("tags", {})
        c = way_coords(e)
        if len(c) >= 2:
            roads.append({"rank": rank.get(t.get("highway"), 0), "name": t.get("name", ""),
                          "bridge": "bridge" in t, "pts": rnd(LineString(c).simplify(1.0).coords)})
    streets = []
    for e in load("oldcity_streets"):
        t = e.get("tags", {})
        if t.get("highway") in ("service", "footway", "path") and not t.get("name"):
            continue
        c = way_coords(e)
        if len(c) >= 2:
            streets.append({"hw": t["highway"], "name": t.get("name", ""), "pts": rnd(LineString(c).simplify(0.8).coords)})
    (out / "roads.json").write_text(json.dumps({"roads": roads, "streets": streets}, ensure_ascii=False))
    print("roads", len(roads), "old-city streets", len(streets))

    # --- bridges over water: centre points (+ length, heading)
    bridges = []
    for e in load("bridges"):
        t = e.get("tags", {})
        c = way_coords(e)
        if len(c) < 2:
            continue
        l = LineString(c)
        mid = l.interpolate(0.5, normalized=True)
        (x0, y0), (x1, y1) = c[0], c[-1]
        bridges.append({"x": round(mid.x, 1), "y": round(mid.y, 1), "len": round(l.length, 1),
                        "dx": round(x1 - x0, 1), "dy": round(y1 - y0, 1), "name": t.get("name", ""),
                        "hw": t.get("highway", ""), "layer": t.get("layer", "")})
    (out / "bridges.json").write_text(json.dumps(bridges, ensure_ascii=False))
    print("bridges", len(bridges))

    # --- heritage: walls + named points
    walls, pois = [], []
    for e in load("heritage"):
        t = e.get("tags", {})
        if t.get("historic") == "citywalls" and e["type"] == "way":
            walls.append({"name": t.get("name", ""), "pts": rnd(way_coords(e))})
            continue
        name = t.get("name")
        if not name:
            continue
        if e["type"] == "node":
            x, y = to_local(e["lon"], e["lat"])
        elif e.get("geometry"):
            c = way_coords(e)
            g = Polygon(c) if len(c) >= 4 and c[0] == c[-1] else LineString(c)
            x, y = g.centroid.x, g.centroid.y
        elif e.get("bounds"):
            b = e["bounds"]
            x, y = to_local((b["minlon"] + b["maxlon"]) / 2, (b["minlat"] + b["maxlat"]) / 2)
        else:
            continue
        kind = t.get("historic") or t.get("leisure") or t.get("tourism") or t.get("building") or t.get("man_made") or ""
        pois.append({"name": name, "kind": kind, "x": round(x, 1), "y": round(y, 1)})
    (out / "heritage.json").write_text(json.dumps({"walls": walls, "pois": pois}, ensure_ascii=False))
    print("walls", len(walls), "pois", len(pois))


if __name__ == "__main__":
    main()
