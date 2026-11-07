"""Write SolveSpace .slvs files programmatically.

The .slvs format is a flat list of "Key=value" lines terminated by an
AddGroup / AddParam / AddRequest / AddConstraint marker.  Entities are NOT
written: SolveSpace regenerates them from the groups + requests on load
(src/file.cpp, ReadSketchFile: "entities are regenerated").  Params ARE
written -- on load they only seed the solver's initial guess, so every param
we emit must already hold the value we want, or a sketch with slack will
settle somewhere else.

Handle arithmetic (src/sketch.h):
    request r -> entity  (r<<16)|i ;  param (r<<16)|i
    group   g -> entity  0x80000000|(g<<16)|i ; param likewise
    point i of a request: entity (r<<16)|(i+1), params (r<<16)|(16+3i+k)
Reference requests 1,2,3 are the XY/YZ/ZX planes; group 1 is #references.
"""
import math

MAGIC = b"\xb1\xb2\xb3SolveSpaceREVa\n\n"

# Group.type
DRAWING_3D, DRAWING_WORKPLANE, EXTRUDE = 5000, 5001, 5100
# Group.subtype
WORKPLANE_BY_POINT_ORTHO = 6000
ONE_SIDED, TWO_SIDED = 7000, 7001
# Group.meshCombine
UNION, DIFFERENCE, ASSEMBLE, INTERSECTION = 0, 1, 2, 3
# Request.type
REQ_WORKPLANE, REQ_DATUM_POINT, REQ_LINE_SEGMENT = 100, 101, 200
REQ_CIRCLE, REQ_ARC, REQ_TTF_TEXT = 400, 500, 600
# Constraint.type
PT_PT_DISTANCE, PT_PLANE_DISTANCE = 30, 31
POINTS_COINCIDENT = 20
PT_IN_PLANE, PT_ON_LINE = 41, 42
AT_MIDPOINT = 70
ANGLE, PARALLEL, PERPENDICULAR = 120, 121, 122
EQUAL_LENGTH_LINES, EQUAL_RADIUS = 50, 130
SYMMETRIC_HORIZ, SYMMETRIC_VERT = 61, 62
HORIZONTAL, VERTICAL = 80, 81
DIAMETER = 90
ARC_LINE_TANGENT = 123
WHERE_DRAGGED = 200

HREQ_XY, HREQ_YZ, HREQ_ZX = 1, 2, 3
HGROUP_REFERENCES = 1
# The three reference workplanes.  ForceReferences() fixes their quaternions,
# so: XY has normal +z, YZ has normal +x, ZX has normal +y -- which is what makes
# PT_PLANE_DISTANCE against them read as a point's z, x and y respectively.
ENT_XY_WORKPLANE = (HREQ_XY << 16) | 0
ENT_YZ_WORKPLANE = (HREQ_YZ << 16) | 0
ENT_ZX_WORKPLANE = (HREQ_ZX << 16) | 0
ENT_ORIGIN       = (HREQ_XY << 16) | 1


