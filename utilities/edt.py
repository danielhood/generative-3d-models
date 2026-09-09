"""Exact Euclidean distance transform on a 0/1 raster (Felzenszwalb &
Huttenlocher 2012), pure Python -- numpy/scipy are not installed here.

    from edt import edt2d
    sq = edt2d(mask, w, h)        # squared distance to the nearest 0 cell
    dist_mm = sqrt(sq[i]) / px_per_mm

`mask[i]` truthy = foreground. The result is the squared distance from each
cell to the nearest *background* cell, so:

    "how wide is the material here"  -> edt2d(material)   * 2
    "how wide is this hole here"     -> edt2d(cut)        * 2
    "erode X by r"                   -> {i : edt2d(X)[i] > r^2}
    "dilate X by r"                  -> {i : edt2d(NOT X)[i] <= r^2 or X[i]}

Note the dilate form: it needs the transform of the COMPLEMENT. Feeding
edt2d(X) to a dilation is a natural-looking mistake that returns the whole
raster (every background cell has distance 0 and passes `<= r^2`), and it
does it silently -- it cost a wrong "opening removed 2506 mm^2" reading
once here before the shape of the number gave it away.

WHY THE SENTINEL IS FINITE
--------------------------
The published algorithm uses +inf for "foreground, no seed yet". That is
wrong in floating point: the lower-envelope step computes

    s = ((f[q] + q^2) - (f[v] + v^2)) / (2q - 2v)

and inf - inf is NaN. `NaN <= z[k]` is False, so the "pop this parabola"
branch never fires, the envelope silently corrupts, and the transform
returns garbage that is too LARGE -- it will not look like an error.

It also passes small unit tests. A 7x7 hand-checked case was green while
the real 2000x2000 raster reported a 112 mm inscribed width inside a 100 mm
disc, which is what finally gave it away. A large FINITE sentinel fixes it
exactly: the offsets cancel, giving the correct s = (q + v) / 2 for two
parabolas of equal height.

Verified against brute force (every foreground cell vs. every background
cell) on random rasters, and against a disc of known radius. If you touch
this file, re-run that check -- see the __main__ block.
"""


def _dt1d(f, n):
    d = [0.0] * n
    v = [0] * n
    z = [0.0] * (n + 1)
    k = 0
    v[0] = 0
    z[0] = -1e30
    z[1] = 1e30
    for q in range(1, n):
        while True:
            s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2.0 * q - 2.0 * v[k])
            if s <= z[k] and k > 0:
                k -= 1
            else:
                break
        k += 1
        v[k] = q
        z[k] = s
        z[k + 1] = 1e30
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        dx = q - v[k]
        d[q] = dx * dx + f[v[k]]
    return d


def edt2d(mask, w, h):
    """Squared distance from every cell to the nearest falsy cell in `mask`."""
    big = float((w + h) * (w + h) * 4)
    f = [0.0 if not m else big for m in mask]
    col = [0.0] * h
    for x in range(w):
        for y in range(h):
            col[y] = f[y * w + x]
        d = _dt1d(col, h)
        for y in range(h):
            f[y * w + x] = d[y]
    for y in range(h):
        b = y * w
        f[b:b + w] = _dt1d(f[b:b + w], w)
    return f


def erode(mask, w, h, r_px):
    """Cells of `mask` at least r_px from the background."""
    sq = edt2d(mask, w, h)
    rr = r_px * r_px
    return bytearray(1 if sq[i] > rr else 0 for i in range(w * h))


def dilate(mask, w, h, r_px):
    """`mask` grown by r_px. Uses the complement's transform -- see above."""
    comp = bytearray(0 if m else 1 for m in mask)
    sq = edt2d(comp, w, h)
    rr = r_px * r_px
    return bytearray(1 if (mask[i] or sq[i] <= rr) else 0 for i in range(w * h))


def opening(mask, w, h, r_px):
    """Erode then dilate: deletes anything thinner than 2*r_px and leaves
    everything wider essentially untouched (convex corners get rounded to
    r_px). This is how you put a hard floor under a minimum feature width
    rather than hoping for one."""
    return dilate(erode(mask, w, h, r_px), w, h, r_px)


if __name__ == "__main__":
    import math
    import random

    random.seed(7)
    for trial in range(3):
        w, h = 37, 29
        mask = [1 if random.random() < 0.85 else 0 for _ in range(w * h)]
        sq = edt2d(mask, w, h)
        bg = [(i % w, i // w) for i in range(w * h) if not mask[i]]
        bad = 0
        for i in range(w * h):
            if not mask[i]:
                continue
            x, y = i % w, i // w
            b = min((x - bx) ** 2 + (y - by) ** 2 for bx, by in bg)
            if abs(b - sq[i]) > 1e-9:
                bad += 1
        print("brute-force trial %d: %d mismatches" % (trial, bad))

    w = h = 600
    mask = [0] * (w * h)
    for y in range(h):
        for x in range(w):
            if (x - 300) ** 2 + (y - 300) ** 2 < 300 * 300:
                mask[y * w + x] = 1
    print("disc r=300px -> max distance %.1f px (expect ~300)"
          % math.sqrt(max(edt2d(mask, w, h))))
