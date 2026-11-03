"""Street (ladder-hatched band) detection by mid-brightness after along-axis blur.
Usage: pj_streets2.py <norm_full.jpg> <lines_v1.json> <out.json> <overlay.jpg>"""
import sys, json
import numpy as np, cv2
from skimage.morphology import skeletonize
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pj_merge_lib import merge  # noqa

X0, Y0, X1, Y1 = 1150, 2100, 3070, 5290
g = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)[Y0:Y1, X0:X1].astype(np.float32) / 255.0
prev = json.load(open(sys.argv[2]))
res = {}
for name, horiz in (("h", True), ("v", False)):
    B = cv2.blur(g, (61, 1) if horiz else (1, 61))
    m = ((B > 0.36) & (B < 0.64)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((13, 1) if horiz else (1, 13), np.uint8))   # thick enough across
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((1, 61) if horiz else (61, 1), np.uint8))   # long enough along
    sk = skeletonize(m > 0).astype(np.uint8) * 255
    segs = cv2.HoughLinesP(sk, 1, np.pi / 180, threshold=40, minLineLength=80, maxLineGap=30)
    segs = [] if segs is None else np.asarray(segs).reshape(-1, 4).tolist()
    items = []
    for x1, y1, x2, y2 in segs:
        ang = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) % 180
        if horiz and (ang < 8 or ang > 172):
            items.append(((y1 + y2) / 2 + Y0, min(x1, x2) + X0, max(x1, x2) + X0))
        if not horiz and 82 < ang < 98:
            items.append(((x1 + x2) / 2 + X0, min(y1, y2) + Y0, max(y1, y2) + Y0))
    # drop anything sitting on a canal (canal edges), keep bands 12-60 px off a canal or free-standing
    canals = prev["canal_h"] if horiz else prev["canal_v"]
    def on_canal(o, a, b):
        return any(abs(o - co) < 12 and min(b, cb) - max(a, ca) > 0.4 * (b - a) for co, ca, cb in canals)
    items = [it for it in items if not on_canal(*it)]
    res[name] = [[round(v) for v in s] for s in merge(items, tol_off=10, gap=50, minlen=90)]
out = dict(prev); out["street_h"] = res["h"]; out["street_v"] = res["v"]
json.dump(out, open(sys.argv[3], "w"))
img = (cv2.cvtColor(cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE), cv2.COLOR_GRAY2BGR) * 0.7).astype(np.uint8)
for o, a, b in out["canal_h"]: cv2.line(img, (a, o), (b, o), (255, 210, 60), 6)
for o, a, b in out["canal_v"]: cv2.line(img, (o, a), (o, b), (255, 210, 60), 6)
for o, a, b in out["street_h"]: cv2.line(img, (a, o), (b, o), (40, 170, 255), 6)
for o, a, b in out["street_v"]: cv2.line(img, (o, a), (o, b), (40, 170, 255), 6)
cv2.imwrite(sys.argv[4], cv2.resize(img[1950:5480, 1050:3250], None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 85])
print({k: len(v) for k, v in out.items()})
