"""Fetch a Sentinel-2 cloudless mosaic around the old city and resample it onto the local metre grid.

Source: EOxCloudless 2016 (s2cloudless, CC BY 4.0, https://cloudless.eox.at by EOX IT Services GmbH,
contains modified Copernicus Sentinel data 2016). Native resolution is 10 m, so it is only ever shown soft.

Usage: satellite.py <out_dir>  ->  sat.jpg + sat.json (local extent of the image)
"""
import io
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

sys.path.insert(0, str(Path(__file__).parent))
from common import to_lonlat  # noqa: E402

URL = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg"
Z = 15
X0, X1, Y0, Y1 = -7000.0, 6500.0, -5500.0, 5000.0  # local metres
RES = 5.0  # output m/px


def merc_px(lon, lat, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def main(out_dir):
    out = Path(out_dir)
    corners = [to_lonlat(x, y) for x in (X0, X1) for y in (Y0, Y1)]
    pxs = [merc_px(lon, lat, Z) for lon, lat in corners]
    tx0, tx1 = int(min(p[0] for p in pxs) // 256), int(max(p[0] for p in pxs) // 256)
    ty0, ty1 = int(min(p[1] for p in pxs) // 256), int(max(p[1] for p in pxs) // 256)
    mosaic = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            req = urllib.request.Request(URL.format(z=Z, x=tx, y=ty), headers={"User-Agent": "suzhou-film-prep/1.0"})
            for attempt in range(4):
                try:
                    data = urllib.request.urlopen(req, timeout=30).read()
                    break
                except Exception:
                    time.sleep(1 + attempt)
            mosaic.paste(Image.open(io.BytesIO(data)).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
    src = np.asarray(mosaic, np.float32)
    # output grid, row 0 = north
    w, h = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
    gx, gy = np.meshgrid(X0 + (np.arange(w) + 0.5) * RES, Y1 - (np.arange(h) + 0.5) * RES)
    lon, lat = to_lonlat(gx.ravel(), gy.ravel())
    n = 256 * 2 ** Z
    mx = (np.asarray(lon) + 180) / 360 * n - tx0 * 256
    my = (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n - ty0 * 256
    rgb = np.stack([map_coordinates(src[..., c], [my, mx], order=1, mode="nearest").reshape(h, w) for c in range(3)], -1)
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(out / "sat.jpg", quality=92)
    (out / "sat.json").write_text(json.dumps({"x0": X0, "x1": X1, "y0": Y0, "y1": Y1, "w": w, "h": h,
                                             "source": "EOxCloudless 2016 (CC BY 4.0), modified Copernicus Sentinel data 2016"}))
    print("tiles", (tx1 - tx0 + 1) * (ty1 - ty0 + 1), "->", w, "x", h)


if __name__ == "__main__":
    main(sys.argv[1])
