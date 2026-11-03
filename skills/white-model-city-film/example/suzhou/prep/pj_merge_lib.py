"""Shared interval-merge helper for Pingjiang line cleanup."""
import numpy as np


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
