"""Register the old public-domain photo of the Pingjiang stele onto the Siyuwj stele-pixel frame used by the
traced lines, and export it as a texture the renderer can morph together with those lines.

Photo: 亜細亜大観 vol. 14 no. 036 「平江之圖（蘇州）」, Wikimedia Commons, public domain.
Usage: pj_photo.py <raw_dir> <pingjiang.json> <out_dir>  ->  pj_photo.jpg + pj_photo.json
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

# texture window in Siyuwj stele px (whole slab below its top edge: title, map, border)
PX0, PX1, PY0, PY1 = 640, 3340, 1000, 5700
SCALE = 0.4  # texture px per stele px (the old photo carries about this much detail)


def register(old, ref):
    """Homography old-photo px -> ref (Siyuwj) px, SIFT + MAGSAC on contrast-equalised images."""
    sb = 0.4
    ref_s = cv2.resize(ref, None, fx=sb, fy=sb, interpolation=cv2.INTER_AREA)
    cl = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    sift = cv2.SIFT_create(nfeatures=20000)
    ka, da = sift.detectAndCompute(cl.apply(old), None)
    kb, db = sift.detectAndCompute(cl.apply(ref_s), None)
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < 0.8 * n.distance]
    pa = np.float32([ka[g.queryIdx].pt for g in good])
    pb = np.float32([kb[g.trainIdx].pt for g in good]) / sb
    H, mask = cv2.findHomography(pa, pb, cv2.USAC_MAGSAC, 8.0, maxIters=20000, confidence=0.999)
    print(f"matches {len(good)}, inliers {int(mask.sum())}")
    return H


def stele_affine(pj):
    """Least-squares affine stele px -> local metres from the georeferenced line samples."""
    src, dst = [], []
    for c in pj["canals"] + pj["streets"]:
        src += c["spx"]; dst += c["pts"]
    src, dst = np.asarray(src, float), np.asarray(dst, float)
    A = np.c_[src, np.ones(len(src))]
    M, *_ = np.linalg.lstsq(A, dst, rcond=None)
    res = np.linalg.norm(A @ M - dst, axis=1)
    print(f"affine fit residual max {res.max():.2f} m")
    return M.T  # 2x3: [x; y] = M @ [px, py, 1]


def main(raw_dir, pj_path, out_dir):
    raw, out = Path(raw_dir), Path(out_dir)
    old = cv2.imread(str(raw / "stele_asiataikan.jpg"), cv2.IMREAD_GRAYSCALE)
    ref = cv2.imread(str(raw / "stele_siyuwj_4016x6016.jpg"), cv2.IMREAD_GRAYSCALE)
    H = register(old, ref)
    # sample the old photo on the texture grid (stele px -> old px)
    w, h = int((PX1 - PX0) * SCALE), int((PY1 - PY0) * SCALE)
    T = np.array([[1 / SCALE, 0, PX0], [0, 1 / SCALE, PY0], [0, 0, 1]])
    tex = cv2.warpPerspective(old, np.linalg.inv(H) @ T, (w, h), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    # even out the 1920s lighting (raking shadow across the top) and lift the chalked canals
    f = tex.astype(np.float32) + 1
    flat = f / cv2.GaussianBlur(f, (0, 0), 40)
    flat = (flat - np.percentile(flat, 2)) / (np.percentile(flat, 99.7) - np.percentile(flat, 2))
    flat = np.clip(flat, 0, 1) ** 1.35
    cv2.imwrite(str(out / "pj_photo.jpg"), (flat * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
    M = stele_affine(json.loads(Path(pj_path).read_text()))
    meta = {"px0": PX0, "px1": PX1, "py0": PY0, "py1": PY1, "w": w, "h": h, "affine": M.round(6).tolist(),
            "source": "亜細亜大観 14-036「平江之圖（蘇州）」, Wikimedia Commons, public domain"}
    (out / "pj_photo.json").write_text(json.dumps(meta, ensure_ascii=False))
    print("texture", w, "x", h)


if __name__ == "__main__":
    main(*sys.argv[1:4])
