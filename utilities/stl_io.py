"""Dependency-free STL loading. Auto-detects ASCII vs binary.

    from stl_io import load_stl
    tris = load_stl("part.stl")   # list of ((x,y,z), (x,y,z), (x,y,z))

OpenSCAD's `-o out.stl` emits ASCII by default in some versions/configs and
binary in others -- don't assume either. This handles both from the same
call, the same way pole-foot/check_stl.py does.
"""
import struct


def load_stl(path):
    with open(path, "rb") as f:
        data = f.read()

    if data[:5] == b"solid" and b"facet normal" in data[:2048]:
        nums = []
        tris = []
        for line in data.decode("ascii", "replace").splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                nums.append(tuple(float(x) for x in line.split()[1:4]))
                if len(nums) == 3:
                    tris.append(tuple(nums))
                    nums = []
        return tris

    n = struct.unpack("<I", data[80:84])[0]
    tris = []
    off = 84
    for _ in range(n):
        vals = struct.unpack("<12fH", data[off : off + 50])
        tris.append((vals[3:6], vals[6:9], vals[9:12]))
        off += 50
    return tris


if __name__ == "__main__":
    import sys

    tris = load_stl(sys.argv[1])
    print(f"{len(tris)} triangles")
