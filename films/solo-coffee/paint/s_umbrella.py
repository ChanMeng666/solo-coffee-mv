"""The crossing from straight above (second chorus): a wet street at night and the umbrellas that stream over it.
um_ground is one opaque sheet, 3072x1728 (1.6x the frame); every umbrella is its own small sprite, anchored at the
canopy centre, with its canopy radius in the manifest ("r"). Light comes from the upper left."""
import math

import cv2
import numpy as np

from kit import *

GW, GH = 3072, 1728
TAU = 2 * math.pi
LA = math.atan2(-1, -1)                 # where the light is (upper left)
LD = np.array([-0.7071, -0.7071])


# ---------------------------------------------------------------------------------------------- small habits
def _lift(s, m, amt, clip=None, soft=1.5, wob=1.2, bleed=0.0, dry=0.0, gran=0.15, flow=0.0, fs=80):
    """Lift with a clip (the engine's own lift has none)."""
    return s.wash(m, None, amt, wob=wob, soft=soft, edge=0, gran=gran, flow=flow, fs=fs, bleed=bleed, dry=dry, lift=True, clip=clip)


def _white(s, m, amt, soft=0.8):
    """Opaque paper showing through a see-through sprite: clear the pigment and mark body (for the plastic umbrella)."""
    if soft > 0:
        m = cv2.GaussianBlur(m, (0, 0), soft)
    m = np.clip(m * amt, 0, 1)
    s.A *= (1 - m)[..., None]
    s.body = np.maximum(s.body, m)


def _bez(a, b, c, n=16):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * a + 2 * t * (1 - t) * c + t * t * b


def _dots(s, pts, rad, r=None):
    m = np.zeros((s.h, s.w), np.uint8)
    for i, (x, y) in enumerate(pts):
        rr = rad if r is None else rad * (0.8 + 0.4 * r.random())
        cv2.circle(m, (int(round(x * 16)), int(round(y * 16))), max(2, int(rr * 16)), 255, -1, cv2.LINE_AA, 4)
    return m.astype(np.float32) / 255


# ---------------------------------------------------------------------------------------------- the street
CA = math.radians(-12)                  # the crossing runs up to the right
C0 = (1536.0, 990.0)
_ca, _sa = math.cos(CA), math.sin(CA)
BAND = 318                              # half the length of a bar


def X(u, v):
    """Crossing coordinates (u along the crossing, v along the road) -> sheet."""
    return (C0[0] + u * _ca - v * _sa, C0[1] + u * _sa + v * _ca)


def ky(x):
    """The kerb line."""
    return 250 - 0.014 * x


def _crack(s, r, x, y, ang, L, w=1.8, k=1.3, color=INKBLUE):
    pts = [(x, y)]
    for _ in range(max(2, int(L / 38))):
        ang += (r.random() - 0.5) * (1.5 if r.random() < 0.2 else 0.45)
        st = 38 * (0.5 + r.random())
        x, y = x + math.cos(ang) * st, y + math.sin(ang) * st
        pts.append((x, y))
    s.ink(pts, w, color, k, tremor=1.3, skip=0.12, smooth=False, taper=(0.15, 0.4))
    return pts


def _mark(s, m, amt, r, tint=0.42):
    """Road paint: thermoplastic gone thin. Lifted paper (broken over the tooth), then a cream wash that pools."""
    s.wash(m, None, amt * 0.86, wob=3.0, soft=1.3, edge=0, gran=0.3, flow=0.35, fs=90, lift=True)
    s.wash(m, None, amt * 0.5, wob=4.0, soft=1.2, edge=0, gran=0.5, flow=0.6, fs=60, dry=0.36, lift=True)
    s.wash(m, CREAM, tint, wob=3.0, soft=1.2, edge=0.6, ew=6, gran=0.4, flow=0.5, fs=80)
    s.wash(m, SLATE, 0.08 + 0.10 * r.random(), wob=5, bleed=9, edge=0.2, gran=0.4, flow=0.6, fs=50)


