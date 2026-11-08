"""Read a .slvs file and say what is in it.

    python3 slvs_info.py part.slvs                      # every group, with counts
    python3 slvs_info.py part.slvs --constraint c039    # what is constraint c039?
    python3 slvs_info.py part.slvs --group groove-profile

    from slvs_info import load, describe_constraint

SolveSpace's GUI reports problems by handle: "c039-pts-coincident",
"c03d-symmetric-h", "c042-angle".  Those are the constraint's handle in HEX, and
by itself it says nothing about WHERE in a 150-constraint file the problem is.
This resolves the handle to its type, the group that owns it, and the entities it
joins -- which is usually enough to see the mistake: four handles reported as
unsolvable turned out to be exactly one group, the 16-equation trapezoid that cuts
a groove, and the diagnosis (a redundant symmetric constraint and an angle whose
two lines ran in opposite directions) followed from seeing which four they were.

The file format, as far as this needs it.  A .slvs is a list of "Key=value"
lines, each record ended by an AddGroup / AddRequest / AddConstraint / AddParam
marker.  Entities are NOT stored (SolveSpace regenerates them), so this reads
groups, requests, constraints and params, and works out entity ownership from the
handle arithmetic:

    request r  -> entity (r << 16) | i       entity 0 is the thing itself, points 1..n
    group g    -> entity 0x80000000 | (g << 16) | i

so the high bit says "owned by a group", otherwise (handle >> 16) is the request.

Handles are written and shown in hex everywhere in SolveSpace; so are they here,
and `--constraint` takes `c039`, `0x39` or `39` (all hex).
"""
import re

GROUP_TYPES = {5000: "3d-drawing", 5001: "workplane", 5100: "extrude", 5101: "lathe",
               5102: "revolve", 5103: "helix", 5200: "rotate", 5201: "translate",
               5300: "linked"}
REQUEST_TYPES = {100: "workplane", 101: "datum-point", 200: "line", 300: "cubic",
                 301: "cubic-periodic", 400: "circle", 500: "arc", 600: "text",
                 700: "image", 800: "named-param", 801: "named-const", 802: "named-link"}
CONSTRAINT_TYPES = {
    20: "pts-coincident", 30: "pt-pt-distance", 31: "pt-plane-distance",
    32: "pt-line-distance", 33: "pt-face-distance", 34: "proj-pt-distance",
    41: "pt-in-plane", 42: "pt-on-line", 43: "pt-on-face", 50: "equal-length",
    51: "length-ratio", 52: "eq-len-pt-line-d", 53: "eq-pt-ln-distances",
    54: "equal-angle", 55: "equal-line-arc-len", 56: "length-difference",
    60: "symmetric", 61: "symmetric-h", 62: "symmetric-v", 63: "symmetric-line",
    70: "at-midpoint", 80: "horizontal", 81: "vertical", 90: "diameter",
    100: "pt-on-circle", 110: "same-orientation", 120: "angle", 121: "parallel",
    122: "perpendicular", 123: "arc-line-tangent", 124: "cubic-line-tangent",
    125: "curve-curve-tangent", 130: "equal-radius", 200: "where-dragged",
    210: "arc-arc-len-ratio", 211: "arc-line-len-ratio", 212: "arc-arc-difference",
    213: "arc-line-difference", 1000: "comment", 1001: "relation"}
COMBINE = {0: "union", 1: "difference", 2: "assemble", 3: "intersection"}
SUBTYPES = {6000: "by-point-ortho", 6001: "by-line-segments", 6002: "by-point-normal",
            7000: "one-sided", 7001: "two-sided", 7004: "one-skewed", 7005: "two-skewed"}


def _hex(v):
    return int(v, 16) if v else 0


def load(path):
    """Parse a .slvs into {"groups": [...], "requests": [...], "constraints": [...],
    "params": {handle: value}}.  Each record is a dict of its Key=value fields
    with the "Group." / "Request." / "Constraint." prefix removed."""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    markers = {"AddGroup": "groups", "AddRequest": "requests",
               "AddConstraint": "constraints", "AddParam": "params"}
    out = {"groups": [], "requests": [], "constraints": [], "params": {}}
    cur, in_remap = {}, False
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if in_remap:                       # skip the entity-remap block of a group
            if line.startswith("}"):
                in_remap = False
            continue
        if line.endswith("{") and "=" in line:
            in_remap = True
            continue
        if line in markers:
            kind = markers[line]
            if kind == "params":
                out["params"][_hex(cur.get("Param.h.v."))] = float(cur.get("Param.val", 0.0))
            else:
                rec = {k.split(".", 1)[1]: v for k, v in cur.items() if "." in k}
                out[kind].append(rec)
            cur = {}
        elif "=" in line:
            k, v = line.split("=", 1)
            cur[k] = v
    return out


