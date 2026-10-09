"""The chair opposite, seen from the protagonist's seat: a corner wall, an empty bentwood chair, the persimmon coat
that gets draped over it, and the near edge of our own table. World sheet 2560x1440.

The chair is built as a small 3-D model (cm) and projected through one seated-eye camera, so that the hoops, the seat
ellipse, the legs and the ring stretcher agree with each other; the same camera lays the herringbone floor and the
adjoining wall. Only the line wobbles, not the construction."""
import math

import cv2
import numpy as np

from kit import *

W, H = 2560, 1440
CHAIR = (1280, 900)            # where the chair anchor (seat centre) goes on the world sheet
DADO_Y, FLOOR_Y = 700, 1085
CORNER_X = 2150                # the room corner; the adjoining wall is to the right of it
POOL = (1290, 370, 620)        # lamp pool on the plaster behind the chair
SW, SH = 1000, 1300            # chair sprite sheet
SA = (470, 690)                # seat centre on it
LIGHT = np.array([-0.55, -0.835])   # toward the light on the page: window to the left, lamp above

# ---------------------------------------------------------------- camera (cm; X right, Y up, Z toward the viewer)
EYE_H, EYE_D, PITCH = 112.0, 165.0, math.radians(17.0)
SEAT_H, SEAT_R = 46.0, 20.5
_C, _S = math.cos(PITCH), math.sin(PITCH)
_ZC0 = EYE_D * _C + (EYE_H - SEAT_H) * _S
F = 430.0 / (2 * SEAT_R) * _ZC0
_Y0 = F * (-EYE_D * _S + (EYE_H - SEAT_H) * _C) / _ZC0
VP_Y = -F * math.tan(PITCH) - _Y0          # horizon of the floor's depth lines, relative to the seat centre


def proj(p, org=(0.0, 0.0)):
    """Chair-space points (...,3) -> page px (seat centre at org), and the local scale in px/cm."""
    p = np.asarray(p, np.float64)
    zw, h = EYE_D - p[..., 2], EYE_H - p[..., 1]
    zc = zw * _C + h * _S
    yc = -zw * _S + h * _C
    return np.stack([org[0] + F * p[..., 0] / zc, org[1] + F * yc / zc - _Y0], -1), F / zc


def floor_z(y_rel):
    """Chair-space z of the floor point on the centre line that lands at page y (relative to the seat centre)."""
    t = (y_rel + _Y0) / F
    # t = (-zw*S + H*C) / (zw*C + H*S)
    zw = EYE_H * (_C - t * _S) / (t * _C + _S)
    return EYE_D - zw


WALL_Z = floor_z(FLOOR_Y - CHAIR[1])       # the wall behind the chair


# ---------------------------------------------------------------- small helpers
def stamp(s, P, Rr):
    m = np.zeros((s.h, s.w), np.uint8)
    for (x, y), rr in zip(P, Rr):
        cv2.circle(m, (int(round(x * 16)), int(round(y * 16))), max(1, int(round(rr * 16))), 255, -1, cv2.LINE_AA, 4)
    return m.astype(np.float32) / 255