def _puddle(s, r, cx, cy, rx, ry, rot=0.0, lift=0.5, k=0.30):
    m = s.blob(cx, cy, rx, ry, 0.26, 9, rot=rot)
    for _ in range(2):
        a = r.random() * TAU
        m = np.maximum(m, s.blob(cx + math.cos(a) * rx * 0.6, cy + math.sin(a) * ry * 0.6, rx * (0.35 + 0.3 * r.random()), ry * (0.35 + 0.3 * r.random()), 0.3, 8, rot=rot + r.random()))
    wet = cv2.GaussianBlur(m, (0, 0), 26)
    s.wash(np.clip(wet * 1.5, 0, 1) * (1 - m), INKBLUE, 0.13, wob=4, bleed=14, edge=0.1, gran=0.35)       # soaked asphalt round it
    _lift(s, m, lift + 0.1, wob=5, bleed=13, gran=0.1, flow=0.3)
    P = s.wash(m, RAIN, k, wob=5, bleed=7, edge=1.0, ew=10, gran=0.2, flow=0.55, fs=80)                   # sky in the water, pooled rim
    s.wash(m, TEAL, 0.12, wob=6, bleed=18, edge=0.3, gran=0.2)
    # the sky is brightest toward the light; the water thins to dark at the bank
    _lift(s, s.blob(cx - rx * 0.22, cy - ry * 0.2, rx * 0.5, ry * 0.42, 0.3, 8, rot=rot), 0.30, clip=P, wob=4, bleed=12)
    s.wash(P * (1 - cv2.GaussianBlur(P, (0, 0), 7)) * 2, PRUSSIAN, 0.30, wob=1, soft=1.5, edge=0, gran=0.3)                # thin water at the bank
    for _ in range(2):                                                                                     # a few glints
        x, y = cx + (r.random() - 0.5) * rx * 1.1, cy + (r.random() - 0.5) * ry * 1.0
        L = 16 + 34 * r.random()
        _lift(s, s.ribbon([(x - L, y + 2), (x, y - 1), (x + L, y + 1)], 3 + 3 * r.random(), (0.45, 0.45)), 0.34, clip=P, soft=1.6, wob=0.7)
    # the pen finds only part of the edge
    cnt, _ = cv2.findContours((P > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if cnt:
        c = max(cnt, key=len)[:, 0, :].astype(np.float64)[::14]
        if len(c) > 12:
            i0 = int(r.integers(0, len(c)))
            c = np.roll(c, -i0, axis=0)
            n = len(c)
            s.ink(c[: int(n * (0.16 + 0.14 * r.random()))], 1.6, INKBLUE, 0.9, tremor=1.0, skip=0.1)
            if r.random() < 0.5:
                s.ink(c[int(n * 0.55): int(n * 0.68)], 1.2, INKBLUE, 0.7, tremor=1.0, skip=0.2)
    return P


def ground():
    s = Sheet(GW, GH, 61)
    r = rs(61)
    # ---- asphalt: deep cool washes, wet in wet
    s.glaze(PRUSSIAN, 0.47, flow=0.6, fs=520, gran=0.3)
    s.glaze(PAYNE, 0.36, grad=0.25 + 0.75 * s.noise(430, 3), flow=0.3, gran=0.35)
    for col, k, n, sz in ((INDIGO, 0.28, 7, 330), (TEAL, 0.26, 7, 300), (VIOLET, 0.15, 4, 260), (INKBLUE, 0.14, 5, 240)):
        for _ in range(n):
            x, y = r.random() * GW, r.random() * GH
            s.wash(s.blob(x, y, sz * (0.6 + 0.8 * r.random()), sz * (0.4 + 0.5 * r.random()), 0.3, 9, rot=r.random() * 3), col, k * (0.6 + 0.6 * r.random()),
                   wob=6, bleed=34, edge=0.3, gran=0.3, flow=0.5, fs=160)
    # backruns: a few hard-edged blooms where a wet brush went back in
    for _ in range(5):
        x, y = r.random() * GW, 300 + r.random() * (GH - 300)
        _lift(s, s.blob(x, y, 150 + 160 * r.random(), 90 + 90 * r.random(), 0.35, 10, rot=r.random() * 3), 0.16, wob=7, bleed=6, flow=0.5)
    # a newer patch of tarmac, upper left
    pc = [(236, 352), (612, 318), (640, 628), (262, 664)]
    pm = Q(s, pc)
    s.wash(pm, INKBLUE, 0.24, wob=3, soft=1.5, edge=0.8, ew=7, gran=0.45, flow=0.5, fs=90)
    s.wash(pm, PAYNE, 0.16, wob=4, bleed=10, dry=0.35, gran=0.4)
    path(s, pc, 1.8, INKBLUE, 1.0, closed=True, over=8, r=r, skip=0.25, tremor=1.2)
    # ---- tyre tracks: darker dry-brush streaks down the road, and one car that turned
    tr = s.zeros()
    for u in (-1065, -585, 505, 985):
        uu = u + (r.random() - 0.5) * 30
        pts = [X(uu + (r.random() - 0.5) * 44, v) for v in np.linspace(-1500, 1500, 9)]
        tr = np.maximum(tr, s.ribbon(pts, 96))
        s.stroke(pts, 100, PAYNE, 0.12, taper=(0, 0), dry=0.36, edge=0.1, wob=5, gran=0.4, flow=0.9, fs=150)
        s.stroke([(x + 10, y) for x, y in pts], 44, INKBLUE, 0.11, taper=(0, 0), dry=0.48, edge=0.15, wob=3, gran=0.4, flow=1.0, fs=90)
        s.stroke([(x - 30, y) for x, y in pts], 22, INKBLUE, 0.10, taper=(0, 0), dry=0.5, edge=0.1, wob=3, gran=0.4, flow=1.0, fs=60)
    for R0, w in ((560, 90), (1010, 80)):       # the turn, pivoting about a point above the top left corner
        a = np.linspace(0.42, 1.25, 9)
        pts = [(240 + math.cos(t) * R0 * 1.25, 130 + math.sin(t) * R0) for t in a]
        s.stroke(pts, w, PAYNE, 0.17, taper=(0.15, 0.25), dry=0.55, edge=0.1, wob=4, gran=0.5, flow=0.8)
    tr = cv2.GaussianBlur(tr, (0, 0), 16)
    # ---- the paint on the road
    wear = 0.62 * s.noise(110, 4, seed=901) + 0.38 * s.noise(15, 3, seed=902) - 0.10 * tr
    hole = sstep(0.19, 0.27, wear)
    for i in range(-7, 8):
        u0 = i * 300 + 40 + (r.random() - 0.5) * 14
        hw = 74 + (r.random() - 0.5) * 12
        v0, v1 = -BAND + (r.random() - 0.5) * 26, BAND + (r.random() - 0.5) * 26
        j = lambda: (r.random() - 0.5) * 12
        cs = [X(u0 - hw + j(), v0 + j()), X(u0 + hw + j(), v0 + j()), X(u0 + hw + j(), v1 + j()), X(u0 - hw + j(), v1 + j())]
        if max(c[0] for c in cs) < -40 or min(c[0] for c in cs) > GW + 40:
            continue
        m = Q(s, cs)
        if r.random() < 0.6:                    # a ghost of the last time it was painted, a hand's width off
            _lift(s, Q(s, [(x + 13, y - 9) for x, y in cs]), 0.13, wob=3, soft=2, dry=0.4)
        for _ in range(int(r.integers(0, 3))):  # a corner or a bite gone
            q = cs[int(r.integers(0, 4))]
            m = m * (1 - s.blob(q[0] + (r.random() - 0.5) * 50, q[1] + (r.random() - 0.5) * 50, 34 + 50 * r.random(), 26 + 40 * r.random(), 0.35, 8))
        if r.random() < 0.3:                    # worn through across the middle
            vv = (r.random() - 0.5) * BAND * 1.3
            q = X(u0 + (r.random() - 0.5) * 60, vv)
            m = m * (1 - 0.9 * s.blob(q[0], q[1], 60 + 60 * r.random(), 22 + 30 * r.random(), 0.4, 9, rot=CA + (r.random() - 0.5)))
        m = m * hole
        _mark(s, m, 0.70 + 0.22 * r.random(), r, tint=0.30 + 0.16 * r.random())
        for _ in range(int(r.integers(1, 4))):  # dirt dragged along it by the wheels
            uu = u0 + (r.random() - 0.5) * hw * 1.6
            va = v0 + r.random() * (v1 - v0) * 0.6
            s.stroke([X(uu, va), X(uu + (r.random() - 0.5) * 16, va + 120), X(uu + (r.random() - 0.5) * 16, va + 180 + 160 * r.random())], 18 + 36 * r.random(), PAYNE,
                     0.10 + 0.10 * r.random(), taper=(0.3, 0.4), dry=0.36 + 0.08 * r.random(), edge=0.25, wob=3, gran=0.4, flow=0.8, fs=50, clip=m)
        # pen: two or three sides, not all of them, and never the whole side
        for a, b in zip(cs, cs[1:] + cs[:1]):
            if r.random() < 0.75:
                a, b = np.asarray(a), np.asarray(b)
                t0, t1 = r.random() * 0.25, 1 - r.random() * 0.25
                seg(s, a + (b - a) * t0 if r.random() < 0.5 else a, a + (b - a) * t1, 1.7, SEPIA, 1.0, over=8 * r.random(), r=r, skip=0.08, tremor=1.1)
        if r.random() < 0.3:
            q = X(u0 + (r.random() - 0.5) * hw, v0 + r.random() * (v1 - v0))
            _crack(s, r, q[0], q[1], r.random() * TAU, 120 + 160 * r.random(), 1.4, 1.0)
    # stop line, centre line and a lane arrow on the near side
    sl = Q(s, [X(150, 418), X(1760, 410), X(1760, 458), X(150, 464)]) * sstep(0.30, 0.42, wear + 0.03)
    _mark(s, sl, 0.74, r, tint=0.4)
    seg(s, X(150, 416), X(1400, 410), 1.6, SEPIA, 0.9, r=r, skip=0.1, tremor=1.2)
    seg(s, X(420, 465), X(1760, 460), 1.6, SEPIA, 0.9, r=r, skip=0.12, tremor=1.2)
    cl = Q(s, [X(100, 418), X(124, 418), X(128, 900), X(102, 900)]) * sstep(0.33, 0.45, wear + 0.02)
    _mark(s, cl, 0.6, r, tint=0.36)
    ar = np.maximum(Q(s, [X(872, 640), X(930, 640), X(926, 878), X(876, 874)]), Q(s, [X(900, 520), X(996, 668), X(806, 664)]))
    _mark(s, ar * sstep(0.31, 0.43, wear), 0.7, r, tint=0.38)
    path(s, [X(900, 518), X(998, 668), X(930, 666), X(926, 880), X(876, 876), X(872, 664), X(804, 664)], 1.6, SEPIA, 0.9, closed=True, over=5, r=r, skip=0.12)
    # tyres went over the paint again
    for u in (-585, 505, 985):
        pts = [X(u + 10 + (r.random() - 0.5) * 20, v) for v in np.linspace(-BAND - 120, BAND + 240, 5)]
        s.stroke(pts, 64, PAYNE, 0.13, taper=(0.2, 0.3), dry=0.42, edge=0.1, wob=3, gran=0.4, flow=1.0, fs=60)
    # ---- manhole cover, left of centre
    mx, my, Rm = 905, 566, 126
    cast(s, s.ellipse(mx, my, Rm + 20, Rm + 20), 5, 6, INKBLUE, 0.35, blur=10)
    fr = s.ellipse(mx, my, Rm + 20, Rm + 20)
    _lift(s, fr, 0.5, soft=1.5)
    s.wash(fr, PAYNE, 0.26, wob=1.5, edge=0.6, ew=7, gran=0.5, flow=0.5, fs=40)
    cov = s.ellipse(mx, my, Rm, Rm)
    s.wash(cov, UMBER, 0.16, wob=1.5, soft=1.5, edge=0.6, ew=8, gran=0.5, flow=0.7, fs=36)
    s.wash(cov, BURNT, 0.16, wob=3, bleed=12, grad=s.rgrad(mx + 40, my + 50, 10, 150, 1, 0), gran=0.6)       # rust
    s.wash(cov, INKBLUE, 0.26, wob=0, soft=0, edge=0, grad=s.rgrad(mx - 50, my - 56, 60, 250, 0, 1))          # dished: far side in shade
    _lift(s, s.ribbon(ell(mx, my, Rm * 0.88, Rm * 0.88, 3.3, 4.5, 16), 15, (0.3, 0.3)), 0.42, soft=3, dry=0.25)   # wet iron catching the light
    _lift(s, s.ribbon(ell(mx, my, Rm * 0.44, Rm * 0.44, 3.4, 4.6, 12), 10, (0.3, 0.3)), 0.36, soft=2.5)
    oval(s, mx, my, Rm + 20, Rm + 20, 2.6, INKBLUE, 1.5, twice=True, tremor=1.0)
    oval(s, mx, my, Rm, Rm, 2.8, INK, 1.6, tremor=0.9)
    for q, w, k in ((0.80, 1.8, 1.3), (0.58, 1.8, 1.3), (0.33, 1.6, 1.2)):
        oval(s, mx + r.random() * 2, my + r.random() * 2, Rm * q, Rm * q, w, INK, k, tremor=0.9, skip=0.12)
    for i in range(28):                         # the tread: three rings of raised bars, each ring out of step with the last
        a = i * TAU / 28
        seg(s, (mx + math.cos(a) * Rm * 0.83, my + math.sin(a) * Rm * 0.83), (mx + math.cos(a) * Rm * 0.97, my + math.sin(a) * Rm * 0.97), 2.4, INK, 1.4, over=0, skip=0.1)
    for i in range(16):
        a = (i + 0.5) * TAU / 16
        s.ink(ell(mx, my, Rm * 0.69, Rm * 0.69, a - 0.12, a + 0.12, 6), 5.5, INK, 1.1, tremor=0.5, taper=(0.3, 0.3))
    for i in range(8):
        a = i * TAU / 8 + 0.2
        seg(s, (mx + math.cos(a) * Rm * 0.36, my + math.sin(a) * Rm * 0.36), (mx + math.cos(a) * Rm * 0.55, my + math.sin(a) * Rm * 0.55), 3.2, INK, 1.2, over=0)
    s.hatch(s.ellipse(mx, my, Rm * 0.30, Rm * 0.30), 0.8, 9, 1.3, INK, 1.1)
    s.hatch(s.ellipse(mx, my, Rm * 0.30, Rm * 0.30), 0.8 + math.pi / 2, 9, 1.3, INK, 1.0)
    for a in (0.9, 0.9 + math.pi):              # the two keyholes
        hx, hy = mx + math.cos(a) * Rm * 0.69, my + math.sin(a) * Rm * 0.69
        s.wash(s.ellipse(hx, hy, 9, 6, math.degrees(a) + 90), INK, 1.4, wob=0.5, soft=0.6)
    # ---- pavement along the top: flags, kerbstones, gutter, a drain
    KS = 42                                                         # kerbstone depth
    pav = Q(s, [(-20, -20), (GW + 20, -20), (GW + 20, ky(GW) - KS), (-20, ky(0) - KS)])
    _lift(s, pav, 0.62, wob=1, soft=1)
    s.wash(pav, SLATE, 0.26, wob=1, soft=1, edge=0.2, gran=0.4, flow=0.5, fs=200)
    s.wash(pav, UMBER, 0.13, wob=4, bleed=20, grad=0.3 + 0.7 * s.noise(260, 3), gran=0.5)
    rows = [(ky(0) - KS - 196, ky(0) - KS), (-40, ky(0) - KS - 196)]
    for ri, (ya, yb) in enumerate(rows):
        x = -130 + 105 * ri - r.random() * 60
        while x < GW + 40:
            wd = 236 + (r.random() - 0.5) * 16
            d = -0.014 * x
            fm = Q(s, [(x + 3, ya + d + 3), (x + wd - 3, ya + d - 0.014 * wd + 3), (x + wd - 3, yb + d - 0.014 * wd - 3), (x + 3, yb + d - 3)])
            q = r.random()
            s.wash(fm, (SLATE, PAYNE, UMBER, RAIN)[int(r.integers(0, 4))], 0.05 + 0.17 * q, wob=2, soft=1.2, edge=0.7, ew=6, gran=0.45, flow=0.7, fs=70)
            if r.random() < 0.35:
                _lift(s, fm, 0.2, wob=3, bleed=10, flow=0.6)
            if r.random() < 0.25:                # a cracked flag
                _crack(s, r, x + wd * r.random(), ya + d + 20, 1.2 + r.random() * 0.8, 170, 1.4, 1.1)
            seg(s, (x, ya + d), (x, yb + d), 1.8, INKBLUE, 1.2, over=5, r=r, skip=0.18, tremor=1.0)
            x += wd
        if ri == 0:
            seg(s, (-10, ya + 2), (GW + 10, ya - 0.014 * GW + 2), 2.0, INKBLUE, 1.25, r=r, skip=0.12, tremor=1.2, bow=0.001)
    s.wash(pav, MOSS, 0.10, wob=4, bleed=16, grad=sstep(0.55, 0.8, s.noise(120, 3)), gran=0.6)              # a little green in the joints
    kerb = Q(s, [(-20, ky(0) - KS), (GW + 20, ky(GW) - KS), (GW + 20, ky(GW)), (-20, ky(0))])
    _lift(s, kerb, 0.66, wob=1, soft=0.8)
    s.wash(kerb, MIST, 0.34, wob=1, soft=0.8, edge=0.5, ew=5, gran=0.6, flow=0.6, fs=120)
    s.wash(kerb, PAYNE, 0.26, wob=1, soft=2, edge=0, grad=s.vgrad(ky(1500) - KS + 8, ky(1500) + 8), gran=0.5)   # its face turns down to the road
    seg(s, (-10, ky(0) - KS), (GW + 10, ky(GW) - KS), 2.2, SEPIA, 1.3, r=r, skip=0.08, tremor=1.2, bow=0.001)
    seg(s, (-10, ky(0)), (GW + 10, ky(GW)), 3.0, INK, 1.6, r=r, tremor=1.3, bow=0.001)
    seg(s, (300, ky(300) + 3), (2500, ky(2500) + 2), 1.6, INK, 0.9, r=r, skip=0.4, tremor=1.3, bow=0.001)
    x = 90.0
    while x < GW:
        seg(s, (x, ky(x) - KS), (x + 2, ky(x)), 1.8, SEPIA, 1.2, over=4, r=r)
        x += 372 + (r.random() - 0.5) * 30
    gut = Q(s, [(-20, ky(0)), (GW + 20, ky(GW)), (GW + 20, ky(GW) + 74), (-20, ky(0) + 74)])
    s.wash(gut, INKBLUE, 0.34, wob=3, bleed=12, edge=0.2, gran=0.4, flow=0.5, fs=200)                       # the kerb's shadow and the wet gutter
    for x0, x1 in ((40, 1500), (1790, 3050)):
        pts = [(x, ky(x) + 30 + 9 * math.sin(x * 0.011)) for x in np.linspace(x0, x1, 9)]
        _lift(s, s.ribbon(pts, 20, (0.2, 0.2)), 0.30, wob=4, bleed=5)                                       # water running to the drain
        s.ink(pts, 1.4, INKBLUE, 0.8, tremor=1.5, skip=0.5)
    gx0, gx1 = 1556, 1738
    gy0 = ky(gx0) + 7
    gc = [(gx0, gy0), (gx1, gy0 - 2.5), (gx1 + 2, gy0 + 96), (gx0 + 2, gy0 + 99)]
    gm = Q(s, gc)
    s.wash(gm, INKBLUE, 1.0, wob=1, soft=0.8, edge=0.5, gran=0.4)
    s.wash(gm, UMBER, 0.2, wob=2, bleed=6)
    for i in range(9):                           # iron slats: lifted, one bent
        xx = gx0 + 14 + i * 19.6
        dx = 5 if i == 5 else 0
        _lift(s, Q(s, [(xx, gy0 + 9), (xx + 9, gy0 + 9), (xx + 9 + dx, gy0 + 88), (xx + dx, gy0 + 88)]), 0.56, clip=gm, soft=0.8, wob=0.8, dry=0.15)
        seg(s, (xx + 9.5, gy0 + 9), (xx + 9.5 + dx, gy0 + 88), 1.3, INK, 1.2, over=0, r=r)
    _lift(s, Q(s, [(gx0 + 4, gy0 + 44), (gx1 - 4, gy0 + 43), (gx1 - 4, gy0 + 52), (gx0 + 4, gy0 + 53)]), 0.5, clip=gm, soft=0.8, wob=0.6)
    path(s, gc, 2.4, INK, 1.6, closed=True, over=7, r=r)
    path(s, [(gx0 - 12, gy0 - 2), (gx1 + 12, gy0 - 4), (gx1 + 14, gy0 + 110), (gx0 - 10, gy0 + 113)], 1.5, INKBLUE, 1.0, closed=True, over=6, r=r, skip=0.25)
    for i in range(3):                           # leaves caught on it
        lx, ly = gx0 + 30 + 60 * i + r.random() * 20, gy0 + 20 + r.random() * 60
        s.wash(s.ellipse(lx, ly, 13, 6, r.random() * 180), (OCHRE, BURNT, MOSS)[i], 0.7, wob=1, soft=0.8, edge=0.5)
    # ---- puddles
    for cx, cy, rx, ry, rot, lf in ((392, 792, 190, 96, -0.25, 0.5), (1290, 462, 150, 70, 0.1, 0.46), (2385, 352, 230, 60, -0.03, 0.5),
                                    (1105, 1178, 150, 100, -0.3, 0.44), (1985, 1392, 210, 105, -0.2, 0.52), (2742, 1020, 120, 78, 0.5, 0.46),
                                    (318, 1568, 170, 80, 0.15, 0.5), (1705, 742, 96, 60, -0.4, 0.4), (2890, 1560, 150, 84, -0.1, 0.48)):
        _puddle(s, r, cx, cy, rx, ry, rot, lf)
    for _ in range(16):                          # and the small ones that fill every dip
        x, y = r.random() * GW, 330 + r.random() * (GH - 330)
        m = s.blob(x, y, 18 + 44 * r.random(), 10 + 22 * r.random(), 0.3, 8, rot=r.random() * 3)
        _lift(s, m, 0.34, wob=3, bleed=5)
        s.wash(m, RAIN, 0.22, wob=3, bleed=3, edge=1.0, ew=5, gran=0.2)
    # ---- where the light will fall: a touch paler, with warm pigment bled in
    for cx, cy, rr, col, sy in ((1240, 800, 430, OCHRE, 0.75), (2370, 880, 400, ROSE, 0.8), (640, 1440, 400, OCHRE, 0.7), (2820, 1400, 360, ROSE, 0.8), (1780, 420, 330, OCHRE, 0.6)):
        m = s.rgrad(cx, cy, rr * 0.1, rr, 1, 0, sy) * (0.55 + 0.45 * s.noise(150, 3))
        s.A *= (1 - 0.30 * m)[..., None]
        s.wash(s.blob(cx, cy, rr * 0.62, rr * 0.62 * sy, 0.3, 9), col, 0.11, wob=6, bleed=46, edge=0.15, gran=0.5, flow=0.5)
        for _ in range(4):                       # light drags down the wet road in streaks
            x = cx + (r.random() - 0.5) * rr
            y = cy + (r.random() - 0.5) * rr * sy
            L = 60 + 110 * r.random()
            _lift(s, s.ribbon([(x, y - L), (x + 6, y), (x + 2, y + L)], 16 + 14 * r.random(), (0.5, 0.5)), 0.13, wob=4, soft=5, dry=0.35)
    # ---- grit, cracks, sparkle
    for _ in range(4):
        _crack(s, r, r.random() * GW, 340 + r.random() * (GH - 380), r.random() * TAU, 200 + 260 * r.random(), 1.4 + 0.8 * r.random(), 1.0)
    s.spatter(650, INKBLUE, 0.34, r=(0.8, 2.6))
    s.spatter(420, None, 0.2, r=(0.7, 2.4), lift=True)
    s.spatter(26, INKBLUE, 0.3, box=(0, 300, GW, GH), r=(3, 9))
    s.salt(s.full(), 0.26, 1.5, 0.0016)
    s.glaze(INDIGO, 0.08, grad=s.rgrad(GW / 2, GH / 2 + 60, 900, 2000, 0, 1), flow=0.2)                    # hold the corners
    s.save("um_ground", opaque=True, q=90)


# ---------------------------------------------------------------------------------------------- umbrellas
def _geom(c, R, seed, n=8, bow=0.15, off=0.05, jit=0.11):
    """Rib tips on a not-quite-regular octagon, a ferrule a little off centre, edges that sag in between the tips."""
    r = rs(seed * 31 + 5)
    ang = r.random() * TAU + np.arange(n) * TAU / n + (r.random(n) - 0.5) * jit
    rad = 1 + (r.random(n) - 0.5) * 0.055
    rad = R * rad / rad.max()
    q = r.random() * TAU
    f = np.array([c + math.cos(q) * R * off, c + math.sin(q) * R * off])
    tips = np.stack([c + np.cos(ang) * rad, c + np.sin(ang) * rad], 1)
    edges = []
    for i in range(n):
        a, b = tips[i], tips[(i + 1) % n]
        mid = (a + b) / 2
        edges.append(_bez(a, b, mid + (f - mid) * bow * (0.75 + 0.5 * r.random())))
    return f, tips, edges, r


def _sc(P, f, k):
    return f + (np.asarray(P) - f) * k


def umbrella(name, R, col, k0, dark, kd, seed, pen=INK, pk=1.6, alt=None, band=None, dots=None, vent=False, hem=False,
             sheen=1.0, gran=0.45, drops=True, tip=None, trim=None):
    """One umbrella from straight above. col/k0: the cloth; dark/kd: its shadow pigment; alt=(colour, k): every other panel
    washed again; band=(lo, hi, colour, k, lift): a border band; dots=(colour, lift): polka dots; vent: a golf umbrella's
    second canopy; trim=(colour, k): piping along the hem."""
    S = int(2 * R + 150)
    c = S / 2
    s = Sheet(S, S, seed)
    f, tips, edges, r = _geom(c, R, seed)
    n = len(tips)
    out = np.vstack(edges)
    W = base(s, s.poly(out, smooth=False), col, k0, wob=1.1, soft=0.8, edge=0.35, ew=6, flow=0.45, fs=70, gran=gran)
    pms, lit = [], []
    for i in range(n):
        pms.append(s.poly(np.vstack([f[None], edges[i]]), smooth=False))
        d = (tips[i] + tips[(i + 1) % n]) / 2 - f
        lit.append(0.5 + 0.5 * math.cos(math.atan2(d[1], d[0]) - LA))
    if alt:
        for i in range(0, n, 2):
            s.wash(pms[i], alt[0], alt[1], wob=0.7, soft=0.7, edge=0.4, ew=5, gran=gran, flow=0.4, fs=60, clip=W)
    if band:
        lo, hi, bc, bk, bl = band
        bm = s.poly(_sc(out, f, hi), smooth=False) * (1 - s.poly(_sc(out, f, lo), smooth=False))
        if bl:
            _lift(s, bm, bl, clip=W, soft=0.8, wob=0.8)
        if bc is not None:
            s.wash(bm, bc, bk, wob=0.8, soft=0.8, edge=0.4, ew=3, gran=gran, clip=W)
    if dots:
        pts = []
        for i in range(n):
            a, b = tips[i] - f, tips[(i + 1) % n] - f
            for t, cnt in ((0.30, 1), (0.50, 2), (0.70, 3), (0.875, 3)):
                for j in range(cnt):
                    q = (j + 0.5) / cnt + (0.25 / cnt if cnt == 3 and t > 0.8 else 0) * (1 if i % 2 else -1)
                    p = f + t * ((1 - q) * a + q * b) * (1 - 0.10 * 4 * q * (1 - q) * (t > 0.8))
                    pts.append(p + (r.random(2) - 0.5) * R * 0.02)
        dm = _dots(s, pts, R * 0.043, r)
        _lift(s, dm, dots[1], clip=W, soft=0.7, wob=0.35)
        s.wash(dm, dots[0], 0.3, wob=0.35, soft=0.7, edge=0.6, ew=2, clip=W)
    # ---- each panel its own value: toward the light paler, away from it darker; a ridge at every rib
    for i in range(n):
        pm, L = pms[i], lit[i]
        sh = float(np.clip(1 - L + (r.random() - 0.5) * 0.22, 0, 1))
        s.wash(pm, dark, kd * (0.10 + 0.90 * sh ** 1.25), wob=0.6, soft=0.7, edge=0.35, ew=5, gran=gran, flow=0.45, fs=46, clip=W)
        if L > 0.5:
            _lift(s, pm, 0.34 * (L - 0.5) * 2 * sheen, clip=W, soft=0.8, wob=0.6, flow=0.5, fs=40)
        j = (i + 1) % n
        near, far = (i, j) if math.cos(math.atan2(*(tips[i] - f)[::-1]) - LA) > math.cos(math.atan2(*(tips[j] - f)[::-1]) - LA) else (j, i)
        e = edges[i] if near == i else edges[i][::-1]
        s.wash(s.poly(np.vstack([f[None], e[:6]]), smooth=False), dark, kd * 0.26, wob=0.8, soft=R * 0.035, edge=0, gran=gran, clip=pm * W)
        _lift(s, s.poly(np.vstack([f[None], e[-5:]]), smooth=False), 0.16 * sheen, clip=pm * W, soft=R * 0.03, wob=0.8)
    # ---- the dome: falls away from the light, a lip of shade along the far edge
    s.wash(W, dark, kd * 0.42, wob=0, soft=0, edge=0, gran=gran, flow=0.3, fs=90, grad=s.rgrad(c - 0.32 * R, c - 0.36 * R, 0.4 * R, 1.75 * R, 0, 1))
    lip = W * (1 - cv2.warpAffine(W, np.float32([[1, 0, -R * 0.07], [0, 1, -R * 0.075]]), (S, S)))
    s.wash(cv2.GaussianBlur(lip, (0, 0), R * 0.02) * W, dark, kd * 0.55, wob=0, soft=0, edge=0, gran=gran)
    _lift(s, s.rgrad(c - 0.30 * R, c - 0.36 * R, 0, 0.62 * R, 1, 0) * W, 0.24 * sheen, soft=0, wob=0)
    if vent:        # the upper canopy overlaps the lower one: its edge, a thin shadow under it
        vt = _sc(tips, f, 0.47)
        ve = [_bez(vt[i], vt[(i + 1) % n], (vt[i] + vt[(i + 1) % n]) / 2 + (f - (vt[i] + vt[(i + 1) % n]) / 2) * 0.05) for i in range(n)]
        vm = s.poly(np.vstack(ve), smooth=False)
        s.wash(cv2.GaussianBlur(cv2.warpAffine(vm, np.float32([[1, 0, 7], [0, 1, 8]]), (S, S)) * (1 - vm), (0, 0), 2.6), dark, 0.9, wob=0, soft=0, edge=0, clip=W)
        _lift(s, vm, 0.20, clip=W, soft=1.0, wob=0.8, flow=0.4, fs=40)
        _lift(s, vm * (1 - s.poly(_sc(np.vstack(ve), f, 0.90), smooth=False)) * s.rgrad(c - 0.5 * R, c - 0.5 * R, 0.2 * R, 0.9 * R, 1, 0), 0.4, clip=W, soft=1.2, wob=0.6)
        for i in range(n):
            s.ink(ve[i][::3], 1.8, pen, pk, tremor=0.7)
    # ---- wet sheen: a broken band of lifted light across the panels that face the lamp, long drags down two of them
    for i in range(n):
        L = lit[i]
        if L < 0.56:
            continue
        a, b = tips[i] - f, tips[(i + 1) % n] - f
        t = 0.56 + (r.random() - 0.5) * 0.10
        p0, p1 = f + t * (0.86 * a + 0.14 * b), f + (t + (r.random() - 0.5) * 0.05) * (0.16 * a + 0.84 * b)
        _lift(s, s.ribbon([p0, (p0 + p1) / 2 + (r.random(2) - 0.5) * 3, p1], R * (0.05 + 0.05 * L), (0.35, 0.35)), (0.26 + 0.34 * (L - 0.56) / 0.44) * sheen,
              clip=W, soft=R * 0.012 + 1.2, wob=0.9, dry=0.2, gran=0.3)
        if L > 0.66 or r.random() < 0.35:
            q = 0.3 + 0.4 * r.random()
            d = (1 - q) * a + q * b
            _lift(s, s.ribbon([f + d * (0.26 + 0.1 * r.random()), f + d * 0.6, f + d * (0.78 + 0.1 * r.random())], R * (0.03 + 0.03 * r.random()), (0.45, 0.5)),
                  (0.24 + 0.22 * L) * sheen, clip=W, soft=R * 0.014 + 1, wob=0.5, dry=0.1)
        if L > 0.8:
            d = (0.72 * a + 0.28 * b)
            _lift(s, s.ribbon([f + d * 0.66, f + d * 0.88], R * 0.016, (0.4, 0.4)), 0.6 * sheen, clip=W, soft=0.9, wob=1.0)
    if drops:
        _lift(s, _dots(s, [(c + (r.random() - 0.5) * 2 * R, c + (r.random() - 0.5) * 2 * R) for _ in range(46)], 1.5, r), 0.55, clip=W, soft=0.5, wob=0.4)
        s.wash(_dots(s, [(c + (r.random() - 0.5) * 2 * R, c + (r.random() - 0.5) * 2 * R) for _ in range(24)], 1.4, r), dark, 0.5, wob=0.4, soft=0.5, edge=0.6, ew=1.5, clip=W)
    if trim:
        tm = s.poly(out, smooth=False) * (1 - s.poly(_sc(out, f, 0.965), smooth=False))
        _lift(s, tm, 0.75, clip=W, soft=0.6, wob=0.5)
        s.wash(tm, trim[0], trim[1], wob=0.5, soft=0.6, edge=0.3, ew=2, clip=W)
    # ---- pen: ribs (a lifted hair of light on the lamp side of each), the scalloped hem edge by edge, tips, ferrule
    for i in range(n):
        d = tips[i] - f
        u = d / np.hypot(*d)
        nrm = np.array([-u[1], u[0]])
        if nrm @ LD < 0:
            nrm = -nrm
        _lift(s, s.ribbon([f + d * 0.10 + nrm * 2.6, tips[i] - u * 4 + nrm * 2.6], 2.6, (0.2, 0.2)), 0.30 * sheen * (0.5 + abs(nrm @ LD)), clip=W, soft=0.7, wob=0.6)
        seg(s, f + d * 0.05, tips[i] + u * (1 + 4 * r.random()), 2.0, pen, pk, over=0, r=r, tremor=0.7, bow=0.004)
    for i in range(n):
        e = edges[i]
        t0, t1 = e[1] - e[0], e[-1] - e[-2]
        ee = np.vstack([e[0] - t0 / np.hypot(*t0) * 5 * r.random(), e[::3], e[-1], e[-1] + t1 / np.hypot(*t1) * 6 * r.random()])
        s.ink(ee, 2.4, pen, pk, tremor=0.8, taper=(0.08, 0.14))
        if r.random() < 0.4:
            s.ink(_sc(e[2:-2:3], f, 1.012) + (r.random(2) - 0.5) * 2, 1.3, pen, pk * 0.6, tremor=0.9, skip=0.2)
        if hem:
            s.ink(_sc(e[1:-1:3], f, 0.945), 1.1, pen, pk * 0.55, tremor=0.7, skip=0.3)
    for i in range(n):
        tm = s.ellipse(tips[i][0], tips[i][1], 4.2, 4.2)
        if tip is not None:
            s.A *= (1 - tm)[..., None]
            s.body = np.maximum(s.body, tm)
            s.wash(tm, tip, 0.5, wob=0.3, soft=0.4, edge=0.5, ew=1.5)
            oval(s, tips[i][0], tips[i][1], 4.2, 4.2, 1.3, pen, pk, tremor=0.3)
        else:
            s.wash(tm, pen, 1.3, wob=0.3, soft=0.5, edge=0.3, body=1)
    rf = R * 0.052
    s.wash(s.ellipse(f[0] + 2.5, f[1] + 3, rf * 2.0, rf * 2.0), dark, kd * 0.5, wob=1, bleed=3, edge=0.2, clip=W)          # the gathered cloth round the top
    oval(s, f[0], f[1], rf * 1.9, rf * 1.9, 1.4, pen, pk * 0.8, tremor=0.6, skip=0.15)
    s.wash(s.ellipse(f[0], f[1], rf, rf), pen, 1.5, wob=0.5, soft=0.6, edge=0.4)
    _lift(s, s.ellipse(f[0] - rf * 0.3, f[1] - rf * 0.35, rf * 0.34, rf * 0.3), 0.8, soft=0.6, wob=0.3)
    s.save(name, crop=True, anchor=(c, c), meta={"r": int(R)})
    return s


def _person(s, x, y, coat, ck, hair, hk, r, rot=0.0, bun=False, sc=1.0, arm=None):
    """Head and shoulders from straight above, facing up the sheet (-y)."""
    co, si = math.cos(rot), math.sin(rot)
    T = lambda px, py: (x + (px * co - py * si) * sc, y + (px * si + py * co) * sc)
    sp = [T(-80, 6), T(-66, -24), T(-28, -36), T(0, -32), T(28, -36), T(66, -24), T(80, 6), T(64, 34), T(22, 42), T(-22, 42), T(-64, 34)]
    sm = s.poly(sp)
    s.wash(sm, coat, ck, wob=1.2, soft=0.8, edge=0.5, ew=5, gran=0.4, flow=0.4, fs=40, body=1)
    s.wash(sm, INKBLUE, 0.20, wob=1, soft=6, edge=0, grad=s.rgrad(x - 40 * sc, y - 40 * sc, 20, 150 * sc, 0, 1))
    _lift(s, s.ribbon([T(-62, -14), T(-34, -27), T(-18, -27)], 9 * sc, (0.4, 0.4)), 0.3, clip=sm, soft=2.5, wob=1)
    s.ink(sp + [sp[0]], 1.9, INK, 1.4, tremor=0.8)
    s.ink([T(-52, -26), T(-46, 0), T(-52, 30)], 1.2, INK, 0.9, skip=0.15)        # where the sleeves are set in
    s.ink([T(52, -26), T(47, 2), T(54, 30)], 1.2, INK, 0.9, skip=0.15)
    if arm is not None:                                                          # a forearm reaching in for the handle
        a0 = np.array(T(56 * arm[2], -16))
        a1 = np.array(arm[:2], float)
        mid = (a0 + a1) / 2 + np.array([0, -10.0])
        am = s.ribbon([a0, mid, a1], 27 * sc, (0, 0), profile=lambda q: 1 - 0.25 * q)
        s.A *= (1 - cv2.GaussianBlur(am, (0, 0), 0.8))[..., None]
        s.wash(am, coat, ck, wob=1, soft=0.8, edge=0.5, ew=4, gran=0.4, flow=0.4, fs=40, body=1)
        nn = (a1 - a0)[::-1] * (1, -1) / np.hypot(*(a1 - a0)) * 12.5 * sc
        s.ink([a0 + nn, mid + nn * 0.95, a1 + nn * 0.8], 1.7, INK, 1.3, tremor=0.7)
        s.ink([a0 - nn, mid - nn * 0.95, a1 - nn * 0.8], 1.7, INK, 1.3, tremor=0.7)
    fx, fy = T(0, -40)                                                           # brow and nose, just clear of the hair
    fm = s.ellipse(fx, fy, 15 * sc, 11 * sc, math.degrees(rot))
    s.A *= (1 - fm)[..., None]
    s.wash(fm, SKIN, 0.75, wob=0.5, soft=0.6, edge=0.4, ew=2, body=1)
    oval(s, fx, fy, 15 * sc, 11 * sc, 1.3, INK, 1.1, rot=rot, tremor=0.4)
    hx, hy = T(0, -8)
    hm = s.ellipse(hx, hy, 33 * sc, 36 * sc, math.degrees(rot))
    s.A *= (1 - cv2.GaussianBlur(hm, (0, 0), 0.8))[..., None]
    s.wash(hm, hair, hk, wob=1, soft=0.8, edge=0.5, ew=4, gran=0.3, flow=0.4, fs=24, body=1)
    _lift(s, s.ribbon([T(-20, -22), T(-8, -30), T(8, -28)], 7 * sc, (0.4, 0.4)), 0.34, soft=2, wob=1)
    oval(s, hx, hy, 33 * sc, 36 * sc, 1.9, INK, 1.4, rot=rot, tremor=0.7)
    s.ink([T(2, -40), T(-2, -14), T(3, 8)], 1.2, INK, 0.9, skip=0.2)             # the parting
    if bun:
        bx, by = T(4, 26)
        bm = s.ellipse(bx, by, 14 * sc, 13 * sc)
        s.wash(bm, hair, hk * 0.9, wob=0.6, soft=0.6, edge=0.5, body=1)
        oval(s, bx, by, 14 * sc, 13 * sc, 1.5, INK, 1.3, tremor=0.5)


def clear():
    """um_7: clear plastic. Two people under it, seen through the dome."""
    R = 190
    S = int(2 * R + 150)
    c = S / 2
    s = Sheet(S, S, 77)
    f, tips, edges, r = _geom(c, R, 77, off=0.035)
    n = len(tips)
    out = np.vstack(edges)
    whole = s.poly(out, smooth=False)
    # the two of them, shoulders touching, the smaller one leaning in
    _person(s, c + 74, c + 66, PAYNE, 0.85, SEPIA, 1.4, r, rot=-0.22, bun=True, sc=0.98)
    _person(s, c - 72, c + 52, UMBER, 0.85, INK, 1.3, r, rot=0.12, sc=1.1, arm=(f[0] - 2, f[1] + 10, 1))
    s.A *= whole[..., None]
    s.body *= whole
    s.A *= 0.90                                    # seen through wet plastic
    W = s.wash(whole, RAIN, 0.20, wob=1.0, soft=0.8, edge=0.8, ew=8, gran=0.3, flow=0.5, fs=60, body=0.24)
    for i in range(n):
        pm = s.poly(np.vstack([f[None], edges[i]]), smooth=False)
        d = (tips[i] + tips[(i + 1) % n]) / 2 - f
        L = 0.5 + 0.5 * math.cos(math.atan2(d[1], d[0]) - LA)
        s.wash(pm, (RAIN, SLATE)[i % 2], 0.05 + 0.20 * (1 - L) + 0.05 * r.random(), wob=0.6, soft=0.7, edge=0.6, ew=5, gran=0.3, flow=0.4, fs=40, clip=W)
        a, b = tips[i] - f, tips[(i + 1) % n] - f
        if L > 0.5:                                # glare on the panels that face the lamp
            _white(s, pm * W * s.rgrad(c - 0.4 * R, c - 0.45 * R, 0.1 * R, 0.9 * R, 1, 0), 0.34 * (L - 0.5) * 2, soft=1.5)
            t = 0.58 + (r.random() - 0.5) * 0.08
            p0, p1 = f + t * (0.85 * a + 0.15 * b), f + t * (0.15 * a + 0.85 * b)
            _white(s, s.ribbon([p0, (p0 + p1) / 2, p1], R * 0.07, (0.4, 0.4)) * W, 0.42 * L, soft=2.2)
        q = 0.3 + 0.4 * r.random()
        d = (1 - q) * a + q * b
        _white(s, s.ribbon([f + d * 0.3, f + d * 0.62, f + d * 0.86], R * 0.02, (0.4, 0.5)) * W, 0.22 + 0.4 * L, soft=1.0)
    lip = W * (1 - cv2.warpAffine(W, np.float32([[1, 0, -R * 0.06], [0, 1, -R * 0.065]]), (S, S)))
    s.wash(cv2.GaussianBlur(lip, (0, 0), 3) * W, SLATE, 0.5, wob=0, soft=0, edge=0)
    # the white rim, the ribs, the cap
    rim = whole * (1 - s.poly(_sc(out, f, 0.935), smooth=False))
    _white(s, rim, 0.88, soft=0.8)
    s.wash(rim, RAIN, 0.10, wob=0.5, soft=0.6, edge=0.3, clip=W)
    for i in range(n):
        d = tips[i] - f
        u = d / np.hypot(*d)
        nrm = np.array([-u[1], u[0]])
        if nrm @ LD < 0:
            nrm = -nrm
        _white(s, s.ribbon([f + d * 0.06 + nrm * 1.6, tips[i] + nrm * 1.6], 3.4), 0.72, soft=0.6)
        seg(s, f + d * 0.05, tips[i] + u * 3 * r.random(), 1.6, PAYNE, 1.5, over=0, r=r, tremor=0.7, bow=0.004)
        e = edges[i]
        s.ink(np.vstack([e[::3], e[-1]]), 2.1, PAYNE, 1.5, tremor=0.8, taper=(0.08, 0.14))
        s.ink(_sc(e[1:-1:3], f, 0.935), 1.2, SLATE, 1.1, tremor=0.7, skip=0.2)
    # rain beading on it
    pts = [(c + (r.random() - 0.5) * 2 * R, c + (r.random() - 0.5) * 2 * R) for _ in range(90)]
    _white(s, _dots(s, pts, 1.7, r) * W, 0.8, soft=0.5)
    s.wash(_dots(s, [(x + 1.3, y + 1.5) for x, y in pts[:50]], 1.4, r), SLATE, 0.7, wob=0.3, soft=0.4, edge=0.5, ew=1.2, clip=W)
    for i in range(n):
        tm = s.ellipse(tips[i][0], tips[i][1], 4.4, 4.4)
        _white(s, tm, 1.0, soft=0.4)
        oval(s, tips[i][0], tips[i][1], 4.4, 4.4, 1.3, PAYNE, 1.4, tremor=0.3)
    rf = R * 0.062
    cap = s.ellipse(f[0], f[1], rf * 1.5, rf * 1.5)
    _white(s, cap, 0.95, soft=0.6)
    s.wash(cap, SLATE, 0.3, wob=0.5, soft=0.8, edge=0.5, grad=s.rgrad(f[0] - 4, f[1] - 4, 2, rf * 2.2, 0, 1))
    oval(s, f[0], f[1], rf * 1.5, rf * 1.5, 1.6, PAYNE, 1.5, tremor=0.5)
    s.wash(s.ellipse(f[0], f[1], rf * 0.55, rf * 0.55), INK, 1.3, wob=0.4, soft=0.5)
    s.save("um_7", crop=True, anchor=(c, c), meta={"r": R})


def shadow():
    S = 660
    s = Sheet(S, S, 88)
    m = cv2.GaussianBlur(s.blob(S / 2, S / 2, 188, 188, 0.05, 9), (0, 0), 20)
    m = np.clip(m * (0.9 + 0.2 * s.noise(60, 3)), 0, 1)
    s.wash(m, INKBLUE, 0.62, wob=0, soft=0, edge=0, gran=0.25, flow=0.2, fs=160)
    s.wash(cv2.GaussianBlur(s.blob(S / 2, S / 2, 120, 120, 0.1, 9), (0, 0), 30), INKBLUE, 0.18, wob=0, soft=0, edge=0, gran=0.2)
    s.save("um_sh", crop=True, anchor=(S / 2, S / 2))


def feet():
    """A pair of shoes mid-stride from above, walking up the sheet (-y): one ahead, one behind."""
    for i, (col, k, sole, wd) in enumerate(((UMBER, 1.0, SEPIA, 17), (PAYNE, 1.05, INKBLUE, 15))):
        s = Sheet(200, 220, 90 + i)
        r = rs(90 + i)
        for sx, oy, rot in ((-1, -26, -0.10), (1, 30, 0.14)):
            cx, cy = 100 + sx * 24, 110 + oy
            co, si = math.cos(rot), math.sin(rot)
            T = lambda px, py: (cx + px * co - py * si, cy + px * si + py * co)
            sp = [T(0, -38), T(wd * 0.75, -30), T(wd, -8), T(wd * 0.8, 18), T(wd * 0.7, 34), T(0, 40), T(-wd * 0.7, 34), T(-wd * 0.8, 18), T(-wd, -8), T(-wd * 0.75, -30)]
            m = s.poly(sp)
            s.wash(cv2.warpAffine(m, np.float32([[1, 0, 6], [0, 1, 7]]), (200, 220)), INKBLUE, 0.6, wob=1, bleed=5, edge=0.1)
            base(s, m, col, k, wob=0.8, edge=0.4, ew=3, gran=0.4)
            s.wash(m, sole, 0.5, wob=0.5, soft=3, edge=0, grad=s.rgrad(cx - 8, cy - 14, 4, 46, 0, 1))
            _lift(s, s.ribbon([T(-wd * 0.35, -28), T(-wd * 0.45, -12)], 4.5, (0.3, 0.3)), 0.5, clip=m, soft=1.0, wob=0.5)
            s.ink(sp + [sp[0]], 1.8, INK, 1.5, tremor=0.5)
            s.ink([T(-wd * 0.62, 2), T(0, -6), T(wd * 0.62, 2)], 1.3, INK, 1.2)              # the throat of the shoe
            s.wash(s.poly([T(-wd * 0.55, 6), T(0, 0), T(wd * 0.55, 6), T(wd * 0.5, 28), T(0, 34), T(-wd * 0.5, 28)]), INKBLUE, 0.8, wob=0.5, soft=1, edge=0.3)    # trouser leg / ankle
            for q in (-20, -12):
                s.ink([T(-wd * 0.3, q), T(wd * 0.3, q + 1)], 1.0, INK, 1.0)                   # laces
        s.save(f"um_feet{i}", crop=True, anchor=(100, 110))


def sprites():
    #         name      R    cloth      k0    shade     kd
    umbrella("um_0", 170, INDIGO, 0.95, INKBLUE, 0.62, 101, hem=True)
    umbrella("um_1", 160, MIST, 0.55, PAYNE, 0.34, 102, pen=SEPIA, pk=1.5, band=(0.74, 0.90, INDIGO, 0.8, 0), sheen=0.8, tip=CREAM)
    umbrella("um_2", 180, MIST, 0.50, PAYNE, 0.36, 103, pen=INK, pk=1.5, alt=(PRUSSIAN, 1.05), sheen=0.9, tip=CREAM)
    umbrella("um_3", 210, PAYNE, 1.0, INKBLUE, 0.85, 104, vent=True, trim=(MIST, 0.5), sheen=1.15)
    umbrella("um_4", 150, TEAL, 0.95, PRUSSIAN, 0.60, 105, dots=(CREAM, 0.86), hem=False)
    umbrella("um_5", 165, MOSS, 0.95, PAYNE, 0.62, 106, hem=True, band=(0.90, 1.01, UMBER, 0.5, 0))
    umbrella("um_6", 175, VIOLET, 0.70, PAYNE, 0.58, 107, band=(0.66, 0.80, None, 0, 0.62), tip=MIST)
    clear()
    umbrella("um_solo", 180, PERSIMMON, 0.92, BURNT, 0.50, 108, pen=SEPIA, pk=1.6, sheen=1.25, gran=0.25, hem=True, tip=CREAM)
    shadow()
    feet()


ALL = {"um_ground": ground, "um_sprites": sprites}
