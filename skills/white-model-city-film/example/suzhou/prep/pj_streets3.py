"""Streets beside canals: for each canal, test ladder-hatch texture on both sides and emit
parallel street runs where it is present. Plus hand-traced free-standing streets.
Usage: pj_streets3.py <norm_full.jpg> <lines_v1.json> <out.json> <overlay.jpg>"""
import sys, json
import numpy as np, cv2

g = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
L = json.load(open(sys.argv[2]))
gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)); gy = np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
OFF, HALF = 24, 8          # street centre offset from canal centre / half band width (px)

def runs(mask, a, minlen=70, gap=25):
    out, s, last = [], None, None
    for i, m in enumerate(mask):
        if m:
            if s is None: s = i
            last = i
        elif s is not None and i - last > gap:
            if last - s >= minlen: out.append((a + s, a + last))
            s = None
    if s is not None and last - s >= minlen: out.append((a + s, a + last))
    return out

def side_energy(o, a, b, horiz, sign):
    c = o + sign * OFF
    if horiz:
        band = gx[c - HALF:c + HALF, a:b]; br = g[c - HALF:c + HALF, a:b]
        e = band.mean(0); m = br.mean(0)
    else:
        band = gy[a:b, c - HALF:c + HALF]; br = g[a:b, c - HALF:c + HALF]
        e = band.mean(1); m = br.mean(1)
    e = np.convolve(e, np.ones(31) / 31, "same"); m = np.convolve(m, np.ones(31) / 31, "same")
    return e, m, c

allE = []
for key, horiz in (("canal_h", True), ("canal_v", False)):
    for o, a, b in L[key]:
        for sgn in (-1, 1):
            e, m, _ = side_energy(o, a, b, horiz, sgn); allE.append(e)
th = np.percentile(np.concatenate(allE), 62)
streets = {"h": [], "v": []}
for key, horiz in (("canal_h", True), ("canal_v", False)):
    for o, a, b in L[key]:
        best = None
        for sgn in (-1, 1):
            e, m, c = side_energy(o, a, b, horiz, sgn)
            ok = (e > th) & (m > 0.28) & (m < 0.72)
            score = float(ok.mean())
            if best is None or score > best[0]: best = (score, ok, c)
        score, ok, c = best
        for s, t in runs(ok, a):
            streets["h" if horiz else "v"].append([int(c), int(s), int(t)])

# free-standing long streets read off the gridded tiles (stele px): [offset, from, to]
MANUAL = {
    "h": [[2440, 1330, 2990], [2686, 1150, 2120]],
    "v": [[1418, 2180, 3170], [2245, 2470, 3170], [2800, 2480, 3170]],
}
for k in ("h", "v"):
    streets[k] += MANUAL[k]
out = dict(L); out["street_h"] = streets["h"]; out["street_v"] = streets["v"]
json.dump(out, open(sys.argv[3], "w"))
img = (cv2.cvtColor((g * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR) * 0.7).astype(np.uint8)
for o, a, b in L["canal_h"]: cv2.line(img, (a, o), (b, o), (255, 210, 60), 6)
for o, a, b in L["canal_v"]: cv2.line(img, (o, a), (o, b), (255, 210, 60), 6)
for o, a, b in streets["h"]: cv2.line(img, (a, o), (b, o), (40, 170, 255), 6)
for o, a, b in streets["v"]: cv2.line(img, (o, a), (o, b), (40, 170, 255), 6)
cv2.imwrite(sys.argv[4], cv2.resize(img[1950:5480, 1050:3250], None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 85])
print("threshold", round(float(th), 4), {k: len(v) for k, v in streets.items()})