def fill(s, P):
    m = np.zeros((s.h, s.w), np.uint8)
    cv2.fillPoly(m, [np.round(np.asarray(P) * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
    return m.astype(np.float32) / 255


def shift(s, m, dx, dy, blur=0.0, scale=1.0, about=(0, 0)):
    M = np.float32([[scale, 0, dx + about[0] * (1 - scale)], [0, scale, dy + about[1] * (1 - scale)]])
    o = cv2.warpAffine(m, M, (s.w, s.h))
    return cv2.GaussianBlur(o, (0, 0), blur) if blur > 0 else o


def pen(s, P, r, w=2.2, color=SEPIA, k=1.5, lo=160, hi=420, jit=0.6, **kw):
    """A long curve drawn the way a hand does it: several strokes, each restarting a little before or after the last
    one stopped (so the line doubles in places and gaps in others), each a hair off the one before."""
    P = resample(np.asarray(P, np.float64), 3.0)
    n, i = len(P), 0
    while i < n - 3:
        j = min(n, i + int(r.uniform(lo, hi) / 3))
        if n - j < 10:
            j = n
        s.ink(P[i:j] + r.normal(0, jit, 2), w * r.uniform(0.85, 1.15), color, k * r.uniform(0.85, 1.1), smooth=False, **kw)
        if j >= n:
            break
        i = max(i + 4, j + int(r.integers(-9, 5)))


def offset(P, d):
    """The curve P pushed sideways by d px (d may vary along it)."""
    g = np.gradient(P, axis=0)
    n = np.stack([-g[:, 1], g[:, 0]], 1)
    n /= np.hypot(n[:, 0], n[:, 1])[:, None] + 1e-9
    return P + n * (np.asarray(d, np.float64).reshape(-1, 1) if np.ndim(d) else d)


# ---------------------------------------------------------------- the chair: geometry
def _back_z(x, y):
    """The back wraps a little round the sitter (it follows the seat ring where it is screwed on) and leans away."""
    t = float(sstep(SEAT_H - 2, SEAT_H + 38, y))
    wrap = math.sqrt(max(1.0, 21.7 ** 2 - x * x))
    flat = 12.6 + 5.4 * (1 - (x / 19.5) ** 2)
    return -((1 - t) * wrap + t * flat) - 0.15 * (y - SEAT_H + 2)


def _hoop(xb, xa, yc, ya, y0=SEAT_H - 2.0, n=13):
    """One bent loop of the back, left foot-of-loop up over the top and down to the right: [(x, y, z)]."""
    pts = []
    for y in np.linspace(y0, yc, 6, endpoint=False):
        pts.append((-(xb + (xa - xb) * float(sstep(y0, yc, y))), y))
    for a in np.linspace(math.pi, 0, n):
        pts.append((xa * math.cos(a), yc + ya * math.sin(a)))
    for y in np.linspace(y0, yc, 6, endpoint=False)[::-1]:
        pts.append((xb + (xa - xb) * float(sstep(y0, yc, y)), y))
    return [(x, y, _back_z(x, y)) for x, y in pts]


def _rod(ctrl, rad, org):
    """3-D control points + radius (cm) at each -> page centre line P (N,2) and half-width R (N,) in px."""
    c = np.asarray([tuple(p) + (rr,) for p, rr in zip(ctrl, rad)], np.float64)
    sp = spline(c, False, 0.35)
    P, sc = proj(sp[:, :3], org)
    Rr = sp[:, 3] * sc
    L = arclen(P)
    u = np.linspace(0, L[-1], max(8, int(L[-1] / 1.5)))
    return np.stack([np.interp(u, L, P[:, 0]), np.interp(u, L, P[:, 1])], 1), np.interp(u, L, Rr)


def chair_geo(org):
    g = {}
    # outer loop: back foot - seat - over the top - seat - back foot, one rod
    oh = _hoop(18.7, 19.3, 76.5, 19.0)
    # below the seat the same rod is the back leg: it draws in a little to meet the ring, then kicks out to the foot
    leg = [(21.0, 0.0, -25.0), (19.2, 13, -20.4), (17.7, 28, -14.8), (18.0, 38, -12.0)]
    legl = [(-x, y, z) for x, y, z in leg]
    legr = leg
    ctrl = legl + oh + legr[::-1]
    rad = []
    for (x, y, z) in ctrl:
        rad.append(1.12 + 0.48 * float(sstep(0, 40, y)) - 0.16 * float(sstep(62, 90, y)))
    g["outer"] = _rod(ctrl, rad, org)
    ih = _hoop(11.3, 12.1, 73.0, 12.6, y0=SEAT_H - 0.5)
    g["inner"] = _rod(ih, [1.12] * len(ih), org)
    # front legs, a slight sabre curve, tapering to the foot
    for sgn, key in ((-1, "fl"), (1, "fr")):
        ctrl = [(sgn * 12.6, 44.0, 13.2), (sgn * 13.3, 32, 14.2), (sgn * 15.2, 15, 17.0), (sgn * 17.6, 0, 20.4)]
        g[key] = _rod(ctrl, [1.7, 1.6, 1.38, 1.15], org)
    # ring stretcher: a circle through the insides of the four legs
    yr = 27.5
    fx, fz = 13.7, 14.7
    bx, bz = 17.7, -15.0
    zc = (fx * fx + fz * fz - bx * bx - bz * bz) / (2 * (fz - bz))
    Rr = math.hypot(fx, fz - zc) - 2.3
    a = np.linspace(0, 2 * math.pi, 73)
    ring = np.stack([Rr * np.cos(a), np.full_like(a, yr), zc + Rr * np.sin(a)], 1)
    P, sc = proj(ring, org)
    g["ring"] = (P, 0.95 * sc)
    # seat
    a = np.linspace(0, 2 * math.pi, 121)[:-1]
    for key, rr, yy in (("seat_top", SEAT_R, SEAT_H), ("seat_bot", SEAT_R - 0.3, SEAT_H - 3.6), ("seat_in", SEAT_R - 3.9, SEAT_H)):
        g[key] = proj(np.stack([rr * np.cos(a), np.full_like(a, yy), rr * np.sin(a)], 1), org)[0]
    g["scale"] = float(proj((0, SEAT_H, 0))[1])
    return g


def _dense(P, Rr=None, step=1.5):
    L = arclen(P)
    u = np.linspace(0, L[-1], max(8, int(L[-1] / step)))
    Q2 = np.stack([np.interp(u, L, P[:, 0]), np.interp(u, L, P[:, 1])], 1)
    return Q2 if Rr is None else (Q2, np.interp(u, L, Rr))


def chair_masks(s, org):
    """Masks of every part, in painting order (far to near)."""
    g = chair_geo(org)
    m = {}
    footy = max(g["outer"][0][0][1], g["outer"][0][-1][1])
    m["outer"] = stamp(s, *g["outer"]) * (s.Y < footy + 2)
    m["inner"] = stamp(s, *g["inner"])
    P, Rr = _dense(*g["ring"])
    m["ring"] = stamp(s, P, Rr)
    for k in ("fl", "fr"):
        m[k] = stamp(s, *g[k]) * (s.Y < g[k][0][-1][1] + 3)
    hull = cv2.convexHull(np.round(np.vstack([g["seat_top"], g["seat_bot"]]) * 16).astype(np.int32))
    sm = np.zeros((s.h, s.w), np.uint8)
    cv2.fillPoly(sm, [hull], 255, cv2.LINE_AA, 4)
    m["seat"] = sm.astype(np.float32) / 255
    m["seat_top"] = fill(s, g["seat_top"])
    m["cane"] = fill(s, g["seat_in"])
    return g, m


def chair_silhouette(s, org):
    g, m = chair_masks(s, org)
    out = s.zeros()
    for k in ("outer", "inner", "ring", "fl", "fr", "seat"):
        out = np.maximum(out, m[k])
    return out


# ---------------------------------------------------------------- the chair: paint
def _paint_rod(s, r, P, Rr, m, k=0.84, hl=0.72, lo=260, hi=640, clip=None):
    """Dark warm bentwood: umber over burnt sienna, a sepia shade on the side away from the light, the varnish
    highlight lifted back to a warm light along the lit side of the bend, then the pen down both edges."""
    base(s, m, UMBER, k, wob=0.7, edge=0.5, ew=3, flow=0.35, fs=160, gran=0.3)
    s.wash(m, BURNT, 0.40, wob=0.7, soft=1.0, edge=0.2, flow=0.5, fs=110, gran=0.25)
    g = np.gradient(P, axis=0)
    n = np.stack([-g[:, 1], g[:, 0]], 1)
    n /= np.hypot(n[:, 0], n[:, 1])[:, None] + 1e-9
    d = n @ LIGHT
    nl = n * np.sign(d + 1e-9)[:, None]
    st = np.abs(d)
    N = len(P)
    # shade
    sh = stamp(s, P - nl * (Rr * 0.46)[:, None], Rr * 0.58) * m
    s.wash(sh, SEPIA, 0.66, wob=0.6, soft=1.6, edge=0.1, gran=0.3, flow=0.3, fs=60)
    # highlight: the varnish catches the light in long runs, broken where the brush ran dry
    gate = np.clip(1.6 * (0.42 + noise1(N, 260, s._s())), 0, 1)
    wdt = Rr * 0.34 * (0.55 + 0.45 * st) * (0.55 + 0.45 * gate)
    on = cv2.GaussianBlur(stamp(s, P, np.where(gate > 0.08, Rr * 1.2, 0.01)), (0, 0), 2.5)
    hm = stamp(s, P + nl * (Rr * 0.36)[:, None], np.maximum(0.3, wdt)) * m * on
    s.lift(hm, hl, soft=1.0, wob=0.7)
    s.wash(hm, AMBER, 0.20, wob=0.7, soft=1.2, edge=0.3, ew=2)
    # the cool window on the left-facing edge
    left = np.clip(-nl[:, 0], 0, 1) * (nl[:, 0] < -0.5)
    if left.max() > 0:
        cm = stamp(s, P + nl * (Rr * 0.78)[:, None], np.maximum(0.3, Rr * 0.16 * left)) * m * cv2.GaussianBlur(stamp(s, P, np.where(left > 0.3, Rr * 1.2, 0.01)), (0, 0), 2)
        s.lift(cm, 0.30, soft=1.0, wob=0.5)
        s.wash(cm, RAIN, 0.22, wob=0.5, soft=1.2, edge=0)
    # pen
    for sg in (1, -1):
        pen(s, P + n * (Rr * sg * 0.97)[:, None], r, 2.3, SEPIA, 1.55, lo=lo, hi=hi, tremor=0.75, jit=0.5, clip=clip)


def chair():
    s = Sheet(SW, SH, 42)
    r = rs(42)
    g, m = chair_masks(s, SA)
    sc = g["scale"]
    # --- far: the outer loop with the back legs, the inner loop
    _paint_rod(s, r, *g["outer"], m["outer"], lo=420, hi=900)
    _paint_rod(s, r, *g["inner"], m["inner"], k=0.8, lo=420, hi=900)
    # --- ring stretcher
    P, Rr = _dense(*g["ring"])
    _paint_rod(s, r, P, Rr, m["ring"], k=0.84, hl=0.5, lo=260, hi=520)
    # the seat throws its shade on what is under it
    under = shift(s, m["seat"], 10, 70, 22) * np.maximum(m["ring"], m["outer"])
    s.wash(under, SEPIA, 0.55, wob=0, soft=0, edge=0, gran=0.3)
    # --- front legs
    for k in ("fl", "fr"):
        _paint_rod(s, r, *g[k], m[k], lo=300, hi=700)
        s.wash(shift(s, m["seat"], 6, 46, 16) * m[k], SEPIA, 0.6, wob=0, soft=0, edge=0, gran=0.3)
    # --- the seat: a wooden ring with a cane panel let into it
    top, bot, cin = g["seat_top"], g["seat_bot"], g["seat_in"]
    base(s, m["seat"], UMBER, 1.0, wob=0.7, edge=0.5, ew=4, flow=0.4, fs=90, gran=0.45)
    s.wash(m["seat"], BURNT, 0.36, wob=0.7, soft=1, edge=0.2, flow=0.5, fs=120)
    side = m["seat"] * (1 - m["seat_top"])
    s.wash(side, SEPIA, 0.55, wob=0.6, soft=1.2, edge=0.3, grad=s.hgrad(SA[0] - 230, SA[0] + 240, 0.35, 1.0))
    s.wash(m["seat_top"], SEPIA, 0.30, wob=0, soft=0, edge=0, grad=s.hgrad(SA[0] - 60, SA[0] + 230, 0, 1), gran=0.4)
    # varnish sheen on the ring, toward the window and under the lamp
    cx, cy = SA
    rx = 0.5 * (top[:, 0].max() - top[:, 0].min())
    ry = 0.5 * (top[:, 1].max() - top[:, 1].min())
    ringm = m["seat_top"] * (1 - m["cane"])
    sheen = ringm * np.clip(s.rgrad(cx - rx * 0.62, cy + ry * 0.35, 20, rx * 0.75, 1, 0, sy=0.5) + 0.7 * s.rgrad(cx + rx * 0.2, cy - ry * 0.86, 10, rx * 0.5, 1, 0, sy=0.3), 0, 1)
    s.lift(sheen * (0.55 + 0.45 * s.noise(26, 2)), 0.72, soft=1.5, wob=1.0)
    s.wash(sheen, AMBER, 0.20, wob=1, soft=2, edge=0)
    # the front edge catches the light where the top rolls over
    fe = top[(top[:, 1] > cy + ry * 0.25)]
    fe = fe[np.argsort(fe[:, 0])]
    s.lift(stamp(s, fe + (0, 3.5), np.full(len(fe), 2.2)) * s.hgrad(cx - rx, cx + rx * 0.6, 1, 0.15), 0.42, soft=1.2, wob=0.6)
    # cane: straw colour sunk a little below the ring, darker under the back edge of the ring's shadow
    cane = m["cane"]
    base(s, cane, OCHRE, 0.78, wob=0.8, edge=0.55, ew=5, flow=0.5, fs=80, gran=0.5)
    s.wash(cane, SIENNA, 0.42, wob=1, soft=1.5, edge=0.3, flow=0.6, fs=60, gran=0.5)
    s.wash(cane, UMBER, 0.42, wob=0, soft=0, edge=0, grad=np.clip(s.hgrad(cx - 120, cx + rx, 0, 0.8) + s.vgrad(cy + ry * 0.2, cy - ry * 0.8, 0, 0.6), 0, 1), gran=0.5, flow=0.3)
    s.wash(cane * (1 - shift(s, cane, -3, 7)), SEPIA, 0.55, wob=0.5, soft=1.6, edge=0)          # the ring's lip shades it
    s.lift(cane * s.rgrad(cx - rx * 0.30, cy + ry * 0.22, 10, rx * 0.55, 1, 0, sy=0.45), 0.30, soft=0, wob=0)
    # the weave, laid out on the seat plane
    cm = cv2.GaussianBlur(cane, (0, 0), 1.0)
    R0 = SEAT_R - 3.9
    for fam, (ca, sa, kk, ww, gap) in enumerate(((0.7071, 0.7071, 0.75, 1.25, 1.55), (0.7071, -0.7071, 0.75, 1.25, 1.55), (1.0, 0.0, 0.38, 1.0, 1.55), (0.0, 1.0, 0.38, 1.0, 1.55))):
        o = -R0 + r.random() * gap
        while o < R0:
            hl = math.sqrt(max(0.0, R0 * R0 - o * o))
            if hl > 1.2:
                t = np.linspace(-hl, hl, 7)
                p3 = np.stack([ca * t - sa * o, np.full_like(t, SEAT_H - 0.3), sa * t + ca * o], 1)
                s.ink(proj(p3, SA)[0], ww, UMBER if fam < 2 else SEPIA, kk * r.uniform(0.8, 1.15), tremor=0.5, skip=0.22 if fam < 2 else 0.4, clip=cm, taper=(0.03, 0.03), smooth=False)
            o += gap * r.uniform(0.9, 1.1)
    # pen on the seat
    loop = np.vstack([top, top[:14]])
    pen(s, loop, r, 2.5, SEPIA, 1.6, lo=500, hi=900, tremor=0.9)
    pen(s, np.vstack([top[60:], top[:8]]) + (1.5, -1.5), r, 1.4, SEPIA, 0.9, lo=200, hi=400, tremor=0.9, skip=0.25)   # the back edge again
    pen(s, np.vstack([cin, cin[:10]]), r, 1.7, SEPIA, 1.25, lo=300, hi=700, tremor=0.8, skip=0.08)
    fb = bot[(bot[:, 1] > bot[:, 1].mean() - 2)]
    fb = fb[np.argsort(fb[:, 0])]
    il, ir = int(np.argmin(top[:, 0])), int(np.argmax(top[:, 0]))
    fb = np.vstack([top[il] + (0.5, 4), fb, top[ir] + (-0.5, 4)])
    pen(s, fb, r, 2.6, INK, 1.6, lo=400, hi=800, tremor=0.9)
    # the little turned collars where the loops are screwed to the seat ring
    for key, i in (("inner", 0), ("inner", -1)):
        P, Rr = g[key]
        q = P[i]
        s.ink([q + (-Rr[i] * 1.25, -1.5), q + (0, 1.0), q + (Rr[i] * 1.25, -1.5)], 1.8, INK, 1.4)
    s.save("ch_chair", crop=True, anchor=SA)


def chair_sh():
    """The bare chair's shadow: on the wall (the window throws it to the right, the lamp throws it down) and pooled
    on the floor under it. Same sheet and anchor as the chair."""
    s = Sheet(SW, SH, 43)
    sil = chair_silhouette(s, SA)
    fl = SA[1] + (FLOOR_Y - CHAIR[1])
    wall = 1 - sstep(fl - 10, fl + 6, s.Y)
    floor = sstep(fl - 4, fl + 14, s.Y)
    about = (SA[0], fl)
    a = shift(s, sil, 104, 6, 17, 0.90, about) * wall
    s.wash(a, UMBER, 0.34, wob=0, soft=0, edge=0, gran=0.45, flow=0.3, fs=160)
    s.wash(a, PAYNE, 0.26, wob=0, soft=0, edge=0, gran=0.45, flow=0.3, fs=160)
    b = shift(s, sil, 36, 44, 30, 0.92, about) * wall
    s.wash(b, UMBER, 0.30, wob=0, soft=0, edge=0, gran=0.45, flow=0.3, fs=200)
    # on the floor: the legs' shadows run back to the right toward the skirting, and a pool under the seat
    g = chair_geo(SA)
    feet = [g["outer"][0][0], g["outer"][0][-1], g["fl"][0][-1], g["fr"][0][-1]]
    fm = s.zeros()
    for (x, y) in feet:
        tip = (x + 0.62 * (y - fl) + 60, fl + 0.25 * (y - fl))
        fm = np.maximum(fm, s.ribbon([(x, y), ((x + tip[0]) / 2 + 6, (y + tip[1]) / 2), tip], 30, taper=(0, 0.5), smooth=True))
    cxs = SA[0] + 70
    fm = np.maximum(fm, 0.8 * s.ellipse(cxs, fl + 150, 270, 95))
    fm = cv2.GaussianBlur(fm, (0, 0), 22) * floor
    s.wash(fm, SEPIA, 0.6, wob=0, soft=0, edge=0, gran=0.4, flow=0.3, fs=150)
    s.wash(cv2.GaussianBlur(fm, (0, 0), 30) * floor, INKBLUE, 0.25, wob=0, soft=0, edge=0, gran=0.3)
    s.save("ch_chair_sh", crop=True, anchor=SA)


# ---------------------------------------------------------------- the wall and the floor
def _picture(s, r, cx, cy, w, h, rot, frame, motif):
    c, sn = math.cos(rot), math.sin(rot)

    def T(x, y):
        return (cx + x * c - y * sn, cy + x * sn + y * c)

    def box(a, b):
        return [T(-a, -b), T(a, -b), T(a, b), T(-a, b)]
    out = box(w / 2, h / 2)
    om = Q(s, out)
    # shadow on the plaster, down and to the right
    s.wash(shift(s, om, 15, 17, 9), UMBER, 0.42, wob=0, soft=0, edge=0, gran=0.45)
    s.wash(shift(s, om, 7, 8, 3), SEPIA, 0.22, wob=0, soft=0, edge=0, gran=0.3)
    fw = 15 if frame is UMBER else 10
    base(s, om, frame, 1.0 if frame is UMBER else 0.85, wob=1.0, edge=0.5, ew=3, flow=0.4, fs=40)
    s.wash(om, SEPIA if frame is UMBER else SIENNA, 0.4, wob=1, soft=1, edge=0.2, grad=s.hgrad(cx - w / 2, cx + w / 2, 0.2, 1))
    inn = box(w / 2 - fw, h / 2 - fw)
    im = Q(s, inn)
    base(s, im, CREAM, 0.26, wob=1.0, edge=0.35, ew=4, flow=0.4, fs=60)
    s.wash(im, RAIN, 0.16, wob=0, soft=0, edge=0, grad=s.hgrad(cx - w / 2, cx + w / 2, 0, 1))
    s.wash(im * (1 - shift(s, im, 5, 6)), UMBER, 0.45, wob=0.5, soft=2.0, edge=0)       # the frame's lip shades the mat
    mat = fw + min(w, h) * 0.13
    if motif == "ring":       # a cup seen from above: the stain a coffee leaves
        rr = (min(w, h) / 2 - mat) * 0.82
        ox, oy = T(2, 4)
        ring = s.ellipse(ox, oy, rr, rr * 0.97) * (1 - s.ellipse(ox + 2, oy + 1, rr * 0.80, rr * 0.79))
        s.wash(ring, UMBER, 0.85, wob=2.2, edge=0.9, ew=3, gran=0.6, flow=0.7, fs=30)
        s.wash(s.ellipse(ox, oy, rr * 0.8, rr * 0.78), SIENNA, 0.16, wob=2, bleed=5, edge=0.4)
        s.ink(ell(ox, oy, rr * 1.01, rr * 0.98, 0.6, 5.2, 40), 1.4, SEPIA, 0.9, tremor=1.0, skip=0.3)
    else:                     # a cup, side on, three brush marks and a wisp
        a = min(w, h) / 2 - mat
        cup = s.poly([T(-a * 0.62, -a * 0.10), T(a * 0.50, -a * 0.10), T(a * 0.40, a * 0.50), T(a * 0.12, a * 0.72), T(-a * 0.24, a * 0.72), T(-a * 0.52, a * 0.50)])
        s.wash(cup, TEAL, 0.85, wob=1.6, edge=0.7, ew=3, gran=0.5, flow=0.6, fs=30)
        s.stroke([T(a * 0.50, 0.02 * a), T(a * 0.86, 0.12 * a), T(a * 0.80, 0.40 * a), T(a * 0.42, 0.42 * a)], 6, TEAL, 0.8, taper=(0.1, 0.2))
        s.stroke([T(-a * 0.78, a * 0.86), T(0, a * 0.90), T(a * 0.72, a * 0.84)], 5, UMBER, 0.6, dry=0.35)
        s.ink([T(-a * 0.16, -a * 0.30), T(-a * 0.02, -a * 0.52), T(-a * 0.20, -a * 0.74), T(-a * 0.04, -a * 0.95)], 1.6, SLATE, 0.9, tremor=0.8)
        s.ink([T(a * 0.14, -a * 0.28), T(a * 0.26, -a * 0.48), T(a * 0.12, -a * 0.66)], 1.4, SLATE, 0.8, tremor=0.8)
    lc = SEPIA if frame is UMBER else UMBER
    path(s, out, 2.3, INK if frame is UMBER else SEPIA, 1.5, closed=True, over=5, r=r)
    path(s, inn, 1.6, lc, 1.2, closed=True, over=3, r=r)
    s.lift(Q(s, [T(-w / 2 + 3, -h / 2 + 3), T(w / 2 - 6, -h / 2 + 3), T(w / 2 - 6, -h / 2 + 6), T(-w / 2 + 3, -h / 2 + 6)]), 0.35, soft=1.2)
    xs = [p[0] for p in out]
    ys = [p[1] for p in out]
    return [int(min(xs)), int(min(ys)), int(max(xs) + 1), int(max(ys) + 1)]


def _sconce(s, r, x, y):
    """A small wall lamp: brass back plate and swan-neck arm, an enamel dome like the pendants (teal outside, cream
    inside). Its glow is left as paper; the compositor lights it."""
    # warm pool it throws down the plaster
    cone = s.poly([(x - 30, y + 46), (x + 78, y + 46), (x + 250, y + 420), (x - 150, y + 420)], smooth=False)
    s.lift(cv2.GaussianBlur(cone, (0, 0), 38) * s.vgrad(y + 20, y + 440, 1, 0), 0.5, soft=0, wob=0)
    s.wash(cv2.GaussianBlur(cone, (0, 0), 46) * s.vgrad(y + 60, y + 460, 1, 0), AMBER, 0.10, wob=0, soft=0, edge=0, gran=0.3)
    plate = s.ellipse(x - 62, y - 6, 17, 30)
    s.wash(shift(s, plate, 10, 12, 6), UMBER, 0.4, wob=0, soft=0, edge=0)
    base(s, plate, OCHRE, 0.9, wob=0.8, edge=0.5)
    s.wash(plate, SIENNA, 0.5, wob=0.6, soft=1.5, grad=s.vgrad(y - 20, y + 26))
    oval(s, x - 62, y - 6, 17, 30, 2.0, SEPIA, 1.4)
    arm = [(x - 60, y - 8), (x - 44, y - 62), (x - 6, y - 84), (x + 22, y - 62), (x + 24, y - 34)]
    am = s.ribbon(arm, 9)
    s.wash(shift(s, am, 12, 14, 5), UMBER, 0.3, wob=0, soft=0, edge=0)
    base(s, am, OCHRE, 0.95, wob=0.5, edge=0.4)
    s.wash(am, SIENNA, 0.5, wob=0.5, soft=1)
    a = spline(arm, False, 2.0)
    pen(s, offset(a, 4.6), r, 1.7, SEPIA, 1.4, lo=120, hi=260)
    pen(s, offset(a, -4.6), r, 1.7, SEPIA, 1.4, lo=120, hi=260)
    # the dome
    dome = [(x - 52, y + 36), (x - 46, y + 4), (x - 24, y - 22), (x + 6, y - 36), (x + 42, y - 36), (x + 72, y - 22), (x + 94, y + 4), (x + 100, y + 36)]
    dm = np.maximum(s.poly(dome + [(x + 60, y + 44), (x - 10, y + 44)]), s.ellipse(x + 24, y + 36, 76, 13))
    s.wash(shift(s, dm, 20, 20, 10), UMBER, 0.38, wob=0, soft=0, edge=0, gran=0.4)
    base(s, dm, TEAL, 1.05, wob=1.0, edge=0.5, ew=4, flow=0.4, fs=60, gran=0.45)
    s.wash(dm, PRUSSIAN, 0.55, wob=1, bleed=8, edge=0.1, grad=s.hgrad(x - 20, x + 100, 0.1, 1))
    s.lift(s.ribbon([(x - 32, y + 16), (x - 16, y - 10), (x + 6, y - 24)], 9, taper=(0.3, 0.3)), 0.45, soft=2)
    mouth = s.ellipse(x + 24, y + 37, 72, 10)
    base(s, mouth, CREAM, 0.16, wob=0.5, edge=0.3)
    s.wash(mouth, AMBER, 0.22, wob=0.5, soft=2, grad=s.hgrad(x - 40, x + 100, 0.2, 1))
    cap = R(s, x + 12, y - 46, x + 36, y - 34)
    base(s, cap, OCHRE, 0.95, wob=0.5)
    s.wash(cap, SIENNA, 0.5, wob=0.4, soft=1)
    s.ink(dome, 2.3, INKBLUE, 1.5, tremor=0.8)
    oval(s, x + 24, y + 37, 76, 12, 2.0, INKBLUE, 1.4, twice=True)
    path(s, [(x + 12, y - 34), (x + 12, y - 46), (x + 36, y - 46), (x + 36, y - 34)], 1.6, SEPIA, 1.3, over=2, r=r)


def bg():
    s = Sheet(W, H, 41)
    r = rs(41)
    vp = (CHAIR[0], CHAIR[1] + VP_Y)

    def sd(y, x=W + 40):       # a horizontal of the adjoining wall, met at the corner at height y, followed out to x
        return y + (y - vp[1]) * (x - CORNER_X) / (CORNER_X - vp[0])
    XR = W + 40
    wallA = Q(s, [(-30, -30), (CORNER_X, -30), (CORNER_X, DADO_Y + 4), (-30, DADO_Y + 4)])
    wallB = Q(s, [(CORNER_X, -30), (XR, -30), (XR, sd(DADO_Y) + 4), (CORNER_X, DADO_Y + 4)])
    plaster = np.maximum(wallA, wallB)
    px, py, pr = POOL
    # ---- plaster: cream, warmed unevenly with ochre, cooler toward the window on the left
    s.wash(plaster, CREAM, 0.46, wob=0, soft=0, edge=0, gran=0.5, flow=0.55, fs=380)
    s.wash(plaster, OCHRE, 0.20, wob=0, soft=0, edge=0, gran=0.45, flow=0.5, fs=240, grad=0.35 + 0.65 * s.noise(520, 3))
    s.wash(plaster, SIENNA, 0.13, wob=0, soft=0, edge=0, gran=0.5, flow=0.4, fs=300, grad=s.rgrad(px, py, pr * 0.8, pr * 2.6, 0, 1, sy=0.8))
    s.wash(plaster, RAIN, 0.24, wob=0, soft=0, edge=0, gran=0.5, flow=0.5, fs=260, grad=s.hgrad(-200, 1000, 1, 0) * (0.55 + 0.45 * s.noise(300, 3)))
    s.wash(plaster, SLATE, 0.12, wob=0, soft=0, edge=0, gran=0.5, flow=0.4, fs=200, grad=s.hgrad(-100, 620, 1, 0) * s.vgrad(-100, 700, 0.5, 1))
    for i in range(11):        # wet-in-wet blooms: where the brush went back in
        bx, by = r.uniform(0, W), r.uniform(0, DADO_Y - 40)
        col = (OCHRE, SIENNA, CREAM, MIST if bx < 900 else OCHRE)[i % 4]
        s.wash(s.blob(bx, by, r.uniform(120, 300), r.uniform(70, 170), 0.3) * plaster, col, r.uniform(0.05, 0.10), wob=5, bleed=r.uniform(26, 46), edge=0.28, ew=9, gran=0.5)
    for i in range(9):         # the plasterer's float: broad dry sweeps
        x0, y0 = r.uniform(-100, W), r.uniform(20, DADO_Y - 60)
        L, a = r.uniform(300, 700), r.uniform(-0.5, 0.3)
        s.stroke([(x0, y0), (x0 + L * 0.5 * math.cos(a), y0 + L * 0.5 * math.sin(a) - 18), (x0 + L * math.cos(a), y0 + L * math.sin(a))], r.uniform(50, 110), OCHRE if i % 3 else UMBER, r.uniform(0.03, 0.06), dry=r.uniform(0.25, 0.4), edge=0.1, wob=3, bleed=12, clip=plaster, taper=(0.2, 0.3))
    # top corners fall away from the lamp
    s.wash(plaster, UMBER, 0.13, wob=0, soft=0, edge=0, gran=0.5, flow=0.4, fs=300, grad=s.rgrad(px, py + 200, 900, 1900, 0, 1, sy=0.75))
    # the lamp's pool behind the chair: the paper itself
    s.lift(s.rgrad(px, py, pr * 0.12, pr, 1, 0, sy=0.86) * plaster, 0.62, soft=0, wob=0)
    s.wash(s.rgrad(px, py, pr * 0.5, pr * 1.15, 0, 1, sy=0.86) * s.rgrad(px, py, pr * 1.0, pr * 1.6, 1, 0, sy=0.86) * plaster, AMBER, 0.10, wob=0, soft=0, edge=0, gran=0.4)
    # the adjoining wall, turned from the lamp
    s.wash(wallB, UMBER, 0.15, wob=0, soft=0, edge=0, gran=0.5, flow=0.5, fs=160)
    s.wash(wallB, SIENNA, 0.12, wob=0, soft=0, edge=0, gran=0.4, flow=0.4, fs=200, grad=s.hgrad(CORNER_X, W, 1, 0.4))
    s.wash(R(s, CORNER_X - 90, -30, CORNER_X, DADO_Y) , UMBER, 0.10, wob=0, soft=0, edge=0, grad=s.hgrad(CORNER_X - 90, CORNER_X, 0, 1))
    s.hatch(wallB * s.vgrad(40, 520, 1, 0.0) * s.hgrad(CORNER_X, CORNER_X + 260, 1, 0.15), ang=1.15, gap=24, w=1.2, color=UMBER, k=0.5, jit=0.7, skip=0.45)
    # hairline cracks and scuffs
    for (x0, y0, dx, dy) in ((300, 40, 60, 150), (1010, 560, -50, 110), (1860, 30, 30, 120), (640, 610, 120, 40)):
        s.ink([(x0, y0), (x0 + dx * 0.3 + 8, y0 + dy * 0.35), (x0 + dx * 0.55 - 6, y0 + dy * 0.7), (x0 + dx, y0 + dy)], 1.1, UMBER, 0.6, tremor=1.6, skip=0.35)
    s.spatter(26, UMBER, 0.22, box=(0, 0, W, DADO_Y - 20), r=(0.8, 2.6))
    # ---- wainscot: dark teal boards
    wainA = Q(s, [(-30, DADO_Y + 2), (CORNER_X, DADO_Y + 2), (CORNER_X, FLOOR_Y), (-30, FLOOR_Y)])
    wainB = Q(s, [(CORNER_X, DADO_Y + 2), (XR, sd(DADO_Y) + 2), (XR, sd(FLOOR_Y)), (CORNER_X, FLOOR_Y)])
    wain = np.maximum(wainA, wainB)
    s.lift(wain, 1.0, soft=0.8, wob=1.0)
    s.wash(wain, TEAL, 0.98, wob=1.2, edge=0.35, ew=6, gran=0.38, flow=0.5, fs=220)
    s.wash(wain, PRUSSIAN, 0.34, wob=0, soft=0, edge=0, gran=0.3, flow=0.6, fs=160, grad=0.5 + 0.5 * s.noise(260, 3))
    s.wash(wain, UMBER, 0.14, wob=0, soft=0, edge=0, gran=0.3, flow=0.5, fs=120)
    xs = []
    x = -40 + r.uniform(0, 60)
    while x < CORNER_X - 40:
        xs.append(x)
        x += 118 * r.uniform(0.94, 1.06)
    for i, x in enumerate(xs):          # each board takes the wash a little differently
        x1 = xs[i + 1] if i + 1 < len(xs) else CORNER_X
        bm = R(s, x + 3, DADO_Y + 16, x1 - 3, FLOOR_Y - 46)
        s.wash(bm, (PRUSSIAN, TEAL, PAYNE)[i % 3], r.uniform(0.04, 0.26), wob=1.5, soft=1.2, edge=0.5, ew=5, gran=0.5, flow=0.5, fs=90)
    s.wash(wainB, PAYNE, 0.40, wob=0, soft=0, edge=0, gran=0.5, flow=0.4, fs=120)
    # light: the window rakes it from the left, the lamp spills a little behind the chair
    s.lift(wain * s.hgrad(-100, 900, 1, 0) * (0.6 + 0.4 * s.noise(200, 2)), 0.26, soft=0, wob=0)
    s.wash(wain, RAIN, 0.16, wob=0, soft=0, edge=0, grad=s.hgrad(-100, 800, 1, 0))
    s.lift(wain * s.rgrad(CHAIR[0] + 10, DADO_Y + 120, 80, 560, 1, 0, sy=0.7), 0.24, soft=0, wob=0)
    s.wash(wainA, INKBLUE, 0.34, wob=0, soft=0, edge=0, gran=0.4, grad=s.vgrad(DADO_Y + 180, FLOOR_Y, 0, 1) * s.hgrad(700, 2100, 0.5, 1))
    s.wash(R(s, -30, DADO_Y + 8, CORNER_X, DADO_Y + 34), INKBLUE, 0.55, wob=1.0, soft=5, edge=0)       # the rail's shadow
    for i, x in enumerate(xs[1:]):
        seg(s, (x, DADO_Y + 12), (x + r.uniform(-2, 2), FLOOR_Y - 44), 2.4, INKBLUE, 1.5, bow=0.002, r=r, tremor=0.9, skip=0.06)
        s.lift(R(s, x + 3.5, DADO_Y + 30, x + 6.5, FLOOR_Y - 52), 0.22, soft=1.2, wob=0.8)
        if i % 3 == 1:
            seg(s, (x - 3, DADO_Y + 30 + r.uniform(0, 60)), (x - 3.5, FLOOR_Y - 60 - r.uniform(0, 80)), 1.2, INKBLUE, 0.9, bow=0.002, r=r, skip=0.3)
    # boards on the adjoining wall, widening as they come toward us
    x, stp = CORNER_X + 74, 96.0
    while x < W + 30:
        seg(s, (x, sd(DADO_Y, x) + 12), (x, sd(FLOOR_Y - 44, x)), 2.4, INKBLUE, 1.4, bow=0.002, r=r, skip=0.08)
        stp *= 1.22
        x += stp
    # skirting board
    skA = Q(s, [(-30, FLOOR_Y - 44), (CORNER_X, FLOOR_Y - 44), (CORNER_X, FLOOR_Y), (-30, FLOOR_Y)])
    skB = Q(s, [(CORNER_X, FLOOR_Y - 44), (XR, sd(FLOOR_Y - 44)), (XR, sd(FLOOR_Y)), (CORNER_X, FLOOR_Y)])
    sk = np.maximum(skA, skB)
    s.wash(sk, PRUSSIAN, 0.42, wob=0.8, soft=1, edge=0.4, ew=4, gran=0.5, flow=0.4, fs=200)
    s.wash(sk, UMBER, 0.22, wob=0.8, soft=1, edge=0.2, gran=0.5)
    s.lift(R(s, -30, FLOOR_Y - 42, 1500, FLOOR_Y - 37) * s.hgrad(0, 1500, 1, 0.1), 0.34, soft=1.4)
    seg(s, (-20, FLOOR_Y - 44), (CORNER_X + 4, FLOOR_Y - 44), 2.2, INKBLUE, 1.5, bow=0.0008, r=r, tremor=1.0)
    seg(s, (60, FLOOR_Y - 36), (CORNER_X - 30, FLOOR_Y - 36.5), 1.2, INKBLUE, 0.9, bow=0.0008, r=r, skip=0.3)
    seg(s, (CORNER_X - 3, FLOOR_Y - 44), (XR, sd(FLOOR_Y - 44)), 2.2, INKBLUE, 1.5, bow=0.001, r=r)
    # ---- dado rail: a thin brass-coloured moulding
    railA = Q(s, [(-30, DADO_Y - 8), (CORNER_X, DADO_Y - 8), (CORNER_X, DADO_Y + 8), (-30, DADO_Y + 8)])
    railB = Q(s, [(CORNER_X, DADO_Y - 8), (XR, sd(DADO_Y - 8)), (XR, sd(DADO_Y + 8) + 6), (CORNER_X, DADO_Y + 8)])
    rail = np.maximum(railA, railB)
    s.lift(rail, 1.0, soft=0.6, wob=0.6)
    s.wash(rail, OCHRE, 0.95, wob=0.6, edge=0.4, ew=2, gran=0.4, flow=0.4, fs=180)
    s.wash(rail * s.vgrad(DADO_Y - 2, DADO_Y + 6, 0, 1) , SIENNA, 0.75, wob=0, soft=0, edge=0, gran=0.4, flow=0.4, fs=160)
    s.wash(railB, UMBER, 0.35, wob=0, soft=0, edge=0)
    s.wash(rail, UMBER, 0.22, wob=0, soft=0, edge=0, grad=s.hgrad(1500, 2150, 0, 1))
    hlm = R(s, -30, DADO_Y - 6, CORNER_X, DADO_Y - 2.5) * np.clip(0.2 + 1.2 * s.noise(240, 2) , 0, 1)
    s.lift(hlm, 0.6, soft=1.0, wob=0.5)
    seg(s, (-20, DADO_Y - 8), (CORNER_X + 5, DADO_Y - 8.5), 2.0, SEPIA, 1.4, bow=0.0006, r=r, tremor=0.9, skip=0.05)
    seg(s, (-20, DADO_Y + 8), (CORNER_X + 3, DADO_Y + 8), 2.4, SEPIA, 1.5, bow=0.0006, r=r, tremor=0.9)
    seg(s, (140, DADO_Y + 1), (CORNER_X - 60, DADO_Y + 0.5), 1.1, UMBER, 0.8, bow=0.0006, r=r, skip=0.4)
    seg(s, (CORNER_X - 4, DADO_Y - 8), (XR, sd(DADO_Y - 8)), 2.0, SEPIA, 1.4, bow=0.001, r=r)
    seg(s, (CORNER_X - 4, DADO_Y + 8), (XR, sd(DADO_Y + 8) + 6), 2.4, SEPIA, 1.5, bow=0.001, r=r)
    # the corner itself: one long line, gone over twice
    seg(s, (CORNER_X, -10), (CORNER_X + 1, FLOOR_Y + 6), 2.6, SEPIA, 1.5, bow=0.0015, r=r, tremor=1.1)
    seg(s, (CORNER_X + 3, 30), (CORNER_X + 2, DADO_Y - 30), 1.3, SEPIA, 0.9, bow=0.002, r=r, skip=0.3)
    # ---- floor: dark herringbone, laid out on the floor plane and seen through the same eye as the chair
    fpoly = [(-30, FLOOR_Y), (CORNER_X, FLOOR_Y), (XR, sd(FLOOR_Y)), (XR, H + 30), (-30, H + 30)]
    fm = Q(s, fpoly)
    s.lift(fm, 1.0, soft=0.8, wob=0.8)
    s.wash(fm, UMBER, 0.62, wob=0.8, edge=0.3, gran=0.5, flow=0.5, fs=260)
    s.wash(fm, BURNT, 0.26, wob=0, soft=0, edge=0, gran=0.4, flow=0.6, fs=180)
    joint = np.maximum(s.ribbon([(-30, FLOOR_Y), (CORNER_X, FLOOR_Y)], 7, smooth=False), s.ribbon([(CORNER_X, FLOOR_Y), (XR, sd(FLOOR_Y))], 7, smooth=False))
    s.wash(joint, SEPIA, 0.9, wob=0.5, soft=1.2, edge=0)           # where board meets floor nothing is left white
    fclip = cv2.GaussianBlur(fm, (0, 0), 1.0)
    PW, n = 7.4, 5
    xside = (CORNER_X - CHAIR[0]) / float(proj((0, 0, WALL_Z))[1])
    q2 = math.sqrt(0.5)
    planks = []
    for strip in range(-9, 10):
        for kk in range(-34, 34):
            for kind in (0, 1):
                if kind == 0:
                    p0, q0, p1, q1 = (kk + 2 * n * strip) * PW, kk * PW, (kk + 2 * n * strip + n) * PW, (kk + 1) * PW
                else:
                    p0, q0, p1, q1 = (kk + n + 2 * n * strip) * PW, (kk - n + 1) * PW, (kk + n + 1 + 2 * n * strip) * PW, (kk + 1) * PW
                cs = [(p0, q0), (p1, q0), (p1, q1), (p0, q1)]
                fl3 = [((p - q) * q2 - 18.0, 0.0, WALL_Z + (p + q) * q2 - 3.0) for p, q in cs]
                X = [c[0] for c in fl3]
                Z = [c[2] for c in fl3]
                if max(Z) < WALL_Z or min(Z) > 34 or max(X) < -205 or min(X) > xside + 2:
                    continue
                planks.append((kind, np.asarray(fl3)))
    for kind, p3 in planks:
        P2 = proj(p3, CHAIR)[0]
        if P2[:, 1].min() > H + 10 or P2[:, 0].max() < -10 or P2[:, 1].max() < FLOOR_Y:
            continue
        pm = fill(s, P2)
        tone = r.random()
        s.wash(pm, (UMBER, SEPIA, UMBER, COFFEE)[int(tone * 4) % 4], 0.22 + 0.5 * r.random() + (0.12 if kind else 0.0), wob=1.6, soft=0.9, edge=0.55, ew=4, gran=0.55, flow=0.5, fs=70, clip=fclip)
        if r.random() < 0.3:
            s.wash(pm, BURNT, 0.25, wob=1.5, soft=1, edge=0.2, clip=fclip)
        a, b, c, d = P2
        long1, long2 = ((a, b), (d, c)) if kind == 0 else ((a, d), (b, c))
        e1, e2 = ((a, d), (b, c)) if kind == 0 else ((a, b), (d, c))
        # far planks are slivers: the pen only hints at them
        thick = 0.5 * (np.hypot(*(e1[1] - e1[0])) + np.hypot(*(e2[1] - e2[0]))) * abs(np.cross((long1[1] - long1[0]) / (np.hypot(*(long1[1] - long1[0])) + 1e-6), (e1[1] - e1[0]) / (np.hypot(*(e1[1] - e1[0])) + 1e-6)))
        far = float(np.clip((thick - 7) / 22, 0.0, 1.0))
        for (u, v) in (long1, long2):
            if r.random() < 0.35 + 0.5 * far:
                seg(s, u, v, 1.2 + 0.7 * far, SEPIA, 0.9 + 0.45 * far, bow=0.004, r=r, clip=fclip, skip=0.12 + 0.2 * (1 - far), tremor=0.9, over=2)
        for (u, v) in (e1, e2):
            if r.random() < 0.7 * far:
                seg(s, u, v, 1.6, SEPIA, 1.2, r=r, clip=fclip, skip=0.1, over=1)
        for j in range(2):          # a grain line or two down the plank
            t = r.uniform(0.25, 0.75)
            u = long1[0] * (1 - t) + long2[0] * t
            v = long1[1] * (1 - t) + long2[1] * t
            w0, w1 = r.uniform(0.05, 0.3), r.uniform(0.6, 0.95)
            if r.random() < 0.7 * far:
                seg(s, u + (v - u) * w0, u + (v - u) * w1, 1.0, SEPIA, 0.7, bow=0.01, r=r, clip=fclip, skip=0.4, tremor=1.0)
    # the floor's light: a cold sheen from the window on the left, dark under the skirting and toward us
    sheen = s.zeros()
    for i in range(7):
        x0 = r.uniform(-40, 760)
        sheen = np.maximum(sheen, R(s, x0, FLOOR_Y + 4, x0 + r.uniform(30, 110), H + 20) * r.uniform(0.4, 1.0))
    sheen = cv2.GaussianBlur(sheen, (0, 0), 16) * fm * s.hgrad(0, 900, 1, 0) * s.vgrad(FLOOR_Y, FLOOR_Y + 60, 0.3, 1)
    s.lift(sheen, 0.34, soft=0, wob=0)
    s.wash(sheen, RAIN, 0.30, wob=0, soft=0, edge=0, gran=0.3)
    s.wash(fm, SEPIA, 0.5, wob=0, soft=0, edge=0, gran=0.4, flow=0.3, grad=s.vgrad(FLOOR_Y - 10, FLOOR_Y + 70, 1, 0))
    s.wash(fm, INKBLUE, 0.30, wob=0, soft=0, edge=0, gran=0.4, flow=0.4, fs=300, grad=np.clip(s.hgrad(1500, 2600, 0, 1) + s.vgrad(1250, 1460, 0, 0.6), 0, 1))
    s.wash(skB, INKBLUE, 0.3, wob=0, soft=0, edge=0)
    seg(s, (-20, FLOOR_Y), (CORNER_X + 6, FLOOR_Y + 0.5), 2.8, INK, 1.6, bow=0.0006, r=r, tremor=1.0)
    seg(s, (CORNER_X - 5, FLOOR_Y), (XR, sd(FLOOR_Y)), 2.8, INK, 1.6, bow=0.001, r=r)
    # ---- things on the wall
    pics = [_picture(s, r, 1778, 318, 196, 250, math.radians(-2.2), UMBER, "ring"),
            _picture(s, r, 1972, 432, 150, 158, math.radians(3.0), OCHRE, "cup")]
    _sconce(s, r, 560, 250)
    s.save("ch_bg", opaque=True, q=90, meta={"chair": [CHAIR[0], CHAIR[1]], "dado_y": DADO_Y, "floor_y": FLOOR_Y, "wall_pool": [POOL[0], POOL[1], POOL[2]], "pictures": pics, "corner_x": CORNER_X})


# ---------------------------------------------------------------- our own table, near edge
TBL = (1280, 1150 + 560, 1560, 560)       # centre x, centre y, rx, ry of the top's far rim


def table():
    s = Sheet(W, H, 45)
    r = rs(45)
    cx, cy, rx, ry = TBL
    top = s.ellipse(cx, cy, rx, ry)
    # what stands behind the rim sits in its shade
    s.wash(shift(s, top, 0, -16, 16) * (1 - top), SEPIA, 0.42, wob=0, soft=0, edge=0, gran=0.4)
    s.lift(top, 1.0, soft=0.6, wob=0.8)
    s.wash(top, SIENNA, 0.86, wob=0.8, soft=0.6, edge=0.35, ew=6, flow=0.45, fs=260, gran=0.45, body=1)
    s.wash(top, BURNT, 0.22, wob=0, soft=0, edge=0, flow=0.5, fs=320, gran=0.4)

    def arc(dy, x0, x1, bend=1.0, n=9):
        """A line of the grain: it runs across us, sagging with the rim as the round top turns away."""
        xs = np.linspace(x0, x1, n)
        ye = cy - ry * np.sqrt(np.clip(1 - ((xs - cx) / rx) ** 2, 0, 1))
        return np.stack([xs, (cy - ry) + dy + (ye - (cy - ry)) * bend], 1)
    tm = cv2.GaussianBlur(top, (0, 0), 1.2)
    for i in range(74):
        dy = 22 + (r.random() ** 1.7) * 300
        L = r.uniform(700, 2300)
        x0 = r.uniform(-300, W - 500)
        bend = max(0.0, 1 - dy / 420) * 0.9
        pts = arc(dy, x0, x0 + L, bend) + np.stack([np.zeros(9), np.sin(np.linspace(0, 6, 9) + i) * 2.0], 1)
        if i < 30:
            s.stroke(pts, (5 + 16 * r.random()) * (0.5 + dy / 200), BURNT if i % 3 else UMBER, 0.10 + 0.18 * r.random(), dry=0.25 + 0.3 * r.random(), edge=0.3, wob=1.2, clip=tm, taper=(0.1, 0.1), gran=0.5)
        else:
            s.ink(pts, 1.3 + 0.5 * r.random(), BURNT if i % 4 else UMBER, 0.55 + 0.5 * r.random(), tremor=1.1, skip=0.4, clip=tm, taper=(0.04, 0.04))
    # lamp pool in the middle, falling off to the sides and toward us
    s.wash(top, OCHRE, 0.24, wob=0, soft=0, edge=0, flow=0.3, grad=s.rgrad(cx - 60, cy - ry + 190, 150, 1000, 1, 0, sy=0.5))
    s.lift(top * s.rgrad(cx - 80, cy - ry + 160, 80, 820, 1, 0, sy=0.42) * (0.75 + 0.25 * s.noise(140, 2)), 0.30, soft=0, wob=0)
    s.wash(top, UMBER, 0.44, wob=0, soft=0, edge=0, flow=0.4, gran=0.5, grad=s.rgrad(cx - 40, cy - ry + 160, 560, 1500, 0, 1, sy=0.7))
    s.wash(top, RAIN, 0.14, wob=0, soft=0, edge=0, grad=s.hgrad(0, 800, 1, 0))                     # the window on the left
    # the rim: a rounded moulding - shade where it rolls over, a thin light on its shoulder, a line where it meets the top
    s.wash(top * (1 - s.ellipse(cx, cy + 24, rx - 6, ry)), UMBER, 0.34, wob=0.8, soft=1.5, edge=0.3)
    s.wash(top * (1 - s.ellipse(cx, cy + 8, rx - 2, ry)), SEPIA, 0.7, wob=0.6, soft=1.0, edge=0.2)
    edge = ell(cx, cy, rx, ry, math.pi * 1.08, math.pi * 1.92, 90)
    s.lift(s.ribbon(edge + (0, 14), 6.0, smooth=False) * top * s.hgrad(200, 1900, 1, 0.3) * (0.35 + 0.65 * s.noise(160, 2)), 0.5, soft=1.2, wob=0.8)
    pen(s, edge, r, 3.4, INK, 1.6, lo=500, hi=1100, tremor=1.2)
    pen(s, edge[10:-6] + (2, 2.5), r, 1.5, SEPIA, 0.9, lo=300, hi=700, tremor=1.3, skip=0.25)
    pen(s, edge + (0, 24), r, 1.7, SEPIA, 1.2, lo=300, hi=800, tremor=1.2, skip=0.2)
    s.spatter(18, UMBER, 0.32, box=(200, 1180, W - 200, H), r=(1, 3.5))
    s.save("ch_table", meta={"edge": [cx, cy, rx, ry]})


# ---------------------------------------------------------------- the coat
CW, CH_ = 900, 1180            # coat sprite sheet
CO = np.array([455.0, 770.0])  # the chair's seat centre on it: every coat coordinate below is relative to that


def _top_y():
    P, Rr = chair_geo((0, 0))["outer"]
    i = int(np.argmin(P[:, 1]))
    return float(P[i, 1] - Rr[i])


def _segs(segs):
    return [spline(np.asarray(sg, np.float64) + CO, False, 3.0) for sg in segs]


def _m(s, segs):
    return fill(s, np.vstack(segs))


def fold(s, r, pts, m, w=26, dark="R", k=0.40, col=BURNT, crest=0.30, line=1.25, lw=1.8, deep=0.0):
    """One fold of heavy cloth: a pen line where the cloth turns under, shade pooling on one side of it and fading
    away, a lifted light on the crest the other side."""
    P = spline(np.asarray(pts, np.float64) + CO, False, 3.0)
    g = P[-1] - P[0]
    n = np.array([-g[1], g[0]])
    n /= np.hypot(*n) + 1e-9
    sg = 1.0 if n @ np.array({"R": (1, 0), "L": (-1, 0), "D": (0, 1), "U": (0, -1)}[dark]) > 0 else -1.0
    t = np.linspace(0, 1, len(P))
    prof = np.sin(np.pi * t) ** 0.55
    sh = stamp(s, offset(P, sg * w * 0.42 * prof), np.maximum(0.5, w * 0.5 * prof))
    s.wash(sh, col, k, wob=1.5, bleed=max(2.0, w * 0.17), edge=0.2, gran=0.45, clip=m)
    if deep:
        s.wash(stamp(s, offset(P, sg * w * 0.2 * prof), np.maximum(0.5, w * 0.22 * prof)), UMBER, deep, wob=1.2, bleed=max(1.5, w * 0.08), edge=0.2, gran=0.4, clip=m)
    if crest:
        s.lift(stamp(s, offset(P, -sg * w * 0.32 * prof), np.maximum(0.5, w * 0.27 * prof)) * m, crest, soft=max(1.5, w * 0.10), wob=1.2)
    if line:
        s.ink(P, lw * r.uniform(0.85, 1.15), SEPIA, line, tremor=0.9, skip=0.10, clip=m, taper=(0.22, 0.4), smooth=False)


def cloth(s, r, m, allowed, k=0.95, cast=(9, 13, 9, 0.5), inside=None):
    """A piece of the coat: its shadow on whatever it lies over, then persimmon, loaded unevenly."""
    if cast:
        s.wash(shift(s, m, cast[0], cast[1], cast[2]) * allowed, UMBER, cast[3], wob=0, soft=0, edge=0, gran=0.35)
        s.wash(shift(s, m, cast[0] * 0.4, cast[1] * 0.4, 3) * allowed, SEPIA, cast[3] * 0.5, wob=0, soft=0, edge=0, gran=0.3)
    s.lift(cv2.erode(m, np.ones((5, 5), np.uint8)), 1.0, soft=0.8, wob=0.6)      # never lift where the new wash may not reach
    inside = getattr(s, "coat_inside", None) if inside is None else inside
    grow = np.maximum(m, np.clip(cv2.GaussianBlur(m, (0, 0), 1.7) * 2.3, 0, 1) * inside) if inside is not None else m   # a loaded brush runs a hair over the pencil where it meets the next piece
    grow = np.maximum(cv2.erode(m, np.ones((3, 3), np.uint8)), grow * (inside if inside is not None else 1))
    s.wash(grow, PERSIMMON, k, wob=1.0, edge=0.5, ew=6, flow=0.5, fs=130, gran=0.36, body=1)
    s.wash(m, AMBER, 0.10, wob=0, soft=0, edge=0, flow=0.9, fs=70, gran=0.3)
    return m


def tone(s, pts, m, k=0.36, col=BURNT, edge=0.55, wob=3.0):
    """A second, shaped wash: the half-tone of a form, with the hard pooled edge a glaze dries to."""
    sm = s.poly(np.asarray(pts, np.float64) + CO)
    s.wash(sm, PERSIMMON, k * 0.8, wob=wob, edge=edge, ew=5, gran=0.4, flow=0.4, fs=80, clip=m)
    s.wash(sm, col, k, wob=wob, edge=edge * 0.6, ew=5, gran=0.4, flow=0.4, fs=80, clip=m)


def valley(s, r, pts, m, w0=6, w1=36, k=0.46, deep=0.22, dark="R"):
    """The hollow between two pipe folds of hanging cloth: narrow where it starts, opening as it falls."""
    P = spline(np.asarray(pts, np.float64) + CO, False, 3.0)
    t = np.linspace(0, 1, len(P))
    wd = (w0 + (w1 - w0) * t ** 0.8) * 0.5
    vm = stamp(s, P, wd)
    s.wash(vm, PERSIMMON, k * 0.6, wob=1.5, soft=1.5, edge=0.5, ew=4, gran=0.4, clip=m)
    s.wash(vm, BURNT, k, wob=1.5, soft=2.0, edge=0.4, ew=4, gran=0.45, clip=m)
    sg = -1.0 if dark == "R" else 1.0
    s.wash(stamp(s, offset(P, sg * wd * 0.45), wd * 0.5), UMBER, deep, wob=1.2, soft=2.0, edge=0.3, gran=0.4, clip=m)
    s.lift(stamp(s, offset(P, -sg * (wd + 7)), np.maximum(1.0, wd * 0.45)) * m, 0.30, soft=3, wob=1.2)
    s.ink(offset(P, sg * wd * 0.92), 1.9 * r.uniform(0.85, 1.15), SEPIA, 1.3, tremor=1.0, skip=0.08, clip=m, taper=(0.15, 0.35), smooth=False)
    if r.random() < 0.7:
        s.ink(offset(P, -sg * wd * 0.9)[int(len(P) * 0.25):int(len(P) * r.uniform(0.6, 0.9))], 1.2, SEPIA, 0.9, tremor=1.0, skip=0.25, clip=m, taper=(0.2, 0.4), smooth=False)


def outline(s, r, segs, w=2.4, k=1.55, color=SEPIA, which=None, **kw):
    for i, sg in enumerate(segs):
        if which is not None and i not in which:
            continue
        a, b = sg[0], sg[-1]
        u = (sg[min(4, len(sg) - 1)] - a)
        v = (b - sg[max(0, len(sg) - 5)])
        ext = np.vstack([a - u / (np.hypot(*u) + 1e-9) * r.uniform(1, 6), sg, b + v / (np.hypot(*v) + 1e-9) * r.uniform(2, 8)])
        pen(s, ext, r, w, color, k, lo=260, hi=620, tremor=0.9, **kw)


def button(s, r, x, y, rad=15):
    x, y = x + CO[0], y + CO[1]
    m = s.ellipse(x, y, rad, rad * 0.94)
    s.wash(shift(s, m, 4, 6, 3.5), UMBER, 0.6, wob=0, soft=0, edge=0)
    base(s, m, UMBER, 1.0, wob=0.6, edge=0.6, ew=3, gran=0.4)
    s.wash(m, SEPIA, 0.5, wob=0.5, soft=1.2, grad=s.rgrad(x - rad * 0.4, y - rad * 0.5, 2, rad * 1.5, 0, 1))
    s.lift(s.ellipse(x - rad * 0.36, y - rad * 0.40, rad * 0.34, rad * 0.2, -35), 0.6, soft=1.2)
    oval(s, x, y, rad, rad * 0.94, 2.0, INK, 1.5, twice=True)
    oval(s, x, y, rad * 0.56, rad * 0.52, 1.1, INK, 0.9, skip=0.2)
    for dx, dy in ((-3, -2.5), (3, -2.5), (-3, 3), (3, 3)):
        s.ink([(x + dx - 0.8, y + dy), (x + dx, y + dy + 0.3), (x + dx + 0.8, y + dy + 0.6)], 1.8, INK, 1.4, taper=(0, 0))


def coat():
    s = Sheet(CW, CH_, 44)
    r = rs(44)
    top = _top_y()                                   # top edge of the chair back, relative to the seat centre
    T = top + 567.0                                  # everything up there was laid out with the hoop top at -567
    g, cm = chair_masks(s, CO)
    seat = cm["seat"]

    def up(pts):                                     # points of the upper half follow the hoop if it is ever re-proportioned
        return [(x, y + T) for x, y in pts]
    B = (6, -258)
    B2 = (12, -248)
    # ---- outlines (segments meet at corners; each is drawn as its own pen stroke)
    collar_back = _segs([up([(-72, -576), (-42, -604), (0, -616), (42, -604), (72, -576)]), up([(72, -576), (62, -570)]),
                         up([(62, -570), (32, -588), (0, -593), (-32, -588), (-62, -570)]), up([(-62, -570), (-72, -576)])])
    lap_l = _segs([up([(-70, -578), (-106, -552), (-128, -514), (-136, -486)]), up([(-136, -486), (-106, -476)]), up([(-106, -476), (-154, -450)]),
                   up([(-154, -450), (-130, -382), (-82, -312), (-32, -274), B]), up([B, (-20, -380), (-46, -480), (-62, -570)]), up([(-62, -570), (-70, -578)])])
    lap_r = _segs([up([(70, -578), (108, -550), (132, -510), (140, -480)]), up([(140, -480), (110, -472)]), up([(110, -472), (162, -440)]),
                   up([(162, -440), (140, -372), (96, -304), (48, -266), B2]), up([B2, (38, -370), (56, -476), (62, -570)]), up([(62, -570), (70, -578)])])
    pan_r = _segs([up([(60, -574), (112, -561), (164, -532), (206, -494), (240, -458)]),
                   up([(240, -458), (246, -380), (230, -250)]) + [(224, -120), (238, -30), (258, 60), (266, 150), (254, 250), (246, 336)],
                   [(246, 336), (206, 356), (160, 346), (112, 366), (64, 350), (22, 364), (-16, 352)],
                   [(-16, 352), (-24, 220), (-13, 100), (0, 20), (11, -60), (15, -160)] + up([B2]),
                   up([B2, (38, -370), (56, -476), (60, -574)])])
    pan_l = _segs([up([(-60, -574), (-112, -561), (-164, -532), (-206, -494), (-240, -458)]),
                   up([(-240, -458), (-246, -380), (-236, -250)]) + [(-240, -100), (-262, 40), (-272, 180), (-264, 330)],
                   [(-264, 330), (-226, 356), (-184, 340), (-146, 354)],
                   [(-146, 354), (-140, 200), (-133, 60), (-129, -20), (-118, -92), (-90, -160), (-42, -226)] + up([B]),
                   up([B, (-20, -380), (-46, -480), (-60, -574)])])
    slv_l = _segs([up([(-190, -510), (-218, -484), (-244, -452)]),
                   up([(-244, -452), (-288, -388), (-303, -270)]) + [(-300, -140), (-309, -20), (-305, 110), (-298, 214)],
                   [(-298, 214), (-238, 228), (-178, 217)],
                   [(-178, 217), (-171, 100), (-173, -30), (-159, -150)] + up([(-161, -300), (-170, -400), (-190, -510)])])
    arm_r = _segs([up([(190, -510), (218, -484), (244, -452)]),
                   up([(244, -452), (288, -386), (304, -270)]) + [(307, -140), (302, -40), (288, 16)],
                   [(288, 16), (240, 40), (190, 30)],
                   [(190, 30), (176, -40), (172, -110), (166, -200)] + up([(162, -310), (172, -400), (190, -510)])])
    arm_f = _segs([[(174, -106), (120, -96), (60, -84), (-18, -66)],
                   [(-18, -66), (-37, -14), (-29, 42), (-12, 65)],
                   [(-12, 65), (60, 63), (130, 53), (220, 44), (288, 16)],
                   [(288, 16), (304, -34), (268, -90), (174, -106)]])
    M = {k: _m(s, v) for k, v in dict(collar_back=collar_back, lap_l=lap_l, lap_r=lap_r, pan_r=pan_r, pan_l=pan_l, slv_l=slv_l, arm_r=arm_r, arm_f=arm_f).items()}
    # the lining seen inside: the neck, and where the left front has swung open
    lin = np.maximum(fill(s, np.asarray(up([(-66, -572), (0, -596), (66, -572), (44, -420), (16, -246), (0, -252), (-34, -400)])) + CO),
                     fill(s, np.asarray(up([(0, -262), (20, -256)]) + [(20, -50), (-196, -24), (-196, -130), (-160, -160), (-112, -212), (-50, -252)]) + CO))
    lin = lin * (1 - seat)
    union = lin.copy()
    for v in M.values():
        union = np.maximum(union, v)
    sil = np.maximum.reduce([cm["outer"], cm["inner"], cm["seat"], cm["fl"], cm["fr"], cm["ring"]])
    allowed = np.clip(cv2.GaussianBlur(np.maximum(union, sil), (0, 0), 1.5) * 1.2, 0, 1)
    s.coat_inside = cv2.erode(union, np.ones((5, 5), np.uint8))

    # ---- 1. lining: a muted teal satin, deep in the hollow
    s.wash(lin, TEAL, 0.80, wob=1.0, edge=0.4, ew=5, flow=0.5, fs=90, gran=0.4, body=1)
    s.wash(lin, UMBER, 0.30, wob=0, soft=0, edge=0, flow=0.5, fs=80, gran=0.4)
    s.wash(lin, PRUSSIAN, 0.55, wob=0, soft=0, edge=0, gran=0.4, grad=np.clip(s.vgrad(CO[1] - 590 + T, CO[1] - 300 + T, 0.9, 0.25) + s.hgrad(CO[0] - 140, CO[0] + 20, 0, 0.7) * s.vgrad(CO[1] - 280, CO[1] - 200, 0, 1), 0, 1))
    lc = cv2.GaussianBlur(lin, (0, 0), 1.0)
    for i in range(7):         # satin: long soft lights down the hang of it
        x0 = -170 + i * 30 + r.uniform(-8, 8)
        s.lift(s.ribbon(np.asarray([(x0, -230), (x0 - 6, -150), (x0 + 4, -50)]) + CO, r.uniform(5, 12), taper=(0.3, 0.3)) * lin, r.uniform(0.16, 0.34), soft=3, wob=1.5)
        if i % 2:
            s.ink(np.asarray([(x0 + 12, -236), (x0 + 5, -150), (x0 + 14, -50)]) + CO, 1.2, INKBLUE, 0.9, tremor=1.0, skip=0.3, clip=lc)
    # the chair back seen inside the coat: its shadow on the lining, then the loops themselves
    hoop = np.maximum(cm["outer"], cm["inner"])
    s.wash(shift(s, hoop, 12, 10, 6) * lin, INKBLUE, 0.7, wob=0, soft=0, edge=0, gran=0.3)
    near_map = cv2.GaussianBlur(lin, (0, 0), 8)
    for key in ("outer", "inner"):
        P, Rr = g[key]
        near = near_map[np.clip(P[:, 1].astype(int), 0, s.h - 1), np.clip(P[:, 0].astype(int), 0, s.w - 1)] > 0.02
        idx = np.where(near)[0]
        if len(idx) < 8:
            continue
        for run in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1):
            if len(run) < 8:
                continue
            Pp, Rp = P[run], Rr[run]
            _paint_rod(s, r, Pp, Rp, stamp(s, Pp, Rp) * lin, clip=lc)

    # ---- 2. the back of the collar, standing behind the neck
    cloth(s, r, M["collar_back"], allowed, 0.95, cast=(3, 10, 5, 0.6))
    s.wash(M["collar_back"], BURNT, 0.5, wob=1, soft=2, edge=0.2, grad=s.vgrad(CO[1] - 618 + T, CO[1] - 580 + T, 0.2, 1))
    outline(s, r, collar_back, 2.3, which=(0, 2))

    # ---- 4. right front: chest, lap, and the skirt going over the front of the seat
    pr = cloth(s, r, M["pan_r"], allowed, 0.80, cast=(-12, 12, 9, 0.55))
    prc = cv2.GaussianBlur(pr, (0, 0), 1)
    front = g["seat_top"]
    front = front[front[:, 1] > CO[1] + 30]
    front = front[np.argsort(front[:, 0])] - CO
    edge_y = lambda x: float(np.interp(x, front[:, 0], front[:, 1]))
    # half-tones: the side turned from the window; everything that hangs below the seat's edge
    tone(s, up([(150, -470), (128, -360), (112, -250)]) + [(96, -140), (116, -60), (190, -60), (240, -200)] + up([(250, -420)]), pr, 0.34)
    hang = [(x, edge_y(min(x, 214)) + 9) for x in (-30, 30, 90, 150, 200)] + [(270, 20), (280, 380), (-40, 380)]
    tone(s, hang, pr, 0.40, wob=2.0)
    s.wash(pr, UMBER, 0.34, wob=0, soft=0, edge=0, gran=0.45, flow=0.4, fs=90, grad=s.vgrad(CO[1] + 200, CO[1] + 370, 0, 1))
    # the lap is lit from above; the cloth turns over the seat's edge on a soft bright crest
    s.lift(s.ribbon(np.asarray([(x, edge_y(x) - 4) for x in range(-10, 215, 8)]) + CO, 15, smooth=False) * pr * (0.45 + 0.55 * s.noise(50, 2)), 0.40, soft=3, wob=1.5)
    # chest
    fold(s, r, up([(182, -430), (156, -330)]) + [(134, -200), (144, -90)], pr, 34, "R", 0.44, deep=0.2)
    fold(s, r, up([(86, -222)]) + [(98, -160), (88, -92)], pr, 24, "R", 0.36)
    fold(s, r, up([(58, -236), (98, -226), (146, -240)]), pr, 18, "D", 0.32, crest=0.24, line=1.0)
    fold(s, r, [(64, -150), (108, -140), (156, -158)], pr, 18, "D", 0.32, crest=0.24, line=1.0)
    fold(s, r, [(20, -110), (40, -84), (30, -66)], pr, 12, "R", 0.26, crest=0.2, line=0.9)
    s.lift(s.ribbon(np.asarray(up([(92, -430), (84, -330)]) + [(60, -200), (56, -100)]) + CO, 26, taper=(0.3, 0.3)) * pr, 0.20, soft=6, wob=2)
    # the skirt: pipe folds starting under the seat's edge and opening as they fall
    for (x0, x1, x2, w1, dk) in ((26, 20, 30, 34, "R"), (92, 108, 100, 46, "R"), (150, 176, 170, 38, "L"), (208, 238, 232, 26, "L")):
        y0 = edge_y(min(x0, 214)) + r.uniform(4, 16)
        valley(s, r, [(x0, y0), ((x0 + x1) / 2 + r.uniform(-4, 4), y0 + 90), (x1, 250), (x2, 350)], pr, 5, w1, 0.46, 0.24, dk)
    for (x0, x1) in ((58, 62), (128, 140), (192, 208)):
        y0 = edge_y(x0) + 22
        s.ink(np.asarray([(x0, y0), (x0 + 5, y0 + 50), (x1, y0 + 110)]) + CO, 1.2, SEPIA, 0.9, tremor=1.0, skip=0.25, clip=prc, taper=(0.2, 0.5))
    # the front edge: a soft roll with a row of stitching inside it
    fe = pan_r[3]
    s.lift(s.ribbon(offset(fe, -7), 9, smooth=False) * pr, 0.34, soft=2.5, wob=1)
    s.wash(s.ribbon(offset(fe, -22), 16, smooth=False), BURNT, 0.28, wob=1, bleed=4, edge=0.1, clip=pr)
    pen(s, offset(fe, -11), r, 1.1, BURNT, 1.0, lo=40, hi=90, skip=0.35, clip=prc)
    outline(s, r, pan_r, 2.5)

    # ---- 5. left front: held by the top button, then swinging away to the left under the weight of its sleeve, so the
    # coat hangs open over the seat and the chair shows inside it
    pl = cloth(s, r, M["pan_l"], allowed, 0.78, cast=(8, 12, 8, 0.6))
    plc = cv2.GaussianBlur(pl, (0, 0), 1)
    tone(s, up([(-250, -330), (-150, -300)]) + [(-70, -226), (-104, -150), (-126, -60), (-150, 10), (-260, 10)], pl, 0.30)
    hang = [(x, edge_y(max(x, -214)) + 9) for x in (-280, -200, -150, -110)] + [(-100, 380), (-290, 380)]
    tone(s, hang, pl, 0.40, wob=2.0)
    s.wash(pl, UMBER, 0.34, wob=0, soft=0, edge=0, gran=0.45, flow=0.4, fs=90, grad=s.vgrad(CO[1] + 200, CO[1] + 370, 0, 1))
    s.lift(s.ribbon(np.asarray([(x, edge_y(x) - 4) for x in range(-176, -124, 6)]) + CO, 13, smooth=False) * pl, 0.36, soft=3, wob=1.5)
    fold(s, r, up([(-200, -440), (-164, -340)]) + [(-120, -226), (-134, -110)], pl, 32, "R", 0.44, deep=0.2)
    fold(s, r, up([(-232, -360), (-212, -270)]) + [(-196, -170)], pl, 22, "R", 0.34)
    fold(s, r, [(-150, -262), (-100, -246), (-40, -256)], pl, 16, "D", 0.28, crest=0.24, line=1.0)
    fold(s, r, [(-166, -40), (-150, 10), (-158, 60)], pl, 14, "R", 0.30, crest=0.2)
    valley(s, r, [(-156, edge_y(-156) + 12), (-162, 190), (-158, 262), (-166, 346)], pl, 5, 26, 0.44, 0.22, "R")
    valley(s, r, [(-214, 232), (-222, 290), (-216, 346)], pl, 5, 24, 0.42, 0.2, "L")
    valley(s, r, [(-256, 236), (-262, 290), (-256, 340)], pl, 5, 18, 0.40, 0.2, "R")
    s.lift(s.ribbon(np.asarray(up([(-150, -440), (-128, -350)]) + [(-84, -262)]) + CO, 24, taper=(0.3, 0.3)) * pl, 0.22, soft=6, wob=2)
    fe = pan_l[3]
    s.lift(s.ribbon(offset(fe, -8), 11, smooth=False) * pl, 0.40, soft=2.5, wob=1)
    s.wash(s.ribbon(offset(fe, -27), 18, smooth=False), BURNT, 0.30, wob=1, bleed=5, edge=0.1, clip=pl)
    pen(s, offset(fe, -12), r, 1.1, BURNT, 1.0, lo=40, hi=90, skip=0.35, clip=plc)
    outline(s, r, pan_l, 2.5)
    # the lamp on both shoulders
    for sg in (-1, 1):
        s.lift(s.ribbon(np.asarray(up([(sg * 84, -556), (sg * 150, -528), (sg * 204, -480)])) + CO, 24, taper=(0.3, 0.3)) * (pl if sg < 0 else pr), 0.30, soft=5, wob=2)

    # ---- 6. lapels and collar: the flattest, lightest planes of the coat
    for key, segs, cst in (("lap_r", lap_r, (-7, 12, 7, 0.6)), ("lap_l", lap_l, (8, 13, 7, 0.6))):
        lm = cloth(s, r, M[key], allowed, 0.76, cast=cst)
        s.lift(lm * s.vgrad(CO[1] - 580 + T, CO[1] - 300 + T, 1, 0.3), 0.14, soft=0, wob=0)
        s.wash(lm, BURNT, 0.30, wob=0, soft=0, edge=0, gran=0.45, grad=s.vgrad(CO[1] - 420 + T, CO[1] - 250 + T, 0, 1) * (1.0 if key == "lap_r" else 0.5))
        roll = segs[4]
        s.wash(s.ribbon(offset(roll, 9 if key == "lap_l" else -9), 14, smooth=False), BURNT, 0.30, wob=1, bleed=4, edge=0.1, clip=lm)     # the roll turns under
        lmc = cv2.GaussianBlur(lm, (0, 0), 1)
        pen(s, offset(np.vstack([segs[0], segs[1][1:]]), -7), r, 1.0, BURNT, 0.9, lo=40, hi=90, skip=0.35, clip=lmc)
        pen(s, offset(segs[3], -7), r, 1.0, BURNT, 0.9, lo=40, hi=90, skip=0.35, clip=lmc)
        outline(s, r, segs, 2.4, which=(0, 1, 2, 3, 4))
        # the gorge seam, collar to lapel
        a, b = segs[1][-1], segs[4][int(len(segs[4]) * 0.72)]
        seg(s, a, b, 1.8, SEPIA, 1.3, r=r, over=2)

    # ---- 7. the sleeve hanging at the side
    sl = cloth(s, r, M["slv_l"], allowed, 0.80, cast=(12, 12, 10, 0.6))
    tone(s, up([(-228, -470), (-216, -300)]) + [(-230, -150), (-214, -20), (-226, 110), (-218, 240), (-150, 240), (-140, -200)] + up([(-150, -520)]), sl, 0.40)
    s.wash(sl, UMBER, 0.22, wob=0, soft=0, edge=0, gran=0.45, grad=s.hgrad(CO[0] - 205, CO[0] - 160, 0, 1))
    s.lift(s.ribbon(offset(slv_l[1], -13), 20, smooth=False) * sl * (0.4 + 0.6 * s.noise(90, 2)), 0.36, soft=4, wob=1.5)      # the window on its outer edge
    fold(s, r, up([(-262, -420), (-248, -300)]) + [(-268, -176), (-252, -70)], sl, 32, "R", 0.42, deep=0.18)
    fold(s, r, up([(-204, -410), (-198, -300)]) + [(-206, -190)], sl, 20, "R", 0.30)
    fold(s, r, [(-160, -166), (-212, -134), (-270, -152)], sl, 22, "D", 0.40, deep=0.2)
    fold(s, r, [(-170, -108), (-208, -86), (-248, -96)], sl, 16, "D", 0.32)
    fold(s, r, [(-306, -84), (-274, -54), (-244, -58)], sl, 14, "D", 0.28, crest=0.22)
    fold(s, r, [(-238, -24), (-226, 56), (-238, 136)], sl, 24, "R", 0.36, deep=0.12)
    fold(s, r, [(-280, 6), (-272, 76), (-282, 136)], sl, 12, "R", 0.22, crest=0.2, line=0.8)
    # cuff: a turned-back band, a button, the dark of the empty sleeve below
    cuff = fill(s, np.vstack(_segs([[(-303, 146), (-240, 159), (-175, 148)], [(-175, 148), (-178, 217)], [(-178, 217), (-238, 228), (-298, 214)], [(-298, 214), (-303, 146)]])))
    s.wash(cuff, BURNT, 0.30, wob=1, soft=1.5, edge=0.4, ew=4, clip=sl)
    s.ink(np.asarray([(-306, 145), (-240, 159), (-172, 147)]) + CO, 2.0, SEPIA, 1.4, tremor=0.9)
    s.ink(np.asarray([(-300, 153), (-240, 167), (-177, 156)]) + CO, 1.0, BURNT, 0.9, tremor=0.9, skip=0.35)
    outline(s, r, slv_l, 2.6)
    hole = s.ellipse(CO[0] - 238, CO[1] + 222, 57, 8, 3)
    s.wash(hole, SEPIA, 1.0, wob=0.8, soft=1.2, edge=0.3, body=1)
    button(s, r, -203, 186, 11)
    # the armhole seam
    pen(s, np.asarray(up([(-190, -508), (-174, -450), (-166, -392), (-164, -340)])) + CO, r, 1.7, SEPIA, 1.2, lo=80, hi=160, skip=0.1)

    # ---- 8. the other sleeve: down from the shoulder, bent at the elbow, laid across the seat
    ar = cloth(s, r, M["arm_r"], allowed, 0.80, cast=(-12, 12, 10, 0.6))
    tone(s, up([(262, -460), (268, -300)]) + [(254, -170), (268, -70), (300, -10), (330, -140)] + up([(330, -300), (300, -440)]), ar, 0.42)
    s.wash(ar, UMBER, 0.24, wob=0, soft=0, edge=0, gran=0.45, grad=s.hgrad(CO[0] + 262, CO[0] + 310, 0, 1))
    s.lift(s.ribbon(offset(arm_r[3], -13), 18, smooth=False) * ar * (0.4 + 0.6 * s.noise(90, 2)), 0.30, soft=4, wob=1.5)
    fold(s, r, up([(232, -440), (250, -310)]) + [(238, -200), (254, -130)], ar, 30, "R", 0.40, deep=0.16)
    fold(s, r, up([(196, -410), (202, -310)]) + [(194, -220)], ar, 20, "R", 0.30)
    fold(s, r, [(168, -176), (214, -154), (270, -172)], ar, 22, "D", 0.38, deep=0.18)
    fold(s, r, [(172, -128), (226, -108), (292, -130)], ar, 24, "D", 0.42, deep=0.22)
    outline(s, r, arm_r, 2.6, which=(0, 1, 3))
    pen(s, np.asarray(up([(190, -508), (176, -450), (168, -392), (166, -340)])) + CO, r, 1.7, SEPIA, 1.2, lo=80, hi=160, skip=0.1)
    # the forearm: no line where it leaves the elbow - the same cloth turns the corner, creasing from the inside of the bend
    af = cloth(s, r, M["arm_f"], allowed, 0.80, cast=(6, 16, 10, 0.7))
    tone(s, up([(262, -460), (268, -300)]) + [(254, -170), (262, -100), (310, -30), (330, -140)] + up([(330, -300), (300, -440)]), af, 0.42)
    tone(s, [(-40, 14), (60, 6), (160, -10), (250, -24), (320, -40), (310, 40), (220, 70), (40, 86), (-40, 86)], af, 0.42)
    s.wash(af, UMBER, 0.28, wob=0, soft=0, edge=0, gran=0.45, grad=s.vgrad(CO[1] + 24, CO[1] + 66, 0, 1) * s.hgrad(CO[0] - 60, CO[0] + 300, 0.5, 1))
    s.lift(s.ribbon(offset(arm_f[0], -16)[8:-6], 22, smooth=False) * af * (0.4 + 0.6 * s.noise(90, 2)), 0.38, soft=4, wob=1.5)        # lamp along the top of the forearm
    fold(s, r, [(236, -40), (150, -20), (70, -10)], af, 24, "D", 0.32, deep=0.12, line=1.0)
    for (ex, ey, w, kk) in ((300, -58, 22, 0.42), (292, -8, 24, 0.44), (252, 30, 22, 0.40), (204, 36, 16, 0.30)):       # creases fanning from the inner elbow
        fold(s, r, [(180, -98), ((180 + ex) / 2 + 8, (-98 + ey) / 2 - 10), (ex, ey)], af, w, "D" if ey < -20 else "L", kk, deep=0.2)
    fold(s, r, [(126, -92), (134, -40), (124, 46)], af, 14, "L", 0.22, crest=0.18, line=0.8)
    cuf = fill(s, np.vstack(_segs([[(32, -80), (-18, -66)], [(-18, -66), (-37, -14), (-29, 42), (-12, 65)], [(-12, 65), (40, 66)], [(40, 66), (46, 0), (32, -80)]])))
    s.wash(cuf, BURNT, 0.28, wob=1, soft=1.5, edge=0.4, ew=4, clip=af)
    s.ink(np.asarray([(31, -82), (46, -4), (39, 66)]) + CO, 2.0, SEPIA, 1.4, tremor=0.9)
    s.ink(np.asarray([(23, -78), (38, -4), (31, 64)]) + CO, 1.0, BURNT, 0.9, tremor=0.9, skip=0.35)
    outline(s, r, arm_f, 2.6, which=(0, 1, 2))
    hole = s.ellipse(CO[0] - 27, CO[1] + 0, 9, 52, -7)
    s.wash(hole, SEPIA, 1.0, wob=0.8, soft=1.2, edge=0.3, body=1)
    s.wash(hole, PRUSSIAN, 0.4, wob=0.5, soft=1.5, edge=0)
    button(s, r, 12, 36, 11)

    # ---- 9. buttons, and the whole coat turned a little from the window
    button(s, r, 40, -232 + T, 16)
    button(s, r, 46, -146, 16)
    body = np.clip(s.body, 0, 1) * (1 - lin)
    s.wash(body, VIOLET, 0.12, wob=0, soft=0, edge=0, gran=0.3, grad=s.hgrad(CO[0] - 40, CO[0] + 310, 0, 1) * s.vgrad(CO[1] - 500, CO[1] - 100, 0.3, 1))
    s.lift(body * s.rgrad(CO[0] - 150, CO[1] - 480 + T, 30, 260, 1, 0), 0.16, soft=0, wob=0)
    s.spatter(22, BURNT, 0.4, box=(CO[0] - 300, CO[1] - 560, CO[0] + 300, CO[1] + 340), r=(0.8, 2.4))
    anchor = (float(CO[0]), float(CO[1] + round(top)))            # the middle of the collar, on top of the chair back
    s.save("ch_coat", crop=True, anchor=anchor, meta={"on_chair": [0, int(round(top))]})
    # its shadow on the wall, for when the compositor wants one (same anchor)
    k = Sheet(CW + 160, CH_, 46)
    fl = CO[1] + (FLOOR_Y - CHAIR[1])
    u2 = np.zeros((k.h, k.w), np.float32)
    u2[:, :CW] = np.clip(s.body, 0, 1)
    wall = 1 - sstep(fl - 10, fl + 6, k.Y)
    a = shift(k, u2, 104, 6, 18, 0.90, (CO[0], fl)) * wall
    k.wash(a, UMBER, 0.36, wob=0, soft=0, edge=0, gran=0.45, flow=0.3, fs=160)
    k.wash(a, PAYNE, 0.28, wob=0, soft=0, edge=0, gran=0.45, flow=0.3, fs=160)
    k.wash(shift(k, u2, 36, 44, 32, 0.92, (CO[0], fl)) * wall, UMBER, 0.28, wob=0, soft=0, edge=0, gran=0.45)
    k.save("ch_coat_sh", crop=True, anchor=anchor)


ALL = {"chair_bg": bg, "chair_chair": chair, "chair_sh": chair_sh, "chair_coat": coat, "chair_table": table}
