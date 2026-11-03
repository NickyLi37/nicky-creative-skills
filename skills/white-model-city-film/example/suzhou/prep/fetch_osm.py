"""Fetch OSM layers for the Suzhou film extent via Overpass.

Usage: python prep/fetch_osm.py <out_dir>
Writes one raw Overpass JSON per layer so each can be re-fetched independently.
"""
import json
import sys
import time
from pathlib import Path

import requests

# south, west, north, east — old city + Gaoxin (west) + SIP / Jinji Lake + Weiting / Caoxieshan (east)
BBOX = (31.235, 120.495, 31.425, 120.835)
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

LAYERS = {
    "water": """
        (
          way["waterway"~"^(river|canal|stream|ditch|drain)$"]({bbox});
          way["natural"="water"]({bbox});
          relation["natural"="water"]({bbox});
          way["water"]({bbox});
          way["landuse"="reservoir"]({bbox});
        );
        out geom;
    """,
    "roads": """
        (
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary|motorway_link|trunk_link)$"]({bbox});
        );
        out geom;
    """,
    "oldcity_streets": """
        (
          way["highway"~"^(residential|unclassified|living_street|pedestrian|service|footway|path)$"](31.288,120.595,31.335,120.652);
        );
        out geom;
    """,
    "bridges": """
        (
          way["bridge"]["highway"]({bbox});
          way["man_made"="bridge"]({bbox});
        );
        out geom;
    """,
    "heritage": """
        (
          nwr["historic"]({bbox});
          nwr["leisure"="garden"]["name"]({bbox});
          nwr["tourism"~"^(attraction|museum)$"]["name"]({bbox});
          nwr["building"="pagoda"]({bbox});
          nwr["tower:type"="pagoda"]({bbox});
          nwr["name"~"塔$"]({bbox});
          nwr["name"~"门$"]["name"~"^(盘|阊|胥|娄|齐|平|相|葑|金|新|蛇|匠)"]({bbox});
          nwr["name"~"草鞋山"]({bbox});
        );
        out geom;
    """,
    "tall": """
        (
          nwr["name"~"(国际金融中心|东方之门|苏州中心|九龙仓)"]({bbox});
          nwr["building"]["height"]({bbox});
          nwr["building"]["building:levels"~"^([3-9][0-9]|1[0-9][0-9])$"]({bbox});
        );
        out geom;
    """,
    "admin": """
        (
          relation["boundary"="administrative"]["admin_level"~"^(6|7)$"]({bbox});
        );
        out tags;
    """,
}


def fetch(query: str) -> dict:
    s, w, n, e = BBOX
    q = "[out:json][timeout:300];" + query.replace("{bbox}", f"{s},{w},{n},{e}")
    last = None
    for attempt in range(6):
        url = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            r = requests.post(url, data={"data": q}, timeout=360,
                              headers={"User-Agent": "SuzhouFilm/0.1 (personal project)"})
            if r.status_code == 200:
                return r.json()
            last = f"{url} HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as ex:
            last = f"{url} {ex}"
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(last)


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[2:])
    for name, q in LAYERS.items():
        if only and name not in only:
            continue
        dst = out / f"{name}.json"
        if dst.exists() and not only:
            print(f"skip {name} (exists)")
            continue
        t = time.time()
        data = fetch(q)
        dst.write_text(json.dumps(data, ensure_ascii=False))
        print(f"{name}: {len(data.get('elements', []))} elements, {dst.stat().st_size/1e6:.1f} MB, {time.time()-t:.0f}s")


if __name__ == "__main__":
    main()
