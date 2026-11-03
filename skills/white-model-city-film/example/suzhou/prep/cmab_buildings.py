"""Clip CMAB buildings to the film extent and pack extruded geometry for the renderer.

Usage: python prep/cmab_buildings.py <shp_or_dir> <out_dir>
Writes buildings.bin (Float32 pos[nv*3] | Float32 height[nv] | Float32 meta[nv*2] | Uint32 idx[ni])
and buildings.json (counts + stats). pos.y is 0 (base) or 1 (top); the shader scales by height.
meta = (ageYear, zone*1000 + rand*999); zone 0 old city, 1 west, 2 east, 3 elsewhere.
"""
import json
import re
import sys
from pathlib import Path

import mapbox_earcut as earcut
import numpy as np
import pyogrio
from shapely.geometry import Polygon, Point
from shapely import prepared

sys.path.insert(0, str(Path(__file__).parent))
from common import BBOX_LONLAT, LOCAL_CRS  # noqa: E402

# old-city interior: the moat centreline ring from film.json when prep/film_layers.py has run, else a hand-drawn fallback
_film = Path(__file__).parent.parent / "data/layers/film.json"
OLD_CITY = (Polygon(json.loads(_film.read_text())["moat"]) if _film.exists()
            else Polygon([(-2050, 1700), (-2000, 2000), (1100, 2380), (1700, -2000), (-1250, -2400), (-1700, -1300), (-2150, 600)]))


def parse_age(v):
    """CMAB 'Age': year built from GAIA impervious surface; 'AF2018' style = after 2018; blanks = pre-1985."""
    if v is None:
        return 1984.0
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none", "0"):
        return 1984.0
    if s.upper().startswith("AF"):
        return 2020.0
    m = re.search(r"(19|20)\d\d", s)
    if m:
        y = float(m.group(0))
        return 1984.0 if y <= 1985 else y
    try:
        y = float(s)
        if 1900 < y < 2100:
            return 1984.0 if y <= 1985 else y
    except ValueError:
        pass
    return 1984.0


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    shps = [src] if src.suffix == ".shp" else sorted(src.rglob("*.shp"))
    w, s, e, n = BBOX_LONLAT
    frames = []
    for shp in shps:
        info = pyogrio.read_info(shp)
        from pyproj import Transformer
        tr = Transformer.from_crs("EPSG:4326", info["crs"] or "EPSG:4326", always_xy=True)
        bx0, by0 = tr.transform(w, s); bx1, by1 = tr.transform(e, n)
        b = info.get("total_bounds")
        if b is not None and (b[2] < bx0 or b[0] > bx1 or b[3] < by0 or b[1] > by1):
            continue
        fields = set(info["fields"])
        hcol = "Height" if "Height" in fields else "pred_h_r"
        df = pyogrio.read_dataframe(shp, bbox=(bx0, by0, bx1, by1), columns=[hcol, "Age"])
        df = df.rename(columns={hcol: "height"})
        df = df.set_crs(info["crs"], allow_override=True)
        if len(df):
            print(shp.name, len(df), info.get("crs"))
            frames.append(df)
    if not frames:
        raise SystemExit("no CMAB features in extent")
    import pandas as pd
    df = pd.concat(frames, ignore_index=True)
    df = df.to_crs(LOCAL_CRS)
    print("features", len(df), "age samples", df["Age"].astype(str).value_counts().head(12).to_dict())

    old = prepared.prep(OLD_CITY)
    rng = np.random.default_rng(7)
    pos, hgt, meta, idx = [], [], [], []
    nv = 0
    stats = {"n": 0, "zone": [0, 0, 0, 0], "h_by_zone": [[], [], [], []], "age_hist": {}}
    tallest_old = (0.0, None)
    for geom, h, age in zip(df.geometry, df["height"], df["Age"]):
        if geom is None or geom.is_empty:
            continue
        parts = list(getattr(geom, "geoms", [geom]))
        h = float(np.clip(h if h == h else 6.0, 3.0, 480.0))
        yr = parse_age(age)
        for p in parts:
            ring = np.asarray(p.exterior.coords[:-1], dtype=np.float64)[:, :2]
            if len(ring) < 3:
                continue
            poly = Polygon(ring).simplify(0.5)
            if poly.is_empty or poly.area < 18 or poly.geom_type != "Polygon":
                continue
            ring = np.array(poly.exterior.coords[:-1], dtype=np.float64)
            k = len(ring)
            c = poly.centroid
            zone = 0 if old.contains(c) else (1 if c.x < -2300 else (2 if c.x > 1900 else 3))
            stats["n"] += 1
            stats["zone"][zone] += 1
            stats["h_by_zone"][zone].append(h)
            stats["age_hist"][int(yr)] = stats["age_hist"].get(int(yr), 0) + 1
            if zone == 0 and h > tallest_old[0]:
                tallest_old = (h, (round(c.x), round(c.y)))
            r = rng.random()
            # verts: bottom ring then top ring
            for t in (0.0, 1.0):
                for x, y in ring:
                    pos.extend((x, t, -y))
                    hgt.append(h)
                    meta.extend((yr, zone * 1000 + r * 999))
            for i in range(k):
                j = (i + 1) % k
                b0, b1, t0, t1 = nv + i, nv + j, nv + k + i, nv + k + j
                idx.extend((b0, b1, t1, b0, t1, t0))
            tri = earcut.triangulate_float32(ring.astype(np.float32), np.array([k], dtype=np.uint32))
            idx.extend((nv + k + tri).tolist())
            nv += 2 * k
    pos = np.asarray(pos, np.float32); hgt = np.asarray(hgt, np.float32)
    meta = np.asarray(meta, np.float32); idx = np.asarray(idx, np.uint32)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "buildings.bin", "wb") as fh:
        for a in (pos, hgt, meta, idx):
            fh.write(a.tobytes())
    q = lambda a, p: round(float(np.percentile(a, p)), 1) if len(a) else None
    report = {
        "nv": int(len(hgt)), "ni": int(len(idx)), "buildings": stats["n"],
        "zone_counts": dict(zip(["old_city", "west", "east", "other"], stats["zone"])),
        "height_pct_by_zone": {z: {"p50": q(np.array(a), 50), "p90": q(np.array(a), 90), "p99": q(np.array(a), 99), "max": q(np.array(a), 100)}
                               for z, a in zip(["old_city", "west", "east", "other"], stats["h_by_zone"])},
        "tallest_in_old_city": {"height_m": round(tallest_old[0], 1), "local_xy": tallest_old[1]},
        "age_hist": dict(sorted(stats["age_hist"].items())),
        "bytes": int(pos.nbytes + hgt.nbytes + meta.nbytes + idx.nbytes),
    }
    (out / "buildings.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "age_hist"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