def _group_names(d):
    return {_hex(g.get("h.v")): g.get("name", "?") for g in d["groups"]}


def _requests(d):
    return {_hex(r.get("h.v")): r for r in d["requests"]}


def describe_entity(d, h):
    """A readable account of an entity handle."""
    if h == 0:
        return "-"
    names, reqs = _group_names(d), _requests(d)
    if h & 0x80000000:
        g = (h >> 16) & 0x3fff
        return "group '%s' entity %d" % (names.get(g, "?"), h & 0xffff)
    r = h >> 16
    req = reqs.get(r)
    if req is None:
        return "request %#x (NOT FOUND) entity %d" % (r, h & 0xffff)
    rt = REQUEST_TYPES.get(int(req.get("type", 0)), req.get("type"))
    i = h & 0xffff
    what = "itself" if i == 0 else ("point %d" % i if i < 32 else "normal/distance")
    return "%s #%#x %s (in '%s')" % (rt, r, what, names.get(_hex(req.get("group.v")), "?"))


def describe_constraint(d, handle):
    """Return a list of lines describing the constraint with this handle, or
    None if there is no such constraint."""
    names = _group_names(d)
    for c in d["constraints"]:
        if _hex(c.get("h.v")) != handle:
            continue
        t = int(c.get("type", 0))
        lines = ["constraint %#x  %s  (type %d)" % (handle, CONSTRAINT_TYPES.get(t, "?"), t),
                 "  group      %s" % names.get(_hex(c.get("group.v")), "?")]
        if c.get("valA"):
            lines.append("  value      %s" % c["valA"].rstrip("0").rstrip("."))
        for key in ("workplane.v", "ptA.v", "ptB.v", "entityA.v", "entityB.v",
                    "entityC.v", "entityD.v"):
            if c.get(key):
                lines.append("  %-10s %s" % (key[:-2], describe_entity(d, _hex(c[key]))))
        if c.get("other") == "1":
            lines.append("  other      1  (negates the first vector / picks the other end)")
        return lines
    return None


def summary(d):
    """Per-group rows: (handle, type, name, detail, requests, constraints)."""
    names = _group_names(d)
    nreq, ncon = {}, {}
    for r in d["requests"]:
        g = _hex(r.get("group.v"))
        nreq[g] = nreq.get(g, 0) + 1
    for c in d["constraints"]:
        g = _hex(c.get("group.v"))
        ncon[g] = ncon.get(g, 0) + 1
    rows = []
    for g in d["groups"]:
        h = _hex(g.get("h.v"))
        t = int(g.get("type", 0))
        det = []
        if t in (5100, 5101):
            det.append(COMBINE.get(int(g.get("meshCombine", 0)), "?"))
            det.append("of '%s'" % names.get(_hex(g.get("opA.v")), "?"))
        if t == 5001:
            det.append(SUBTYPES.get(int(g.get("subtype", 0)), ""))
        if g.get("visible") == "0":
            det.append("hidden")
        rows.append((h, GROUP_TYPES.get(t, str(t)), g.get("name", "?"), ", ".join(x for x in det if x),
                     nreq.get(h, 0), ncon.get(h, 0)))
    return rows


if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser(description="Describe a .slvs file.")
    ap.add_argument("slvs")
    ap.add_argument("--constraint", metavar="HANDLE", help="e.g. c039, 0x39 or 39 (hex)")
    ap.add_argument("--group", metavar="NAME", help="list one group's requests and constraints")
    a = ap.parse_args()
    d = load(a.slvs)
    if a.constraint:
        h = _hex(re.sub(r"^(c|0x)", "", a.constraint.lower()))
        lines = describe_constraint(d, h)
        if lines is None:
            sys.exit("no constraint with handle %#x (the file has %d constraints)"
                     % (h, len(d["constraints"])))
        print("\n".join(lines))
    elif a.group:
        gh = [h for h, n in _group_names(d).items() if n == a.group]
        if not gh:
            sys.exit("no group named %r" % a.group)
        for r in d["requests"]:
            if _hex(r.get("group.v")) in gh:
                print("request %#x  %s" % (_hex(r["h.v"]), REQUEST_TYPES.get(int(r["type"]), r["type"])))
        for c in d["constraints"]:
            if _hex(c.get("group.v")) in gh:
                print("\n".join(describe_constraint(d, _hex(c["h.v"]))))
    else:
        print("%s: %d groups, %d requests, %d constraints, %d params\n"
              % (a.slvs, len(d["groups"]), len(d["requests"]), len(d["constraints"]), len(d["params"])))
        print("%-5s %-11s %-26s %4s %5s  %s" % ("group", "type", "name", "reqs", "cons", "detail"))
        for h, t, n, det, nr, nc in summary(d):
            print("%-5x %-11s %-26s %4d %5d  %s" % (h, t, n, nr, nc, det))
