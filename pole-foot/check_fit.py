"""Elliptical fit probe.

Casts rays outward from the axis at height z, finds the first material
boundary, and reports its signed distance from the NOMINAL pole ellipse
(positive = outside the pole, i.e. a gap).

Expected for this design:
    at a ridge crest   ->  0.000   (crest sits on the nominal ellipse)
    between ridges     -> +clearance
"""
import sys, math
from check_stl import load

def section_segments(tris, z):
    segs = []
    for t in tris:
        pts = []
        for i in range(3):
            p, q = t[i], t[(i+1) % 3]
            if (p[2]-z) * (q[2]-z) < 0:
                f = (z - p[2]) / (q[2] - p[2])
                pts.append((p[0] + f*(q[0]-p[0]), p[1] + f*(q[1]-p[1])))
        if len(pts) == 2:
            segs.append(pts)
    return segs

def ray_first_hit(segs, ang):
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    best = None
    for (x1, y1), (x2, y2) in segs:
        dx, dy = x2-x1, y2-y1
        den = ux*dy - uy*dx
        if abs(den) < 1e-12:
            continue
        s = (x1*dy - y1*dx) / den          # distance along the ray
        u = (x1*uy - y1*ux) / den          # position along the segment
        if s > 1e-9 and -1e-9 <= u <= 1 + 1e-9:
            if best is None or s < best:
                best = s
    return best

def dist_from_ellipse(px, py, a, b):
    """Signed distance from the ellipse (positive outside). Dense sample then
    local refine - no dependencies, accurate to ~1e-5 mm."""
    def d2(t):
        return (px - a*math.cos(t))**2 + (py - b*math.sin(t))**2
    n = 2000
    best_t = min((2*math.pi*i/n for i in range(n)), key=d2)
    lo, hi = best_t - 2*math.pi/n, best_t + 2*math.pi/n
    for _ in range(80):
        m1, m2 = lo + (hi-lo)/3, hi - (hi-lo)/3
        if d2(m1) < d2(m2): hi = m2
        else:               lo = m1
    t = (lo+hi)/2
    d = math.sqrt(d2(t))
    inside = (px/a)**2 + (py/b)**2 < 1
    return -d if inside else d

def probe(path, a, b, ridge_count, zs):
    tris = load(path)
    # polar angles at which the ridge crests sit (NOT i*360/n - the ellipse
    # parameter and the polar angle differ)
    crest_ang = [math.degrees(math.atan2(b*math.sin(math.radians(i*360/ridge_count)),
                                         a*math.cos(math.radians(i*360/ridge_count))))
                 % 360 for i in range(ridge_count)]
    gap_ang = [(crest_ang[i] + crest_ang[(i+1) % ridge_count]
                + (360 if i == ridge_count-1 else 0)) / 2 % 360
               for i in range(ridge_count)]
    print(f"{path}   nominal ellipse {2*a:.1f} x {2*b:.1f}")
    for z in zs:
        segs = section_segments(tris, z)
        if not segs:
            print(f"  z={z:<6} no section"); continue
        def gap(ang):
            s = ray_first_hit(segs, ang)
            if s is None: return None
            return dist_from_ellipse(s*math.cos(math.radians(ang)),
                                     s*math.sin(math.radians(ang)), a, b)
        cg = [gap(x) for x in crest_ang]
        gg = [gap(x) for x in gap_ang]
        sweep = [gap(x*0.5) for x in range(720)]
        sweep = [v for v in sweep if v is not None]
        print(f"  z={z}")
        print(f"    at crests   {min(cg):+.3f} .. {max(cg):+.3f} mm from nominal")
        print(f"    between     {min(gg):+.3f} .. {max(gg):+.3f} mm from nominal")
        print(f"    full sweep  {min(sweep):+.3f} .. {max(sweep):+.3f} mm")

if __name__ == '__main__':
    f = sys.argv[1]; a = float(sys.argv[2]); b = float(sys.argv[3])
    n = int(sys.argv[4]); zs = [float(x) for x in sys.argv[5:]]
    probe(f, a, b, n, zs)
