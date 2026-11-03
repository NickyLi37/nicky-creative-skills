"""Directional detection of canals (smooth bright bands) and streets (ladder-hatched bands)
on the Pingjiang stele. Writes masks + Hough segments (stele px coords).
Usage: pj_detect.py <norm_full.jpg> <out_dir>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
from skimage.morphology import skeletonize

X0, Y0, X1, Y1 = 1150, 2000, 3150, 5420          # inside the city wall (stele px)
src, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
g = cv2.imread(src, cv2.IMREAD_GRAYSCALE)[Y0:Y1, X0:X1].astype(np.float32) / 255.0
L = 61
def dirblur(a, horizontal):
    k = (L, 1) if horizontal else (1, L)
    return cv2.blur(a, k)
gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)); gy = np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
res = {}
for name, horiz in (("h", True), ("v", False)):
    bright = dirblur(g, horiz)                                  # canal: stays bright along its axis
    hatch = dirblur(gx if horiz else gy, horiz)                 # street: strokes across the axis
    across = cv2.GaussianBlur(bright, (0, 0), 3)
    canal = (bright > 0.62) & (hatch < np.percentile(hatch, 70))
    street = (hatch > np.percentile(hatch, 88)) & (bright > 0.35) & ~canal
    for kind, m in (("canal", canal), ("street", street)):
        m = m.astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        sk = skeletonize(m > 0).astype(np.uint8) * 255
        segs = cv2.HoughLinesP(sk, 1, np.pi / 180, threshold=40, minLineLength=70, maxLineGap=25)
        segs = [] if segs is None else np.asarray(segs).reshape(-1, 4).tolist()
        keep = []
        for x1, y1, x2, y2 in segs:
            ang = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) % 180
            ok = (ang < 12 or ang > 168) if horiz else (78 < ang < 102)
            if ok:
                keep.append([x1 + X0, y1 + Y0, x2 + X0, y2 + Y0])
        res[f"{kind}_{name}"] = keep
        cv2.imwrite(str(out / f"{kind}_{name}.png"), m * 255)
json.dump(res, open(out / "hough.json", "w"))
vis = cv2.cvtColor((g * 200).astype(np.uint8), cv2.COLOR_GRAY2BGR)
for key, col in (("canal_h", (255, 200, 40)), ("canal_v", (255, 200, 40)), ("street_h", (60, 120, 255)), ("street_v", (60, 120, 255))):
    for x1, y1, x2, y2 in res[key]:
        cv2.line(vis, (x1 - X0, y1 - Y0), (x2 - X0, y2 - Y0), col, 5)
cv2.imwrite(str(out / "detect_overlay.jpg"), cv2.resize(vis, None, fx=0.42, fy=0.42), [cv2.IMWRITE_JPEG_QUALITY, 85])
print({k: len(v) for k, v in res.items()})
