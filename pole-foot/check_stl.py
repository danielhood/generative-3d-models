"""Dependency-free STL sanity check: manifoldness, winding, volume, bbox,
connected components, and a radial slice profile at a given Z."""
import struct, sys, math
from collections import defaultdict

def load(path):
    with open(path, 'rb') as f:
        data = f.read()
    if data[:5] == b'solid' and b'facet normal' in data[:2048]:
        nums = []
        tris = []
        for line in data.decode('ascii', 'replace').splitlines():
            line = line.strip()
            if line.startswith('vertex'):
                nums.append(tuple(float(x) for x in line.split()[1:4]))
                if len(nums) == 3:
                    tris.append(tuple(nums)); nums = []
        return tris
    n = struct.unpack('<I', data[80:84])[0]
    tris = []
    off = 84
    for _ in range(n):
        vals = struct.unpack('<12fH', data[off:off+50])
        tris.append((vals[3:6], vals[6:9], vals[9:12]))
        off += 50
    return tris

def key(v, q=1e-5):
    return tuple(round(c/q) for c in v)

def analyze(path):
    tris = load(path)
    idx, verts = {}, []
    faces = []
    for t in tris:
        f = []
        for v in t:
            k = key(v)
            if k not in idx:
                idx[k] = len(verts); verts.append(v)
            f.append(idx[k])
        faces.append(tuple(f))

    # edge manifoldness + consistent winding
    directed = defaultdict(int)
    undirected = defaultdict(int)
    for a, b, c in faces:
        for e in ((a,b), (b,c), (c,a)):
            directed[e] += 1
            undirected[tuple(sorted(e))] += 1
    bad = {n: sum(1 for v in undirected.values() if v == n)
           for n in sorted(set(undirected.values())) if n != 2}
    flipped = sum(1 for e, c in directed.items() if c > 1)

    # signed volume
    vol = 0.0
    for a, b, c in faces:
        p, q, r = verts[a], verts[b], verts[c]
        vol += (p[0]*(q[1]*r[2]-q[2]*r[1])
                - p[1]*(q[0]*r[2]-q[2]*r[0])
                + p[2]*(q[0]*r[1]-q[1]*r[0])) / 6.0

    # connected components over shared vertices
    parent = list(range(len(verts)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry: parent[rx] = ry
    for a, b, c in faces:
        union(a, b); union(b, c)
    comps = len({find(i) for i in range(len(verts))})

    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
    print(f"file            {path}")
    print(f"triangles       {len(faces)}   vertices {len(verts)}")
    print(f"non-manifold    {bad if bad else 'none (every edge shared by 2 faces)'}")
    print(f"winding         {'consistent' if flipped == 0 else f'{flipped} mismatched directed edges'}")
    print(f"signed volume   {vol/1000:.3f} cm^3  ({'outward normals' if vol > 0 else 'INVERTED'})")
    print(f"shells          {comps}")
    print(f"bbox            X {min(xs):.2f}..{max(xs):.2f}  "
          f"Y {min(ys):.2f}..{max(ys):.2f}  Z {min(zs):.2f}..{max(zs):.2f}")
    print(f"size            {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} x {max(zs)-min(zs):.2f} mm")
    return tris

def radii_at_z(path, z):
    """Ray-cast +X..all directions: report min/max radius of material at height z
    by intersecting triangles with the plane and collecting radii."""
    tris = load(path)
    rs = []
    for t in tris:
        for i in range(3):
            p, q = t[i], t[(i+1) % 3]
            if (p[2]-z) * (q[2]-z) < 0:
                f = (z - p[2]) / (q[2] - p[2])
                x = p[0] + f*(q[0]-p[0]); y = p[1] + f*(q[1]-p[1])
                rs.append(math.hypot(x, y))
    if not rs:
        print(f"  z={z:<6} no material"); return
    rs.sort()
    inner = [r for r in rs if r < (rs[0]+rs[-1])/2]
    print(f"  z={z:<6} radii min {rs[0]:.3f} (dia {2*rs[0]:.2f})   "
          f"max {rs[-1]:.3f} (dia {2*rs[-1]:.2f})   "
          f"inner-band spread {min(inner):.3f}..{max(inner):.3f}")

if __name__ == '__main__':
    p = sys.argv[1]
    analyze(p)
    print("cross-sections:")
    for z in [float(a) for a in sys.argv[2:]]:
        radii_at_z(p, z)
