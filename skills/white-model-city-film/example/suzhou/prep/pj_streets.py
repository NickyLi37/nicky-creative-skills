"""Filter canals to inside the inner city ring; derive streets = hatched segments running
parallel and close to a canal (the 河街并行 pattern). Stele px coords.
Usage: pj_streets.py <hough.json> <canals_auto.json> <norm_full.jpg> <out.json> <overlay.jpg>"""
import sys, json
import numpy as np, cv2
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pj_merge_lib import merge  # noqa

hough = json.load(open(sys.argv[1])); can = json.load(open(sys.argv[2]))
XMIN, XMAX, YMIN, YMAX = 1150, 3065, 2115, 5275
H = [l for l in can["h"] if YMIN <= l[0] <= YMAX and l[2] > XMIN and l[1] < XMAX]
V = [l for l in can["v"] if XMIN <= l[0] <= XMAX and l[2] > YMIN and l[1] < YMAX]

def near_parallel(seg_off, a, b, lines, lo=14, hi=48):
    for o, la, lb in lines:
        if lo <= abs(seg_off - o) <= hi and min(b, lb) - max(a, la) > 0.5 * (b - a):
            return True
    return False

SH = [((y1 + y2) / 2, min(x1, x2), max(x1, x2)) for x1, y1, x2, y2 in hough["street_h"]]
SV = [((x1 + x2) / 2, min(y1, y2), max(y1, y2)) for x1, y1, x2, y2 in hough["street_v"]]
SH = [s for s in SH if YMIN <= s[0] <= YMAX and near_parallel(*s, H)]
SV = [s for s in SV if XMIN <= s[0] <= XMAX and near_parallel(*s, V)]
SH = merge(SH, tol_off=10, gap=60, minlen=80); SV = merge(SV, tol_off=10, gap=60, minlen=80)
out = {"canal_h": H, "canal_v": V, "street_h": [[round(v) for v in s] for s in SH], "street_v": [[round(v) for v in s] for s in SV]}
json.dump(out, open(sys.argv[4], "w"))
img = (cv2.cvtColor(cv2.imread(sys.argv[3], cv2.IMREAD_GRAYSCALE), cv2.COLOR_GRAY2BGR) * 0.7).astype(np.uint8)
for o, a, b in H: cv2.line(img, (a, o), (b, o), (255, 210, 60), 7)
for o, a, b in V: cv2.line(img, (o, a), (o, b), (255, 210, 60), 7)
for o, a, b in out["street_h"]: cv2.line(img, (a, o), (b, o), (60, 190, 255), 5)
for o, a, b in out["street_v"]: cv2.line(img, (o, a), (o, b), (60, 190, 255), 5)
cv2.imwrite(sys.argv[5], cv2.resize(img[1950:5480, 1050:3250], None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 85])
print({k: len(v) for k, v in out.items()})
