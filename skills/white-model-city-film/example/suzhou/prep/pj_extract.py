"""Extract the canal (smooth white band) mask from the Pingjiang stele photo.
Usage: pj_extract.py <stele.jpg> <out_dir>"""
import sys
from pathlib import Path
import numpy as np
import cv2
from skimage.morphology import skeletonize, remove_small_objects

src, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
X0, Y0, X1, Y1 = 700, 1780, 3360, 5640           # map region on the stele (full-res px)
img = cv2.imread(src, cv2.IMREAD_GRAYSCALE)[Y0:Y1, X0:X1].astype(np.float32)
bg = cv2.GaussianBlur(img, (0, 0), 40)
norm = img / (bg + 1)                               # illumination-normalised brightness
mean = cv2.blur(norm, (9, 9)); sq = cv2.blur(norm * norm, (9, 9))
std = np.sqrt(np.maximum(sq - mean * mean, 0))      # local texture
bright = cv2.GaussianBlur(norm, (0, 0), 2.0)
river = (bright > np.percentile(bright, 84)) & (std < np.percentile(std, 60))
river = cv2.morphologyEx(river.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
river = cv2.morphologyEx(river, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
river = remove_small_objects(river.astype(bool), 1500)
cv2.imwrite(str(out / "river_mask.png"), (river * 255).astype(np.uint8))
sk = skeletonize(river)
cv2.imwrite(str(out / "river_skel.png"), (sk * 255).astype(np.uint8))
vis = cv2.cvtColor(np.clip(norm * 110, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
vis[river] = (0.45 * vis[river] + 0.55 * np.array([255, 200, 60])).astype(np.uint8)
vis[cv2.dilate(sk.astype(np.uint8), np.ones((3, 3))) > 0] = (40, 40, 255)
cv2.imwrite(str(out / "river_overlay.jpg"), cv2.resize(vis, None, fx=0.45, fy=0.45), [cv2.IMWRITE_JPEG_QUALITY, 88])
print("river px", int(river.sum()), "skeleton px", int(sk.sum()))