def quat_from_uv(u, v):
    """Quaternion (w,vx,vy,vz) whose rotation maps x->u, y->v, z->u x v."""
    def norm(a):
        m = math.sqrt(sum(c * c for c in a))
        return [c / m for c in a]
    u = norm(u); v = norm(v)
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    n = norm(n)
    # columns of the rotation matrix are u, v, n
    m = [[u[0], v[0], n[0]], [u[1], v[1], n[1]], [u[2], v[2], n[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        w = (m[2][1] - m[1][2]) / s; x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s; z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        w = (m[0][2] - m[2][0]) / s; x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s; z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
        w = (m[1][0] - m[0][1]) / s; x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s; z = 0.25 * s
    if w < 0:
        w, x, y, z = -w, -x, -y, -z
    return (w, x, y, z)


class Sketch:
    def __init__(self):
        self.lines = []
        self.next_group = 2        # 1 is #references
        self.next_request = 4      # 1..3 are the reference planes
        self.next_constraint = 1
        self.params = []           # (handle, value)
        # bookkeeping for dof_report(); none of it is written to the file
        self._pt = {}              # point entity -> dict(group, wp, params)
        self._line = {}            # line entity  -> (ptA, ptB)
        self._arc = {}             # arc entity   -> (centre, start, end)
        self._cons = []            # dicts, in emission order
        self.group_names = {}      # group handle -> name
        self._extrude_groups = []  # handles, for dof_report
        self._wp = {}              # workplane entity -> frame, for dof_report
        self._text = {}            # text entity -> aspect + its 4 points
        self._emit_references()

    # ---------- low level record emission ----------
    def _rec(self, marker, fields):
        for k, v in fields:
            if v is None:
                continue
            self.lines.append("%s=%s" % (k, v))
        self.lines.append(marker)
        self.lines.append("")

    @staticmethod
    def f(x):
        return "%.20f" % x

    @staticmethod
    def x(h):
        return "%08x" % h

    # ---------- references ----------
    def _emit_references(self):
        self._rec("AddGroup", [
            ("Group.h.v", self.x(HGROUP_REFERENCES)),
            ("Group.type", DRAWING_3D),
            ("Group.name", "#references"),
            ("Group.color", "ff000000"),
            ("Group.visible", 1),
            ("Group.scale", self.f(1.0)),
            ("Group.remap", "{\n}"),
        ])
        for h in (HREQ_XY, HREQ_YZ, HREQ_ZX):
            self._rec("AddRequest", [
                ("Request.h.v", self.x(h)),
                ("Request.type", REQ_WORKPLANE),
                ("Request.group.v", self.x(HGROUP_REFERENCES)),
                ("Request.construction", 0),
            ])

    # ---------- groups ----------
    def group_3d(self, name, visible=True):
        g = self.next_group; self.next_group += 1
        self.group_names[g] = name
        self._rec("AddGroup", [
            ("Group.h.v", self.x(g)),
            ("Group.type", DRAWING_3D),
            ("Group.order", g - 1),
            ("Group.name", name),
            ("Group.color", "ff000000"),
            ("Group.visible", 1 if visible else 0),
            ("Group.scale", self.f(1.0)),
            ("Group.remap", "{\n}"),
        ])
        return g

    def workplane_group(self, name, origin_entity, u, v, visible=True):
        """A DRAWING_WORKPLANE group whose plane passes through `origin_entity`
        with in-plane axes u (sketch +x) and v (sketch +y)."""
        g = self.next_group; self.next_group += 1
        self.group_names[g] = name
        q = quat_from_uv(u, v)
        self._rec("AddGroup", [
            ("Group.h.v", self.x(g)),
            ("Group.type", DRAWING_WORKPLANE),
            ("Group.order", g - 1),
            ("Group.name", name),
            ("Group.activeWorkplane.v", self.x(0x80000000 | (g << 16) | 0)),
            ("Group.color", "ff000000"),
            ("Group.subtype", WORKPLANE_BY_POINT_ORTHO),
            ("Group.predef.q.w", self.f(q[0])),
            ("Group.predef.q.vx", self.f(q[1])),
            ("Group.predef.q.vy", self.f(q[2])),
            ("Group.predef.q.vz", self.f(q[3])),
            ("Group.predef.origin.v", self.x(origin_entity)),
            ("Group.visible", 1 if visible else 0),
            ("Group.scale", self.f(1.0)),
            ("Group.remap", "{\n}"),
        ])
        wp = 0x80000000 | (g << 16) | 0
        self._wp[wp] = {"origin": origin_entity, "u": u, "v": v}
        return g, wp

    @staticmethod
    def workplane_origin(g):
        """The POINT_N_COPY a DRAWING_WORKPLANE group makes at predef.origin
        (Group::Generate puts it at h.entity(2)); handy as a sketch datum."""
        return 0x80000000 | (g << 16) | 2

    def extrude(self, name, sketch_group, vec, combine=UNION,
                subtype=ONE_SIDED, color="00646464", visible=True):
        """vec is HALF the extrusion for ONE_SIDED (bottom at the sketch
        plane, top at sketch + 2*vec) -- see Group::Generate, ai=0 af=2."""
        g = self.next_group; self.next_group += 1
        self._rec("AddGroup", [
            ("Group.h.v", self.x(g)),
            ("Group.type", EXTRUDE),
            ("Group.order", g - 1),
            ("Group.name", name),
            ("Group.opA.v", self.x(sketch_group)),
            ("Group.color", color),
            ("Group.subtype", subtype),
            ("Group.meshCombine", combine),
            ("Group.visible", 1 if visible else 0),
            ("Group.scale", self.f(1.0)),
            ("Group.remap", "{\n}"),
        ])
        base = 0x80000000 | (g << 16)
        for i in range(3):
            self.params.append((base | i, vec[i]))
        self._extrude_groups.append(g)
        return g

    # ---------- requests ----------
    def _request(self, rtype, group, workplane, pts, construction=False, extra=()):
        r = self.next_request; self.next_request += 1
        self._rec("AddRequest", [
            ("Request.h.v", self.x(r)),
            ("Request.type", rtype),
            ("Request.workplane.v", self.x(workplane) if workplane else None),
            ("Request.group.v", self.x(group)),
            ("Request.construction", 1 if construction else 0),
        ] + list(extra))
        for i, p in enumerate(pts):
            ph = []
            for k, val in enumerate(p):
                h = (r << 16) | (16 + 3 * i + k)
                self.params.append((h, val))
                ph.append(h)
            ent = (r << 16) | (i + (0 if rtype == REQ_DATUM_POINT else 1))
            self._pt[ent] = {"group": group, "wp": workplane, "params": ph}
        return r

    def datum_point(self, group, xyz):
        """DATUM_POINT free in 3D. Its point entity is (r<<16)|0."""
        r = self._request(REQ_DATUM_POINT, group, None, [xyz])
        return r, (r << 16) | 0

    def line(self, group, workplane, a, b, construction=False):
        """-> (line entity, point A entity, point B entity).  The request's own
        entity is (r<<16)|0; its points start at 1 (Request::Generate)."""
        r = self._request(REQ_LINE_SEGMENT, group, workplane, [a, b], construction)
        self._line[(r << 16) | 0] = ((r << 16) | 1, (r << 16) | 2)
        return (r << 16) | 0, (r << 16) | 1, (r << 16) | 2

    def arc(self, group, workplane, center, start, end, construction=False):
        """Counter-clockwise from `start` to `end` about `center`
        (EntityBase::ArcGetAngles normalises dtheta into (0, 2pi])."""
        r = self._request(REQ_ARC, group, workplane, [center, start, end], construction)
        self._arc[(r << 16) | 0] = ((r << 16) | 1, (r << 16) | 2, (r << 16) | 3)
        return (r << 16) | 0, (r << 16) | 1, (r << 16) | 2, (r << 16) | 3

    def text(self, group, workplane, string, font, bot_left, height, aspect,
             kerning=False):
        """A TrueType text request.  -> (entity, top-left pt, bottom-left pt).

        SolveSpace defines text by two free points: point[0] is the TOP-left and
        point[1] the BOTTOM-left of the first glyph, so their separation is the
        font's cap height (everything is scaled by 1/capHeight, see
        TtfFont::PlotString).  The text runs along (v x normal), i.e. along +u
        when v is up, and is `aspect` cap-heights long.  Points 2 and 3 (the
        bottom-right and top-right of the box) are not free: SolveSpace
        generates four equations pinning them to the first two (see
        EntityBase::GenerateEquations), so they are seeded here and cost no
        degrees of freedom.

        `aspect` must be the font's true advance-width/cap-height ratio for
        this string -- text_fit.measure() gets it from SolveSpace itself --
        because a wrong seed leaves points 2/3 off their equations.
        """
        ox, oy = bot_left
        tl = (ox, oy + height)
        br = (ox + height * aspect, oy)
        tr = (ox + height * aspect, oy + height)
        r = self._request(REQ_TTF_TEXT, group, workplane, [tl, bot_left, br, tr],
                          extra=[("Request.str", string),
                                 ("Request.font", font),
                                 ("Request.aspectRatio", self.f(aspect)),
                                 ("Request.extraPoints", 1 if kerning else None)])
        ent = (r << 16) | 0
        pts = [(r << 16) | i for i in (1, 2, 3, 4)]
        self._text[ent] = {"aspect": aspect, "pts": pts}
        return ent, pts[0], pts[1]

    # ---------- constraints ----------
    def constraint(self, ctype, group, workplane=None, valA=None, ptA=None, ptB=None,
                   entityA=None, entityB=None, entityC=None, entityD=None,
                   other=False, other2=False, disp=(5.0, 5.0, 0.0)):
        c = self.next_constraint; self.next_constraint += 1
        self._cons.append({"h": c, "type": ctype, "group": group,
                           "wp": workplane, "valA": valA, "ptA": ptA, "ptB": ptB,
                           "entityA": entityA, "entityB": entityB,
                           "other": other})
        self._rec("AddConstraint", [
            ("Constraint.h.v", self.x(c)),
            ("Constraint.type", ctype),
            ("Constraint.group.v", self.x(group)),
            ("Constraint.workplane.v", self.x(workplane) if workplane else None),
            ("Constraint.valA", self.f(valA) if valA is not None else None),
            ("Constraint.ptA.v", self.x(ptA) if ptA else None),
            ("Constraint.ptB.v", self.x(ptB) if ptB else None),
            ("Constraint.entityA.v", self.x(entityA) if entityA else None),
            ("Constraint.entityB.v", self.x(entityB) if entityB else None),
            ("Constraint.entityC.v", self.x(entityC) if entityC else None),
            ("Constraint.entityD.v", self.x(entityD) if entityD else None),
            ("Constraint.other", 1 if other else 0),
            ("Constraint.other2", 1 if other2 else 0),
            ("Constraint.reference", 0),
            ("Constraint.disp.offset.x", self.f(disp[0])),
            ("Constraint.disp.offset.y", self.f(disp[1])),
            ("Constraint.disp.offset.z", self.f(disp[2])),
        ])
        return c

    def lock_point(self, group, pt, xyz):
        """Pin a 3D point with three dimensions, one per reference plane, so
        the critical heights live in editable constraints instead of only in
        the seeded Param values."""
        for value, plane in zip(xyz, (ENT_YZ_WORKPLANE, ENT_ZX_WORKPLANE,
                                      ENT_XY_WORKPLANE)):
            if abs(value) < 1e-12:
                self.constraint(PT_IN_PLANE, group, ptA=pt, entityA=plane)
            else:
                self.constraint(PT_PLANE_DISTANCE, group, valA=value,
                                ptA=pt, entityA=plane)

    # ---------- output ----------
    def write(self, path):
        body = []
        # groups + requests + constraints were appended in call order already;
        # params must be emitted too.  Record order in the file does not matter
        # to the loader, but keep params after the groups/requests that own them.
        out = "\n".join(self.lines) + "\n"
        pm = []
        for h, val in self.params:
            pm.append("Param.h.v.=%s" % self.x(h))
            pm.append("Param.val=%s" % self.f(val))
            pm.append("AddParam")
            pm.append("")
        with open(path, "wb") as fh:
            fh.write(MAGIC)
            fh.write(out.encode("utf-8"))
            fh.write(("\n".join(pm) + "\n").encode("utf-8"))


# ---------------------------------------------------------------------------
# Degree-of-freedom analysis
#
# Why this exists: SolveSpace regenerates a file happily, exports a correct
# mesh and prunes nothing, and STILL open in the GUI showing "unsolvable
# constraints" -- because the seeded Param values already satisfy a system
# that is simultaneously redundant and under-determined.  Neither
# `solvespace-cli regenerate` nor the exported mesh can see that.  This can.
#
# It rebuilds each group's equations from what the writer emitted, takes a
# numeric Jacobian at the seeded solution, and row-reduces it.  Then:
#     redundant = equations - rank     (constraints the GUI will complain about)
#     dof       = unknowns  - rank     (what is still free to drag)
# A healthy sketch has both at zero.
# ---------------------------------------------------------------------------
import math as _math

# the three reference planes, as (normal, offset)
_REF_PLANES = {
    ENT_XY_WORKPLANE: ((0.0, 0.0, 1.0), 0.0),
    ENT_YZ_WORKPLANE: ((1.0, 0.0, 0.0), 0.0),
    ENT_ZX_WORKPLANE: ((0.0, 1.0, 0.0), 0.0),
}


def _rank(rows, ncol, tol=1e-7):
    """Rank by Gaussian elimination with partial pivoting.  The matrix is at
    most a few dozen square, so there is no reason to be clever."""
    m = [list(r) for r in rows]
    rank, row = 0, 0
    for col in range(ncol):
        piv, best = None, tol
        for i in range(row, len(m)):
            if abs(m[i][col]) > best:
                piv, best = i, abs(m[i][col])
        if piv is None:
            continue
        m[row], m[piv] = m[piv], m[row]
        pv = m[row][col]
        for i in range(row + 1, len(m)):
            if m[i][col]:
                f = m[i][col] / pv
                for j in range(col, ncol):
                    m[i][j] -= f * m[row][j]
        row += 1
        rank += 1
        if row == len(m):
            break
    return rank


class _Eval:
    """Evaluates one group's equations for a given param vector."""

    def __init__(self, sk, group):
        self.sk = sk
        self.group = group
        self.base = dict(sk.params)
        self.unknown = []          # param handles owned by this group
        seen = set()
        for ent, d in sk._pt.items():
            if d["group"] != group:
                continue
            for h in d["params"]:
                if h not in seen:
                    seen.add(h)
                    self.unknown.append(h)
        self.index = {h: i for i, h in enumerate(self.unknown)}

    # -- coordinate access -------------------------------------------------
    def uv(self, ent, x):
        """A point's (u, v) in its workplane.  A workplane group's own origin
        copy (handle |2) sits at the sketch origin and has no params."""
        d = self.sk._pt.get(ent)
        if d is None:
            return (0.0, 0.0)
        return tuple(self.val(h, x) for h in d["params"][:2])

    def xyz(self, ent, x):
        """A point's 3D position.  A sketch point only has (u, v), so it has to
        be lifted through its workplane's frame -- which is what lets a plane
        constraint (PT_PLANE_DISTANCE) pin a point drawn in a 2D sketch."""
        d = self.sk._pt.get(ent)
        if d is None:
            return (0.0, 0.0, 0.0)
        if len(d["params"]) >= 3:
            return tuple(self.val(h, x) for h in d["params"][:3])
        wp = self.sk._wp[d["wp"]]
        o = self.xyz(wp["origin"], x)
        u, v = (self.val(h, x) for h in d["params"][:2])
        return tuple(o[i] + u * wp["u"][i] + v * wp["v"][i] for i in range(3))

    def val(self, h, x):
        i = self.index.get(h)
        return x[i] if i is not None else self.base[h]

    def line_dir(self, ent, x):
        a, b = self.sk._line[ent]
        pa, pb = self.uv(a, x), self.uv(b, x)
        return (pb[0] - pa[0], pb[1] - pa[1])

    # -- the equations -----------------------------------------------------
    def residuals(self, x):
        sk, g = self.sk, self.group
        out = []
        # an arc carries its own equation: both ends the same distance out
        for ent, (c, s, e) in sk._arc.items():
            if sk._pt[c]["group"] != g:
                continue
            pc, ps, pe = self.uv(c, x), self.uv(s, x), self.uv(e, x)
            out.append(_math.hypot(ps[0] - pc[0], ps[1] - pc[1]) -
                       _math.hypot(pe[0] - pc[0], pe[1] - pc[1]))
        # text carries four equations of its own: its bottom-right and
        # top-right corners are functions of the two free points and the
        # aspect ratio (EntityBase::GenerateEquations / RectGetPointsExprs).
        # The perpendicular to the height vector, scaled by the aspect ratio,
        # is the baseline.
        for ent, d in sk._text.items():
            tl, bl, br, tr = d["pts"]
            if sk._pt[tl]["group"] != g:
                continue
            a, o = self.uv(tl, x), self.uv(bl, x)
            eu = (a[0] - o[0], a[1] - o[1])
            ev = (eu[1] * d["aspect"], -eu[0] * d["aspect"])
            b, cc = self.uv(br, x), self.uv(tr, x)
            out += [b[0] - (o[0] + ev[0]), b[1] - (o[1] + ev[1]),
                    cc[0] - (o[0] + eu[0] + ev[0]), cc[1] - (o[1] + eu[1] + ev[1])]
        for c in sk._cons:
            if c["group"] != g:
                continue
            t, va = c["type"], c["valA"] or 0.0
            if t == POINTS_COINCIDENT:
                a, b = self.uv(c["ptA"], x), self.uv(c["ptB"], x)
                out += [a[0] - b[0], a[1] - b[1]]
            elif t == HORIZONTAL:
                if c["entityA"]:
                    a, b = sk._line[c["entityA"]]
                else:
                    a, b = c["ptA"], c["ptB"]
                out.append(self.uv(a, x)[1] - self.uv(b, x)[1])
            elif t == VERTICAL:
                # VERTICAL takes either a line, or two points
                if c["entityA"]:
                    a, b = sk._line[c["entityA"]]
                else:
                    a, b = c["ptA"], c["ptB"]
                out.append(self.uv(a, x)[0] - self.uv(b, x)[0])
            elif t == PT_PT_DISTANCE:
                a, b = self.uv(c["ptA"], x), self.uv(c["ptB"], x)
                out.append(_math.hypot(a[0] - b[0], a[1] - b[1]) - va)
            elif t == SYMMETRIC_HORIZ:
                a, b = self.uv(c["ptA"], x), self.uv(c["ptB"], x)
                out += [a[1] - b[1], a[0] + b[0]]
            elif t == SYMMETRIC_VERT:
                a, b = self.uv(c["ptA"], x), self.uv(c["ptB"], x)
                out += [a[0] - b[0], a[1] + b[1]]
            elif t == AT_MIDPOINT:
                p = self.uv(c["ptA"], x)
                a, b = sk._line[c["entityA"]]
                pa, pb = self.uv(a, x), self.uv(b, x)
                out += [p[0] - (pa[0] + pb[0]) / 2.0,
                        p[1] - (pa[1] + pb[1]) / 2.0]
            elif t == PT_ON_LINE:
                p = self.uv(c["ptA"], x)
                a, b = sk._line[c["entityA"]]
                pa, pb = self.uv(a, x), self.uv(b, x)
                out.append((pb[0] - pa[0]) * (p[1] - pa[1]) -
                           (pb[1] - pa[1]) * (p[0] - pa[0]))
            elif t == ARC_LINE_TANGENT:
                cen, s, e = sk._arc[c["entityA"]]
                pe = self.uv(e if c["other"] else s, x)
                pc = self.uv(cen, x)
                d = self.line_dir(c["entityB"], x)
                out.append(d[0] * (pc[0] - pe[0]) + d[1] * (pc[1] - pe[1]))
            elif t == EQUAL_RADIUS:
                r = []
                for ent in (c["entityA"], c["entityB"]):
                    cen, s, _ = sk._arc[ent]
                    pc, ps = self.uv(cen, x), self.uv(s, x)
                    r.append(_math.hypot(ps[0] - pc[0], ps[1] - pc[1]))
                out.append(r[0] - r[1])
            elif t == DIAMETER:
                cen, s, _ = sk._arc[c["entityA"]]
                pc, ps = self.uv(cen, x), self.uv(s, x)
                out.append(2 * _math.hypot(ps[0] - pc[0], ps[1] - pc[1]) - va)
            elif t == ANGLE:
                da = self.line_dir(c["entityA"], x)
                db = self.line_dir(c["entityB"], x)
                if c["other"]:
                    da = (-da[0], -da[1])
                ma = _math.hypot(*da) or 1e-12
                mb = _math.hypot(*db) or 1e-12
                dot = (da[0] * db[0] + da[1] * db[1]) / (ma * mb)
                out.append(dot - _math.cos(_math.radians(va)))
            elif t in (PT_IN_PLANE, PT_PLANE_DISTANCE):
                n, d0 = _REF_PLANES[c["entityA"]]
                p = self.xyz(c["ptA"], x)
                out.append(sum(n[i] * p[i] for i in range(3)) - d0 - va)
            else:
                raise ValueError("dof_report: constraint type %d not modelled" % t)
        return out


def dof_report(sk, names=None):
    """-> list of dicts, one per group that owns params.

    `names` maps group handle -> name, purely for the printout.
    """
    rows = []
    groups = []
    for d in sk._pt.values():
        if d["group"] not in groups:
            groups.append(d["group"])
    for g in sorted(groups):
        ev = _Eval(sk, g)
        n = len(ev.unknown)
        if n == 0:
            continue
        x0 = [ev.base[h] for h in ev.unknown]
        f0 = ev.residuals(x0)
        if not f0:
            rows.append({"group": g, "name": (names or {}).get(g, str(g)),
                         "unknowns": n, "equations": 0, "rank": 0,
                         "dof": n, "redundant": 0, "residual": 0.0})
            continue
        jac = []
        for j in range(n):
            step = 1e-6 * max(1.0, abs(x0[j]))
            xp = list(x0); xp[j] += step
            xm = list(x0); xm[j] -= step
            fp, fm = ev.residuals(xp), ev.residuals(xm)
            jac.append([(fp[i] - fm[i]) / (2 * step) for i in range(len(f0))])
        # jac is columns; transpose to rows = equations
        mat = [[jac[j][i] for j in range(n)] for i in range(len(f0))]
        r = _rank(mat, n)
        rows.append({"group": g, "name": (names or {}).get(g, str(g)),
                     "unknowns": n, "equations": len(f0), "rank": r,
                     "dof": n - r, "redundant": len(f0) - r,
                     "residual": max(abs(v) for v in f0)})
    return rows


def print_dof_report(sk, names=None):
    """Prints the report; returns True if every group is clean.

    Extrude groups are listed too, with the 3 degrees of freedom of their
    extrusion vector.  That is not a defect -- SolveSpace extrude depth is a
    dragged param unless you constrain it against the extrude's own remapped
    top-face entities -- but it should be visible rather than quietly left
    out of the table.
    """
    rows = dof_report(sk, names)
    print("  %-22s %8s %6s %5s %4s %5s %10s" %
          ("group", "unknowns", "eqs", "rank", "dof", "redun", "residual"))
    ok = True
    for r in rows:
        bad = r["dof"] or r["redundant"] or r["residual"] > 1e-7
        ok = ok and not bad
        print("  %-22s %8d %6d %5d %4d %5d %10.2e%s" %
              (r["name"], r["unknowns"], r["equations"], r["rank"],
               r["dof"], r["redundant"], r["residual"],
               "   <-- " + ", ".join(
                   ([] if not r["dof"] else ["%d dof left" % r["dof"]]) +
                   ([] if not r["redundant"] else
                    ["%d redundant" % r["redundant"]]) +
                   ([] if r["residual"] <= 1e-7 else ["not at a solution"]))
               if bad else ""))
    n = len(sk._extrude_groups)
    if n:
        print("  %-22s %8d %6d %5d %4d %5d %10s   (extrusion vectors, free "
              "by design)" % ("%d extrude groups" % n, 3 * n, 0, 0, 3 * n, 0, "-"))
    return ok
