"""Merge Hough fragments into clean axis-aligned canal lines.
Usage: pj_merge.py <hough.json> <norm_full.jpg> <out.json> <overlay.jpg>"""
import sys, json
import numpy as np, cv2

segs = json.load(open(sys.argv[1]))
def merge(items, tol_off=14, gap=45, minlen=90):
    # items: (offset, a, b)
    items = sorted(items)
    clusters = []
    for it in items:
        if clusters and abs(it[0] - np.mean([c[0] for c in clusters[-1]])) <= tol_off:
            clusters[-1].append(it)
        else:
            clusters.append([it])
    lines = []
    for cl in clusters:
        off = float(np.median([c[0] for c in cl]))
        iv = sorted((min(a, b), max(a, b)) for _, a, b in cl)
        cur = list(iv[0])
        for a, b in iv[1:]:
            if a <= cur[1] + gap:
                cur[1] = max(cur[1], b)
            else:
                lines.append((off, *cur)); cur = [a, b]
        lines.append((off, *cur))
    return [l for l in lines if l[2] - l[1] >= minlen]

H = merge([((y1 + y2) / 2, x1, x2) for x1, y1, x2, y2 in segs["canal_h"]])
V = merge([((x1 + x2) / 2, y1, y2) for x1, y1, x2, y2 in segs["canal_v"]])
out = {"h": [[round(o), round(a), round(b)] for o, a, b in H], "v": [[round(o), round(a), round(b)] for o, a, b in V]}
json.dump(out, open(sys.argv[3], "w"))
img = cv2.cvtColor(cv2.imread(sys.argv[2], cv2.IMREAD_GRAYSCALE), cv2.COLOR_GRAY2BGR)
img = (img * 0.75).astype(np.uint8)
for i, (o, a, b) in enumerate(H):
    cv2.line(img, (int(a), int(o)), (int(b), int(o)), (40, 220, 255), 7)
    cv2.putText(img, f"h{i}", (int(a), int(o) - 6), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)
for i, (o, a, b) in enumerate(V):
    cv2.line(img, (int(o), int(a)), (int(o), int(b)), (255, 160, 40), 7)
    cv2.putText(img, f"v{i}", (int(o) + 6, int(a) + 30), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 0, 255), 3)
crop = img[1950:5480, 1050:3250]
cv2.imwrite(sys.argv[4], cv2.resize(crop, None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 85])
print("h", len(H), "v", len(V))
