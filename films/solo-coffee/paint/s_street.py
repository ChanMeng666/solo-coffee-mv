"""The street outside the café: a row of old low-rise fronts across a wet road at rainy dusk, one warm shopfront.
World sheet 3072x1728. Layers back to front: st_sky, st_far, [st_inside behind the glass], st_main, st_road,
then the near sprites st_lamp, st_fg_bike, st_fg_branch.
The upper storeys are drawn squat and the shopfronts tall, the way a sketcher does when the ground floor is the subject."""
import math

import cv2
import numpy as np

from kit import *

W, H = 3072, 1728
PAVE = 1290                        # wall meets pavement
KERB = 1374                        # top edge of the kerb
VP = (1700.0, 1000.0)              # eye level, a little left of the café window
WIN = (1470, 795, 2090, 1225)      # café window glass, outer bounds
DOORG = (2150, 896, 2294, 1150)    # door glass
DOOR = (2126, 862, 2318, 1284)     # door leaf
SIGN = (1452, 612, 2338, 694)      # fascia board
NEON = (1035, 520, 1365, 940)      # plain wall on the neighbour
INSIDE_AT = (1410, 720)
LIT = []                           # lit upper windows, filled as they are painted
BRACKETS = [(1431, 902), (2371, 902)]


# ---------------------------------------------------------------------------------------------- a window onto a sheet
class Sub(Sheet):
    """A rectangular part of a sheet that paints in the parent's coordinates (same paper, same pigment arrays).
    Washes cost what their neighbourhood costs instead of what the whole 5-megapixel sheet costs."""

    def __init__(self, s, x0, y0, x1, y1):
        px, py = getattr(s, "ox", 0), getattr(s, "oy", 0)
        x0, y0 = max(px, int(x0)), max(py, int(y0))
        x1, y1 = min(px + s.w, int(x1)), min(py + s.h, int(y1))
        self.ox, self.oy = x0, y0
        self.w, self.h = x1 - x0, y1 - y0
        sl = (slice(y0 - py, y1 - py), slice(x0 - px, x1 - px))
        self.A, self.body, self.P, self.G = s.A[sl], s.body[sl], s.P[sl], s.G[sl]
        self.seed, self.n = s.seed * 31 + x0 * 7 + y0 * 3 + 1, 0
        self.Y, self.X = s.Y[:self.h, :self.w], s.X[:self.h, :self.w]
        self._raw = False
        self._g = rs(self.seed + 977)

    def _p(self, pts):
        P = np.asarray(pts, np.float64)
        return P if self._raw else P - (self.ox, self.oy)

    def poly(self, pts, smooth=True, step=3.0):
        return Sheet.poly(self, self._p(pts), smooth, step)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        return Sheet.ellipse(self, cx - self.ox, cy - self.oy, rx, ry, rot)

    def ribbon(self, pts, w, taper=(0.0, 0.0), profile=None, smooth=True, closed=False):
        return Sheet.ribbon(self, self._p(pts), w, taper, profile, smooth, closed)

    def vgrad(self, y0, y1, a0=0.0, a1=1.0):
        return Sheet.vgrad(self, y0 - self.oy, y1 - self.oy, a0, a1)

    def hgrad(self, x0, x1, a0=0.0, a1=1.0):
        return Sheet.hgrad(self, x0 - self.ox, x1 - self.ox, a0, a1)

    def rgrad(self, cx, cy, r0, r1, a0=1.0, a1=0.0, sy=1.0):
        return Sheet.rgrad(self, cx - self.ox, cy - self.oy, r0, r1, a0, a1, sy)

    def ink(self, pts, w=2.0, color=INK, k=1.7, taper=(0.10, 0.22), tremor=0.7, press=0.35, closed=False, smooth=True, skip=0.0, dry=0.25, clip=None):
        """The engine's pen line (same pressure, taper, tremor, skips), drawing its hand-noise from one generator per
        sheet instead of seeding a new one five times a stroke: a street has several thousand strokes."""
        g = self._g
        P = self._p(pts)
        P = spline(P, closed, 2.0) if smooth else P
        P = resample(P, 0.7)
        n = len(P)
        if n < 3:
            return

        def nz(wl):
            kk = max(4, int(n * 0.7 / max(1.0, wl)) + 4)
            gg = g.random(kk) * 2 - 1
            x = np.linspace(0, kk - 3, n)
            i = x.astype(int)
            f = x - i
            f = f * f * (3 - 2 * f)
            return gg[i] * (1 - f) + gg[i + 1] * f

        L = n * 0.7
        d = np.gradient(P, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None] + 1e-9
        P = P + nrm * (tremor * (0.6 * nz(9) + 1.1 * nz(70)))[:, None]
        t = np.linspace(0, 1, n)
        wd = w * 0.5 * (1 + press * nz(55) + 0.15 * press * nz(7))
        if not closed:
            ta, tb = min(taper[0], 40 / L + taper[0] * 0.3), min(taper[1], 60 / L + taper[1] * 0.3)
            wd *= (0.18 + 0.82 * sstep(0, max(ta, 1e-3), t)) * (0.10 + 0.90 * (1 - sstep(1 - max(tb, 1e-3), 1, t)))
        if skip > 0:
            wd *= sstep(-0.2, 0.1, nz(26) + 1 - 2 * skip)
        x0, y0 = int(max(0, P[:, 0].min() - w - 4)), int(max(0, P[:, 1].min() - w - 4))
        x1, y1 = int(min(self.w, P[:, 0].max() + w + 5)), int(min(self.h, P[:, 1].max() + w + 5))
        if x1 <= x0 or y1 <= y0:
            return
        m = np.zeros(((y1 - y0) * 2, (x1 - x0) * 2), np.uint8)
        X = np.round((P[:, 0] - x0) * 32).astype(int).tolist()
        Y = np.round((P[:, 1] - y0) * 32).astype(int).tolist()
        Rr = np.round(wd * 32).astype(int).tolist()
        for i in range(n):
            if wd[i] > 0.12:
                cv2.circle(m, (X[i], Y[i]), max(3, Rr[i]), 255, -1, cv2.LINE_AA, 4)
        m = cv2.resize(m, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        roi = (slice(y0, y1), slice(x0, x1))
        if dry > 0:
            m *= 1 - dry * sstep(0.52, 0.80, self.P[roi])
        if clip is not None:
            m *= clip[roi]
        self.A[roi] += m[..., None] * (k * absorb(color))

    def hatch(self, *a, **kw):
        self._raw = True
        try:
            Sheet.hatch(self, *a, **kw)
        finally:
            self._raw = False

    def spatter(self, n, color, k=0.8, box=None, **kw):
        if box is not None:
            box = (box[0] - self.ox, box[1] - self.oy, box[2] - self.ox, box[3] - self.oy)
        return Sheet.spatter(self, n, color, k, box, **kw)


class Off(Sub):
    """A sheet of its own that is painted in world coordinates: its top-left corner sits at (ox, oy) on the world."""

    def __init__(self, w, h, ox, oy, seed=0):
        Sheet.__init__(self, w, h, seed)
        self.ox, self.oy, self._raw = int(ox), int(oy), False
        self._g = rs(seed + 977)


# ---------------------------------------------------------------------------------------------- small habits
def J(r, v=1.0):
    return (r.random() - 0.5) * 2 * v


def U(r, a, b):
    return a + (b - a) * r.random()


def box(s, r, x0, y0, x1, y1, w=2.0, c=SEPIA, k=1.5, over=5.0, dbl=0.3, j=1.2, **kw):
    """A pen rectangle the way a hand draws it: four separate strokes, corners crossing, now and then gone over twice."""
    P = [(x0 + J(r, j), y0 + J(r, j)), (x1 + J(r, j), y0 + J(r, j)), (x1 + J(r, j), y1 + J(r, j)), (x0 + J(r, j), y1 + J(r, j))]
    for a, b in zip(P, P[1:] + P[:1]):
        seg(s, a, b, w, c, k, over=over * (0.2 + r.random()), r=r, **kw)
        if r.random() < dbl:
            d = (J(r, 2.2), J(r, 2.2))
            seg(s, (a[0] + d[0], a[1] + d[1]), (b[0] + d[0], b[1] + d[1]), w * 0.7, c, k * 0.6, over=over * r.random(), r=r, skip=0.25)


def line(s, r, a, b, w=2.0, c=SEPIA, k=1.5, over=4.0, dbl=0.0, **kw):
    seg(s, a, b, w, c, k, over=over * (0.3 + r.random()), r=r, **kw)
    if dbl and r.random() < dbl:
        d = (J(r, 2), J(r, 2))
        seg(s, (a[0] + d[0], a[1] + d[1]), (b[0] + d[0], b[1] + d[1]), w * 0.7, c, k * 0.6, r=r, skip=0.3)


def put(s, m, color, k=0.8, lift=0.9, wob=1.2, **kw):
    """An object over what is already painted: lift most of what is under it, lay its wash, keep it opaque."""
    if lift > 0:
        s.lift(m, lift, soft=0.7, wob=0)
    return s.wash(m, color, k, wob=wob, body=1, **kw)


def streaks(s, r, x0, x1, y0, y1, n, color=PAYNE, k=0.2, w=(5, 16), clip=None, dry=0.45):
    """Rain stains: thin dry-ish vertical drags of darker water."""
    for _ in range(n):
        x = U(r, x0, x1)
        ya = U(r, y0, y0 + (y1 - y0) * 0.5)
        yb = min(y1, ya + U(r, 0.25, 0.9) * (y1 - y0))
        s.stroke([(x, ya), (x + J(r, 3), (ya + yb) / 2), (x + J(r, 4), yb)], U(r, *w), color, k * U(r, 0.5, 1.3), dry=dry * U(r, 0.6, 1.2),
                 edge=0.3, wob=1.5, taper=(0.05, 0.6), clip=clip)


def mottle(s, r, x0, y0, x1, y1, colors, n=5, k=0.2, size=(60, 160), clip=None, bleed=18):
    """Wet-in-wet touches of neighbouring colour dropped into a wall while it is damp."""
    for i in range(n):
        c = colors[int(r.integers(0, len(colors)))]
        rx, ry = U(r, *size), U(r, *size)
        s.wash(s.blob(U(r, x0, x1), U(r, y0, y1), rx, ry * 0.8, irr=0.35), c, k * U(r, 0.5, 1.4), wob=4, bleed=bleed * U(r, 0.7, 1.4), edge=0.25, clip=clip)


# ---------------------------------------------------------------------------------------------- sky
def bump(s, y0, y1, f=0.5):
    """A soft horizontal band 0..1: rises over the first part of y0..y1, falls over the rest."""
    ym = y0 + (y1 - y0) * f
    return s.vgrad(y0, ym, 0, 1) * s.vgrad(ym, y1, 1, 0)


def sky():
    s = Sheet(W, H, 41)
    r = rs(41)
    s.glaze(RAIN, 0.36, flow=0.3, fs=600, gran=0.2)
    s.glaze(SLATE, 0.5, grad=s.vgrad(560, 1000, 0, 1), flow=0.2, gran=0.2)       # never seen: the street hides it
    t = Sub(s, 0, 0, W, 800)
    F = t.full()
    t.wash(F, PRUSSIAN, 0.80, wob=0, soft=0, edge=0, grad=t.vgrad(-140, 400, 1, 0), flow=0.45, fs=420, gran=0.22)
    t.wash(F, INDIGO, 0.34, wob=0, soft=0, edge=0, grad=t.vgrad(-20, 230, 1, 0), flow=0.5, fs=260, gran=0.2)
    # the last of the day, low down: rose over ochre
    t.wash(F, ROSE, 0.26, wob=0, soft=0, edge=0, grad=bump(t, 150, 390), flow=0.7, fs=380, gran=0.2)
    t.wash(F, OCHRE, 0.15, wob=0, soft=0, edge=0, grad=bump(t, 230, 500, 0.4), flow=0.7, fs=300, gran=0.2)
    # cloud masses, wet in wet: long ragged bodies, soft above, heavier bellies
    clouds = [(330, 95, 560, 70, 0.34), (1480, 50, 760, 60, 0.30), (2640, 120, 520, 72, 0.36), (1010, 205, 470, 44, 0.24),
              (2080, 232, 560, 40, 0.24), (2960, 290, 330, 30, 0.16), (120, 262, 330, 32, 0.18)]
    for cx, cy, rx, ry, k in clouds:
        t.wash(t.blob(cx, cy, rx, ry, irr=0.42, n=15), PAYNE, k, wob=9, bleed=34, edge=0.2, ew=10, flow=0.5, fs=200, gran=0.25)
        t.wash(t.blob(cx + J(r, 60), cy + ry * 0.55, rx * 0.72, ry * 0.42, irr=0.4, n=13), INDIGO, k * 0.9, wob=6, bleed=16, edge=0.5, ew=8, flow=0.4, fs=120, gran=0.3)
        t.wash(t.blob(cx + J(r, 100), cy + ry * 0.9, rx * 0.5, ry * 0.26, irr=0.4), VIOLET, k * 0.35, wob=6, bleed=22, edge=0.1, gran=0.2)
    # light breaking between them (a damp brush), and a back-run or two where water crept into a drying wash
    for cx, cy, rx, ry, a in [(880, 118, 250, 34, 0.36), (2120, 150, 300, 34, 0.34), (1560, 180, 240, 26, 0.26), (1330, 318, 460, 34, 0.30),
                              (2520, 330, 420, 34, 0.26), (480, 340, 420, 34, 0.26)]:
        t.lift(t.blob(cx, cy, rx, ry, irr=0.4, n=13), a, bleed=26, wob=7)
    for cx, cy, rx, ry in [(1190, 112, 190, 52), (2360, 60, 150, 44), (640, 220, 150, 30)]:
        t.wash(t.blob(cx, cy, rx, ry, irr=0.45, n=13), RAIN, 0.14, wob=7, soft=2, edge=1.0, ew=6, flow=0.8, fs=60, gran=0.3)
    # the city farther off: pale cool blocks that lose their feet in the mist
    x = -60
    while x < W + 40:
        w = U(r, 60, 190)
        top = U(r, 190, 330) if r.random() < 0.75 else U(r, 110, 180)
        if top < 180:
            w *= 0.6
        m = t.rect(x, top, x + w, 640)
        if r.random() < 0.4:         # a setback, or a plant room on the roof
            m = np.maximum(m, t.rect(x + w * U(r, 0.1, 0.4), top - U(r, 14, 44), x + w * U(r, 0.5, 0.9), top + 4))
        t.wash(m, SLATE if r.random() < 0.6 else RAIN, U(r, 0.20, 0.34), wob=0.8, soft=1.4, edge=0.35, ew=5, grad=t.vgrad(top - 20, top + U(r, 170, 260), 1, 0.1), flow=0.5, fs=90, gran=0.3)
        if r.random() < 0.25:        # a mast
            xm = x + w * U(r, 0.2, 0.8)
            t.stroke([(xm, top + 2), (xm + J(r, 2), top - U(r, 30, 70))], 2.6, SLATE, 0.3, taper=(0, 0.6), wob=0.6, edge=0.2)
        x += w * U(r, 0.6, 1.2)
    x = -40
    while x < W + 40:                # a nearer, slightly firmer row
        w = U(r, 90, 250)
        top = U(r, 270, 400)
        pts = [(x, top), (x + w, top), (x + w, 660), (x, 660)]
        if r.random() < 0.3:         # a pitched roof
            pts = [(x, top + 26), (x + w * 0.5, top - 14), (x + w, top + 26), (x + w, 660), (x, 660)]
        m = Q(t, pts)
        t.wash(m, SLATE, U(r, 0.24, 0.38), wob=0.8, soft=1.1, edge=0.4, ew=5, grad=t.vgrad(top - 20, top + 220, 1, 0.2), flow=0.5, fs=80, gran=0.3)
        if r.random() < 0.5:
            t.wash(m, VIOLET, 0.12, wob=3, bleed=6, edge=0.1, grad=t.vgrad(top - 20, top + 150, 1, 0))
        x += w * U(r, 0.7, 1.3)
    s.wash(s.full(), None, 0.4, wob=0, soft=0, edge=0, gran=0, flow=0.5, fs=300, grad=s.vgrad(430, 620, 0, 1) * s.vgrad(700, 1000, 1, 0), lift=True)   # mist at their feet
    s.save("st_sky", opaque=True, q=88)


# ---------------------------------------------------------------------------------------------- the roofs behind
def far():
    S = Sheet(W, H, 42)
    r = rs(42)
    s = Sub(S, 0, 100, W, 780)
    BOT = 740
    PEN = PAYNE

    def mass(pts, c=SLATE, k=0.72, top=300, c2=PAYNE, k2=0.16):
        m = Q(s, pts)
        s.wash(m, c, k, wob=1.4, soft=0.8, edge=0.45, ew=6, flow=0.55, fs=130, gran=0.4, body=1, grad=s.vgrad(top - 30, top + 320, 1.0, 0.6))
        s.wash(m, c2, k2 * U(r, 0.7, 1.3), wob=3, bleed=10, edge=0.2, flow=0.6, fs=70, gran=0.4, grad=s.vgrad(top - 30, top + 200, 1, 0.2))
        return m

    def roof(pts, k=0.42, c=PAYNE):
        m = Q(s, pts)
        s.wash(m, c, k, wob=1.2, soft=0.8, edge=0.5, ew=4, flow=0.5, fs=60, gran=0.45)
        return m

    def pl(pts, w=1.5, k=1.1, **kw):
        for a, b in zip(pts, pts[1:]):
            line(s, r, a, b, w, PEN, k, over=3, **kw)

    def wins(x0, x1, y, n, w=17, h=26, lit=(), skipn=()):
        for i in range(n):
            if i in skipn:
                continue
            x = x0 + (x1 - x0) * (i + 0.5) / n + J(r, 3)
            ww, hh, yy = w + J(r, 2), h + J(r, 3), y + J(r, 2.5)
            m = s.rect(x - ww / 2, yy, x + ww / 2, yy + hh)
            if i in lit:
                s.lift(m, 1.0, soft=0.8, wob=0.5)
                s.wash(m, OCHRE, U(r, 0.35, 0.6), wob=0.8, soft=0.8, edge=0.5, ew=2)
                s.wash(s.rect(x - ww / 2, yy, x + ww / 2, yy + hh * U(r, 0.25, 0.5)), SIENNA, 0.35, wob=0.6, soft=0.8)      # a blind half down
                s.wash(s.blob(x, yy + hh / 2, ww * 1.6, hh * 1.3), AMBER, 0.07, wob=2, bleed=7, edge=0)
            else:
                s.wash(m, PAYNE, U(r, 0.35, 0.6), wob=0.9, soft=0.7, edge=0.6, ew=2)
            if r.random() < 0.6:
                box(s, r, x - ww / 2, yy, x + ww / 2, yy + hh, 1.1, PEN, 0.9, over=2, dbl=0.1, j=0.8, skip=0.15)
            else:
                line(s, r, (x - ww / 2 - 3, yy + hh + 2), (x + ww / 2 + 3, yy + hh + 2), 1.3, PEN, 1.0)

    def chimney(x, base, top, w=26, pots=2):
        m = s.rect(x, top, x + w, base + 6)
        put(s, m, SLATE, 0.8, lift=0.6, edge=0.5, ew=3)
        s.wash(s.rect(x + w * 0.55, top, x + w, base + 6), PAYNE, 0.3, wob=0.8, soft=1)
        s.wash(s.rect(x - 3, top - 5, x + w + 3, top + 2), PAYNE, 0.5, wob=0.6, soft=0.6, body=1)
        for i in range(pots):
            px = x + w * (i + 0.5) / pots
            put(s, Q(s, [(px - 4, top - 5), (px - 3, top - 19 - J(r, 3)), (px + 3, top - 19), (px + 4, top - 5)]), BURNT, 0.5, lift=0, wob=0.5, edge=0.4, ew=2)
            s.wash(s.rect(px - 4, top - 19, px + 4, top - 5), PAYNE, 0.35, wob=0.4, soft=0.5)
        pl([(x, base), (x, top - 4), (x + w, top - 4), (x + w, base)], 1.3, 1.0)

    def tank(x, y, w, h):
        """A rooftop water tank on a steel stand; y is the roof it stands on."""
        ty = y - h - 26
        m = np.maximum(s.rect(x, ty + 6, x + w, ty + h), s.ellipse(x + w / 2, ty + 7, w / 2, 8))
        put(s, m, SLATE, 0.85, lift=0.5, edge=0.5, ew=4)
        s.wash(m, PAYNE, 0.4, wob=1, soft=2, edge=0, grad=s.hgrad(x + w * 0.3, x + w))
        s.wash(m, BURNT, 0.12, wob=2, bleed=5, grad=s.vgrad(ty + h * 0.4, ty + h))               # rust creeping up
        for q in (0.08, 0.5, 0.92):
            line(s, r, (x + w * q, ty + h), (x + w * q + J(r, 1.5), y + 2), 1.6, PEN, 1.2, over=1)
        line(s, r, (x + w * 0.08, y - 4), (x + w * 0.92, ty + h + 3), 1.1, PEN, 0.9)
        line(s, r, (x + w * 0.08, ty + h + 3), (x + w * 0.92, y - 4), 1.1, PEN, 0.9)
        pl([(x, ty + h), (x, ty + 7)], 1.4)
        pl([(x + w, ty + 7), (x + w, ty + h)], 1.4)
        s.ink(ell(x + w / 2, ty + 7, w / 2, 8, math.pi, 2 * math.pi, 20), 1.4, PEN, 1.1)
        for q in (0.35, 0.7):
            line(s, r, (x - 1, ty + h * q), (x + w + 1, ty + h * q + J(r, 1)), 1.0, PEN, 0.8, skip=0.2)
        line(s, r, (x - 2, ty + h), (x + w + 2, ty + h), 1.4, PEN, 1.1)

    def aerial(x, y, h=70, bars=3, lean=0.0):
        top = (x + lean * h, y - h)
        s.ink([(x, y), (x + lean * h * 0.5 + J(r, 1), y - h / 2), top], 1.4, PEN, 1.1, taper=(0.02, 0.1))
        for i in range(bars):
            yy = y - h + 5 + i * U(r, 7, 10)
            hw = U(r, 9, 17) * (1 - i * 0.15)
            line(s, r, (top[0] - hw, yy + J(r, 1.5)), (top[0] + hw, yy + J(r, 1.5)), 1.1, PEN, 1.0, over=1)

    def rail(x0, x1, y, h=16, gap=11):
        line(s, r, (x0, y - h), (x1, y - h + J(r, 1.5)), 1.2, PEN, 1.0)
        x = x0 + 2
        while x < x1:
            line(s, r, (x, y - h - 1), (x + J(r, 0.8), y), 0.9, PEN, 0.8, over=0.5, skip=0.1)
            x += gap * U(r, 0.8, 1.2)

    # 1  a hipped roof at the far left
    mass([(-40, 345), (330, 345), (330, BOT), (-40, BOT)], top=300)
    roof([(-40, 300), (265, 296), (328, 348), (-40, 350)], 0.5)
    pl([(-20, 298), (266, 295), (330, 348)])
    chimney(120, 300, 262, 30, 2)
    aerial(236, 296, 62, 3, 0.03)
    # 2  a flat-roofed block with its tank
    mass([(318, 262), (585, 258), (585, BOT), (318, BOT)], top=262, c2=VIOLET)
    pl([(318, 360), (318, 262), (585, 258), (585, 380)])
    line(s, r, (322, 272), (582, 268), 1.0, PEN, 0.8, skip=0.2)
    tank(372, 262, 70, 44)
    rail(470, 580, 259, 15)
    wins(335, 575, 292, 6, lit=(4,), skipn=(1,))
    # 3  a gable end
    g3 = [(575, 372), (690, 296), (808, 368), (808, BOT), (575, BOT)]
    mass(g3, top=300, k=0.78)
    pl([(572, 376), (690, 294), (812, 372)], 1.7, 1.2)
    pl([(588, 376), (690, 306), (797, 372)], 1.0, 0.7, skip=0.3)
    put(s, s.ellipse(690, 338, 11, 13), PAYNE, 0.6, lift=0.4, edge=0.6, ew=2)
    oval(s, 690, 338, 11, 13, 1.1, PEN, 1.0)
    chimney(760, 345, 290, 24, 2)
    # 4  a low flat roof with a stair hut and aerials
    mass([(800, 334), (1075, 330), (1075, BOT), (800, BOT)], top=330, c2=PRUSSIAN)
    hut = [(905, 334), (905, 292), (985, 286), (985, 334)]
    mass(hut, top=286, k=0.3, c2=PAYNE, k2=0.3)
    pl([(905, 336), (905, 291), (986, 285), (986, 334)])
    put(s, s.rect(930, 304, 952, 334), PAYNE, 0.55, lift=0.3, edge=0.5, ew=2)
    pl([(800, 370), (800, 334), (1075, 330)])
    rail(810, 900, 333, 15)
    aerial(1030, 331, 84, 4, -0.02)
    aerial(858, 333, 52, 2, 0.05)
    wins(815, 1065, 362, 6, lit=(), skipn=(2,))
    # 5  the bigger block behind the plain building: this one is seen
    mass([(1062, 306), (1312, 302), (1312, BOT), (1062, BOT)], top=304, k=0.8, c2=VIOLET, k2=0.2)
    s.wash(s.rect(1056, 300, 1318, 314), PAYNE, 0.4, wob=1, soft=0.8, edge=0.5, ew=2)       # coping
    pl([(1060, 480), (1062, 304), (1316, 300), (1314, 420)], 1.6, 1.2)
    line(s, r, (1058, 316), (1316, 312), 1.1, PEN, 0.9, skip=0.15)
    tank(1088, 303, 62, 40)
    aerial(1262, 301, 66, 3, 0.02)
    wins(1080, 1300, 344, 5, 21, 32, lit=(1,), skipn=())
    wins(1080, 1300, 412, 5, 21, 32, lit=(3,), skipn=(0,))
    s.ink([(1196, 316), (1198, 400), (1195, 500)], 2.4, PEN, 0.8, tremor=0.6)               # a downpipe
    streaks(s, r, 1070, 1305, 312, 470, 7, PAYNE, 0.14, (5, 12))
    mass([(1305, 402), (1440, 384), (1440, BOT), (1305, BOT)], top=390, k=0.7)
    roof([(1305, 402), (1440, 384), (1440, 420), (1305, 436)], 0.45)
    pl([(1303, 404), (1442, 383)], 1.5)
    pl([(1305, 436), (1440, 421)], 1.0, 0.8, skip=0.2)
    chimney(1352, 398, 348, 26, 2)
    # 6  a long hipped roof behind the café
    mass([(1430, 352), (1730, 352), (1730, BOT), (1430, BOT)], top=300)
    roof([(1430, 352), (1478, 296), (1700, 292), (1734, 352)], 0.5)
    pl([(1432, 350), (1478, 295), (1700, 291), (1736, 352)])
    for i in range(7):
        x = 1470 + i * 36 + J(r, 6)
        line(s, r, (x, 300 + J(r, 3)), (x - 6 + J(r, 3), 348), 0.9, PEN, 0.6, skip=0.35)
    chimney(1560, 296, 256, 34, 3)
    aerial(1668, 293, 58, 3, 0.04)
    # 7  a taller block: a hoarding frame on its roof, seen from behind
    mass([(1722, 286), (2118, 282), (2118, BOT), (1722, BOT)], top=284, k=0.78, c2=PRUSSIAN, k2=0.2)
    pl([(1722, 352), (1722, 286), (2118, 282), (2118, 360)], 1.6, 1.2)
    line(s, r, (1726, 296), (2114, 292), 1.0, PEN, 0.8, skip=0.2)
    hb = s.rect(1800, 196, 1990, 252)
    put(s, hb, SLATE, 0.5, lift=0, edge=0.5, ew=3, flow=0.5, fs=40)
    box(s, r, 1800, 196, 1990, 252, 1.4, PEN, 1.1, over=3)
    for x in (1818, 1866, 1924, 1972):
        line(s, r, (x, 252), (x + J(r, 2), 284), 1.4, PEN, 1.1, over=1)
    line(s, r, (1818, 284), (1866, 252), 1.0, PEN, 0.8)
    line(s, r, (1924, 252), (1972, 284), 1.0, PEN, 0.8)
    tank(2030, 283, 64, 42)
    rail(1730, 1795, 285, 15)
    wins(1740, 2105, 318, 8, lit=(5,), skipn=(2,))
    # 8  another gable end, with a lit attic
    g8 = [(2108, 352), (2262, 262), (2440, 356), (2440, BOT), (2108, BOT)]
    mass(g8, top=270, k=0.74, c2=VIOLET)
    pl([(2104, 356), (2262, 260), (2444, 360)], 1.7, 1.2)
    pl([(2122, 356), (2262, 274), (2426, 358)], 1.0, 0.7, skip=0.3)
    m = s.rect(2248, 300, 2278, 338)
    s.lift(m, 1.0, soft=0.8, wob=0.5)
    s.wash(m, OCHRE, 0.5, wob=0.8, soft=0.8, edge=0.5, ew=2)
    s.wash(s.blob(2263, 319, 44, 46), AMBER, 0.08, wob=2, bleed=8, edge=0)
    box(s, r, 2248, 300, 2278, 338, 1.2, PEN, 1.1, over=2)
    line(s, r, (2263, 300), (2263, 338), 1.0, PEN, 0.9)
    chimney(2362, 330, 268, 28, 2)
    # 9  behind the narrow building: seen
    mass([(2432, 334), (2660, 330), (2660, BOT), (2432, BOT)], top=332, k=0.8, c2=PRUSSIAN, k2=0.2)
    s.wash(s.rect(2426, 328, 2666, 341), PAYNE, 0.4, wob=1, soft=0.8, edge=0.5, ew=2)
    pl([(2432, 470), (2432, 334), (2662, 330), (2662, 400)], 1.6, 1.2)
    line(s, r, (2430, 343), (2664, 340), 1.0, PEN, 0.8, skip=0.15)
    wins(2448, 2650, 366, 4, 22, 34, lit=(2,), skipn=())
    wins(2448, 2650, 428, 4, 22, 34, lit=(), skipn=(3,))
    aerial(2500, 332, 74, 4, -0.03)
    rail(2560, 2658, 331, 14)
    streaks(s, r, 2440, 2655, 342, 470, 6, PAYNE, 0.14, (5, 12))
    mass([(2652, 388), (2830, 388), (2830, BOT), (2652, BOT)], top=380, k=0.7)
    roof([(2652, 392), (2690, 352), (2800, 350), (2832, 392)], 0.5)
    pl([(2650, 392), (2690, 351), (2800, 349), (2834, 392)])
    chimney(2722, 352, 312, 26, 2)
    wins(2665, 2820, 412, 3, 20, 30, lit=(), skipn=())
    # 10  far right
    mass([(2822, 300), (W + 40, 296), (W + 40, BOT), (2822, BOT)], top=300, k=0.76, c2=VIOLET)
    pl([(2822, 392), (2822, 300), (W + 10, 296)], 1.6, 1.2)
    tank(2900, 298, 72, 46)
    aerial(3024, 297, 60, 3, 0.02)
    wins(2836, 3066, 330, 5, lit=(1,))
    # the damp air between here and there
    s.wash(s.rect(-60, 380, W + 60, 800), None, 0.22, wob=0, soft=0, edge=0, gran=0, flow=0.8, fs=260, grad=s.vgrad(380, 560, 0, 1), lift=True)
    S.body[452:BOT, :] = 1.0                 # below every roof the row is solid
    S.save("st_far", q=90)


# ---------------------------------------------------------------------------------------------- façade vocabulary
def hl(s, pts, w=2.0, amt=0.3, dry=0.0, clip=None):
    """A wet highlight: pigment lifted along a line (rain on an edge catching the sky)."""
    s.wash(s.ribbon(pts, w, smooth=len(pts) > 2), None, amt, wob=0, soft=0.7, edge=0, gran=0.2, flow=0, lift=True, dry=dry, clip=clip)


def wallwash(s, r, m, washes, y0, y1, dark_top=True, bx=None, drags=6):
    """A wall: the first wash sets the body and pools at its edges, the others are dropped in while it is wet,
    then a few drags of a nearly dry flat brush so the hand shows."""
    c, k = washes[0]
    m = s.wash(m, c, k, wob=2.0, soft=0.9, edge=0.4, ew=8, flow=0.5, fs=230, gran=0.38, body=1)
    for i, (c, k) in enumerate(washes[1:]):
        g = s.vgrad(y0 - 40, y0 + (y1 - y0) * U(r, 0.5, 0.9), 1, 0.4) if (dark_top and i == 0) else None
        s.wash(m, c, k, wob=3, bleed=10, edge=0.15, flow=0.6, fs=U(r, 150, 260), gran=0.35, grad=g, clip=m)
    if bx is not None and drags:
        xa, xb = bx
        c2 = washes[1][0] if len(washes) > 1 else c
        for _ in range(drags):
            if r.random() < 0.6:
                y = U(r, y0 + 10, y1 - 10)
                a = U(r, xa, xa + (xb - xa) * 0.5)
                b = min(xb, a + U(r, 0.3, 0.8) * (xb - xa))
                pts = [(a, y), ((a + b) / 2, y + J(r, 8)), (b, y + J(r, 10))]
            else:
                x = U(r, xa + 10, xb - 10)
                a = U(r, y0, y0 + (y1 - y0) * 0.5)
                b = min(y1, a + U(r, 0.3, 0.7) * (y1 - y0))
                pts = [(x, a), (x + J(r, 8), (a + b) / 2), (x + J(r, 10), b)]
            s.stroke(pts, U(r, 26, 70), c2, U(r, 0.07, 0.15), dry=U(r, 0.42, 0.6), edge=0.25, wob=2, taper=(0.1, 0.3), gran=0.5, clip=m)
    return m


def window(s, r, x0, y0, x1, y1, kind="sash", cols=1, lit=False, frame=MIST, fk=0.42, glass=INKBLUE, gk=0.85, sill=True, pen=SEPIA,
           curtain=None, head=None, halo=True, f=5.0, bar=3.0, dim=0.3):
    """One window, drawn for itself: frame, panes laid one by one, what the glass shows, sill and its drip."""
    x0, x1, y0, y1 = x0 + J(r, 2), x1 + J(r, 2), y0 + J(r, 2), y1 + J(r, 2)
    m = s.rect(x0, y0, x1, y1)
    put(s, m, frame, fk, lift=0.85, wob=0.8, edge=0.4, ew=3)
    s.wash(m, PAYNE, 0.22, wob=1, soft=1, edge=0, flow=0.5, fs=30)
    gx0, gy0, gx1, gy1 = x0 + f, y0 + f, x1 - f, y1 - f
    rows = {"sash": 2, "case": 3, "grid": 3, "one": 1}[kind]
    if kind == "case":
        cols = 2
    pw, ph = (gx1 - gx0 - bar * (cols - 1)) / cols, (gy1 - gy0 - bar * (rows - 1)) / rows
    if curtain is None and lit:
        curtain = ("drapes", "drawn", "blind")[int(r.integers(0, 3))]
    for i in range(cols):
        for j in range(rows):
            px, py = gx0 + i * (pw + bar), gy0 + j * (ph + bar)
            pm = Q(s, [(px + J(r, 1.2), py + J(r, 1.2)), (px + pw + J(r, 1.2), py + J(r, 1.2)), (px + pw + J(r, 1.2), py + ph + J(r, 1.2)), (px + J(r, 1.2), py + ph + J(r, 1.2))])
            if lit:
                s.lift(pm, 1.0, soft=0.6, wob=0)
                s.wash(pm, OCHRE, U(r, 0.4, 0.55), wob=0, soft=0.8, edge=0.4, ew=2, flow=0.4, fs=30)
            else:
                s.wash(pm, glass, gk * U(r, 0.8, 1.15), wob=0, soft=0.8, edge=0.5, ew=3, flow=0.5, fs=30)
    gw, gh = gx1 - gx0, gy1 - gy0
    gm = s.rect(gx0, gy0, gx1, gy1)
    if lit:
        if curtain == "drapes":
            for sd in (0, 1):
                xa = gx0 if sd == 0 else gx1 - gw * U(r, 0.24, 0.34)
                xb = gx0 + gw * U(r, 0.24, 0.34) if sd == 0 else gx1
                cm = Q(s, [(xa, gy0), (xb, gy0), (xb + (-5 if sd == 0 else 0), gy1), (xa + (0 if sd == 0 else 5), gy1)])
                s.wash(cm, SIENNA, 0.5, wob=1, soft=1, edge=0.5, ew=2, clip=gm)
                for q in (0.3, 0.65):
                    xx = xa + (xb - xa) * q
                    s.ink([(xx, gy0 + 2), (xx + J(r, 2), gy0 + gh / 2), (xx + J(r, 2), gy1 - 2)], 1.0, BURNT, 0.6, skip=0.2, clip=gm)
        elif curtain == "drawn":
            s.wash(gm, AMBER, 0.32, wob=1, soft=1, edge=0.3)
            s.wash(gm, SIENNA, 0.25, wob=1, soft=1, edge=0, grad=s.vgrad(gy0, gy1, 0.2, 1))
            for q in np.linspace(0.12, 0.9, 6):
                xx = gx0 + gw * q + J(r, 3)
                s.ink([(xx, gy0 + 2), (xx + J(r, 2), gy0 + gh / 2), (xx + J(r, 2), gy1 - 2)], 1.0, BURNT, 0.5, skip=0.25, clip=gm)
        else:
            bm = s.rect(gx0, gy0, gx1, gy0 + gh * U(r, 0.35, 0.6))
            s.wash(bm, SIENNA, 0.38, wob=0.8, soft=0.8, edge=0.5, ew=2)
            px = gx0 + gw * U(r, 0.3, 0.7)                                                          # a pot plant on the sill inside
            s.wash(s.rect(px - 7, gy1 - 11, px + 7, gy1), BURNT, 0.8, wob=0, soft=0.8, clip=gm)
            for _ in range(6):
                s.stroke([(px + J(r, 3), gy1 - 10), (px + J(r, 16), gy1 - U(r, 22, 44))], U(r, 3, 5), UMBER, 0.8, taper=(0, 0.7), wob=0.5, edge=0.3, clip=gm)
        s.wash(gm, SIENNA, dim, wob=1, soft=1, edge=0.3, ew=4, flow=0.6, fs=40)              # a small lamp somewhere inside, no more
        if halo:
            hm = s.blob((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 1.1, (y1 - y0) * 0.95, irr=0.15) * (1 - m)
            s.wash(hm, None, 0.14, wob=2, bleed=12, edge=0, gran=0, flow=0, lift=True)
            s.wash(hm, AMBER, 0.07, wob=2, bleed=12, edge=0)
        LIT.append([int(x0), int(y0), int(x1), int(y1)])
    else:
        q = r.random()
        if q < 0.75:            # the sky in the upper glass
            a = U(r, 0.4, 0.8)
            s.lift(Q(s, [(gx0, gy0), (gx0 + gw * a, gy0), (gx0 + gw * a * 0.3, gy0 + gh * U(r, 0.35, 0.6)), (gx0, gy0 + gh * U(r, 0.45, 0.7))]), U(r, 0.16, 0.3), soft=2.5, wob=1.5)
        q = r.random() if curtain is None else {"net": 0.1, "blind": 0.4, "none": 0.9}[curtain]
        if q < 0.3:             # a net curtain
            s.lift(Q(s, [(gx0, gy0 + gh * U(r, 0.3, 0.5)), (gx1, gy0 + gh * U(r, 0.3, 0.5)), (gx1, gy1), (gx0, gy1)]), U(r, 0.22, 0.34), soft=1.2, wob=1.2)
        elif q < 0.45:          # a blind left half down
            s.lift(s.rect(gx0, gy0, gx1, gy0 + gh * U(r, 0.3, 0.55)), U(r, 0.25, 0.4), soft=1, wob=0.8)
    box(s, r, x0, y0, x1, y1, 1.9, pen, 1.5, over=4, dbl=0.35)
    for i in range(1, cols):
        xx = gx0 + i * (pw + bar) - bar / 2
        line(s, r, (xx, gy0), (xx + J(r, 1), gy1), 1.2, pen, 1.1, over=1, skip=0.1)
    for j in range(1, rows):
        yy = gy0 + j * (ph + bar) - bar / 2
        line(s, r, (gx0, yy), (gx1, yy + J(r, 1)), 1.4 if kind == "sash" else 1.1, pen, 1.1, over=1, skip=0.1)
    if r.random() < 0.6:
        box(s, r, gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, 1.0, pen, 0.8, over=1, dbl=0, j=0.6, skip=0.3)
    if head == "lintel":
        lm = s.rect(x0 - 8, y0 - 15, x1 + 8, y0 - 2)
        s.lift(lm, 0.4, soft=0.8, wob=0.8)
        box(s, r, x0 - 8, y0 - 15, x1 + 8, y0 - 2, 1.3, pen, 1.1, over=3, dbl=0.2, skip=0.1)
    elif head == "arch":
        cx, w2 = (x0 + x1) / 2, (x1 - x0) / 2
        for dy, ww, kk in ((0, 1.6, 1.3), (-13, 1.2, 1.0)):
            s.ink([(x0 - 5, y0 + 2 + dy * 0.3), (cx, y0 - 9 + dy), (x1 + 5, y0 + 2 + dy * 0.3)], ww, pen, kk)
        for q in np.linspace(-0.85, 0.85, 8):
            xx = cx + q * w2
            yy = y0 - 9 * (1 - q * q) + 1
            if r.random() < 0.8:
                line(s, r, (xx, yy - 1), (xx + q * 4, yy - 12), 0.9, pen, 0.8, over=0)
    elif head == "hood":
        hl(s, [(x0 - 9, y0 - 7), (x1 + 9, y0 - 7)], 5, 0.35)
        line(s, r, (x0 - 10, y0 - 3), (x1 + 10, y0 - 3), 1.8, pen, 1.4, dbl=0.5)
        line(s, r, (x0 - 8, y0 - 11), (x1 + 8, y0 - 11), 1.1, pen, 1.0, skip=0.15)
    if sill:
        sm = s.rect(x0 - 7, y1, x1 + 7, y1 + 8)
        put(s, sm, MIST, 0.4, lift=0.75, wob=0.6, edge=0.3, ew=2)
        s.wash(s.rect(x0 - 4, y1 + 8, x1 + 4, y1 + 19), SEPIA, 0.32, wob=1.5, bleed=3, edge=0.1)
        line(s, r, (x0 - 8, y1 + 8), (x1 + 8, y1 + 8), 2.0, pen, 1.5, dbl=0.4)
        line(s, r, (x0 - 7, y1), (x1 + 7, y1), 1.0, pen, 0.9, skip=0.2)
        for _ in range(int(r.integers(1, 4))):
            xx = U(r, x0 - 4, x1 + 4)
            s.stroke([(xx, y1 + 8), (xx + J(r, 2), y1 + U(r, 30, 90))], U(r, 4, 9), PAYNE, U(r, 0.12, 0.24), dry=0.3, edge=0.3, wob=1, taper=(0, 0.7))
    return x0, y0, x1, y1


def louvres(s, r, x0, y0, x1, y1, c=TEAL, k=0.9, pen=SEPIA, gap=6.5):
    """A louvred shutter leaf."""
    m = s.rect(x0, y0, x1, y1)
    put(s, m, c, k, lift=0.85, wob=0.8, edge=0.5, ew=3, flow=0.4, fs=30)
    s.wash(m, PAYNE, 0.35, wob=1, soft=1, edge=0, grad=s.vgrad(y0, y1, 0.4, 1))
    y = y0 + gap
    while y < y1 - 3:
        seg(s, (x0 + 3, y + J(r, 0.6)), (x1 - 3, y + J(r, 0.6)), 1.0, pen, U(r, 0.6, 1.0), r=r, skip=0.15)
        y += gap * U(r, 0.9, 1.1)
    box(s, r, x0, y0, x1, y1, 1.5, pen, 1.3, over=2, dbl=0.2)


def acbox(s, r, x, y, w=58, h=38, pen=SEPIA):
    m = s.rect(x, y, x + w, y + h)
    put(s, m, MIST, 0.6, lift=0.85, wob=0.7, edge=0.4, ew=3)
    s.wash(m, PAYNE, 0.4, wob=1, soft=2, edge=0, grad=s.hgrad(x, x + w, 0.3, 1))
    oval(s, x + w * 0.36, y + h * 0.5, h * 0.34, h * 0.34, 1.1, pen, 1.0)
    s.wash(s.ellipse(x + w * 0.36, y + h * 0.5, h * 0.3, h * 0.3), PAYNE, 0.5, wob=0.6, soft=0.8)
    for q in (0.3, 0.5, 0.7):
        line(s, r, (x + w * 0.7, y + h * q), (x + w * 0.93, y + h * q), 0.9, pen, 0.9, over=0)
    box(s, r, x, y, x + w, y + h, 1.5, pen, 1.4, over=2, dbl=0.2)
    line(s, r, (x + 6, y + h), (x + 2, y + h + 12), 1.3, pen, 1.2, over=0)
    line(s, r, (x + w - 6, y + h), (x + w - 2, y + h + 12), 1.3, pen, 1.2, over=0)
    xx = x + w * U(r, 0.3, 0.7)
    s.stroke([(xx, y + h + 4), (xx + J(r, 3), y + h + U(r, 60, 130))], U(r, 5, 9), PAYNE, 0.26, dry=0.25, edge=0.4, wob=1.2, taper=(0, 0.7))


def pipe(s, r, x, y0, y1, w=8.0, pen=SEPIA):
    hl(s, [(x - 1, y0), (x - 1, y1)], w * 0.8, 0.3)
    s.ink([(x - w / 2, y0), (x - w / 2 + J(r, 1.2), (y0 + y1) / 2), (x - w / 2, y1)], 1.3, pen, 1.2, tremor=0.9, skip=0.05)
    s.ink([(x + w / 2, y0), (x + w / 2 + J(r, 1.2), (y0 + y1) / 2), (x + w / 2, y1)], 1.9, pen, 1.5, tremor=0.9)
    yy = y0 + U(r, 30, 80)
    while yy < y1 - 20:
        seg(s, (x - w / 2 - 4, yy), (x + w / 2 + 4, yy + J(r, 1)), 2.2, pen, 1.4, r=r)
        yy += U(r, 110, 170)


def railing(s, r, x0, x1, y, h, gap=10.0, pen=INKBLUE, slab=7.0, knots=0.0):
    """A balcony front: slab edge, bars one by one, a wet top rail."""
    if slab:
        sm = s.rect(x0 - 5, y, x1 + 5, y + slab)
        put(s, sm, SLATE, 0.6, lift=0.6, wob=0.7, edge=0.4, ew=2)
        s.wash(s.rect(x0 - 2, y + slab, x1 + 2, y + slab + 14), SEPIA, 0.4, wob=1.5, bleed=4, edge=0.1)
        line(s, r, (x0 - 6, y + slab), (x1 + 6, y + slab), 2.0, SEPIA, 1.5, dbl=0.4)
        line(s, r, (x0 - 6, y), (x1 + 6, y), 1.1, SEPIA, 1.0, skip=0.15)
    x = x0 + 3
    while x < x1 - 2:
        seg(s, (x + J(r, 0.8), y - h), (x + J(r, 1.2), y - 1), 1.3, pen, U(r, 1.0, 1.5), r=r, skip=0.05)
        if knots and r.random() < knots:
            oval(s, x + gap / 2, y - h * U(r, 0.4, 0.6), gap * 0.42, gap * 0.5, 0.9, pen, 1.0)
        x += gap * U(r, 0.85, 1.15)
    line(s, r, (x0 - 3, y - h), (x1 + 3, y - h + J(r, 1.5)), 2.4, pen, 1.5, dbl=0.6)
    line(s, r, (x0, y - h + 7), (x1, y - h + 7 + J(r, 1)), 1.1, pen, 1.1, skip=0.1)
    hl(s, [(x0, y - h - 2.5), (x1, y - h - 2.5)], 1.8, 0.4)


def roller(s, r, x0, y0, x1, y1, c=SLATE, k=0.8, gap=10.0, pen=SEPIA, housing=22):
    m = s.rect(x0, y0, x1, y1)
    put(s, m, c, k, lift=0.85, wob=1.0, edge=0.4, ew=5, flow=0.5, fs=90, gran=0.45)
    s.wash(m, PAYNE, 0.38, wob=1, soft=2, edge=0, grad=s.vgrad(y0, y1, 0.25, 1.0), flow=0.6, fs=60)       # grime rising from the pavement
    y = y0 + gap
    while y < y1 - 4:
        seg(s, (x0 + 2 + J(r, 2), y + J(r, 0.8)), (x1 - 2 + J(r, 2), y + J(r, 0.8)), U(r, 0.9, 1.5), pen, U(r, 0.5, 1.0), r=r, skip=0.12, bow=0.002)
        if r.random() < 0.3:    # light caught on the curl of a slat
            a = U(r, x0 + 4, x0 + (x1 - x0) * 0.5)
            hl(s, [(a, y - gap * 0.55), (min(x1 - 4, a + U(r, 40, (x1 - x0) * 0.6)), y - gap * 0.55)], 2.4, U(r, 0.14, 0.26))
        y += gap * U(r, 0.92, 1.08)
    streaks(s, r, x0 + 6, x1 - 6, y0, y1, max(3, int((x1 - x0) / 45)), PAYNE, 0.16, (6, 16), clip=m)
    s.wash(s.rect(x0, y1 - 16, x1, y1), PAYNE, 0.4, wob=1, soft=1.5, edge=0.3)                           # bottom bar
    line(s, r, (x0, y1 - 16), (x1, y1 - 16), 1.6, pen, 1.3)
    lk = x0 + (x1 - x0) * U(r, 0.4, 0.6)
    put(s, s.rect(lk - 8, y1 - 26, lk + 8, y1 - 8), SEPIA, 0.7, lift=0.3, wob=0.5)
    box(s, r, x0, y0, x1, y1, 2.0, pen, 1.5, over=5, dbl=0.4)
    if housing:
        hm = s.rect(x0 - 6, y0 - housing, x1 + 6, y0)
        put(s, hm, c, k * 0.9, lift=0.85, wob=0.8, edge=0.5, ew=3)
        s.wash(hm, PAYNE, 0.5, wob=1, soft=1.5, edge=0, grad=s.vgrad(y0 - housing, y0, 0.3, 1))
        box(s, r, x0 - 6, y0 - housing, x1 + 6, y0, 1.6, pen, 1.4, over=4, dbl=0.3)
        s.wash(s.rect(x0, y0, x1, y0 + 14), SEPIA, 0.4, wob=1.5, bleed=4, edge=0.1)


def bricks(s, r, x0, y0, x1, y1, n=10, course=10.0, bl=25.0, pen=SEPIA, k=0.8, clip=None, tint=(BURNT, UMBER, VIOLET)):
    """Brickwork said in patches: a few courses here and there, and single bricks touched in darker or redder."""
    for _ in range(n):
        cx, cy = U(r, x0 + 20, x1 - 20), U(r, y0 + 10, y1 - 10)
        rows, cols = int(r.integers(2, 6)), int(r.integers(2, 6))
        j0 = round((cy - y0) / course)
        for j in range(rows):
            y = y0 + (j0 + j) * course
            if not (y0 < y < y1):
                continue
            xa = cx - cols * bl / 2 + J(r, bl * 0.6)
            xb = xa + cols * bl * U(r, 0.6, 1.1)
            seg(s, (max(x0, xa), y + J(r, 0.6)), (min(x1, xb), y + J(r, 0.6)), 1.0, pen, k * U(r, 0.6, 1.0), r=r, skip=0.2, clip=clip)
            off = (bl / 2) if (j0 + j) % 2 else 0
            for i in range(cols):
                x = cx - cols * bl / 2 + i * bl + off + J(r, 1.5)
                if x0 < x < x1 and r.random() < 0.7:
                    seg(s, (x, y + 1), (x + J(r, 0.8), y + course - 1), 0.9, pen, k * 0.8, r=r, clip=clip)
    for _ in range(n * 3):
        j = int(r.integers(0, max(1, int((y1 - y0) / course))))
        x = U(r, x0, x1 - bl)
        bm = s.rect(x, y0 + j * course + 1, x + bl * U(r, 0.8, 1.0), y0 + (j + 1) * course - 1)
        if r.random() < 0.3:
            s.lift(bm, U(r, 0.15, 0.3), soft=0.9, wob=0)
        else:
            s.wash(bm, tint[int(r.integers(0, len(tint)))], U(r, 0.15, 0.4), wob=0, soft=0.9, edge=0.4, ew=2, flow=0, clip=clip)


def cable(s, r, a, b, sag, w=1.4, c=INKBLUE, k=1.2):
    mid = ((a[0] + b[0]) / 2 + J(r, 6), (a[1] + b[1]) / 2 + sag)
    q1 = ((a[0] * 3 + b[0]) / 4, (a[1] * 3 + b[1]) / 4 + sag * 0.75)
    q3 = ((a[0] + b[0] * 3) / 4, (a[1] + b[1] * 3) / 4 + sag * 0.75)
    s.ink([a, q1, mid, q3, b], w, c, k, tremor=0.5, press=0.2, taper=(0.02, 0.02), dry=0.15)


# ---------------------------------------------------------------------------------------------- the row, house by house
def bld_c(S, r):
    """The plain rendered hall left of the café: a blind wall for the neon, a garage shutter, a mean little door."""
    x0, x1, top = 1008, 1391, 482
    s = Sub(S, x0 - 70, top - 110, x1 + 70, PAVE + 40)
    pts = [(x0, top), (x0 + 96, top), (x0 + 96, top - 34), (x1 - 96, top - 34), (x1 - 96, top), (x1, top), (x1, PAVE + 14), (x0, PAVE + 14)]
    m = Q(s, [(x0 - 6, top)] + pts[1:5] + [(x1 + 6, top), (x1 + 6, PAVE + 14), (x0 - 6, PAVE + 14)])
    m = wallwash(s, r, m, [(PAYNE, 0.72), (SLATE, 0.42), (VIOLET, 0.14)], top, PAVE, bx=(x0, x1), drags=7)
    mottle(s, r, x0 + 30, 540, x1 - 30, 930, [VIOLET, PRUSSIAN, SLATE, TEAL], 5, 0.10, size=(70, 150), clip=m)
    s.lift(s.blob(1230, 700, 150, 190, irr=0.3), 0.12, bleed=40, wob=5)
    streaks(s, r, x0 + 10, x1 - 10, top + 6, 760, 8, PAYNE, 0.11, (6, 18), clip=m)
    # coping along the stepped parapet
    cop = [(x0 - 4, top), (x0 + 96, top), (x0 + 96, top - 34), (x1 - 96, top - 34), (x1 - 96, top), (x1 + 4, top)]
    for a, b in zip(cop, cop[1:]):
        hl(s, [(a[0], a[1] + 4), (b[0], b[1] + 4)], 6, 0.35)
        line(s, r, a, b, 2.2, SEPIA, 1.5, dbl=0.5)
        line(s, r, (a[0], a[1] + 9), (b[0], b[1] + 9), 1.1, SEPIA, 1.0, skip=0.15)
    # three louvred vents under the parapet
    for cx in (1150, 1250):
        vm = s.rect(cx - 22, 486, cx + 22, 508)
        s.wash(vm, INKBLUE, 0.7, wob=0.8, soft=0.8, edge=0.5, ew=2)
        for yy in (491, 497, 503):
            line(s, r, (cx - 20, yy), (cx + 20, yy + J(r, 0.8)), 1.0, SEPIA, 1.0, over=0, skip=0.1)
        box(s, r, cx - 22, 486, cx + 22, 508, 1.5, SEPIA, 1.3, over=3)
    # a string course over the ground storey
    hl(s, [(x0 + 2, 952), (x1 - 2, 952)], 7, 0.3)
    line(s, r, (x0, 946), (x1, 947), 1.3, SEPIA, 1.1, skip=0.1)
    line(s, r, (x0, 958), (x1, 958), 2.0, SEPIA, 1.4, dbl=0.5)
    s.wash(s.rect(x0, 958, x1, 978), SEPIA, 0.3, wob=1.5, bleed=5, edge=0.1)
    gm = s.rect(x0, 960, x1, PAVE + 14)
    s.wash(gm, PAYNE, 0.3, wob=2, bleed=8, edge=0.2, flow=0.6, fs=80)
    # garage shutter
    roller(s, r, 1040, 1006, 1262, PAVE, SLATE, 0.85, gap=10.5, housing=24)
    s.wash(s.blob(1100, 1150, 60, 90, irr=0.3), TEAL, 0.14, wob=4, bleed=14, edge=0.2)
    # the door, a step, a little tin canopy
    dm = s.rect(1294, 1040, 1366, PAVE - 6)
    put(s, dm, PRUSSIAN, 0.9, lift=0.8, wob=1, edge=0.5, ew=4, flow=0.5, fs=50)
    s.wash(dm, PAYNE, 0.4, wob=1, soft=2, edge=0, grad=s.vgrad(1040, PAVE, 0.3, 1))
    box(s, r, 1294, 1040, 1366, PAVE - 6, 2.0, SEPIA, 1.5, over=4, dbl=0.4)
    box(s, r, 1304, 1052, 1356, 1140, 1.2, SEPIA, 1.1, over=2)
    box(s, r, 1304, 1154, 1356, 1268, 1.2, SEPIA, 1.1, over=2)
    s.wash(s.rect(1306, 1054, 1354, 1138), INKBLUE, 0.5, wob=0.8, soft=1, edge=0.4, ew=2)
    s.wash(s.ellipse(1350, 1166, 4, 4), OCHRE, 0.2, wob=0.3, soft=0.5)
    oval(s, 1350, 1166, 4, 4, 1.0, SEPIA, 1.2)
    put(s, s.rect(1286, PAVE - 6, 1374, PAVE + 6), MIST, 0.5, lift=0.7, wob=0.8, edge=0.4, ew=2)
    line(s, r, (1284, PAVE - 6), (1376, PAVE - 6), 1.6, SEPIA, 1.4)
    cp = [(1280, 1026), (1380, 1026), (1386, 1006), (1276, 1008)]
    put(s, Q(s, cp), SLATE, 0.7, lift=0.6, wob=0.8, edge=0.5, ew=3)
    path(s, cp, 1.6, SEPIA, 1.4, closed=True, over=3, r=r)
    s.wash(s.rect(1284, 1026, 1376, 1050), SEPIA, 0.4, wob=1.5, bleed=5, edge=0.1)
    # a junction box and conduit that climb the edge
    put(s, s.rect(1268, 1090, 1286, 1122), SLATE, 0.6, lift=0.5, wob=0.5, edge=0.4, ew=2)
    box(s, r, 1268, 1090, 1286, 1122, 1.3, SEPIA, 1.3, over=2)
    s.ink([(1277, 1090), (1278, 1020), (1379, 1000), (1380, 960)], 1.5, SEPIA, 1.2, tremor=0.8)
    pipe(s, r, 1021, top + 8, PAVE, 9)
    # the foot of the wall, dark with splash
    s.wash(s.rect(x0, PAVE - 46, x1, PAVE + 14), SEPIA, 0.3, wob=3, bleed=10, edge=0.1, clip=m)
    path(s, pts[:6], 2.3, SEPIA, 1.5, over=5, r=r)
    line(s, r, (x0, top), (x0 + J(r, 2), PAVE), 2.2, SEPIA, 1.4, dbl=0.4)
    line(s, r, (x1, top), (x1 + J(r, 2), 600), 2.2, SEPIA, 1.4, dbl=0.4)


def cafe_front(S, r):
    """The café's ground floor: dark timber, a big three-light window, a glazed door, a wet striped awning."""
    s = Sub(S, 1330, 540, 2470, PAVE + 40)
    X0, X1 = 1391, 2409
    wx0, wy0, wx1, wy1 = WIN
    T = s.rect(X0 - 7, 594, X1 + 7, PAVE + 14)
    T = s.wash(T, UMBER, 0.92, wob=1.0, soft=0.9, edge=0.4, ew=7, flow=0.55, fs=150, gran=0.45, body=1)
    s.wash(T, SEPIA, 0.42, wob=3, bleed=12, edge=0.15, flow=0.8, fs=110, gran=0.4, clip=T)
    s.wash(T, INDIGO, 0.12, wob=3, bleed=16, edge=0.1, flow=0.8, fs=200, grad=s.vgrad(600, 760, 1, 0.2), clip=T)
    for _ in range(10):                      # the grain of long boards, dragged dry
        y = U(r, 620, PAVE - 10)
        a = U(r, X0, X1 - 300)
        s.stroke([(a, y), (a + U(r, 200, 600), y + J(r, 4))], U(r, 10, 30), SEPIA, U(r, 0.08, 0.16), dry=0.5, edge=0.2, wob=1.5, taper=(0.1, 0.3), clip=T)
    # cornice over the fascia
    cm = s.rect(X0 - 8, 594, X1 + 8, 611)
    put(s, cm, UMBER, 0.8, lift=0.7, wob=0.8, edge=0.4, ew=3)
    hl(s, [(X0 - 6, 596), (X1 + 6, 596)], 3.0, 0.5)
    s.wash(s.rect(X0, 611, X1, 628), SEPIA, 0.5, wob=1.5, bleed=4, edge=0.1)
    line(s, r, (X0 - 9, 594), (X1 + 9, 593), 2.2, SEPIA, 1.5, dbl=0.5)
    line(s, r, (X0 - 8, 611), (X1 + 8, 611), 2.4, SEPIA, 1.6, dbl=0.5)
    line(s, r, (X0 - 4, 603), (X1 + 4, 603), 1.0, SEPIA, 0.9, skip=0.25)
    # fascia board: left blank
    sx0, sy0, sx1, sy1 = SIGN
    fm = s.rect(sx0, sy0, sx1, sy1)
    put(s, fm, UMBER, 0.72, lift=0.72, wob=1.0, edge=0.45, ew=5, flow=0.5, fs=160, gran=0.45)
    s.wash(fm, PAYNE, 0.22, wob=2, bleed=10, edge=0.1, flow=0.8, fs=120)
    for _ in range(9):
        y = U(r, sy0 + 8, sy1 - 8)
        xa = U(r, sx0 + 10, sx1 - 300)
        s.stroke([(xa, y), (xa + U(r, 150, 500), y + J(r, 3))], U(r, 6, 16), SEPIA, U(r, 0.08, 0.16), dry=0.5, edge=0.2, wob=1, taper=(0.1, 0.2), clip=fm)
    box(s, r, sx0, sy0, sx1, sy1, 2.2, SEPIA, 1.5, over=6, dbl=0.5)
    box(s, r, sx0 + 8, sy0 + 7, sx1 - 8, sy1 - 7, 1.1, SEPIA, 1.0, over=2, dbl=0.1, skip=0.15)
    # pilasters with consoles, panels and plinth blocks
    for px0, px1 in ((1397, 1462), (2338, 2403)):
        pm = s.rect(px0, 700, px1, PAVE + 6)
        s.lift(s.rect(px0 + 8, 720, px1 - 8, 1236), 0.16, soft=4, wob=2)
        line(s, r, (px0, 612), (px0 + J(r, 1.5), PAVE), 2.2, SEPIA, 1.5, dbl=0.5)
        line(s, r, (px1, 612), (px1 + J(r, 1.5), PAVE), 2.2, SEPIA, 1.5, dbl=0.5)
        box(s, r, px0 + 13, 930, px1 - 13, 1206, 1.3, SEPIA, 1.2, over=3, dbl=0.3)
        s.wash(s.rect(px0 + 15, 932, px1 - 15, 1204), SEPIA, 0.25, wob=1, soft=1.5, edge=0.4, ew=3)
        hl(s, [(px0 + 16, 1203), (px1 - 16, 1203)], 1.8, 0.3)
        bm = s.rect(px0 - 4, 1238, px1 + 4, PAVE + 6)
        put(s, bm, UMBER, 0.9, lift=0.6, wob=0.8, edge=0.5, ew=3)
        s.wash(bm, SEPIA, 0.5, wob=1, soft=2, grad=s.vgrad(1238, PAVE, 0.3, 1))
        box(s, r, px0 - 4, 1238, px1 + 4, PAVE + 2, 1.8, SEPIA, 1.5, over=3, dbl=0.3)
        hl(s, [(px0 - 2, 1240), (px1 + 2, 1240)], 2.2, 0.4)
        # console bracket under the cornice
        cx = (px0 + px1) / 2
        con = [(px0 + 4, 612), (px1 - 4, 612), (px1 - 6, 650), (px1 - 14, 684), (cx, 698), (px0 + 14, 684), (px0 + 6, 650)]
        km = s.poly(con)
        put(s, km, UMBER, 0.85, lift=0.6, wob=0.8, edge=0.5, ew=3)
        s.wash(km, SEPIA, 0.4, wob=1, soft=2, edge=0, grad=s.hgrad(px0, px1, 0.2, 1))
        s.ink(con + [con[0]], 1.8, SEPIA, 1.5)
        s.ink(ell(cx, 640, 13, 15, 0.5, 5.6, 24), 1.2, SEPIA, 1.2)
        s.ink(ell(cx, 672, 8, 9, 3.6, 8.8, 20), 1.1, SEPIA, 1.1)
    # window frame, sill, stall riser
    s.lift(s.rect(wx0 - 9, wy0 - 14, wx1 + 9, wy1 + 2), 0.12, soft=2, wob=1)
    sill = s.rect(wx0 - 16, wy1 + 1, wx1 + 14, wy1 + 15)
    put(s, sill, UMBER, 0.75, lift=0.75, wob=0.8, edge=0.4, ew=3)
    hl(s, [(wx0 - 14, wy1 + 3), (wx1 + 12, wy1 + 3)], 3.0, 0.55)
    s.wash(s.rect(wx0 - 14, wy1 + 1, wx1 + 12, wy1 + 7), OCHRE, 0.22, wob=0.6, soft=0.8, edge=0)
    s.wash(s.rect(wx0 - 12, wy1 + 15, wx1 + 10, wy1 + 30), SEPIA, 0.55, wob=1.5, bleed=4, edge=0.1)
    line(s, r, (wx0 - 17, wy1 + 15), (wx1 + 15, wy1 + 15), 2.2, SEPIA, 1.6, dbl=0.6)
    line(s, r, (wx0 - 17, wy1 + 1), (wx1 + 15, wy1 + 1), 1.4, SEPIA, 1.3)
    pw = (wx1 - wx0 - 24) / 3
    for i in range(3):
        ax = wx0 + i * (pw + 12)
        a0, a1 = ax + 10, ax + pw - 10
        pm = s.rect(a0, wy1 + 26, a1, PAVE - 14)
        s.wash(pm, SEPIA, 0.3, wob=1, soft=1.5, edge=0.5, ew=4)
        s.lift(s.rect(a0 + 10, wy1 + 34, a1 - 10, PAVE - 22), 0.14, soft=3, wob=1.5)
        box(s, r, a0, wy1 + 26, a1, PAVE - 14, 1.5, SEPIA, 1.3, over=3, dbl=0.4)
        box(s, r, a0 + 8, wy1 + 33, a1 - 8, PAVE - 21, 1.0, SEPIA, 1.0, over=2, dbl=0.1, skip=0.15)
        hl(s, [(a0 + 9, PAVE - 22), (a1 - 9, PAVE - 22)], 1.6, 0.3)
    plinth = s.rect(1462, PAVE - 9, 2126, PAVE + 6)
    s.wash(plinth, SEPIA, 0.45, wob=1, soft=1.5, edge=0.3)
    line(s, r, (1462, PAVE - 9), (2126, PAVE - 9), 1.6, SEPIA, 1.4, dbl=0.4)
    # door: post, leaf, head panel, kick panel, threshold
    dx0, dy0, dx1, dy1 = DOOR
    gx0, gy0, gx1, gy1 = DOORG
    leaf = s.rect(dx0, dy0, dx1, dy1)
    put(s, leaf, UMBER, 0.95, lift=0.6, wob=0.8, edge=0.4, ew=4, flow=0.5, fs=80)
    s.wash(leaf, PRUSSIAN, 0.18, wob=2, bleed=8, edge=0.1)
    s.lift(s.rect(dx0 + 6, gy1 + 10, dx1 - 6, dy1 - 10), 0.14, soft=3, wob=1.5)
    box(s, r, dx0, dy0, dx1, dy1, 2.2, SEPIA, 1.6, over=5, dbl=0.5)
    box(s, r, gx0 - 7, gy0 - 7, gx1 + 7, gy1 + 7, 1.2, SEPIA, 1.2, over=2, dbl=0.2)
    kp = (dx0 + 22, gy1 + 30, dx1 - 22, dy1 - 24)
    s.wash(s.rect(*kp), SEPIA, 0.35, wob=1, soft=1.5, edge=0.5, ew=4)
    box(s, r, *kp, 1.5, SEPIA, 1.3, over=3, dbl=0.4)
    box(s, r, kp[0] + 9, kp[1] + 9, kp[2] - 9, kp[3] - 9, 1.0, SEPIA, 1.0, over=2, dbl=0.1, skip=0.15)
    hl(s, [(kp[0] + 3, kp[3] - 3), (kp[2] - 3, kp[3] - 3)], 1.6, 0.3)
    kick = s.rect(dx0 + 6, dy1 - 18, dx1 - 6, dy1 - 3)                      # brass kick plate, dull
    put(s, kick, OCHRE, 0.55, lift=0.7, wob=0.6, edge=0.4, ew=2)
    s.wash(kick, UMBER, 0.5, wob=1, soft=1, edge=0, flow=0.8, fs=30)
    box(s, r, dx0 + 6, dy1 - 18, dx1 - 6, dy1 - 3, 1.1, SEPIA, 1.1, over=1)
    hd = s.rect(dx0 + 9, 1030, dx0 + 17, 1112)                              # brass pull
    put(s, hd, OCHRE, 0.5, lift=0.9, wob=0.4, edge=0.5, ew=2)
    s.wash(s.rect(dx0 + 13, 1030, dx0 + 17, 1112), UMBER, 0.4, wob=0.3, soft=0.5)
    s.ink([(dx0 + 9, 1028), (dx0 + 9, 1114)], 1.2, SEPIA, 1.3)
    s.ink([(dx0 + 17, 1028), (dx0 + 18, 1114)], 1.4, SEPIA, 1.4)
    for px in (2098, 2126, 2318, 2338):
        line(s, r, (px, 800), (px + J(r, 1), PAVE - 2), 1.8, SEPIA, 1.4, dbl=0.4)
    hp = (2132, 806, 2312, 852)                                             # the panel over the door
    s.wash(s.rect(*hp), SEPIA, 0.35, wob=1, soft=1.5, edge=0.5, ew=4)
    box(s, r, *hp, 1.4, SEPIA, 1.3, over=3, dbl=0.4)
    st = s.rect(2112, PAVE - 7, 2332, PAVE + 8)
    put(s, st, MIST, 0.55, lift=0.8, wob=0.8, edge=0.4, ew=2)
    s.wash(st, OCHRE, 0.2, wob=1, soft=1)
    line(s, r, (2110, PAVE - 7), (2334, PAVE - 7), 1.8, SEPIA, 1.5, dbl=0.4)
    # the light from inside, caught on the edges that face it
    mull = [wx0 + pw, wx0 + pw + 12, wx0 + 2 * pw + 12, wx0 + 2 * pw + 24]
    for x in (wx0 - 2, mull[0] + 2, mull[1] - 2, mull[2] + 2, mull[3] - 2, wx1 + 2):
        hl(s, [(x, wy0 + 6), (x, wy1 - 2)], 2.6, 0.5)
        s.wash(s.ribbon([(x, wy0 + 6), (x, wy1 - 2)], 3, smooth=False), AMBER, 0.3, wob=0.4, soft=0.6, edge=0)
    for x in (gx0 - 2, gx1 + 2):
        hl(s, [(x, gy0), (x, gy1)], 2.6, 0.5)
        s.wash(s.ribbon([(x, gy0), (x, gy1)], 3, smooth=False), AMBER, 0.3, wob=0.4, soft=0.6, edge=0)
    hl(s, [(gx0, gy1 + 2), (gx1, gy1 + 2)], 2.6, 0.45)
    # shadow thrown down by the awning
    s.wash(s.rect(X0, 770, X1, 880), SEPIA, 0.5, wob=0, soft=0, edge=0, flow=0.5, fs=80, grad=s.vgrad(800, 880, 1, 0))
    # ---- the glass: holes in the sheet
    hole = s.zeros()
    panes = []
    for i in range(3):
        ax = wx0 + i * (pw + 12)
        panes.append((ax, wy0, ax + pw, 884))
        panes.append((ax, 896, ax + pw, wy1))
    panes.append((gx0, gy0, gx1, gy1))
    for p in panes:
        hole = np.maximum(hole, s.rect(*p))
    s.A *= (1 - hole)[..., None]
    s.body *= (1 - hole)
    for p in panes:
        box(s, r, p[0] - 1, p[1] - 1, p[2] + 1, p[3] + 1, 1.6, SEPIA, 1.5, over=3, dbl=0.35, j=0.8)
    box(s, r, wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 1, 2.0, SEPIA, 1.5, over=6, dbl=0.5)
    # ---- awning
    N = 20
    xt = lambda i: 1440 + 910 * i / N
    xb = lambda i: 1420 + 980 * i / N
    YT, YF, YV = 700, 768, 788
    slope = Q(s, [(xt(0), YT), (xt(N), YT), (xb(N), YF), (xb(0), YF)])
    val = s.rect(xb(0), YF, xb(N), YV)
    for i in range(N):
        val = np.maximum(val, s.ellipse((xb(i) + xb(i + 1)) / 2, YV, 980 / N / 2, 18))
    aw = np.maximum(slope, val)
    put(s, aw, CREAM, 0.62, lift=1.0, wob=0.8, edge=0.3, ew=4, flow=0.4, fs=90)
    s.wash(aw, RAIN, 0.20, wob=1, soft=1, edge=0, flow=0.7, fs=120, gran=0.45)
    s.wash(aw, UMBER, 0.10, wob=1, soft=1, edge=0, flow=0.9, fs=70, gran=0.45)
    for i in range(0, N, 2):
        q = [(xt(i) + J(r, 1.5), YT), (xt(i + 1) + J(r, 1.5), YT), (xb(i + 1) + J(r, 1.5), YF), (xb(i) + J(r, 1.5), YF)]
        s.wash(Q(s, q), BURNT, U(r, 0.75, 0.95), wob=1.2, soft=0.8, edge=0.5, ew=4, flow=0.6, fs=40, gran=0.45, clip=aw)
        vm = np.maximum(s.rect(xb(i) + 1, YF, xb(i + 1) - 1, YV), s.ellipse((xb(i) + xb(i + 1)) / 2, YV, 980 / N / 2 - 1, 18))
        s.wash(vm, BURNT, U(r, 0.85, 1.05), wob=1.0, soft=0.8, edge=0.5, ew=4, flow=0.6, fs=40, gran=0.45, clip=aw)
    s.wash(slope, PAYNE, 0.5, wob=0, soft=0, edge=0, grad=s.vgrad(YT - 6, YT + 46, 1, 0.12), flow=0.5, fs=100)      # under the cornice it is darker
    s.wash(val, UMBER, 0.34, wob=0, soft=0, edge=0, flow=0.5, fs=60)                                          # the hanging edge is soaked
    s.wash(val, AMBER, 0.14, wob=0, soft=0, edge=0, grad=s.vgrad(YF, YV + 18, 0, 1))                          # and lit a little from below
    for i in range(26):                                                                                      # runs of water down the canvas
        q = U(r, 0.02, 0.98)
        a, b = (1440 + 910 * q, YT + U(r, 2, 30)), (1420 + 980 * q, YF - U(r, 0, 16))
        if r.random() < 0.5:
            hl(s, [a, b], U(r, 2, 4), U(r, 0.18, 0.34), clip=aw)
        else:
            s.stroke([a, b], U(r, 3, 7), PAYNE, U(r, 0.15, 0.3), dry=0.3, edge=0.3, wob=1, taper=(0.1, 0.5), clip=aw)
    hl(s, [(xb(0) + 4, YF + 1), (xb(N) - 4, YF + 1)], 2.2, 0.4)
    line(s, r, (xt(0) - 3, YT), (xt(N) + 3, YT), 2.0, SEPIA, 1.5, dbl=0.5)
    line(s, r, (xb(0), YF - 2), (xb(N), YF - 2), 1.8, SEPIA, 1.4, dbl=0.6)
    line(s, r, (xb(0), YF + 5), (xb(N), YF + 5), 1.0, SEPIA, 1.0, skip=0.2)
    line(s, r, (xt(0), YT), (xb(0), YF), 2.0, SEPIA, 1.5, dbl=0.4)
    line(s, r, (xt(N), YT), (xb(N), YF), 2.0, SEPIA, 1.5, dbl=0.4)
    for i in range(1, N):
        if r.random() < 0.8:
            seg(s, (xt(i) + J(r, 1), YT + U(r, 0, 12)), (xb(i) + J(r, 1), YF - U(r, 0, 8)), 1.0, SEPIA, U(r, 0.6, 1.0), r=r, skip=0.2)
    for i in range(N):
        cx = (xb(i) + xb(i + 1)) / 2
        s.ink(ell(cx + J(r, 0.8), YV, 980 / N / 2, 18 + J(r, 1), -0.1, math.pi + 0.1, 18), 1.7, SEPIA, 1.5, tremor=0.5)
        s.wash(s.ellipse(cx, YV + 12, 14, 5), SEPIA, 0.3, wob=0.8, soft=1.5, clip=aw)                         # water gathering at the tip
    line(s, r, (xb(0), YF), (xb(0), YV + 2), 1.6, SEPIA, 1.4)
    line(s, r, (xb(N), YF), (xb(N), YV + 2), 1.6, SEPIA, 1.4)
    # ---- bracket lamps on the pilasters
    for (lx, ly), sd in zip(BRACKETS, (1, -1)):
        wxp = lx - sd * 24
        halo = s.rgrad(lx, ly, 14, 120, 1, 0) * (1 - hole)
        s.wash(halo, None, 0.34, wob=0, soft=0, edge=0, gran=0.2, flow=0, lift=True)
        s.wash(halo, AMBER, 0.2, wob=0, soft=0, edge=0)
        s.ink([(wxp, ly - 6), (wxp + sd * 6, ly - 34), (lx - sd * 4, ly - 44), (lx, ly - 30)], 2.4, SEPIA, 1.6, tremor=0.5)
        s.ink(ell(wxp + sd * 10, ly - 18, 8, 9, 0.4, 5.4, 20), 1.3, SEPIA, 1.3)
        lan = [(lx - 9, ly - 16), (lx + 9, ly - 16), (lx + 13, ly + 14), (lx - 13, ly + 14)]
        lm = Q(s, lan)
        s.lift(lm, 1.0, soft=0.7, wob=0.4)
        s.wash(lm, OCHRE, 0.32, wob=0.6, soft=0.8, edge=0.5, ew=3, body=1)
        capm = Q(s, [(lx - 13, ly - 16), (lx, ly - 30), (lx + 13, ly - 16)])
        put(s, capm, SEPIA, 0.9, lift=0.5, wob=0.5)
        put(s, s.rect(lx - 11, ly + 14, lx + 11, ly + 20), SEPIA, 0.9, lift=0.5, wob=0.5)
        path(s, lan, 1.5, SEPIA, 1.5, closed=True, over=2, r=r)
        line(s, r, (lx, ly - 16), (lx, ly + 14), 1.0, SEPIA, 1.0, over=0)
        path(s, [(lx - 14, ly - 16), (lx, ly - 31), (lx + 14, ly - 16)], 1.5, SEPIA, 1.5, over=1, r=r)
    # ---- plants: a clipped bay by the door, something spiky in a trough at the other end
    pot = [(2350, 1226), (2398, 1226), (2392, PAVE + 6), (2356, PAVE + 6)]
    put(s, Q(s, pot), BURNT, 0.8, lift=0.85, wob=0.8, edge=0.5, ew=3, flow=0.5, fs=30)
    s.wash(Q(s, pot), PAYNE, 0.45, wob=1, soft=2, edge=0, grad=s.hgrad(2352, 2398, 0.15, 1))
    s.wash(s.rect(2347, 1220, 2401, 1232), BURNT, 0.5, wob=0.6, soft=0.6, body=1)
    path(s, pot, 1.7, SEPIA, 1.5, closed=True, over=2, r=r)
    box(s, r, 2347, 1220, 2401, 1232, 1.3, SEPIA, 1.3, over=2)
    s.ink([(2374, 1222), (2372, 1180), (2375, 1140)], 3.2, SEPIA, 1.5, tremor=0.8)
    ball = s.blob(2374, 1096, 50, 54, irr=0.16, n=14)
    ball = put(s, ball, MOSS, 1.0, lift=0.8, wob=0.7, edge=0.5, ew=5, flow=0.6, fs=40, gran=0.5)
    s.wash(ball, PRUSSIAN, 0.75, wob=2, bleed=6, edge=0.2, grad=s.hgrad(2330, 2410, 0.25, 1) * s.vgrad(1040, 1150, 0.5, 1), clip=ball)
    s.wash(ball, PAYNE, 0.3, wob=2, bleed=6, edge=0.2, flow=0.9, fs=24, clip=ball)
    s.wash(ball, AMBER, 0.22, wob=2, bleed=8, edge=0, grad=s.hgrad(2326, 2372, 1, 0), clip=ball)
    for _ in range(46):
        a, d = U(r, 0, 6.28), U(r, 0.2, 1.0) ** 0.6
        x, y = 2374 + math.cos(a) * 48 * d, 1096 + math.sin(a) * 52 * d
        an = a + J(r, 0.8)
        s.ink([(x, y), (x + math.cos(an) * 5, y + math.sin(an) * 5 - 2), (x + math.cos(an) * 10, y + math.sin(an) * 10)], U(r, 1.2, 2.6), SEPIA if r.random() < 0.6 else INKBLUE, U(r, 0.6, 1.1), tremor=0.4)
    s.ink(spline(ell(2374, 1096, 50, 54, 0.4, 5.6, 16) + np.array([[J(r, 3), J(r, 3)] for _ in range(16)])), 1.4, SEPIA, 1.2, skip=0.25, smooth=False)
    tr = [(1396, 1250), (1460, 1250), (1456, PAVE + 6), (1400, PAVE + 6)]
    put(s, Q(s, tr), SLATE, 0.75, lift=0.85, wob=0.8, edge=0.5, ew=3)
    s.wash(Q(s, tr), PAYNE, 0.5, wob=1, soft=2, edge=0, grad=s.vgrad(1250, PAVE, 0.2, 1))
    for i in range(15):
        bx = U(r, 1404, 1452)
        tip = (bx + J(r, 30), U(r, 1150, 1215))
        midp = ((bx + tip[0]) / 2 + J(r, 6), (1250 + tip[1]) / 2)
        s.stroke([(bx, 1252), midp, tip], U(r, 5, 9), MOSS if r.random() < 0.6 else TEAL, U(r, 0.6, 0.95), taper=(0, 0.8), wob=0.8, edge=0.5, body=0.9)
        s.ink([(bx, 1252), midp, tip], 1.1, SEPIA, 1.0, skip=0.15)
    path(s, tr, 1.7, SEPIA, 1.5, closed=True, over=3, r=r)
    return hole


def bld_d(S, r):
    """The café's house: one storey of dusty mauve plaster over the shop, a slate mansard with two dormers."""
    x0, x1 = 1385, 2415
    EAVE, CORN = 428, 596
    s = Sub(S, x0 - 80, 230, x1 + 80, 700)
    # mansard
    mp = [(x0 + 14, EAVE), (x0 + 30, 362), (x1 - 74, 358), (x1 - 60, EAVE)]
    mm = Q(s, mp)
    mm = s.wash(mm, PAYNE, 0.9, wob=1.6, soft=0.9, edge=0.4, ew=6, flow=0.6, fs=120, gran=0.5, body=1)
    s.wash(mm, INDIGO, 0.3, wob=3, bleed=10, edge=0.2, flow=0.8, fs=90, clip=mm)
    s.wash(mm, VIOLET, 0.18, wob=3, bleed=14, edge=0.1, flow=0.9, fs=140, clip=mm)
    s.lift(s.blob(1900, 388, 260, 20, irr=0.3), 0.2, bleed=10, wob=3)                 # wet slates catching the sky
    s.lift(s.blob(1500, 380, 60, 14, irr=0.3), 0.16, bleed=8, wob=3)
    yy = 372
    while yy < EAVE - 4:
        xa = x0 + 30
        while xa < x1 - 80:
            ln = U(r, 60, 260)
            if r.random() < 0.6:
                seg(s, (xa, yy + J(r, 1)), (min(x1 - 66, xa + ln), yy + J(r, 1)), 1.0, SEPIA, U(r, 0.6, 1.0), r=r, skip=0.2, clip=mm)
                for xx in np.arange(xa + 6, min(x1 - 66, xa + ln), 15):
                    if r.random() < 0.45:
                        seg(s, (xx + J(r, 2), yy + 1), (xx + J(r, 2), yy + 11), 0.9, SEPIA, 0.7, r=r, clip=mm)
            xa += ln + U(r, 10, 80)
        yy += 13
    hl(s, [(x0 + 30, 364), (x1 - 74, 360)], 4, 0.4)
    line(s, r, (x0 + 26, 361), (x1 - 70, 357), 2.2, SEPIA, 1.5, dbl=0.6)
    line(s, r, (x0 + 30, 369), (x1 - 74, 365), 1.0, SEPIA, 0.9, skip=0.2)
    # party-wall upstand at the left, chimney stack at the right
    up = s.rect(x0, 350, x0 + 22, EAVE + 4)
    s.wash(up, SLATE, 0.8, wob=1, soft=0.8, edge=0.5, ew=3, body=1)
    s.wash(up, PAYNE, 0.4, wob=1, soft=1)
    box(s, r, x0, 350, x0 + 22, EAVE + 4, 1.8, SEPIA, 1.4, over=3)
    hl(s, [(x0 + 1, 353), (x0 + 21, 353)], 3, 0.4)
    ch = s.rect(x1 - 62, 296, x1 - 4, EAVE + 4)
    s.wash(ch, BURNT, 0.55, wob=1.2, soft=0.8, edge=0.5, ew=4, flow=0.5, fs=40, gran=0.5, body=1)
    s.wash(ch, PAYNE, 0.6, wob=2, bleed=5, edge=0.2, flow=0.6, fs=40)
    s.wash(s.rect(x1 - 30, 296, x1 - 4, EAVE), PAYNE, 0.3, wob=1, soft=2)
    bricks(s, r, x1 - 60, 304, x1 - 6, EAVE, 4, 9, 20, clip=ch)
    capm = s.rect(x1 - 68, 288, x1 + 2, 302)
    put(s, capm, SLATE, 0.7, lift=0, wob=0.8, edge=0.5, ew=3)
    hl(s, [(x1 - 66, 290), (x1, 290)], 2.4, 0.4)
    for i, px in enumerate((x1 - 52, x1 - 33, x1 - 14)):
        ph = 24 + J(r, 5)
        pot = Q(s, [(px - 6, 288), (px - 5, 288 - ph), (px + 5, 288 - ph), (px + 6, 288)])
        put(s, pot, BURNT, 0.75, lift=0, wob=0.5, edge=0.5, ew=2)
        s.wash(pot, PAYNE, 0.4, wob=0.5, soft=1, grad=s.hgrad(px - 6, px + 6, 0.2, 1))
        path(s, [(px - 6, 288), (px - 5, 288 - ph), (px + 5, 288 - ph), (px + 6, 288)], 1.3, SEPIA, 1.4, over=1, r=r)
    box(s, r, x1 - 68, 288, x1 + 2, 302, 1.6, SEPIA, 1.4, over=3)
    line(s, r, (x1 - 62, 302), (x1 - 62, EAVE), 2.0, SEPIA, 1.5)
    line(s, r, (x1 - 4, 302), (x1 - 3, EAVE), 2.0, SEPIA, 1.5)
    # wall
    m = s.rect(x0 - 5, EAVE - 2, x1 + 5, CORN + 8)
    m = wallwash(s, r, m, [(SLATE, 0.74), (VIOLET, 0.36), (PAYNE, 0.26)], EAVE, CORN, bx=(x0, x1), drags=6)
    mottle(s, r, x0 + 40, EAVE + 20, x1 - 40, CORN - 10, [VIOLET, ROSE, PRUSSIAN, SLATE], 7, 0.11, size=(60, 140), clip=m)
    s.lift(s.blob(1700, 520, 200, 50, irr=0.4), 0.14, bleed=24, wob=4)
    streaks(s, r, x0 + 10, x1 - 10, EAVE + 14, CORN, 14, PAYNE, 0.12, (5, 15), clip=m)
    # dormers
    for dx in (1574, 2148):
        dw = 92
        face = Q(s, [(dx, EAVE - 4), (dx, 372), (dx + dw / 2, 334), (dx + dw, 372), (dx + dw, EAVE - 4)])
        put(s, face, SLATE, 0.72, lift=0.9, wob=0.8, edge=0.4, ew=3)
        s.wash(face, VIOLET, 0.3, wob=1, soft=1, edge=0)
        s.wash(face, PAYNE, 0.3, wob=1, soft=2, edge=0, grad=s.vgrad(334, 380, 1, 0.2))
        window(s, r, dx + 20, 376, dx + dw - 20, EAVE - 10, "sash", 2, frame=MIST, sill=False, gk=0.9)
        rf = [(dx - 9, 376), (dx + dw / 2, 328), (dx + dw + 9, 376)]
        hl(s, [(rf[0][0] + 4, rf[0][1] - 3), (rf[1][0], rf[1][1] - 1)], 3, 0.35)
        path(s, rf, 2.2, SEPIA, 1.6, over=4, r=r)
        path(s, [(dx + 3, 378), (dx + dw / 2, 340), (dx + dw - 3, 378)], 1.1, SEPIA, 1.0, over=1, r=r, skip=0.15)
        line(s, r, (dx, 372), (dx, EAVE - 2), 1.8, SEPIA, 1.5)
        line(s, r, (dx + dw, 372), (dx + dw, EAVE - 2), 1.8, SEPIA, 1.5)
        s.wash(Q(s, [(dx + dw, 380), (dx + dw + 26, EAVE - 4), (dx + dw, EAVE - 4)]), INKBLUE, 0.4, wob=1, soft=1.5, clip=mm)
    # eaves cornice with little brackets
    em = s.rect(x0 - 8, EAVE - 6, x1 + 8, EAVE + 9)
    put(s, em, MIST, 0.55, lift=0.9, wob=0.8, edge=0.4, ew=3)
    s.wash(em, PAYNE, 0.35, wob=1, soft=1, edge=0, flow=0.6, fs=90)
    s.wash(s.rect(x0, EAVE + 9, x1, EAVE + 30), SEPIA, 0.42, wob=0, soft=0, edge=0, grad=s.vgrad(EAVE + 9, EAVE + 30, 1, 0), flow=0.5, fs=70)
    line(s, r, (x0 - 10, EAVE - 6), (x1 + 10, EAVE - 7), 2.0, SEPIA, 1.5, dbl=0.5)
    line(s, r, (x0 - 8, EAVE + 9), (x1 + 8, EAVE + 9), 2.2, SEPIA, 1.6, dbl=0.6)
    line(s, r, (x0 - 6, EAVE + 1), (x1 + 6, EAVE + 1), 1.0, SEPIA, 0.9, skip=0.25)
    for xx in np.arange(x0 + 14, x1 - 6, 43):
        bx = xx + J(r, 3)
        s.wash(s.rect(bx, EAVE + 9, bx + 10, EAVE + 20), SEPIA, 0.5, wob=0.5, soft=0.6)
        path(s, [(bx, EAVE + 9), (bx + 1, EAVE + 20), (bx + 10, EAVE + 17), (bx + 10, EAVE + 9)], 1.1, SEPIA, 1.1, over=1, r=r)
    # first-floor windows, each in a plain stone surround
    for i, cx in enumerate((1516, 1768, 2036, 2288)):
        w, h = 90 + J(r, 4), 122 + J(r, 4)
        wx, wy = cx - w / 2, 462 + J(r, 3)
        sur = s.rect(wx - 10, wy - 12, wx + w + 10, wy + h + 2)
        s.lift(sur, 0.32, soft=1, wob=1)
        box(s, r, wx - 10, wy - 12, wx + w + 10, wy + h + 2, 1.2, SEPIA, 1.0, over=3, dbl=0.2, skip=0.15)
        if i == 3:
            window(s, r, wx, wy, wx + w, wy + h, "sash", 2, lit=True, curtain="drapes")
        elif i == 0:
            window(s, r, wx, wy, wx + w, wy + h, "sash", 2, curtain="blind")
        else:
            window(s, r, wx, wy, wx + w, wy + h, "sash", 2)
        key = [(cx - 8, wy - 12), (cx - 11, wy - 30), (cx + 11, wy - 30), (cx + 8, wy - 12)]
        s.lift(Q(s, key), 0.35, soft=0.8, wob=0.6)
        path(s, key, 1.2, SEPIA, 1.1, closed=True, over=2, r=r)
        if i == 1:      # a window box
            wb = s.rect(wx - 6, wy + h - 12, wx + w + 6, wy + h + 6)
            put(s, wb, UMBER, 0.8, lift=0.8, wob=0.8, edge=0.5, ew=2)
            for _ in range(22):
                bx = U(r, wx - 2, wx + w + 2)
                s.stroke([(bx, wy + h - 10), (bx + J(r, 7), wy + h - U(r, 18, 36))], U(r, 4, 8), MOSS if r.random() < 0.7 else TEAL, U(r, 0.6, 0.9), taper=(0, 0.7), wob=0.8, edge=0.5, body=0.9)
            box(s, r, wx - 6, wy + h - 12, wx + w + 6, wy + h + 6, 1.4, SEPIA, 1.3, over=2)
    # a patch of mended plaster
    s.wash(s.blob(1650, 548, 46, 22, irr=0.3), SLATE, 0.2, wob=2, soft=1, edge=0.8, ew=3)
    line(s, r, (x0, EAVE), (x0 + J(r, 2), CORN), 2.2, SEPIA, 1.5, dbl=0.5)
    line(s, r, (x1, EAVE), (x1 + J(r, 2), CORN), 2.2, SEPIA, 1.5, dbl=0.5)


def stone_band(s, r, x0, x1, y, h=12, lift=0.34, shadow=16):
    """A string course or cornice: a paler strip with a line under it and the shadow it throws."""
    s.lift(s.rect(x0, y, x1, y + h), lift, soft=0.8, wob=0.8)
    line(s, r, (x0 - 3, y), (x1 + 3, y + J(r, 1)), 1.2, SEPIA, 1.1, skip=0.1)
    line(s, r, (x0 - 4, y + h), (x1 + 4, y + h + J(r, 1)), 2.1, SEPIA, 1.5, dbl=0.5)
    if shadow:
        s.wash(s.rect(x0, y + h, x1, y + h + shadow), SEPIA, 0.36, wob=0, soft=0, edge=0, grad=s.vgrad(y + h, y + h + shadow, 1, 0), flow=0.5, fs=70)


def door(s, r, x0, y0, x1, y1, c=PRUSSIAN, k=0.9, panels=2, glass=False, knob=1):
    m = s.rect(x0, y0, x1, y1)
    put(s, m, c, k, lift=0.8, wob=1, edge=0.5, ew=4, flow=0.5, fs=50)
    s.wash(m, PAYNE, 0.4, wob=1, soft=2, edge=0, grad=s.vgrad(y0, y1, 0.3, 1))
    box(s, r, x0, y0, x1, y1, 2.0, SEPIA, 1.5, over=4, dbl=0.4)
    h = (y1 - y0 - 12) / panels
    for j in range(panels):
        a, b = y0 + 10 + j * h, y0 + 4 + (j + 1) * h
        if j == 0 and glass:
            s.wash(s.rect(x0 + 10, a, x1 - 10, b), INKBLUE, 0.6, wob=0.8, soft=1, edge=0.4, ew=2)
            s.lift(Q(s, [(x0 + 10, a), (x0 + 10 + (x1 - x0) * 0.4, a), (x0 + 10, a + h * 0.5)]), 0.25, soft=2)
        else:
            s.wash(s.rect(x0 + 10, a, x1 - 10, b), PAYNE, 0.22, wob=0.8, soft=1, edge=0.5, ew=3)
        box(s, r, x0 + 9, a, x1 - 9, b, 1.2, SEPIA, 1.1, over=2, dbl=0.2)
    kx = x0 + 8 if knob < 0 else x1 - 8
    ky = y0 + (y1 - y0) * 0.56
    s.wash(s.ellipse(kx, ky, 3.5, 3.5), OCHRE, 0.25, wob=0.3, soft=0.5)
    oval(s, kx, ky, 3.6, 3.6, 1.0, SEPIA, 1.3)


def bld_a(S, r):
    """Far left: a tiled block from the seventies, two bays of strip windows, a shutter and a grille at street level."""
    x0, x1, PAR, G = -40, 505, 346, 760
    s = Sub(S, 0, 230, x1 + 70, PAVE + 40)
    m = s.rect(x0, PAR, x1 + 8, PAVE + 14)
    m = wallwash(s, r, m, [(TEAL, 0.72), (PAYNE, 0.55), (PRUSSIAN, 0.2)], PAR, PAVE, bx=(0, x1), drags=7)
    mottle(s, r, 20, PAR + 20, x1 - 20, G, [VIOLET, PRUSSIAN, MOSS, SLATE], 6, 0.11, size=(60, 150), clip=m)
    # roof: coping, a hut, a rail, a dish
    hut = s.rect(296, 300, 400, PAR + 4)
    s.wash(hut, SLATE, 0.8, wob=1, soft=0.8, edge=0.5, ew=4, body=1, flow=0.5, fs=40)
    s.wash(hut, PAYNE, 0.5, wob=1, soft=2, edge=0, grad=s.hgrad(300, 400, 0.3, 1))
    box(s, r, 296, 300, 400, PAR, 1.8, SEPIA, 1.4, over=4)
    line(s, r, (290, 300), (406, 299), 2.2, SEPIA, 1.5)
    door(s, r, 318, 312, 350, PAR - 2, PAYNE, 0.6, 1)
    stone_band(s, r, x0, x1 + 4, PAR, 12, 0.36, 14)
    x = 20
    while x < 280:
        seg(s, (x, PAR - 26), (x + J(r, 1), PAR), 1.2, INKBLUE, 1.2, r=r)
        x += U(r, 16, 22)
    line(s, r, (10, PAR - 26), (284, PAR - 25), 2.0, INKBLUE, 1.4, dbl=0.5)
    line(s, r, (10, PAR - 14), (284, PAR - 14), 1.1, INKBLUE, 1.1, skip=0.1)
    s.ink(ell(452, 318, 20, 22, 0.9, 3.9, 20), 1.8, SEPIA, 1.4)
    s.ink([(438, 302), (466, 334)], 1.3, SEPIA, 1.3)
    s.ink([(452, 318), (470, 306)], 1.2, SEPIA, 1.2)
    s.ink([(456, 326), (458, PAR)], 2.0, SEPIA, 1.4)
    # three storeys of strip windows in two shallow bays, the recess between them holding the stair lights
    bays = ((14, 236), (282, 498))
    for fl in range(3):
        fy = G - fl * 138                      # this storey's floor line
        for bi, (ba, bb) in enumerate(bays):
            sp = s.rect(ba, fy - 46, bb, fy - 2)                 # tiled spandrel, paler
            s.lift(sp, 0.26, soft=1, wob=1)
            s.wash(sp, MIST, 0.12, wob=1, soft=1, edge=0.4, ew=3)
            box(s, r, ba, fy - 46, bb, fy - 2, 1.3, SEPIA, 1.1, over=3, dbl=0.3, skip=0.1)
            for _ in range(3):                                   # the tile grid, where the eye bothers
                tx, ty = U(r, ba + 10, bb - 70), fy - 44
                nn = int(r.integers(3, 6))
                for i in range(nn):
                    seg(s, (tx + i * 13, ty + 2), (tx + i * 13 + J(r, 1), ty + 40), 0.8, SEPIA, 0.6, r=r, skip=0.25)
                for j in (13, 26):
                    seg(s, (tx - 6, ty + j), (tx + nn * 13, ty + j + J(r, 1)), 0.8, SEPIA, 0.6, r=r, skip=0.25)
            lit = (fl == 0 and bi == 0)
            wy0, wy1 = fy - 46 - 84, fy - 48
            nl = 3
            lw = (bb - ba - 28) / nl
            for i in range(nl):
                wx = ba + 14 + i * lw
                if lit and i == 1:
                    window(s, r, wx + 2, wy0, wx + lw - 2, wy1, "sash", 1, lit=True, curtain="drawn", frame=SLATE, fk=0.6, sill=False)
                else:
                    window(s, r, wx + 2, wy0, wx + lw - 2, wy1, "sash", 1 if r.random() < 0.6 else 2, frame=SLATE, fk=0.6, sill=False)
            line(s, r, (ba - 2, wy1 + 2), (bb + 2, wy1 + 2), 1.8, SEPIA, 1.4, dbl=0.4)
            s.wash(s.rect(bb - 2, fy - 136, bb + 12, fy), PAYNE, 0.4, wob=1.2, soft=2, edge=0.2)        # the bay's own shadow
        # glass blocks in the recess
        gy = fy - 122
        gm = s.rect(244, gy, 274, gy + 92)
        put(s, gm, SLATE, 0.5, lift=0.7, wob=0.8, edge=0.4, ew=3)
        s.wash(gm, TEAL, 0.3, wob=1, soft=1, edge=0, flow=0.8, fs=20)
        if fl == 1:
            s.wash(gm, OCHRE, 0.16, wob=1, soft=1)
        for i in range(1, 3):
            seg(s, (244 + i * 10, gy), (244 + i * 10, gy + 92), 0.9, SEPIA, 0.9, r=r, skip=0.1)
        for j in range(1, 9):
            seg(s, (244, gy + j * 10.2), (274, gy + j * 10.2), 0.9, SEPIA, 0.9, r=r, skip=0.1)
        box(s, r, 244, gy, 274, gy + 92, 1.4, SEPIA, 1.3, over=2)
    for ba, bb in bays:
        line(s, r, (ba, PAR + 12), (ba + J(r, 2), G - 4), 1.8, SEPIA, 1.4, dbl=0.4)
        line(s, r, (bb, PAR + 12), (bb + J(r, 2), G - 4), 2.2, SEPIA, 1.5, dbl=0.4)
    acbox(s, r, 318, G - 138 - 40, 60, 36)
    acbox(s, r, 150, G - 276 - 40, 56, 36)
    # washing left out under a window
    ly = G - 276 - 44
    s.ink([(300, ly - 2), (400, ly + 3), (492, ly - 1)], 1.2, INKBLUE, 1.2)
    for lx, lw2, lh, c in ((330, 30, 34, MIST), (368, 22, 26, ROSE), (398, 34, 38, MIST), (440, 26, 30, OCHRE)):
        cm = Q(s, [(lx, ly + 2), (lx + lw2, ly + 3), (lx + lw2 - 3 + J(r, 3), ly + lh), (lx + 2 + J(r, 3), ly + lh + J(r, 3))])
        put(s, cm, c, 0.35, lift=0.85, wob=1, edge=0.4, ew=2)
        s.wash(cm, SLATE, 0.5, wob=1, soft=1.5, edge=0, grad=s.hgrad(lx, lx + lw2, 0.3, 1))
        s.ink(spline([(lx, ly + 2), (lx + 2, ly + lh), (lx + lw2 - 3, ly + lh), (lx + lw2, ly + 3)]), 1.1, SEPIA, 1.1, smooth=False, skip=0.1)
    # street level: a canopy slab, a dead light-box, shutter, grille door
    cs = s.rect(x0, G - 8, x1 + 6, G + 10)
    put(s, cs, SLATE, 0.7, lift=0.8, wob=0.8, edge=0.4, ew=3)
    hl(s, [(0, G - 6), (x1 + 4, G - 6)], 3, 0.4)
    s.wash(s.rect(x0, G + 10, x1, G + 60), SEPIA, 0.5, wob=0, soft=0, edge=0, grad=s.vgrad(G + 10, G + 60, 1, 0), flow=0.5, fs=80)
    line(s, r, (0, G - 8), (x1 + 8, G - 9), 1.8, SEPIA, 1.4, dbl=0.4)
    line(s, r, (0, G + 10), (x1 + 8, G + 10), 2.4, SEPIA, 1.6, dbl=0.6)
    gz = s.rect(x0, G + 10, x1, PAVE + 14)
    s.wash(gz, PAYNE, 0.3, wob=2, bleed=8, edge=0.1, flow=0.6, fs=120, clip=m)
    lb = s.rect(44, 782, 322, 822)
    put(s, lb, MIST, 0.55, lift=0.85, wob=0.8, edge=0.4, ew=4, flow=0.5, fs=60)
    s.wash(lb, SLATE, 0.4, wob=2, bleed=6, edge=0.1, flow=0.8, fs=50)
    box(s, r, 44, 782, 322, 822, 1.9, SEPIA, 1.5, over=4, dbl=0.4)
    box(s, r, 50, 788, 316, 816, 1.0, SEPIA, 0.9, over=1, dbl=0, skip=0.2)
    roller(s, r, 34, 852, 336, PAVE, SLATE, 0.8, gap=11, housing=22)
    s.wash(s.blob(200, 1100, 110, 130, irr=0.3), PRUSSIAN, 0.2, wob=4, bleed=16, edge=0.2)
    gm = s.rect(376, 884, 470, PAVE - 4)
    put(s, gm, INKBLUE, 0.85, lift=0.6, wob=1, edge=0.5, ew=5, flow=0.5, fs=50)
    s.lift(s.blob(423, 1000, 30, 80, irr=0.3), 0.15, bleed=10)
    xx = 384
    while xx < 468:
        seg(s, (xx, 888), (xx + J(r, 1), PAVE - 8), 1.4, SEPIA, 1.3, r=r, skip=0.04)
        hl(s, [(xx + 2.5, 900), (xx + 2.5, PAVE - 20)], 1.3, 0.25)
        xx += U(r, 9.5, 12)
    for yy in (930, 1090, 1240):
        line(s, r, (376, yy), (470, yy + J(r, 1)), 1.9, SEPIA, 1.4)
    box(s, r, 376, 884, 470, PAVE - 4, 2.1, SEPIA, 1.5, over=4, dbl=0.4)
    put(s, s.rect(402, 846, 444, 866), SLATE, 0.6, lift=0.5, wob=0.5, edge=0.4, ew=2)        # a number plate, blank
    box(s, r, 402, 846, 444, 866, 1.3, SEPIA, 1.3, over=2)
    for yy in (1150, 1200, 1250):                                                              # tiled dado
        line(s, r, (336, yy), (376, yy), 0.9, SEPIA, 0.7, skip=0.2)
        line(s, r, (470, yy), (x1 - 4, yy), 0.9, SEPIA, 0.7, skip=0.2)
    s.wash(s.rect(x0, PAVE - 50, x1, PAVE + 14), SEPIA, 0.3, wob=3, bleed=10, edge=0.1, clip=m)
    line(s, r, (x1, PAR), (x1 + J(r, 2), PAVE), 2.3, SEPIA, 1.5, dbl=0.5)


def bld_b(S, r):
    """A brick shop-house: curved gable, arched sashes, a long balcony with shuttered french windows, a shut shop."""
    x0, x1, PAR, G = 500, 1012, 405, 716
    s = Sub(S, x0 - 70, 260, x1 + 70, PAVE + 40)
    ped = [(642, PAR), (668, 392), (700, 372), (756, 357), (812, 372), (844, 392), (870, PAR)]
    pts = [(x0 - 6, PAR)] + ped + [(x1 + 6, PAR), (x1 + 6, PAVE + 14), (x0 - 6, PAVE + 14)]
    m = Q(s, pts)
    m = wallwash(s, r, m, [(BURNT, 0.56), (PAYNE, 0.52), (VIOLET, 0.2)], PAR, PAVE, bx=(x0, x1), drags=8)
    mottle(s, r, x0 + 30, PAR + 20, x1 - 30, G, [BURNT, VIOLET, UMBER, PRUSSIAN], 8, 0.14, size=(50, 130), clip=m)
    bricks(s, r, x0 + 12, PAR + 22, x1 - 12, G - 16, 26, 10.5, 26, clip=m)
    streaks(s, r, x0 + 10, x1 - 10, PAR + 10, G, 12, PAYNE, 0.13, (5, 14), clip=m)
    # coping round the gable; a blank roundel in it
    cop = [(x0 - 4, PAR)] + ped + [(x1 + 4, PAR)]
    for a, b in zip(cop, cop[1:]):
        hl(s, [(a[0], a[1] + 4), (b[0], b[1] + 4)], 6, 0.38)
        line(s, r, a, b, 2.2, SEPIA, 1.5, dbl=0.5)
        line(s, r, (a[0], a[1] + 10), (b[0], b[1] + 10), 1.1, SEPIA, 1.0, skip=0.15)
    s.lift(s.ellipse(756, 386, 17, 15), 0.35, soft=1)
    oval(s, 756, 386, 17, 15, 1.4, SEPIA, 1.3, twice=True)
    for bx in (x0 + 2, x1 - 18):                                   # little urn-blocks at the corners
        put(s, s.rect(bx, PAR - 20, bx + 16, PAR + 2), SLATE, 0.7, lift=0, wob=0.6, edge=0.5, ew=2)
        box(s, r, bx, PAR - 20, bx + 16, PAR + 2, 1.4, SEPIA, 1.4, over=2)
    stone_band(s, r, x0, x1, 552, 10, 0.3, 12)
    # second floor: three arched sashes
    for i, cx in enumerate((590, 756, 922)):
        w, h = 80 + J(r, 4), 104 + J(r, 5)
        window(s, r, cx - w / 2, 436 + J(r, 3), cx + w / 2, 436 + h, "sash", 2, head="arch", curtain=("net", None, "blind")[i])
    acbox(s, r, 566, 566, 56, 34)
    # first floor: french windows with louvred shutters, the middle one lit
    for i, cx in enumerate((606, 756, 906)):
        w = 82 + J(r, 3)
        ya, yb = 574 + J(r, 2), 696
        louvres(s, r, cx - w / 2 - 30, ya + 2, cx - w / 2 - 2, yb - 4, MOSS, 0.8)
        if i != 2:
            louvres(s, r, cx + w / 2 + 2, ya + 2, cx + w / 2 + 30, yb - 4, MOSS, 0.8)
        else:               # one leaf swung half shut
            louvres(s, r, cx + w / 2 - 14, ya + 2, cx + w / 2 + 8, yb - 4, MOSS, 0.95)
        window(s, r, cx - w / 2, ya, cx + w / 2, yb, "case", 2, lit=(i == 1), curtain="drawn" if i == 1 else None, sill=False, head="lintel")
    # the ground-storey cornice, then the balcony in front
    cb = s.rect(x0 - 6, G - 14, x1 + 6, G + 4)
    put(s, cb, MIST, 0.5, lift=0.8, wob=0.8, edge=0.4, ew=3)
    s.wash(cb, PAYNE, 0.4, wob=1, soft=1, edge=0, flow=0.6, fs=80)
    s.wash(s.rect(x0, G + 4, x1, G + 30), SEPIA, 0.45, wob=0, soft=0, edge=0, grad=s.vgrad(G + 4, G + 30, 1, 0), flow=0.5, fs=70)
    line(s, r, (x0 - 8, G - 14), (x1 + 8, G - 15), 1.8, SEPIA, 1.4, dbl=0.4)
    line(s, r, (x0 - 8, G + 4), (x1 + 8, G + 4), 2.4, SEPIA, 1.6, dbl=0.6)
    for px, pw_, ph, c in ((640, 22, 30, MOSS), (838, 18, 22, TEAL), (958, 24, 36, MOSS)):        # pots on the balcony
        put(s, s.blob(px, 690 - ph, pw_, ph * 0.7, irr=0.3), c, 0.8, lift=0.6, wob=2, edge=0.5, ew=3)
        s.wash(s.blob(px + 6, 690 - ph * 0.8, pw_ * 0.7, ph * 0.5, irr=0.3), PRUSSIAN, 0.4, wob=2, bleed=4)
        put(s, Q(s, [(px - 9, 676), (px + 9, 676), (px + 7, 696), (px - 7, 696)]), BURNT, 0.7, lift=0.6, wob=0.5, edge=0.4, ew=2)
    railing(s, r, 556, 990, 696, 56, gap=11, knots=0.12)
    for bx in (570, 700, 830, 960):                                                                # brackets under the slab
        path(s, [(bx - 6, 703), (bx - 5, 722), (bx + 7, 703)], 1.3, SEPIA, 1.3, over=1, r=r)
    # an iron bracket with a blank hanging board
    s.ink([(504, 588), (540, 586), (566, 590)], 2.4, SEPIA, 1.6, tremor=0.5)
    s.ink([(506, 628), (528, 612), (552, 592)], 1.6, SEPIA, 1.4)
    s.ink(ell(524, 602, 8, 8, 0.6, 5.6, 20), 1.1, SEPIA, 1.2)
    bd = [(538, 600), (566, 598), (568, 664), (540, 668)]
    put(s, Q(s, bd), MIST, 0.6, lift=0.9, wob=0.8, edge=0.5, ew=3, flow=0.6, fs=20)
    s.wash(Q(s, bd), PAYNE, 0.4, wob=1, soft=1.5, edge=0, grad=s.vgrad(600, 668, 0.3, 1))
    path(s, bd, 1.7, SEPIA, 1.5, closed=True, over=2, r=r)
    for hx in (544, 562):
        line(s, r, (hx, 589), (hx, 600), 1.2, SEPIA, 1.3, over=0)
    # street level: stone piers, a faded fascia, a green shutter, the house door with its fanlight
    for pa, pb in ((x0, 542), (970, x1)):
        s.lift(s.rect(pa + 3, G + 6, pb - 3, PAVE), 0.24, soft=2, wob=1.5)
        for yy in np.arange(G + 60, PAVE - 20, 58):
            line(s, r, (pa + 2, yy + J(r, 2)), (pb - 2, yy + J(r, 2)), 1.1, SEPIA, 0.9, skip=0.2)
        line(s, r, (pb if pa == x0 else pa, G + 4), (pb if pa == x0 else pa, PAVE), 1.9, SEPIA, 1.4, dbl=0.4)
    gz = s.rect(542, G + 4, 970, PAVE + 14)
    s.wash(gz, PAYNE, 0.34, wob=2, bleed=6, edge=0.2, flow=0.6, fs=100, clip=m)
    fa = s.rect(556, 738, 956, 794)
    put(s, fa, MIST, 0.6, lift=0.85, wob=1, edge=0.45, ew=5, flow=0.6, fs=90)
    s.wash(fa, SLATE, 0.45, wob=2, bleed=8, edge=0.1, flow=0.9, fs=60)
    s.wash(fa, BURNT, 0.12, wob=3, bleed=12, edge=0.2, flow=0.9, fs=40)
    streaks(s, r, 566, 946, 740, 794, 7, PAYNE, 0.16, (5, 12), clip=fa)
    box(s, r, 556, 738, 956, 794, 2.0, SEPIA, 1.5, over=5, dbl=0.5)
    box(s, r, 564, 745, 948, 787, 1.0, SEPIA, 0.9, over=2, dbl=0, skip=0.2)
    roller(s, r, 560, 836, 838, PAVE, TEAL, 0.75, gap=10.5, housing=22)
    s.wash(s.rect(866, 822, 958, 872), INKBLUE, 0.8, wob=0.8, soft=0.8, edge=0.5, ew=3)          # fanlight
    s.lift(Q(s, [(866, 822), (910, 822), (880, 860), (866, 866)]), 0.22, soft=2)
    for a in np.linspace(0.5, 2.64, 5):
        line(s, r, (912, 872), (912 - math.cos(a) * 52, 872 - math.sin(a) * 48), 1.1, SEPIA, 1.1, over=0)
    box(s, r, 866, 822, 958, 872, 1.7, SEPIA, 1.4, over=3, dbl=0.3)
    door(s, r, 868, 880, 956, PAVE - 8, VIOLET, 0.8, 2, knob=-1)
    s.wash(s.rect(868, 880, 956, PAVE - 8), PAYNE, 0.3, wob=1, soft=1, edge=0)
    put(s, s.rect(856, PAVE - 8, 968, PAVE + 6), MIST, 0.5, lift=0.7, wob=0.8, edge=0.4, ew=2)
    line(s, r, (854, PAVE - 8), (970, PAVE - 8), 1.6, SEPIA, 1.4)
    s.ink([(912, 808), (912, 796), (900, 790)], 1.6, SEPIA, 1.4)                                 # a dead lamp over the door
    put(s, s.ellipse(912, 812, 9, 7), SLATE, 0.6, lift=0.6, wob=0.5, edge=0.4, ew=2)
    oval(s, 912, 812, 9, 7, 1.1, SEPIA, 1.3)
    pipe(s, r, 1001, PAR + 12, PAVE, 9)
    s.wash(s.rect(x0, PAVE - 50, x1, PAVE + 14), SEPIA, 0.3, wob=3, bleed=10, edge=0.1, clip=m)
    line(s, r, (x0, PAR), (x0 + J(r, 2), PAVE), 2.3, SEPIA, 1.5, dbl=0.5)


def bld_e(S, r):
    """The narrow blue-green house right of the café: a closed little shop under a juliet balcony."""
    x0, x1, PAR, G = 2410, 2792, 462, 746
    s = Sub(S, x0 - 70, 340, x1 + 70, PAVE + 40)
    m = s.rect(x0 - 6, PAR, x1 + 6, PAVE + 14)
    m = wallwash(s, r, m, [(PRUSSIAN, 0.6), (TEAL, 0.36), (PAYNE, 0.3)], PAR, PAVE, bx=(x0, x1), drags=7)
    mottle(s, r, x0 + 30, PAR + 20, x1 - 30, G, [VIOLET, TEAL, SLATE, PRUSSIAN], 6, 0.12, size=(50, 130), clip=m)
    s.lift(s.blob(2600, 640, 120, 60, irr=0.4), 0.14, bleed=20, wob=4)
    streaks(s, r, x0 + 10, x1 - 10, PAR + 20, G, 10, PAYNE, 0.13, (5, 14), clip=m)
    # a moulded cornice with dentils
    cm = s.rect(x0 - 8, PAR - 8, x1 + 8, PAR + 12)
    put(s, cm, MIST, 0.55, lift=0, wob=0.8, edge=0.4, ew=3)
    s.wash(cm, PAYNE, 0.4, wob=1, soft=1, edge=0, flow=0.6, fs=80)
    hl(s, [(x0 - 6, PAR - 6), (x1 + 6, PAR - 6)], 2.6, 0.4)
    s.wash(s.rect(x0, PAR + 12, x1, PAR + 34), SEPIA, 0.42, wob=0, soft=0, edge=0, grad=s.vgrad(PAR + 12, PAR + 34, 1, 0), flow=0.5, fs=70)
    line(s, r, (x0 - 10, PAR - 8), (x1 + 10, PAR - 9), 2.0, SEPIA, 1.5, dbl=0.5)
    line(s, r, (x0 - 8, PAR + 12), (x1 + 8, PAR + 12), 2.3, SEPIA, 1.6, dbl=0.6)
    line(s, r, (x0 - 6, PAR + 2), (x1 + 6, PAR + 2), 1.0, SEPIA, 0.9, skip=0.25)
    for xx in np.arange(x0 + 8, x1 - 8, 17):
        if r.random() < 0.85:
            box(s, r, xx, PAR + 12, xx + 8, PAR + 20, 0.9, SEPIA, 0.9, over=1, dbl=0, j=0.6)
    # second floor: two sashes, the left one lit behind a blind
    window(s, r, 2476, 492, 2558, 596, "sash", 2, lit=True, curtain="blind", head="hood")
    window(s, r, 2648, 494, 2730, 598, "sash", 2, head="hood", curtain="net")
    stone_band(s, r, x0, x1, 606, 8, 0.24, 10)
    acbox(s, r, 2712, 628, 56, 36)
    # first floor: a pair of french windows behind a juliet balcony
    louvres(s, r, 2504, 626, 2538, 738, MOSS, 0.85)
    louvres(s, r, 2664, 626, 2698, 738, MOSS, 0.85)
    window(s, r, 2540, 622, 2662, 740, "case", 2, sill=False, head="lintel", curtain="none")
    railing(s, r, 2524, 2680, 740, 52, gap=10, knots=0.2, slab=6)
    # an iron bracket with a blank oval board
    s.ink([(2414, 652), (2450, 648), (2472, 654)], 2.4, SEPIA, 1.6, tremor=0.5)
    s.ink([(2416, 690), (2436, 672), (2456, 654)], 1.5, SEPIA, 1.4)
    om = s.ellipse(2452, 692, 15, 26)
    put(s, om, MIST, 0.6, lift=0.9, wob=0.8, edge=0.5, ew=3, flow=0.6, fs=20)
    s.wash(om, PAYNE, 0.4, wob=1, soft=1.5, edge=0, grad=s.vgrad(660, 720, 0.3, 1))
    oval(s, 2452, 692, 15, 26, 1.6, SEPIA, 1.5, twice=True)
    line(s, r, (2452, 652), (2452, 666), 1.2, SEPIA, 1.3, over=0)
    # the shop: painted timber, a rolled-up canvas blind, a dark display window, a recessed door
    sm = s.rect(x0 + 10, G, x1 - 10, PAVE + 14)
    put(s, sm, TEAL, 0.85, lift=0.5, wob=1.2, edge=0.4, ew=6, flow=0.6, fs=120, gran=0.45)
    s.wash(sm, PAYNE, 0.5, wob=2, bleed=8, edge=0.15, flow=0.7, fs=90, clip=sm)
    s.wash(sm, UMBER, 0.14, wob=3, bleed=12, edge=0.1, flow=0.9, fs=60, clip=sm)
    stone_band(s, r, x0 + 6, x1 - 6, G - 2, 12, 0.3, 18)
    rb = s.rect(x0 + 16, 770, x1 - 16, 800)                              # the blind, rolled into its box
    put(s, rb, CREAM, 0.55, lift=0.85, wob=0.8, edge=0.4, ew=4)
    s.wash(rb, SLATE, 0.6, wob=1, soft=2, edge=0, grad=s.vgrad(770, 800, 0.3, 1), flow=0.7, fs=60)
    for xx in np.arange(x0 + 40, x1 - 30, 36):
        if r.random() < 0.7:
            s.ink([(xx, 772), (xx + 3 + J(r, 2), 786), (xx + J(r, 2), 799)], 1.0, SEPIA, 0.9, skip=0.15)
    box(s, r, x0 + 16, 770, x1 - 16, 800, 1.8, SEPIA, 1.5, over=4, dbl=0.4)
    s.wash(s.rect(x0 + 16, 800, x1 - 16, 822), SEPIA, 0.4, wob=1.5, bleed=4, edge=0.1)
    dw = (2440, 836, 2644, 1196)
    gm = s.rect(*dw)
    put(s, gm, INKBLUE, 0.78, lift=0.7, wob=1, edge=0.45, ew=6, flow=0.6, fs=110)
    s.wash(gm, PRUSSIAN, 0.3, wob=2, bleed=10, edge=0.1, flow=0.9, fs=70, clip=gm)
    s.lift(s.rect(dw[0] + 4, dw[1] + 4, dw[2] - 4, dw[1] + 110), 0.26, soft=2, wob=1.5)                   # a holland blind, a third down
    line(s, r, (dw[0] + 4, dw[1] + 110), (dw[2] - 4, dw[1] + 111), 1.3, SEPIA, 1.2)
    s.ink([(2542, 946), (2542, 962)], 1.0, SEPIA, 1.2)
    oval(s, 2542, 966, 3.5, 3.5, 0.9, SEPIA, 1.2)
    s.lift(Q(s, [(2452, 960), (2520, 960), (2470, 1180), (2452, 1180)]), 0.14, soft=6, wob=3)             # the street in the glass
    s.lift(Q(s, [(2560, 960), (2580, 960), (2540, 1180), (2524, 1180)]), 0.10, soft=5, wob=3)
    sh = s.rect(2450, 1096, 2634, 1104)                                                                   # a shelf of jars, barely there
    s.lift(sh, 0.2, soft=1)
    for xx in np.arange(2462, 2626, 23):
        jh = U(r, 22, 44)
        jm = s.rect(xx, 1096 - jh, xx + U(r, 12, 17), 1096)
        s.lift(jm, U(r, 0.1, 0.24), soft=1, wob=0.8)
        if r.random() < 0.6:
            box(s, r, xx, 1096 - jh, xx + 14, 1096, 0.9, SEPIA, 0.7, over=1, dbl=0, skip=0.3)
    box(s, r, *dw, 2.1, SEPIA, 1.5, over=5, dbl=0.5)
    box(s, r, dw[0] + 6, dw[1] + 6, dw[2] - 6, dw[3] - 6, 1.0, SEPIA, 1.0, over=1, dbl=0, skip=0.2)
    line(s, r, (2542, dw[1]), (2543, dw[3]), 1.6, SEPIA, 1.3)
    put(s, s.rect(dw[0] - 8, dw[3], dw[2] + 8, dw[3] + 10), TEAL, 0.6, lift=0.6, wob=0.6, edge=0.4, ew=2)
    hl(s, [(dw[0] - 6, dw[3] + 2), (dw[2] + 6, dw[3] + 2)], 2.2, 0.4)
    line(s, r, (dw[0] - 9, dw[3] + 10), (dw[2] + 9, dw[3] + 10), 2.0, SEPIA, 1.5, dbl=0.5)
    for a, b in ((2446, 2536), (2548, 2638)):
        s.wash(s.rect(a, 1220, b, PAVE - 14), PAYNE, 0.3, wob=1, soft=1.5, edge=0.5, ew=3)
        box(s, r, a, 1220, b, PAVE - 14, 1.4, SEPIA, 1.3, over=3, dbl=0.4)
    s.wash(s.rect(2664, 836, 2766, PAVE - 6), INKBLUE, 0.5, wob=1, soft=1.5, edge=0.4, ew=4)              # the recess
    door(s, r, 2674, 866, 2758, PAVE - 8, TEAL, 0.9, 2, glass=True)
    box(s, r, 2664, 836, 2766, PAVE - 6, 1.8, SEPIA, 1.4, over=4, dbl=0.4)
    put(s, s.rect(2656, PAVE - 8, 2774, PAVE + 6), MIST, 0.5, lift=0.7, wob=0.8, edge=0.4, ew=2)
    line(s, r, (2654, PAVE - 8), (2776, PAVE - 8), 1.6, SEPIA, 1.4)
    pipe(s, r, 2780, PAR + 14, PAVE, 9)
    s.wash(s.rect(x0, PAVE - 50, x1, PAVE + 14), SEPIA, 0.3, wob=3, bleed=10, edge=0.1, clip=m)
    line(s, r, (x1, PAR), (x1 + J(r, 2), PAVE), 2.3, SEPIA, 1.5, dbl=0.5)
    line(s, r, (x0, CORN_D), (x0 + J(r, 2), PAVE), 2.0, SEPIA, 1.4, dbl=0.4)


CORN_D = 596


def bld_f(S, r):
    """Far right: a tall soot-brown brick warehouse front with a carriage arch and wooden gates."""
    x0, x1, PAR, G = 2788, W + 40, 346, 730
    s = Sub(S, x0 - 70, 230, W, PAVE + 40)
    m = s.rect(x0 - 6, PAR, x1, PAVE + 14)
    m = wallwash(s, r, m, [(PAYNE, 0.74), (BURNT, 0.42), (UMBER, 0.2)], PAR, PAVE, bx=(x0, W), drags=7)
    mottle(s, r, x0 + 30, PAR + 20, W, G, [BURNT, VIOLET, UMBER, PRUSSIAN], 6, 0.13, size=(50, 130), clip=m)
    bricks(s, r, x0 + 12, PAR + 30, W - 4, G - 10, 16, 10.5, 26, clip=m)
    streaks(s, r, x0 + 10, W - 10, PAR + 20, G, 9, PAYNE, 0.13, (5, 14), clip=m)
    cm = s.rect(x0 - 10, PAR - 10, x1, PAR + 14)
    put(s, cm, SLATE, 0.75, lift=0, wob=0.8, edge=0.4, ew=3)
    s.wash(cm, PAYNE, 0.4, wob=1, soft=1, edge=0, flow=0.6, fs=80)
    hl(s, [(x0 - 8, PAR - 8), (W, PAR - 8)], 2.6, 0.4)
    s.wash(s.rect(x0, PAR + 14, x1, PAR + 40), SEPIA, 0.45, wob=0, soft=0, edge=0, grad=s.vgrad(PAR + 14, PAR + 40, 1, 0), flow=0.5, fs=70)
    line(s, r, (x0 - 12, PAR - 10), (W + 4, PAR - 11), 2.0, SEPIA, 1.5, dbl=0.5)
    line(s, r, (x0 - 10, PAR + 14), (W + 4, PAR + 14), 2.4, SEPIA, 1.6, dbl=0.6)
    for xx in np.arange(x0 + 6, W, 30):
        path(s, [(xx, PAR + 14), (xx + 1, PAR + 27), (xx + 11, PAR + 22), (xx + 11, PAR + 14)], 1.0, SEPIA, 1.0, over=1, r=r)
    for fl in range(3):
        fy = G - fl * 128
        stone_band(s, r, x0, W, fy - 6, 8, 0.24, 10)
        for i, cx in enumerate((2872, 3006)):
            w, h = 76 + J(r, 4), 90 + J(r, 4)
            kind = "sash"
            cur = None
            if (fl, i) == (1, 0):
                cur = "blind"
            if (fl, i) == (2, 1):
                cur = "net"
            window(s, r, cx - w / 2, fy - 30 - h, cx + w / 2, fy - 30, kind, 2, head="arch", curtain=cur, frame=SLATE, fk=0.55)
        window(s, r, 3090, fy - 122, 3140, fy - 30, "sash", 1, head="arch", frame=SLATE, fk=0.55)
    acbox(s, r, 2978, G - 128 - 24, 56, 34)
    # the carriage arch
    ax0, ax1, sp, cr = 2852, 3050, 948, 868
    arch = np.maximum(s.rect(ax0, sp, ax1, PAVE - 2), s.ellipse((ax0 + ax1) / 2, sp, (ax1 - ax0) / 2, sp - cr))
    sur = np.maximum(s.rect(ax0 - 22, sp, ax1 + 22, PAVE), s.ellipse((ax0 + ax1) / 2, sp, (ax1 - ax0) / 2 + 22, sp - cr + 22))
    s.lift(sur, 0.26, soft=1.5, wob=1.5)
    put(s, arch, SEPIA, 0.8, lift=0.6, wob=1, edge=0.4, ew=6, flow=0.6, fs=90, gran=0.5)
    s.wash(arch, INDIGO, 0.45, wob=2, bleed=8, edge=0.1, flow=0.8, fs=70, clip=arch)
    s.wash(arch, PAYNE, 0.4, wob=0, soft=0, edge=0, grad=s.vgrad(cr, sp + 60, 1, 0), clip=arch)
    cxa = (ax0 + ax1) / 2
    for xx in np.arange(ax0 + 14, ax1 - 4, 17):
        ytop = sp - (sp - cr) * math.sqrt(max(0.0, 1 - ((xx - cxa) / ((ax1 - ax0) / 2)) ** 2))
        seg(s, (xx + J(r, 1), ytop + 3), (xx + J(r, 1.5), PAVE - 4), 1.1, SEPIA, U(r, 0.7, 1.1), r=r, skip=0.12)
        if r.random() < 0.3:
            hl(s, [(xx + 5, ytop + 30), (xx + 5, PAVE - 30)], 2.2, 0.14)
    line(s, r, (cxa, cr + 2), (cxa + 1, PAVE - 2), 2.0, SEPIA, 1.5, dbl=0.5)
    for yy in (sp + 20, 1180):
        line(s, r, (ax0 + 2, yy), (ax1 - 2, yy + J(r, 1)), 1.6, SEPIA, 1.3)
    box(s, r, cxa + 14, 1010, cxa + 84, PAVE - 6, 1.5, SEPIA, 1.3, over=2, dbl=0.3)                   # the wicket in the gate
    oval(s, cxa + 24, 1150, 3.6, 3.6, 1.0, SEPIA, 1.3)
    s.ink(np.vstack([[(ax0, PAVE - 2), (ax0, sp)], ell(cxa, sp, (ax1 - ax0) / 2, sp - cr, math.pi, 2 * math.pi, 30), [(ax1, sp), (ax1, PAVE - 2)]]), 2.2, SEPIA, 1.6)
    s.ink(ell(cxa, sp, (ax1 - ax0) / 2 + 22, sp - cr + 22, math.pi, 2 * math.pi, 30), 1.4, SEPIA, 1.2, skip=0.1)
    for a in np.linspace(math.pi + 0.12, 2 * math.pi - 0.12, 11):
        ca, sa = math.cos(a), math.sin(a)
        line(s, r, (cxa + ca * (ax1 - ax0) / 2, sp + sa * (sp - cr)), (cxa + ca * ((ax1 - ax0) / 2 + 22), sp + sa * (sp - cr + 22)), 1.0, SEPIA, 1.0, over=0)
    for bx in (ax0 - 22, ax1 + 22):
        line(s, r, (bx, sp), (bx + J(r, 1), PAVE), 1.4, SEPIA, 1.2, skip=0.1)
    s.ink([(cxa, 838), (cxa, 822), (cxa + 14, 814)], 1.6, SEPIA, 1.4)                                 # a dead lamp over the arch
    put(s, Q(s, [(cxa - 10, 838), (cxa + 10, 838), (cxa + 7, 858), (cxa - 7, 858)]), SLATE, 0.6, lift=0.6, wob=0.5, edge=0.4, ew=2)
    path(s, [(cxa - 10, 838), (cxa + 10, 838), (cxa + 7, 858), (cxa - 7, 858)], 1.2, SEPIA, 1.3, closed=True, over=1, r=r)
    gz = s.rect(x0, G + 2, x1, PAVE + 14)
    s.wash(gz, PAYNE, 0.25, wob=2, bleed=8, edge=0.1, flow=0.6, fs=120, clip=m)
    pipe(s, r, 2806, PAR + 16, PAVE, 9)
    s.wash(s.rect(x0, PAVE - 50, x1, PAVE + 14), SEPIA, 0.3, wob=3, bleed=10, edge=0.1, clip=m)
    line(s, r, (x0, PAR), (x0 + J(r, 2), 470), 2.3, SEPIA, 1.5, dbl=0.5)


def cables(S, r):
    """Wires slung between the houses, across the gaps of sky."""
    for a, b, sag in (((1006, 428), (1394, 366), 50), ((1006, 436), (1394, 372), 72), ((1004, 470), (1392, 410), 34), ((1008, 498), (1390, 446), 22),
                      ((2404, 332), (2796, 372), 62), ((2404, 340), (2796, 384), 86), ((2408, 404), (2794, 420), 30),
                      ((503, 372), (648, 404), 16), ((-10, 300), (300, 312), 18)):
        cable(S, r, a, b, sag, U(r, 1.2, 1.8), INKBLUE, U(r, 1.0, 1.4))
    for x, y in ((1005, 432), (1393, 369), (2405, 336), (2796, 378)):
        S.ink([(x - 5, y - 8), (x - 5, y + 10)], 2.4, SEPIA, 1.5)
        S.ink([(x - 9, y - 2), (x + 3, y - 2)], 1.6, SEPIA, 1.4)
        S.ink([(x - 9, y + 5), (x + 3, y + 5)], 1.6, SEPIA, 1.4)


def main():
    S = Sheet(W, H, 43)
    LIT.clear()
    bld_a(S, rs(431))
    bld_b(S, rs(432))
    bld_c(S, rs(433))
    bld_e(S, rs(435))
    bld_f(S, rs(436))
    bld_d(S, rs(434))
    cafe_front(S, rs(439))
    cables(S, rs(437))
    for jx, ytop in ((503, 424), (1010, 500), (1388, 500), (2412, 482), (2790, 482)):      # the party walls: no chink between houses
        S.body[ytop:PAVE + 14, jx - 12:jx + 12] = 1.0
    meta = {"win": list(WIN), "door": list(DOORG), "door_leaf": list(DOOR), "sign": list(SIGN), "awning_edge": [1420, 806, 2400],
            "neon": list(NEON), "lit": [list(v) for v in LIT], "brackets": [list(v) for v in BRACKETS], "pave_y": PAVE, "vp": list(VP)}
    S.save("st_main", q=90, meta=meta)


# ---------------------------------------------------------------------------------------------- the room, seen from the street
def inside():
    """What shows through the café glass: a lit wall, two pendants, a table and a bentwood chair, the counter end.
    Painted in world coordinates on a small sheet; mostly reserved paper, because this is the light."""
    ox, oy = INSIDE_AT
    s = Off(960, 620, ox, oy, 44)
    r = rs(44)
    x0, y0, x1, y1 = ox, oy, ox + 960, oy + 620
    F = s.full()
    L1, L2 = (1574, 962), (1986, 958)                     # the two pendants (bottom of each shade)
    # the wall: a breath of cream everywhere, ochre gathering away from the lamps
    s.wash(F, CREAM, 0.42, wob=0, soft=0, edge=0, flow=0.5, fs=260, gran=0.3)
    far_from = np.minimum(s.rgrad(L1[0], L1[1] + 40, 60, 330, 0, 1, sy=0.9), s.rgrad(L2[0], L2[1] + 40, 60, 330, 0, 1, sy=0.9))
    s.wash(F, OCHRE, 0.5, wob=0, soft=0, edge=0, grad=far_from, flow=0.6, fs=180, gran=0.35)
    s.wash(F, AMBER, 0.3, wob=0, soft=0, edge=0, grad=far_from * s.vgrad(1010, 760, 0.25, 1), flow=0.7, fs=140, gran=0.35)
    s.wash(F, SIENNA, 0.34, wob=0, soft=0, edge=0, grad=s.vgrad(900, 740, 0, 1), flow=0.6, fs=200)        # the ceiling end of the wall is dimmer
    s.wash(s.rect(x0, y0, 1500, y1), SIENNA, 0.25, wob=6, bleed=40, edge=0)
    s.wash(s.rect(2300, y0, x1, y1), SIENNA, 0.3, wob=6, bleed=40, edge=0)
    # a picture rail, three frames (nothing readable in them), a clock without hands
    s.stroke([(x0, 846), (1800, 842), (x1, 846)], 6, SIENNA, 0.5, wob=1.5, edge=0.4, taper=(0, 0), soft=1.6)
    for fx, fy, fw, fh, c in ((1702, 918, 78, 98, TEAL), (1802, 936, 56, 70, BURNT), (1872, 906, 46, 58, MOSS)):
        fm = s.rect(fx, fy, fx + fw, fy + fh)
        s.wash(fm, SIENNA, 0.75, wob=1.5, soft=1.6, edge=0.5, ew=3)
        im = s.rect(fx + 9, fy + 9, fx + fw - 9, fy + fh - 9)
        s.lift(im, 0.8, soft=1.5, wob=1)
        s.wash(im, c, 0.32, wob=2, bleed=4, edge=0.4, flow=0.9, fs=16)
        s.wash(s.blob(fx + fw / 2, fy + fh * 0.6, fw * 0.22, fh * 0.2, irr=0.4), UMBER, 0.3, wob=2, bleed=3)
        box(s, r, fx, fy, fx + fw, fy + fh, 1.4, BURNT, 1.0, over=3, dbl=0.4, skip=0.15)
        s.wash(s.rect(fx + 4, fy + fh, fx + fw + 8, fy + fh + 8), SIENNA, 0.3, wob=2, bleed=4, edge=0)
    # panelling below a dado rail
    DADO = 1096
    wm = s.rect(x0, DADO, x1, y1)
    s.wash(wm, SIENNA, 0.62, wob=2, soft=2, edge=0.3, ew=6, flow=0.6, fs=120, gran=0.4)
    s.wash(wm, BURNT, 0.35, wob=0, soft=0, edge=0, grad=s.vgrad(DADO, 1260, 0.2, 1), flow=0.6, fs=90)
    s.stroke([(x0, DADO), (1800, DADO - 2), (x1, DADO)], 7, BURNT, 0.6, wob=1.5, edge=0.4, taper=(0, 0), soft=1.5)
    for xx in np.arange(x0 + 30, x1, 92):
        s.ink([(xx + J(r, 4), DADO + 8), (xx + J(r, 4), 1250)], 1.6, BURNT, 0.7, skip=0.2, tremor=1.0)
    # shelves with cups and jars at the left
    for sy, n in ((952, 6), (1012, 7)):
        s.stroke([(1486, sy), (1560, sy + 1), (1650, sy)], 6, UMBER, 0.7, wob=1, edge=0.4, taper=(0, 0), soft=1.3)
        s.wash(s.rect(1490, sy + 4, 1650, sy + 14), SIENNA, 0.3, wob=2, bleed=4, edge=0)
        xx = 1494
        for i in range(n):
            w = U(r, 13, 21)
            h = U(r, 12, 20) if r.random() < 0.65 else U(r, 24, 34)
            cm = s.rect(xx, sy - 3 - h, xx + w, sy - 3)
            if h > 22:        # a jar or a tin
                s.wash(cm, (TEAL, BURNT, UMBER, MOSS)[int(r.integers(0, 4))], U(r, 0.45, 0.8), wob=1, soft=1.4, edge=0.4, ew=2)
            else:             # a cup: paper, with a shadow side and a handle
                s.lift(cm, 0.85, soft=1.2, wob=0.8)
                s.wash(cm, SIENNA, 0.3, wob=0.8, soft=1.4, edge=0, grad=s.hgrad(xx, xx + w))
                s.ink(ell(xx + w + 2, sy - 3 - h / 2, 4, h * 0.3, -1.4, 1.4, 10), 1.1, BURNT, 0.9)
            if r.random() < 0.75:
                box(s, r, xx, sy - 3 - h, xx + w, sy - 3, 1.0, BURNT, 0.8, over=1, dbl=0.1, j=0.8, skip=0.2)
            xx += w + U(r, 4, 10)
            if xx > 1640:
                break
    # the counter end and the machine, mostly seen through the door
    cnt = s.rect(2086, 1070, x1, y1)
    s.wash(cnt, SIENNA, 0.8, wob=2, soft=2, edge=0.4, ew=6, flow=0.6, fs=90)
    s.wash(cnt, BURNT, 0.5, wob=0, soft=0, edge=0, grad=s.vgrad(1070, 1240, 0.3, 1) , flow=0.6, fs=70)
    s.stroke([(2076, 1068), (2200, 1066), (x1, 1068)], 9, UMBER, 0.8, wob=1.2, edge=0.4, taper=(0, 0), soft=1.2)
    hl(s, [(2082, 1062), (2330, 1061)], 2.5, 0.5)
    for xx in (2146, 2222, 2300):
        s.ink([(xx + J(r, 3), 1082), (xx + J(r, 3), 1250)], 1.6, UMBER, 0.7, skip=0.2, tremor=1.0)
    mc = s.poly([(2176, 1062), (2176, 984), (2190, 972), (2268, 972), (2280, 984), (2280, 1062)], smooth=False)
    s.lift(mc, 0.7, soft=1.5, wob=1)
    s.wash(mc, SLATE, 0.8, wob=1.5, soft=1.6, edge=0.5, ew=4, flow=0.5, fs=30)
    s.wash(mc, TEAL, 0.5, wob=1.5, soft=2, edge=0, grad=s.vgrad(972, 1062, 0.2, 1))
    s.lift(s.rect(2184, 990, 2272, 1000), 0.6, soft=1.5)                                # a chrome band
    for xx in (2200, 2228, 2256):
        s.wash(s.rect(xx - 6, 1026, xx + 6, 1046), UMBER, 0.8, wob=0.8, soft=1.2)      # group handles
    for xx in (2192, 2214, 2236, 2258):
        cm = s.rect(xx - 7, 958, xx + 7, 972)
        s.lift(cm, 0.9, soft=1.2)                                                       # cups warming on top
        s.wash(cm, SIENNA, 0.25, wob=0.5, soft=1.2, grad=s.hgrad(xx - 7, xx + 7))
    s.ink([(2176, 1062), (2176, 984), (2190, 972), (2268, 972), (2280, 984), (2280, 1062)], 1.5, UMBER, 1.0, skip=0.1)
    dome = s.ellipse(2126, 1062, 30, 34) * s.rect(2090, 1020, 2160, 1063)                # a cake under glass
    s.lift(dome, 0.55, soft=1.5)
    s.wash(s.rect(2108, 1044, 2144, 1062), SIENNA, 0.6, wob=1.5, soft=1.5, edge=0.4, ew=2)
    s.ink(ell(2126, 1062, 30, 34, math.pi, 2 * math.pi, 20), 1.2, BURNT, 0.9, skip=0.1)
    oval(s, 2126, 1026, 4, 3, 1.0, BURNT, 0.9)
    for sy in (900, 946):                                                               # bottles on the back shelf
        s.stroke([(2140, sy), (2240, sy + 1), (2340, sy)], 5, UMBER, 0.6, wob=1, edge=0.4, taper=(0, 0), soft=1.3)
        xx = 2148
        while xx < 2332:
            w, h = U(r, 9, 14), U(r, 22, 38)
            bm = np.maximum(s.rect(xx, sy - 3 - h * 0.7, xx + w, sy - 3), s.rect(xx + w * 0.3, sy - 3 - h, xx + w * 0.7, sy - 3))
            s.wash(bm, (TEAL, BURNT, MOSS, UMBER, SIENNA)[int(r.integers(0, 5))], U(r, 0.45, 0.85), wob=1, soft=1.3, edge=0.4, ew=2)
            xx += w + U(r, 4, 9)
    # the far table with two chairs, small and soft
    def chair(cx, seat, sc=1.0, k=1.0, face=1):
        """A bentwood chair in silhouette: the hooped back, the round seat edge, two splayed legs."""
        w, hh = 34 * sc, 96 * sc
        hoop = [(cx - w, seat), (cx - w * 1.02, seat - hh * 0.55), (cx - w * 0.7, seat - hh * 0.92), (cx, seat - hh), (cx + w * 0.7, seat - hh * 0.92), (cx + w * 1.02, seat - hh * 0.55), (cx + w, seat)]
        s.stroke(hoop, 7.5 * sc, UMBER, 1.0 * k, wob=0.8, edge=0.4, taper=(0, 0), soft=1.2)
        inner = [(cx - w * 0.5, seat), (cx - w * 0.52, seat - hh * 0.45), (cx, seat - hh * 0.74), (cx + w * 0.52, seat - hh * 0.45), (cx + w * 0.5, seat)]
        s.stroke(inner, 5 * sc, UMBER, 0.9 * k, wob=0.8, edge=0.4, taper=(0, 0), soft=1.2)
        st = s.ellipse(cx, seat + 4 * sc, w * 1.18, 8 * sc)
        s.wash(st, UMBER, 1.0 * k, wob=0.8, soft=1.3, edge=0.4, ew=2)
        s.wash(st, SEPIA, 0.4 * k, wob=0.8, soft=1.5, edge=0, grad=s.vgrad(seat, seat + 12 * sc))
        for sd in (-1, 1):
            s.stroke([(cx + sd * w * 0.9, seat + 8 * sc), (cx + sd * w * 1.08, seat + 110 * sc)], 6 * sc, UMBER, 0.95 * k, wob=0.8, edge=0.4, taper=(0, 0.2), soft=1.2)
        s.ink(hoop, 1.3, SEPIA, 0.9 * k, skip=0.2, tremor=0.9)

    def table(cx, top, rx, k=1.0):
        tm = s.ellipse(cx, top, rx, max(5, rx * 0.085))
        s.lift(tm, 0.6, soft=1.2)
        s.wash(tm, SIENNA, 0.7 * k, wob=0.8, soft=1.2, edge=0.5, ew=2)
        s.lift(s.ellipse(cx - rx * 0.2, top - 2, rx * 0.5, 2.5), 0.5, soft=1.5)          # lamp on the polish
        s.wash(s.ellipse(cx, top + rx * 0.085 + 3, rx * 0.96, 5), UMBER, 0.9 * k, wob=0.8, soft=1.2)
        s.stroke([(cx, top + 6), (cx + 1, top + 150)], 11, UMBER, 1.0 * k, wob=0.8, edge=0.4, taper=(0, 0), soft=1.2)
        s.ink(ell(cx, top, rx, max(5, rx * 0.085), 0, math.pi, 30), 1.3, SEPIA, 0.9 * k, skip=0.15)

    chair(1516, 1150, 0.82, 0.8)
    chair(1640, 1150, 0.82, 0.8)
    table(1578, 1128, 62, 0.85)
    cup = s.rect(1566, 1110, 1584, 1124)
    s.lift(cup, 0.9, soft=1)
    s.wash(cup, SIENNA, 0.3, wob=0.5, soft=1.2, grad=s.hgrad(1566, 1584))
    # the window table, nearer: its chair pulled out and empty
    chair(1868, 1196, 1.08, 1.0)
    table(1990, 1158, 104, 1.0)
    s.stroke([(1880, 1100), (1882, 1150)], 4, UMBER, 0.6, wob=0.8, soft=1.2, taper=(0, 0))
    # the pendants: flex, dark teal enamel shade, the bulb is bare paper
    for lx, ly in (L1, L2):
        glow = s.rgrad(lx, ly + 24, 10, 150, 1, 0, sy=1.15)
        s.wash(glow, None, 0.92, wob=0, soft=0, edge=0, gran=0, flow=0, lift=True)
        s.wash(s.rgrad(lx, ly + 30, 60, 230, 0.0, 1.0) * s.rgrad(lx, ly + 30, 200, 330, 1, 0), OCHRE, 0.10, wob=0, soft=0, edge=0)
        s.ink([(lx + 1, y0), (lx - 1, (y0 + ly) / 2), (lx, ly - 50)], 2.0, UMBER, 1.2, tremor=0.6)
        sh = s.poly([(lx - 9, ly - 52), (lx + 9, ly - 52), (lx + 16, ly - 34), (lx + 44, ly - 6), (lx + 46, ly), (lx - 46, ly), (lx - 44, ly - 6), (lx - 16, ly - 34)], smooth=False)
        s.lift(sh, 1.0, soft=1.0, wob=0.6)
        s.wash(sh, TEAL, 1.15, wob=1.0, soft=1.2, edge=0.5, ew=4, flow=0.4, fs=30)
        s.wash(sh, PRUSSIAN, 0.6, wob=1, soft=2, edge=0, grad=s.hgrad(lx - 10, lx + 46, 0.1, 1))
        s.lift(Q(s, [(lx - 30, ly - 16), (lx - 22, ly - 22), (lx - 12, ly - 36), (lx - 18, ly - 20)]), 0.4, soft=1.5)
        s.ink([(lx - 46, ly), (lx - 44, ly - 6), (lx - 16, ly - 34), (lx - 9, ly - 52), (lx + 9, ly - 52), (lx + 16, ly - 34), (lx + 44, ly - 6), (lx + 46, ly)], 1.5, INKBLUE, 1.1, skip=0.08, smooth=False)
        bulb = s.ellipse(lx, ly + 7, 9, 10)
        s.lift(bulb, 1.0, soft=1.2)
        s.ink(ell(lx, ly + 7, 9, 10, 0.3, 2.9, 14), 1.0, SIENNA, 0.7)
    # seen through wet glass: let everything run together a little, then a very thin cool film
    s.A[:] = cv2.GaussianBlur(s.A, (0, 0), 1.25)
    s.wash(F, RAIN, 0.05, wob=0, soft=0, edge=0, flow=0.9, fs=90, gran=0.5)
    s.save("st_inside", opaque=True, q=92, meta={"at": [ox, oy]})


# ---------------------------------------------------------------------------------------------- pavement and wet road
def pxv(x_at_wall, y):
    """Perspective: a line running away from us that meets the wall foot at x_at_wall, followed to sheet height y."""
    return VP[0] + (x_at_wall - VP[0]) * (y - VP[1]) / (PAVE - VP[1])


def yd(d):
    """Depth in metres from the eye -> sheet y on the ground (the wall foot is 14 m away)."""
    return VP[1] + (PAVE - VP[1]) * 14.0 / d


def reflect(s, r, xa, xb, y0, y1, amt, warm, n, wide=(12, 40), gaps=(), glow=0.55, fade=0.45, c=AMBER):
    """A light lying on wet tarmac: reserved by lifting -- a soft pool first, then separate long wobbling strokes drawn
    downward with a damp brush -- and glazed warm only where the paper came back. Wet in wet: no hard edge anywhere."""
    core = s.rect(xa, y0, xb, y1)
    fall = s.vgrad(y0, y1, 1, fade)
    acc = s.wash(core, None, amt * glow, wob=8, bleed=22, edge=0, gran=0.2, flow=0.4, fs=90, lift=True, grad=fall) * fall * glow
    for i in range(n):
        x = U(r, xa + 4, xb - 4)
        ya = y0 + U(r, 0, 0.5) ** 1.6 * (y1 - y0)
        if any(abs(x - gx) < gw and ya < gy for gx, gw, gy in gaps):
            continue
        yb = min(y1 + 40, ya + U(r, 0.3, 1.0) * (y1 - y0))
        ph, am = U(r, 0, 6.28), U(r, 3, 9)
        pts = [(x + math.sin(ph + q * U(r, 5, 9)) * am * (0.3 + q), ya + (yb - ya) * q) for q in np.linspace(0, 1, 8)]
        f = (1 - 0.4 * (ya - y0) / (y1 - y0)) * U(r, 0.5, 0.95)
        acc = np.maximum(acc, s.wash(s.ribbon(pts, U(r, *wide), taper=(0.25, 0.55)), None, amt * f, wob=3.5, soft=U(r, 3.5, 6.5), edge=0, gran=0.25, flow=0, lift=True) * f)
    if warm > 0:
        acc = np.clip(acc * 1.25, 0, 1)
        s.wash(acc, c, warm, wob=0, soft=0, edge=0, flow=0.5, fs=60, gran=0.3)
        s.wash(acc, SIENNA, warm * 0.7, wob=0, soft=0, edge=0, grad=s.vgrad(y0, y0 + (y1 - y0) * 0.35, 1, 0), flow=0.8, fs=40)
    return acc


def road():
    S = Sheet(W, H, 45)
    r = rs(45)
    s = Sub(S, 0, 1150, W, H)
    RD = KERB + 18                                    # where the tarmac begins, at the foot of the kerb
    # ---- pavement
    pm = s.rect(-30, PAVE - 1, W + 30, KERB + 4)
    pm = s.wash(pm, SLATE, 0.74, wob=1.2, soft=0.8, edge=0.3, ew=6, flow=0.5, fs=260, gran=0.42, body=1)
    s.wash(pm, PAYNE, 0.34, wob=2, bleed=8, edge=0.1, flow=0.8, fs=170, gran=0.4, clip=pm)
    s.wash(pm, VIOLET, 0.10, wob=2, bleed=8, edge=0.1, flow=0.9, fs=110, clip=pm)
    s.wash(s.rect(-30, PAVE - 1, W + 30, PAVE + 26), SEPIA, 0.34, wob=0, soft=0, edge=0, grad=s.vgrad(PAVE, PAVE + 26, 1, 0), flow=0.6, fs=90)    # damp at the wall foot
    # the flags, joint by joint; a few of them a different stone, a few shining
    rows = [PAVE, PAVE + 24, PAVE + 52, KERB - 1]
    xs = np.arange(-2600, 6000, 118.0)
    for j in range(3):
        ya, yb = rows[j], rows[j + 1]
        off = (0.5 if j % 2 else 0.0) * 118
        for x in xs:
            a, b = x + off + J(r, 5), x + off + 118 + J(r, 5)
            if pxv(b, yb) < -20 or pxv(a, yb) > W + 20:
                continue
            q = [(pxv(a, ya), ya), (pxv(b, ya), ya), (pxv(b, yb), yb), (pxv(a, yb), yb)]
            u = r.random()
            if u < 0.22:
                s.wash(Q(s, q), (PAYNE, VIOLET, UMBER, TEAL)[int(r.integers(0, 4))], U(r, 0.08, 0.2), wob=0, soft=1.2, edge=0.5, ew=3, flow=0)
            elif u < 0.36:
                s.lift(Q(s, q), U(r, 0.1, 0.22), soft=1.5, wob=0)
            if r.random() < 0.9:
                seg(s, q[0], q[3], 1.1, SEPIA, U(r, 0.6, 1.0), r=r, skip=0.2)
        if j:
            xx = -10.0
            while xx < W:
                ln = U(r, 200, 700)
                seg(s, (xx, ya + J(r, 1)), (min(W + 10, xx + ln), ya + J(r, 1.5)), 1.1, SEPIA, U(r, 0.6, 1.0), r=r, skip=0.2, bow=0.001)
                xx += ln + U(r, 0, 40)
    # the light that falls out of the café onto the flags
    pool = Q(s, [(1452, PAVE), (2336, PAVE), (2430, KERB + 2), (1362, KERB + 2)])
    pool = s.wash(pool, None, 0.74, wob=5, bleed=14, edge=0, gran=0.25, flow=0.5, fs=90, lift=True, clip=pm)
    s.wash(pool, OCHRE, 0.4, wob=0, soft=0, edge=0, flow=0.5, fs=60)
    s.wash(pool, AMBER, 0.22, wob=0, soft=0, edge=0, grad=s.vgrad(PAVE, KERB, 0.3, 1), flow=0.8, fs=40)
    for xa, xb, kk in ((1669, 1681, 0.16), (1879, 1891, 0.16), (2096, 2146, 0.22)):                   # shadows of the posts across it
        q = [(xa, PAVE), (xb, PAVE), (xb + (xb - 1780) * 0.12 + 5, KERB), (xa + (xa - 1780) * 0.12 - 5, KERB)]
        s.wash(Q(s, q), SEPIA, kk, wob=2, bleed=6, edge=0, clip=pm)
    s.wash(s.rect(1456, PAVE, 2126, PAVE + 18), SEPIA, 0.4, wob=0, soft=0, edge=0, grad=s.vgrad(PAVE, PAVE + 18, 1, 0))                   # under the stall-riser
    # ---- kerb
    s.lift(s.rect(-30, KERB - 12, W + 30, KERB + 1), 0.26, soft=1, wob=1)
    kf = s.rect(-30, KERB, W + 30, RD + 2)
    put(s, kf, SLATE, 0.62, lift=0.5, wob=0.8, edge=0.3, ew=3, flow=0.5, fs=200)
    s.wash(kf, PAYNE, 0.6, wob=0, soft=0, edge=0, flow=0.7, fs=120, grad=s.vgrad(KERB, RD, 0.5, 1))
    hl(s, [(-10, KERB - 1), (W + 10, KERB - 1)], 2.6, 0.42)
    line(s, r, (-10, KERB - 12), (W + 10, KERB - 12), 1.1, SEPIA, 0.9, skip=0.2)
    line(s, r, (-10, KERB + 1), (W + 10, KERB + 1), 1.9, SEPIA, 1.4, dbl=0.6)
    for x in np.arange(-2400, 6000, 236.0):
        xa = pxv(x + J(r, 8), KERB)
        if -10 < xa < W + 10:
            seg(s, (pxv(x, KERB - 12), KERB - 12), (xa, KERB + 1), 1.2, SEPIA, 1.0, r=r)
            seg(s, (xa, KERB + 1), (xa + J(r, 1), RD), 1.3, SEPIA, 1.1, r=r)
    # ---- tarmac: dark and cool, a little paler far off where it mirrors the sky
    rm = s.rect(-30, RD, W + 30, H + 30)
    rm = s.wash(rm, PAYNE, 0.88, wob=1.0, soft=0.8, edge=0.2, ew=8, flow=0.5, fs=320, gran=0.45, body=1)
    s.wash(rm, INDIGO, 0.46, wob=0, soft=0, edge=0, flow=0.7, fs=240, gran=0.4, grad=s.vgrad(RD - 20, H, 0.35, 1))
    s.wash(rm, PRUSSIAN, 0.26, wob=0, soft=0, edge=0, flow=1.0, fs=150, gran=0.4)
    s.wash(s.rect(-30, RD, W + 30, RD + 26), SEPIA, 0.5, wob=0, soft=0, edge=0, grad=s.vgrad(RD, RD + 26, 1, 0), flow=0.5, fs=80)          # the gutter
    for _ in range(22):                                                                              # the grain of the road, dragged across
        y = U(r, RD + 20, H)
        a = U(r, -100, W - 300)
        f = (y - RD) / (H - RD)
        s.stroke([(a, y), (a + U(r, 300, 1100), y + J(r, 6))], U(r, 14, 30) * (1 + 1.6 * f), PAYNE if r.random() < 0.6 else INKBLUE, U(r, 0.08, 0.2), dry=U(r, 0.4, 0.6),
                 edge=0.2, wob=2, taper=(0.15, 0.3), gran=0.5, clip=rm)
    for _ in range(8):                                                                               # and where it is simply wetter
        y = U(r, RD + 30, H)
        f = (y - RD) / (H - RD)
        s.lift(s.blob(U(r, 0, W), y, U(r, 200, 500), 10 + 26 * f, irr=0.35), U(r, 0.08, 0.16), bleed=10, wob=4)
    # ---- what the wet road holds of the street
    for xa, xb, a in ((1046, 1360, 0.2), (2440, 2770, 0.16), (-20, 60, 0.1)):                         # gaps of sky between the roofs
        reflect(s, r, xa, xb, RD + 60, H, a, 0.0, 9, wide=(16, 46), glow=0.7)
        s.wash(s.rect(xa, RD + 60, xb, H), RAIN, 0.08, wob=6, bleed=20, edge=0)
    reflect(s, r, 1474, 2086, RD + 2, H + 30, 0.92, 0.5, 46, wide=(14, 46), gaps=((1675, 13, 1540), (1885, 13, 1540)), glow=0.62, fade=0.7)
    reflect(s, r, 2152, 2292, RD + 2, H + 30, 0.88, 0.46, 13, wide=(10, 30), glow=0.55, fade=0.6)
    for lx in (BRACKETS[0][0], BRACKETS[1][0]):
        reflect(s, r, lx - 12, lx + 12, RD + 50, H, 0.6, 0.34, 4, wide=(5, 11), glow=0.3)
    for (lx0, ly0, lx1, ly1), a in zip(LIT or LIT_GUESS, (0.3, 0.34, 0.3, 0.3)):
        reflect(s, r, lx0, lx1, 1480, H + 30, a, 0.2, 5, wide=(8, 20), glow=0.6, fade=1.0)
    # ripples and tyre-wet that break the lights across
    for _ in range(12):
        y = U(r, RD + 30, H)
        f = (y - RD) / (H - RD)
        a = U(r, 1420, 2200)
        s.stroke([(a, y), (a + U(r, 120, 380) * (0.6 + f), y + J(r, 2))], U(r, 5, 9) * (1 + 1.5 * f), PAYNE, U(r, 0.14, 0.26), wob=2.5, soft=U(r, 3, 5), edge=0, taper=(0.35, 0.45), clip=rm)
    # ---- puddles: lighter, sky-coloured, soft
    for cx, cy, rx, ry, warm in ((1030, 1470, 170, 15, 0), (2700, 1604, 250, 26, 0), (2236, 1452, 120, 11, 1), (380, 1420, 240, 9, 0), (1500, 1690, 300, 30, 1), (2990, 1440, 130, 10, 0)):
        pm2 = s.blob(cx, cy, rx, ry, irr=0.3, n=13)
        pm2 = s.wash(pm2, None, 0.4, wob=4, soft=5, edge=0, gran=0.2, flow=0.4, fs=60, lift=True, clip=rm)
        s.wash(pm2, AMBER if warm else RAIN, 0.26, wob=0, soft=0, edge=0.5, ew=6, flow=0.5, fs=50)
        s.wash(s.blob(cx + rx * 0.1, cy + ry * 0.8, rx * 0.9, max(3, ry * 0.3), irr=0.3), INKBLUE, 0.3, wob=3, soft=3, edge=0, clip=rm)     # the near bank
    # ---- a zebra crossing going away to the left, worn; and a lane dash or two
    ZL, ZR = -150.0, 640.0                    # where its edges leave the sheet at the bottom
    zx = lambda xb, y: VP[0] + (xb - VP[0]) * (y - VP[1]) / (H - VP[1])
    d = 9.8
    while yd(d) < H + 10:
        ya, yb = yd(d), yd(d - 0.5)
        q = [(zx(ZL, ya) + J(r, 4), ya), (zx(ZR, ya) + J(r, 4), ya), (zx(ZR, yb) + J(r, 5), yb), (zx(ZL, yb) + J(r, 5), yb)]
        bm = Q(s, q)
        s.wash(bm, None, 0.56, wob=2.5, soft=1.6, edge=0, gran=0.5, flow=0.9, fs=70, lift=True, dry=0.22, clip=rm)
        s.wash(bm, MIST, 0.4, wob=2.5, soft=1.6, edge=0.5, ew=4, flow=0.7, fs=40, gran=0.5, clip=rm)
        s.wash(bm, PAYNE, 0.12, wob=3, bleed=8, edge=0, flow=1.0, fs=30, clip=rm)
        path(s, q, 1.3, SEPIA, 0.9, closed=True, over=3, r=r, skip=0.35)
        d -= 1.0
    for xa, xb in ((1180, 1420), (2360, 2700), (2960, 3100)):
        ya, yb = yd(6.95), yd(6.8)
        bm = Q(s, [(xa, ya), (xb, ya), (xb + 8, yb), (xa - 8, yb)])
        s.wash(bm, None, 0.5, wob=2, soft=1.2, edge=0, gran=0.5, flow=0.8, fs=40, lift=True, dry=0.35, clip=rm)
        s.wash(bm, MIST, 0.26, wob=2, soft=1.2, edge=0.5, ew=3, clip=rm)
    # ---- ironwork: a gully grate in the gutter, a manhole in the carriageway
    gq = [(1196, RD + 3), (1282, RD + 3), (1290, RD + 26), (1190, RD + 26)]
    put(s, Q(s, gq), INKBLUE, 0.8, lift=0.4, wob=0.8, edge=0.5, ew=3)
    path(s, gq, 1.8, SEPIA, 1.5, closed=True, over=3, r=r)
    for xx in np.arange(1206, 1280, 10.5):
        seg(s, (xx, RD + 5), (xx + (xx - 1238) * 0.08, RD + 24), 1.6, SEPIA, 1.4, r=r)
    hl(s, [(1198, RD + 4), (1280, RD + 4)], 1.6, 0.4)
    mh = s.ellipse(2560, 1566, 78, 17)
    s.wash(mh, UMBER, 0.3, wob=1, soft=1, edge=0.6, ew=3, clip=rm)
    s.lift(s.ellipse(2540, 1562, 40, 6), 0.2, soft=3)
    oval(s, 2560, 1566, 78, 17, 1.8, SEPIA, 1.4, twice=True)
    oval(s, 2560, 1566, 64, 13, 1.1, SEPIA, 1.0, skip=0.2)
    for xx in np.arange(2510, 2612, 14):
        seg(s, (xx, 1558), (xx + 8, 1574), 1.0, SEPIA, 0.9, r=r, skip=0.2)
    # ---- the A-board on the pavement, turned a little toward the door light
    ax, ay = 2452, 1326
    fr = [(ax - 30, ay - 126), (ax + 26, ay - 132), (ax + 31, ay - 6), (ax - 34, ay)]
    s.wash(Q(s, [(ax - 36, ay - 2), (ax + 34, ay - 8), (ax + 70, ay + 22), (ax - 20, ay + 26)]), SEPIA, 0.5, wob=3, bleed=7, edge=0.1)   # its shadow, thrown away from the door
    bk = [(ax + 26, ay - 132), (ax + 44, ay - 124), (ax + 50, ay - 14), (ax + 31, ay - 6)]
    put(s, Q(s, bk), SEPIA, 1.0, lift=0.5, wob=0.8, edge=0.4, ew=2)
    fm = Q(s, fr)
    put(s, fm, UMBER, 0.95, lift=0.9, wob=0.8, edge=0.4, ew=3)
    inner = [(ax - 23, ay - 117), (ax + 20, ay - 122), (ax + 24, ay - 26), (ax - 26, ay - 21)]
    im = Q(s, inner)
    s.wash(im, INKBLUE, 0.9, wob=0.8, soft=0.8, edge=0.4, ew=3, flow=0.6, fs=20)
    for _ in range(5):                               # chalk, rubbed out and rained on
        cy2 = U(r, ay - 108, ay - 40)
        s.wash(s.ribbon([(ax - 18, cy2), (ax, cy2 + J(r, 3)), (ax + 16, cy2 + J(r, 3))], U(r, 4, 8), taper=(0.2, 0.3)), None, U(r, 0.12, 0.26), wob=1.5, soft=1.5, edge=0, gran=0.5, flow=0, lift=True, dry=0.4, clip=im)
    hl(s, [(ax - 32, ay - 122), (ax - 35, ay - 6)], 3.0, 0.45)
    s.wash(s.ribbon([(ax - 32, ay - 122), (ax - 35, ay - 6)], 4, smooth=False), AMBER, 0.3, wob=0, soft=0.8, edge=0)
    path(s, fr, 2.0, SEPIA, 1.5, closed=True, over=3, r=r)
    path(s, inner, 1.2, SEPIA, 1.2, closed=True, over=2, r=r)
    path(s, bk, 1.5, SEPIA, 1.4, closed=True, over=2, r=r)
    for fx in (ax - 33, ax + 30, ax + 50):
        s.ink([(fx, ay - 8), (fx + (-2 if fx < ax else 2), ay + 5)], 2.6, SEPIA, 1.6)
    # ---- splashes: specks of light on the wet, a few dark flecks
    s.spatter(150, None, 0.5, box=(0, RD + 6, W, H), r=(0.8, 2.4), lift=True)
    s.spatter(60, None, 0.4, box=(0, PAVE + 6, W, KERB - 4), r=(0.7, 1.8), lift=True)
    s.spatter(70, INKBLUE, 0.35, box=(0, RD + 6, W, H), r=(0.8, 2.6))
    line(s, r, (-10, PAVE), (1392, PAVE + 1), 2.2, SEPIA, 1.4, dbl=0.5)
    line(s, r, (2408, PAVE), (W + 10, PAVE + 1), 2.2, SEPIA, 1.4, dbl=0.5)
    line(s, r, (-10, RD), (W + 10, RD + 1), 1.6, SEPIA, 1.2, skip=0.15)
    S.body[PAVE:, :] = 1.0
    S.save("st_road", q=90, meta={"pave_y": PAVE, "kerb_y": KERB, "road_y": RD, "vp": list(VP)})


LIT_GUESS = [(94, 631, 155, 710), (712, 573, 798, 694), (2477, 490, 2558, 597), (2244, 460, 2333, 583)]   # = st_main "lit", for when the road is painted on its own


# ---------------------------------------------------------------------------------------------- near things
def iron(s, m, k=1.0, c=SEPIA, c2=INKBLUE, wob=0.45):
    """Wet black ironwork up close: the darkest thing in the picture, but two pigments, not one flat black."""
    m = s.wash(m, c, 1.05 * k, wob=wob, soft=0.8, edge=0.4, ew=4, flow=0.45, fs=70, gran=0.4, body=1)
    s.wash(m, c2, 0.7 * k, wob=1.5, soft=1.5, edge=0.2, flow=0.8, fs=40, gran=0.4, clip=m)
    return m


def lamp():
    """An old cast-iron street lamp: fluted base, tapering shaft, ladder bar, a swan-neck and a hanging lantern.
    Anchor = the middle of the lantern glass."""
    s = Off(420, 1500, 0, 0, 46)
    r = rs(46)
    PX, LX, LY, Z = 122, 322, 252, 1.2
    Lp = lambda dx, dy: (LX + dx * Z, LY + dy * Z)                 # lantern coordinates, from the top of its glass
    hw = lambda y: 15 + 10 * (y - 330) / 926.0                    # half-width of the shaft at height y
    arm = [(PX, 336), (PX + 1, 250), (PX + 22, 150), (PX + 84, 84), (PX + 160, 80), (LX - 5, 124), (LX, 178)]
    # the swan-neck and its scrolls
    iron(s, s.ribbon(arm, 19, profile=lambda t: 1 - 0.45 * t))
    scroll = [(PX + 8, 318), (PX + 50, 298), (PX + 78, 252), (PX + 64, 208), (PX + 34, 212), (PX + 30, 244), (PX + 50, 254)]
    iron(s, s.ribbon(scroll, 11, profile=lambda t: 1 - 0.5 * t))
    sc2 = [(PX + 98, 88), (PX + 124, 120), (PX + 156, 128), (PX + 172, 108), (PX + 156, 98)]
    iron(s, s.ribbon(sc2, 8, profile=lambda t: 1 - 0.5 * t))
    # shaft, collars, ladder bar
    iron(s, Q(s, [(PX - hw(1256), 1256), (PX - hw(330), 330), (PX + hw(330), 330), (PX + hw(1256), 1256)]))
    for y, ex, hh in ((1250, 10, 10), (1168, 7, 8), (880, 7, 9), (860, 4, 5), (430, 7, 8), (336, 9, 10)):
        iron(s, s.rect(PX - hw(y) - ex, y - hh, PX + hw(y) + ex, y + hh))
    bar = s.rect(PX - 70, 397, PX + 70, 409)
    iron(s, np.maximum(bar, np.maximum(s.ellipse(PX - 72, 403, 9, 9), s.ellipse(PX + 72, 403, 9, 9))))
    # base: a bell on a square plinth
    bell = [(PX - 60, 1446), (PX - 55, 1404), (PX - 38, 1362), (PX - 31, 1304), (PX - 28, 1256), (PX + 28, 1256), (PX + 31, 1304), (PX + 38, 1362), (PX + 55, 1404), (PX + 60, 1446)]
    iron(s, Q(s, bell))
    iron(s, s.rect(PX - 70, 1444, PX + 70, 1494))
    # the lantern: a vented cap, a tapering glass cage, a drop finial
    cap = [Lp(-11, -50), Lp(11, -50), Lp(15, -36), Lp(50, -10), Lp(53, 0), Lp(-53, 0), Lp(-50, -10), Lp(-15, -36)]
    glass = [Lp(-46, 0), Lp(46, 0), Lp(30, 98), Lp(-30, 98)]
    foot = [Lp(-33, 98), Lp(33, 98), Lp(26, 110), Lp(8, 116), Lp(0, 134), Lp(-8, 116), Lp(-26, 110)]
    gm = Q(s, glass)
    s.wash(gm, OCHRE, 0.24, wob=0.8, soft=0.8, edge=0.4, ew=5, flow=0.4, fs=30, body=1)
    cx, cy = Lp(0, 50)
    s.wash(gm, AMBER, 0.16, wob=1, soft=3, edge=0, grad=s.rgrad(cx, cy, 16, 74, 0, 1))
    s.lift(s.ellipse(cx, cy, 15, 24), 0.9, soft=5)                                   # the mantle: bare paper
    iron(s, Q(s, cap))
    iron(s, Q(s, foot))
    iron(s, s.ellipse(*Lp(0, -57), 8, 9))
    for a, b in ((Lp(-46, 0), Lp(-30, 98)), (Lp(46, 0), Lp(30, 98))):
        iron(s, s.ribbon([a, b], 9, smooth=False))
    for a, b in ((Lp(-16, 2), Lp(-10, 98)), (Lp(16, 2), Lp(10, 98))):
        s.ink([a, b], 3.0, SEPIA, 1.5, tremor=0.5)
    s.ink([Lp(-40, 36), Lp(40, 36)], 1.5, SEPIA, 1.0, skip=0.15)
    # wet edges: the sky down the left of the shaft, the lamp's own light under the neck and on the cap's skirt
    hl(s, [(PX - hw(1240) + 7, 1240), (PX - hw(345) + 5, 345)], 3.6, 0.34, dry=0.25)
    hl(s, [(PX - 50, 1440), (PX - 31, 1362), (PX - 23, 1262)], 3.4, 0.3, dry=0.25)
    hl(s, [(PX - 66, 1449), (PX + 66, 1449)], 2.6, 0.3)
    hl(s, [(PX - 68, 399), (PX + 68, 399)], 2.2, 0.3)
    for y in (1242, 1162, 873, 424, 328):
        hl(s, [(PX - hw(y) - 4, y), (PX + 6, y)], 2.2, 0.3)
    hl(s, [(PX - 6, 300), (PX - 5, 250), (PX + 15, 152), (PX + 82, 76)], 3.0, 0.3)
    for pts, w_, g in (([(PX + 60, 100), (PX + 160, 90), (LX - 11, 128), (LX - 7, 176)], 6, None), ([Lp(-49, -3), Lp(49, -3)], 5, None),
                       ([(PX + hw(345) - 5, 345), (PX + hw(560) - 5, 560), (PX + hw(800) - 5, 800)], 5, s.vgrad(340, 800, 1, 0))):
        wm = s.ribbon(pts, w_, smooth=len(pts) > 2)
        s.wash(wm, None, 0.42, wob=0, soft=1, edge=0, lift=True, gran=0.2, flow=0, grad=g)
        s.wash(wm, AMBER, 0.5, wob=0, soft=1, edge=0, grad=g)
    # pen: flutes, mouldings, outlines that overshoot
    for q in (-0.55, -0.2, 0.15, 0.5):
        s.ink([(PX + q * 54, 1440), (PX + q * 36, 1364), (PX + q * 28, 1262)], 1.4, INK, 1.2, skip=0.15)
    for q in (-0.35, 0.3):
        s.ink([(PX + q * 24, 1240), (PX + q * 19, 800), (PX + q * 16, 440)], 1.3, INK, 0.9, skip=0.3, tremor=1.0)
    path(s, bell, 2.4, INK, 1.5, over=3, r=r)
    box(s, r, PX - 70, 1444, PX + 70, 1494, 2.4, INK, 1.5, over=4, dbl=0.5)
    line(s, r, (PX - hw(1256), 1256), (PX - hw(330), 330), 2.2, INK, 1.4, dbl=0.4)
    line(s, r, (PX + hw(1256), 1256), (PX + hw(330), 330), 2.4, INK, 1.5, dbl=0.4)
    path(s, cap + [cap[0]], 2.2, INK, 1.5, over=2, r=r)
    path(s, glass, 2.0, INK, 1.4, closed=True, over=3, r=r)
    path(s, foot + [foot[0]], 2.0, INK, 1.4, over=2, r=r)
    s.save("st_lamp", crop=True, anchor=(cx, cy), q=92)


def bike():
    """A town bicycle with a basket, leant on a street railing; dark, wet, close. Anchor = on the ground between the wheels."""
    s = Off(1040, 720, 0, 0, 47)
    r = rs(47)
    GY = 646
    # its shadow and the wet under it
    s.wash(s.ellipse(520, GY + 5, 470, 13), INKBLUE, 0.55, wob=2, soft=7, edge=0)
    s.wash(s.ellipse(514, GY + 3, 300, 7), SEPIA, 0.6, wob=2, soft=4, edge=0)
    # the railing behind: posts with ball tops, two rails, plain bars
    for px in (64, 368, 672, 976):
        iron(s, np.maximum(s.rect(px - 9, 212, px + 9, GY), s.ellipse(px, 198, 13, 14)), 0.8, PAYNE, SEPIA)
        iron(s, s.rect(px - 13, 222, px + 13, 232), 0.8, PAYNE, SEPIA)
        hl(s, [(px - 5, 236), (px - 5, GY - 10)], 2.4, 0.26, dry=0.3)
        hl(s, [(px - 5, 190), (px - 3, 196)], 3, 0.4)
        oval(s, px, 198, 13, 14, 1.6, INK, 1.3)
        line(s, r, (px - 9, 232), (px - 9, GY), 1.6, INK, 1.2)
        line(s, r, (px + 9, 232), (px + 9, GY), 1.8, INK, 1.3)
    for ry_, w_ in ((262, 9), (596, 9)):
        iron(s, s.rect(20, ry_ - w_ / 2, 1020, ry_ + w_ / 2), 0.8, PAYNE, SEPIA)
        hl(s, [(24, ry_ - w_ / 2 + 1), (1016, ry_ - w_ / 2 + 1)], 1.8, 0.34, dry=0.2)
        line(s, r, (18, ry_ + w_ / 2), (1022, ry_ + w_ / 2), 1.5, INK, 1.2, dbl=0.4)
    x = 96.0
    while x < 1000:
        if min(abs(x - px) for px in (64, 368, 672, 976)) > 22:
            s.stroke([(x + J(r, 1), 264), (x + J(r, 1.5), 430), (x + J(r, 1), 594)], 4.5, PAYNE, 1.0, wob=0.4, edge=0.4, taper=(0, 0), body=1)
            s.ink([(x + 2.2, 266), (x + 2.2 + J(r, 1), 592)], 1.1, SEPIA, 1.1, skip=0.1)
        x += U(r, 42, 50)
    # the bicycle
    RW, FW, RR = (300, 492), (728, 492), 148
    BB, ST, HT, HB = (480, 498), (432, 300), (668, 286), (684, 350)
    def tube(pts, w, k=1.0, **kw):
        m = s.ribbon(pts, w, **kw)
        iron(s, m, k)
        return m
    for c in (RW, FW):
        tube(ell(c[0], c[1], RR, RR, 0, 2 * math.pi, 40), 13, closed=True)                    # tyre
        s.ink(ell(c[0], c[1], RR - 11, RR - 11, 0.2, 0.2 + 2 * math.pi + 0.2, 60), 1.3, INK, 1.1, skip=0.08)
        a0 = U(r, 0, 1)
        for i in range(16):
            a = a0 + i * math.pi / 8 + J(r, 0.04)
            hx, hy = c[0] + math.cos(a + 1.2) * 7, c[1] + math.sin(a + 1.2) * 7
            s.ink([(hx, hy), (c[0] + math.cos(a) * (RR - 10), c[1] + math.sin(a) * (RR - 10))], 1.0, INKBLUE, 1.0, skip=0.12, tremor=0.4, taper=(0.02, 0.02))
        iron(s, s.ellipse(c[0], c[1], 11, 11))
        hl(s, ell(c[0], c[1], RR + 3, RR + 3, 3.5, 4.5, 14), 2.2, 0.3)
    tube(ell(RW[0], RW[1], RR + 13, RR + 13, 2.7, 6.2, 30), 6)                                # mudguards
    tube(ell(FW[0], FW[1], RR + 13, RR + 13, 3.6, 5.9, 30), 6)
    hl(s, ell(RW[0], RW[1], RR + 15, RR + 15, 3.6, 5.2, 20), 1.8, 0.4)
    hl(s, ell(FW[0], FW[1], RR + 15, RR + 15, 4.0, 5.2, 16), 1.8, 0.4)
    tube([BB, RW], 7)                                                                         # chain stay
    tube([ST, RW], 6)                                                                         # seat stay
    tube([BB, ST, (424, 262)], 11, smooth=False)                                              # seat tube and post
    tube([(672, 318), (604, 372), (512, 418), (446, 426)], 10)                                # the swooping top tube
    tube([HB, (590, 424), BB], 11)                                                            # down tube
    tube([(664, 262), HT, HB], 12, smooth=False)                                              # head tube
    tube([HB, (704, 420), FW], 8)                                                             # fork
    tube([(664, 262), (650, 240), (612, 236), (572, 250)], 7)                                 # swept-back bar
    tube([(586, 246), (566, 252)], 12, smooth=False)                                          # grip
    hl(s, [(668, 320), (604, 368), (514, 412)], 2.2, 0.36)
    hl(s, [(680, 352), (590, 420), (486, 492)], 2.0, 0.22)
    sad = [(376, 262), (420, 252), (474, 254), (482, 264), (446, 276), (384, 276)]
    iron(s, s.poly(sad))
    hl(s, [(384, 258), (420, 250), (468, 252)], 2.4, 0.36)
    s.ink([(400, 276), (408, 290), (398, 296), (410, 304)], 1.3, INK, 1.2)
    tube([(286, 334), (436, 326)], 6, smooth=False)                                           # rack
    s.ink([(292, 336), (300, 480)], 1.6, INK, 1.3)
    s.ink([(350, 334), (304, 484)], 1.4, INK, 1.2)
    cg = [(292, 474), (470, 462), (508, 480), (508, 506), (476, 520), (294, 506)]             # chain case
    iron(s, s.poly(cg), 0.95)
    hl(s, [(300, 477), (468, 466)], 1.8, 0.3)
    s.ink(spline(cg, True), 1.5, INK, 1.2, smooth=False)
    tube([BB, (512, 566)], 7, smooth=False)                                                   # crank and pedal
    iron(s, s.rect(494, 562, 538, 574))
    tube([(446, 506), (414, GY - 2)], 5, smooth=False)                                        # stand
    # the basket: wicker, a shade lighter, the weave drawn
    bk = [(692, 226), (806, 222), (794, 318), (702, 320)]
    bm = Q(s, bk)
    bm = s.wash(bm, UMBER, 0.95, wob=1.2, soft=0.8, edge=0.5, ew=4, flow=0.6, fs=40, gran=0.5, body=1)
    s.wash(bm, INKBLUE, 0.45, wob=1.5, soft=2, edge=0, grad=s.hgrad(700, 800, 0.2, 1), clip=bm)
    for i in range(1, 9):
        yy = 226 + i * 10.5
        s.ink([(694 + i * 0.9, yy), (750, yy + J(r, 1.5)), (804 - i * 1.1, yy - 1)], 1.1, INK, 1.0, skip=0.15, tremor=0.9, clip=bm)
    for i in range(1, 10):
        xx = 692 + i * 11.4
        s.ink([(xx, 226), (xx + (750 - xx) * 0.08, 318)], 1.0, INK, 0.8, skip=0.3, clip=bm)
    hl(s, [(694, 228), (804, 224)], 3, 0.34)
    path(s, bk, 2.0, INK, 1.5, closed=True, over=3, r=r)
    s.ink([(760, 320), (744, 400), (728, 488)], 1.6, INK, 1.3)                                # basket stay
    lm = s.ellipse(700, 344, 9, 10)                                                           # a dead front lamp
    s.wash(lm, MIST, 0.5, wob=0.5, soft=0.8, edge=0.5, ew=2, body=1)
    s.wash(lm, PAYNE, 0.4, wob=0.5, soft=1.5, grad=s.hgrad(692, 710))
    oval(s, 700, 344, 9, 10, 1.3, INK, 1.3)
    s.save("st_fg_bike", crop=True, anchor=(514, GY), q=92)


def branch():
    """A bare wet branch reaching in from the top-right corner, a few leaves still on. Anchor = that corner of its sheet."""
    BW, BH = 1200, 720
    s = Off(BW, BH, 0, 0, 48)
    r = rs(48)
    leaves = []

    def twig(p0, ang, ln, w, depth):
        bend = J(r, 0.35)
        pts = [p0]
        a = ang
        for i in range(4):
            a += bend / 4 + J(r, 0.06)
            pts.append((pts[-1][0] + math.cos(a) * ln / 4, pts[-1][1] + math.sin(a) * ln / 4))
        m = s.ribbon(pts, w, profile=lambda t: 1 - 0.6 * t)
        iron(s, m, 0.95, SEPIA, INKBLUE)
        s.ink([(p[0] + w * 0.22, p[1] + w * 0.3) for p in pts], max(1.0, w * 0.13), INK, 1.2, skip=0.12, tremor=0.9)
        if w > 7:
            hl(s, [(p[0] - w * 0.15, p[1] - w * 0.3) for p in pts], max(1.4, w * 0.14), 0.3, dry=0.3)
        if depth > 0:
            for q in ((0.45, 0.8) if depth > 1 else (0.6,)):
                i = int(q * 4)
                sd = 1 if r.random() < 0.5 else -1
                twig(pts[i], a + sd * U(r, 0.45, 0.95), ln * U(r, 0.5, 0.72), w * 0.55, depth - 1)
        if depth <= 1:
            leaves.append((pts[-1], a))
            for _ in range(int(r.integers(1, 4))):            # the finest twigs, pen only
                i = int(r.integers(1, 5))
                aa = a + J(r, 1.1)
                l2 = U(r, 26, 70)
                q0 = pts[i]
                s.ink([q0, (q0[0] + math.cos(aa) * l2 * 0.5 + J(r, 3), q0[1] + math.sin(aa) * l2 * 0.5 + J(r, 3)), (q0[0] + math.cos(aa + 0.2) * l2, q0[1] + math.sin(aa + 0.2) * l2)],
                      U(r, 1.6, 2.6), INK, 1.5, taper=(0.02, 0.5), tremor=0.8)
        return pts

    main = [(BW + 20, -10), (1080, 70), (930, 128), (780, 196), (640, 286), (520, 392), (430, 500)]
    mm = s.ribbon(main, 58, profile=lambda t: (1 - t) ** 0.9 * 0.9 + 0.1)
    iron(s, mm, 1.0)
    for _ in range(26):                              # bark
        t = U(r, 0.02, 0.8)
        i = min(len(main) - 2, int(t * (len(main) - 1)))
        f = t * (len(main) - 1) - i
        px_, py_ = main[i][0] + (main[i + 1][0] - main[i][0]) * f, main[i][1] + (main[i + 1][1] - main[i][1]) * f
        dx, dy = main[i + 1][0] - main[i][0], main[i + 1][1] - main[i][1]
        L = math.hypot(dx, dy)
        o = J(r, 20 * (1 - t))
        a0 = (px_ - dy / L * o, py_ + dx / L * o)
        s.ink([a0, (a0[0] + dx / L * U(r, 20, 60), a0[1] + dy / L * U(r, 20, 60) + J(r, 3))], U(r, 1.0, 1.8), INK, 1.1, skip=0.2, tremor=1.0, clip=mm)
    hl(s, [(1150, 28), (1040, 62), (900, 116), (770, 176), (640, 262)], 4, 0.3, dry=0.35)
    s.ink([(p[0] + 4, p[1] + 20 * (1 - i / 7)) for i, p in enumerate(main)], 2.2, INK, 1.4, skip=0.08)
    twig((1010, 100), 2.0, 300, 20, 2)
    twig((860, 160), 3.6, 260, 17, 2)
    twig((710, 240), 1.75, 250, 15, 2)
    twig((600, 318), 3.5, 240, 13, 2)
    twig((500, 420), 2.9, 230, 11, 1)
    twig((430, 500), 2.2, 170, 9, 1)
    twig((1120, 50), 1.5, 210, 18, 1)
    twig((940, 126), 3.9, 150, 10, 1)
    # the last leaves, hanging heavy; a drop at some tips
    for (p, a) in leaves:
        if r.random() < 0.3:
            continue
        an = math.pi / 2 + J(r, 0.6)
        ln, wd = U(r, 46, 78), U(r, 16, 26)
        ca, sa = math.cos(an), math.sin(an)
        tip = (p[0] + ca * ln, p[1] + sa * ln)
        lp = [p, (p[0] + ca * ln * 0.4 - sa * wd * 0.5, p[1] + sa * ln * 0.4 + ca * wd * 0.5), tip, (p[0] + ca * ln * 0.45 + sa * wd * 0.5, p[1] + sa * ln * 0.45 - ca * wd * 0.5)]
        lm = s.poly(lp)
        u = r.random()
        c1 = MOSS if u < 0.55 else (BURNT if u < 0.85 else OCHRE)
        lm = s.wash(lm, c1, 1.0, wob=1, soft=0.8, edge=0.5, ew=3, flow=0.5, fs=20, gran=0.4, body=1)
        s.wash(lm, SEPIA if u < 0.55 else UMBER, 0.6, wob=1, soft=1.5, edge=0.2, grad=s.rgrad(tip[0], tip[1], 6, ln, 1, 0.3), clip=lm)
        s.wash(lm, INKBLUE, 0.35, wob=1, soft=1.5, edge=0, clip=lm)
        hl(s, [(p[0] + ca * 8 - sa * 3, p[1] + sa * 8 + ca * 3), (p[0] + ca * ln * 0.6 - sa * 4, p[1] + sa * ln * 0.6 + ca * 4)], 2.0, 0.3)
        s.ink([p, (p[0] + ca * ln * 0.5 + J(r, 2), p[1] + sa * ln * 0.5), tip], 1.2, INK, 1.2, skip=0.05)
        s.ink(spline(lp, True), 1.3, INK, 1.2, smooth=False, skip=0.1)
        if r.random() < 0.5:
            dm = s.ellipse(tip[0], tip[1] + 7, 3.2, 5)
            s.wash(dm, RAIN, 0.4, wob=0, soft=0.6, edge=0.6, ew=1.5, body=1)
            s.ink(ell(tip[0], tip[1] + 7, 3.4, 5.2, 0.6, 5.9, 12), 0.9, INK, 1.1)
    s.save("st_fg_branch", crop=True, anchor=(BW, 0), q=92)


def fg():
    bike()
    branch()


ALL = {"street_sky": sky, "street_far": far, "street_main": main, "street_inside": inside, "street_road": road, "street_lamp": lamp, "street_fg": fg}
