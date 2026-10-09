"""The whole café in one look: 「整家店 安静的自由」. One-point perspective from just inside the door.
Sheet 3456x1944. The lamps, the person and the coat are added by the page (they move); their light is painted here."""
import math

import cv2
import numpy as np

from kit import *

SW, SH = 3456, 1944
VP = (1850, 800)
BX0, BX1, BY0, BY1 = 900, 2800, 420, 1150          # the back wall


def to_vp(p, x):
    """y at abscissa x on the line from p to the vanishing point."""
    return p[1] + (VP[1] - p[1]) * (x - p[0]) / (VP[0] - p[0])


def lwall(x, f):
    """Point on the left wall at abscissa x, f = 0 (ceiling) .. 1 (floor)."""
    return (x, lerp(to_vp((BX0, BY0), x), to_vp((BX0, BY1), x), f))


def rwall(x, f):
    return (x, lerp(to_vp((BX1, BY0), x), to_vp((BX1, BY1), x), f))


def lerp(a, b, u):
    return a + (b - a) * u


def fsc(y):
    """Scale of things standing on the floor at screen height y (1 at the back wall)."""
    return (y - VP[1]) / (BY1 - VP[1])


LAMPS = [(1300, 700, 0.62), (2350, 690, 0.62), (1850, 610, 0.85), (900, 520, 1.25), (2740, 560, 1.15), (1780, 330, 1.9)]   # bulb x, y, scale
TABLES = [(1420, 1215, 0), (2150, 1235, 1), (2700, 1205, 2), (760, 1330, 3), (1700, 1440, 4), (2560, 1560, 5), (760, 1750, 6)]
SEAT = {"table": [2700, 1205], "fig": [2575, 1262], "coat": [2835, 1178], "sc": 1.16}


def small_table(s, x, y, seed=0, bare=False):
    sc = fsc(y)
    h, rx = 252 * sc, 138 * sc
    ry = rx * (0.20 + 0.05 * sc)
    s.wash(s.ellipse(x + 34 * sc, y + 10 * sc, rx * 1.05, ry * 1.0), SEPIA, 0.32, wob=3, bleed=10 * sc, edge=0.1)
    foot = s.ellipse(x, y, 64 * sc, 17 * sc)
    base(s, foot, UMBER, 1.1, wob=1.2, edge=0.5)
    oval(s, x, y, 64 * sc, 17 * sc, max(1.4, 1.6 * sc), INK, 1.3)
    ped = s.poly([(x - 12 * sc, y - h + 6), (x + 12 * sc, y - h + 6), (x + 9 * sc, y - 60 * sc), (x + 20 * sc, y - 4 * sc), (x - 20 * sc, y - 4 * sc), (x - 9 * sc, y - 60 * sc)], smooth=False)
    base(s, ped, UMBER, 1.15, wob=1, edge=0.5)
    s.wash(ped, SEPIA, 0.5, wob=1, soft=2, grad=s.hgrad(x - 4 * sc, x + 20 * sc))
    contour(s, ped, max(1.3, 1.5 * sc), INK, 1.3)
    rimm = s.ellipse(x, y - h + 13 * sc, rx, ry)
    base(s, rimm, UMBER, 1.1, wob=1, edge=0.4)
    top = s.ellipse(x, y - h, rx, ry)
    wood(s, top, SIENNA, BURNT, 0.75, ang=0.0, n=int(8 + 6 * sc), seed=seed + 50, lw=1.0 + 0.2 * sc, wob=1.2)
    s.lift(s.ellipse(x - rx * 0.1, y - h - ry * 0.1, rx * 0.6, ry * 0.5), 0.5, soft=6 * sc, wob=2)        # the lamp lying on it
    oval(s, x, y - h, rx, ry, max(1.6, 1.9 * sc), INK, 1.4, twice=sc > 1.3)
    s.ink(ell(x, y - h + 13 * sc, rx, ry, 0.1, math.pi - 0.1, 24), max(1.3, 1.5 * sc), INK, 1.2)
    if not bare:           # a sugar bowl, a folded card
        bx, by = x + rx * 0.3, y - h - ry * 0.15
        bowl = s.ellipse(bx, by, 17 * sc, 9 * sc)
        base(s, bowl, CREAM, 0.3, wob=0.6)
        s.wash(s.ellipse(bx, by, 17 * sc, 9 * sc) * (1 - s.ellipse(bx, by - 2 * sc, 13 * sc, 6 * sc)), TEAL, 0.9, wob=0.5, soft=1)
        oval(s, bx, by, 17 * sc, 9 * sc, max(1.1, 1.2 * sc), INK, 1.1)
    return (x, y - h)


def small_chair(s, x, y, face, seed=0):
    """A bentwood chair standing at (x, y) on the floor. face: 'L' / 'R' it faces left / right (seen side-on),
    'F' it faces us, 'B' its back is to us."""
    sc = fsc(y)
    w = max(1.4, 2.0 * sc)
    sh, sr = 148 * sc, 60 * sc
    seat_y = y - sh
    s.wash(s.ellipse(x + 26 * sc, y + 6 * sc, sr * 1.2, 14 * sc), SEPIA, 0.3, wob=2, bleed=8 * sc, edge=0.1)

    def stick(a, b, ww=None, bow=0.0):
        ww = ww or 11 * sc
        mid = ((a[0] + b[0]) / 2 + bow, (a[1] + b[1]) / 2)
        m = s.ribbon([a, mid, b], ww)
        base(s, m, UMBER, 1.15, wob=0.8, edge=0.5)
        s.wash(m, SEPIA, 0.4, wob=0.8, soft=1.5)
        s.ink([a, mid, b], w * 0.75, INK, 1.1, tremor=0.5)
        return m
    side = face in ("L", "R")
    d = -1 if face == "L" else 1
    if side:
        # back leg + back post in one bent piece at the rear, front leg at the front
        rear, front = x - d * sr * 0.85, x + d * sr * 0.85
        stick((rear - d * 8 * sc, y), (rear, seat_y), bow=-d * 4 * sc)
        stick((front + d * 6 * sc, y), (front, seat_y))
        stick((rear, seat_y), (rear - d * 26 * sc, seat_y - 190 * sc), bow=d * 10 * sc)
        stick((rear - d * 2 * sc, seat_y - 24 * sc), (rear - d * 20 * sc, seat_y - 150 * sc), ww=8 * sc, bow=d * 16 * sc)
        seat = s.ellipse(x, seat_y, sr, 15 * sc)
    else:
        for dx in (-0.8, 0.8):
            stick((x + dx * sr * 1.12, y - 6 * sc * (face == "B")), (x + dx * sr * 0.9, seat_y))
        for dx in (-0.6, 0.6):
            stick((x + dx * sr, y - 20 * sc + 14 * sc * (face == "B")), (x + dx * sr * 0.8, seat_y), ww=9 * sc)
        hoop = [(x - sr * 0.92, seat_y), (x - sr * 0.98, seat_y - 120 * sc), (x - sr * 0.6, seat_y - 196 * sc), (x, seat_y - 216 * sc), (x + sr * 0.6, seat_y - 196 * sc), (x + sr * 0.98, seat_y - 120 * sc), (x + sr * 0.92, seat_y)]
        inner = [(x - sr * 0.56, seat_y), (x - sr * 0.6, seat_y - 100 * sc), (x, seat_y - 160 * sc), (x + sr * 0.6, seat_y - 100 * sc), (x + sr * 0.56, seat_y)]
        seat = s.ellipse(x, seat_y, sr, 19 * sc)
        if face == "F":
            for P, ww in ((hoop, 11 * sc), (inner, 8 * sc)):
                m = s.ribbon(P, ww)
                base(s, m, UMBER, 1.15, wob=0.8, edge=0.5)
                s.ink(P, w * 0.75, INK, 1.1, tremor=0.5)
    base(s, seat, UMBER, 1.0, wob=1, edge=0.5)
    s.wash(seat, SIENNA, 0.4, wob=1, soft=2, grad=s.rgrad(x - sr * 0.2, seat_y - 3, 4, sr, 1, 0, sy=0.3))
    oval(s, x, seat_y, sr, (15 if side else 19) * sc, w, INK, 1.3)
    if face == "B":
        for P, ww in ((hoop, 11 * sc), (inner, 8 * sc)):
            m = s.ribbon(P, ww)
            base(s, m, UMBER, 1.15, wob=0.8, edge=0.5)
            s.wash(m, SEPIA, 0.35, wob=0.8, soft=1.5)
            s.ink(P, w * 0.75, INK, 1.1, tremor=0.5)
    return (x, seat_y)


def room():
    s = Sheet(SW, SH, 81)
    r = rs(81)
    back = s.rect(BX0, BY0, BX1, BY1)
    left = Q(s, [(-10, to_vp((BX0, BY0), -10)), (BX0, BY0), (BX0, BY1), (-10, to_vp((BX0, BY1), -10))])
    right = Q(s, [(BX1, BY0), (SW + 10, to_vp((BX1, BY0), SW + 10)), (SW + 10, to_vp((BX1, BY1), SW + 10)), (BX1, BY1)])
    ceil = Q(s, [(-10, -10), (SW + 10, -10), (SW + 10, to_vp((BX1, BY0), SW + 10)), (BX1, BY0), (BX0, BY0), (-10, to_vp((BX0, BY0), -10))])
    floor = Q(s, [(-10, to_vp((BX0, BY1), -10)), (BX0, BY1), (BX1, BY1), (SW + 10, to_vp((BX1, BY1), SW + 10)), (SW + 10, SH + 10), (-10, SH + 10)])

    # ---- ceiling: warm dark, beams running to the vanishing point
    s.wash(ceil, SIENNA, 0.6, wob=0, edge=0, flow=0.5, fs=400, gran=0.4)
    s.wash(ceil, UMBER, 0.55, wob=0, edge=0, grad=s.vgrad(0, 420, 1, 0.3), flow=0.4)
    u = (BY0 + 10) / (VP[1] + 10)
    for x in range(-2600, SW + 2700, 330):
        seg(s, (x, -10), (x + (VP[0] - x) * u, BY0), 2.2, SEPIA, 1.0, skip=0.15, r=r, clip=ceil)

    # ---- walls: cream-ochre plaster, lamp-lit
    for m in (back, left, right):
        s.wash(m, CREAM, 0.5, wob=0, edge=0, flow=0.45, fs=380, gran=0.4)
        s.wash(m, OCHRE, 0.42, wob=0, edge=0, flow=0.5, fs=300, grad=0.6 + 0.4 * s.noise(340, 3))
    s.wash(left, SIENNA, 0.28, wob=0, edge=0, grad=s.hgrad(0, BX0, 1, 0.2))
    s.wash(right, UMBER, 0.30, wob=0, edge=0, grad=s.hgrad(BX1, SW, 0.3, 1))
    s.wash(back, UMBER, 0.18, wob=0, edge=0, grad=s.vgrad(BY0, BY0 + 200, 1, 0))
    # wainscot on all three, with the dado rail
    wf = 0.60
    wl = Q(s, [lwall(-10, wf), lwall(BX0, wf), (BX0, BY1), (-10, to_vp((BX0, BY1), -10))])
    wb = s.rect(BX0, lerp(BY0, BY1, wf), BX1, BY1)
    wr = Q(s, [rwall(BX1, wf), rwall(SW + 10, wf), (SW + 10, to_vp((BX1, BY1), SW + 10)), (BX1, BY1)])
    for m, g in ((wl, s.hgrad(0, BX0, 0.5, 0.15)), (wb, 0.2), (wr, s.hgrad(BX1, SW, 0.3, 0.7))):
        base(s, m, TEAL, 1.05, wob=1.5, edge=0.3, flow=0.5, fs=240, gran=0.5)
        s.wash(m, PRUSSIAN, 0.7, wob=0, edge=0, grad=g if not np.isscalar(g) else s.full() * g, flow=0.3)
    for x in range(BX0 + 60, BX1, 118):
        seg(s, (x, lerp(BY0, BY1, wf) + 12), (x, BY1), 1.5, INKBLUE, 0.9, skip=0.15, r=r)
    for i in range(1, 12):
        x = BX0 * (1 - (i / 12) ** 1.5)
        seg(s, (lwall(x, wf)[0], lwall(x, wf)[1] + 8), lwall(x, 1), 1.6 + 1.2 * (1 - x / BX0), INKBLUE, 0.9, skip=0.15, r=r)
        x2 = BX1 + (SW - BX1) * (i / 12) ** 1.5 * 1.1
        if x2 < SW:
            seg(s, (rwall(x2, wf)[0], rwall(x2, wf)[1] + 8), rwall(x2, 1), 1.6 + 1.2 * (x2 - BX1) / 650, INKBLUE, 0.9, skip=0.15, r=r)
    for a, b, ta, tb in ((lwall(-10, wf), lwall(BX0, wf), 18, 9), (lwall(BX0, wf), rwall(BX1, wf), 9, 9), (rwall(BX1, wf), rwall(SW + 10, wf), 9, 18)):
        rail = Q(s, [(a[0], a[1] - ta), (b[0], b[1] - tb), (b[0], b[1] + 5), (a[0], a[1] + 5)])
        base(s, rail, OCHRE, 0.95, wob=0.8, edge=0.5)
        seg(s, a, b, 1.8, SEPIA, 1.2, r=r)
        seg(s, (a[0], a[1] + 5), (b[0], b[1] + 5), 1.8, SEPIA, 1.2, r=r)
    # room edges
    for a, b in (((BX0, BY0), (BX0, BY1)), ((BX1, BY0), (BX1, BY1)), ((BX0, BY0), (BX1, BY0)), ((BX0, BY1), (BX1, BY1)), ((BX0, BY0), (-10, to_vp((BX0, BY0), -10))),
                 ((BX1, BY0), (SW + 10, to_vp((BX1, BY0), SW + 10))), ((BX0, BY1), (-10, to_vp((BX0, BY1), -10))), ((BX1, BY1), (SW + 10, to_vp((BX1, BY1), SW + 10)))):
        seg(s, a, b, 2.4, INK, 1.3, r=r, over=6)

    # ---- floor: dark boards running to the vanishing point, herringbone hinted by short cross strokes
    base(s, floor, UMBER, 0.95, wob=1, edge=0.2, flow=0.5, fs=300, gran=0.5)
    s.wash(floor, SEPIA, 0.38, wob=0, edge=0, grad=s.vgrad(BY1, SH, 0.15, 1) * (0.6 + 0.4 * s.noise(300, 3)), flow=0.4)
    s.wash(floor, PRUSSIAN, 0.25, wob=0, edge=0, grad=s.hgrad(0, 1200, 1, 0))                    # window light, cool, from the left
    for i in range(-40, 41):
        x1 = VP[0] + i * 190
        a = (VP[0] + (x1 - VP[0]) * (BY1 - VP[1]) / (SH - VP[1]), BY1)
        seg(s, a, (x1, SH + 10), 1.4 + 0.02 * abs(i), SEPIA, 0.9, skip=0.2, r=r, clip=floor)
    for j in range(15):
        y = BY1 + 12 + (SH - BY1) * (j / 15) ** 1.7
        for i in range(-40, 41):
            k = (y - VP[1]) / (SH - VP[1])
            xa, xb = VP[0] + i * 190 * k, VP[0] + (i + 1) * 190 * k
            if xb < 0 or xa > SW or r.random() < 0.45:
                continue
            dy = 26 * k * (1 if (i + j) % 2 else -1)
            s.ink([(xa + 4, y - dy), (xb - 4, y + dy)], 1.2 + k, SEPIA, 0.5 + 0.3 * r.random(), skip=0.25, clip=floor, taper=(0.1, 0.1))

    # ---- left wall: three tall windows, the street soft behind them
    wins = []
    for xa, xb in ((40, 330), (400, 590), (650, 800)):
        q = [lwall(xa, 0.16), lwall(xb, 0.16), lwall(xb, 0.565), lwall(xa, 0.565)]
        m = Q(s, q)
        s.lift(m, 1.0, soft=0.8, wob=0.8)
        s.wash(m, RAIN, 0.7, wob=1, edge=0.2, flow=0.5, fs=160, body=1)
        s.wash(m, PRUSSIAN, 0.55, wob=2, bleed=14, grad=s.vgrad(q[0][1] + 150, q[3][1], 0.1, 1) * (0.5 + 0.5 * s.noise(120, 3)))
        for _ in range(int(10 * (xb - xa) / 200)):
            bx, by = lerp(xa, xb, r.random()), lerp(q[0][1], q[3][1], 0.35 + 0.6 * r.random())
            bm = s.blob(bx, by, 14 + 16 * r.random(), 16 + 16 * r.random(), 0.2) * m
            s.lift(bm, 0.7, soft=7)
            s.wash(bm, [AMBER, ROSE, OCHRE][int(r.random() * 3)], 0.35, wob=3, bleed=9, clip=m)
        fw = 0.07
        for u in (0.0, 0.5, 1.0):                        # jambs and one mullion
            x = lerp(xa, xb, u)
            ww = (xb - xa) * fw * (0.7 if u == 0.5 else 1)
            mem = Q(s, [lwall(x - ww / 2, 0.16), lwall(x + ww / 2, 0.16), lwall(x + ww / 2, 0.565), lwall(x - ww / 2, 0.565)])
            base(s, mem, UMBER, 1.1, wob=0.8, edge=0.4)
            contour(s, mem, 1.6, INK, 1.2)
        for f in (0.16, 0.27, 0.565):                    # head, transom, sill
            mem = Q(s, [lwall(xa - 10, f - 0.012), lwall(xb + 10, f - 0.012), lwall(xb + 10, f + 0.012), lwall(xa - 10, f + 0.012)])
            base(s, mem, UMBER if f < 0.5 else SIENNA, 1.1 if f < 0.5 else 0.9, wob=0.8, edge=0.4)
            contour(s, mem, 1.6, INK, 1.2)
        wins.append([[float(v) for v in p] for p in q])
        # the window's cool light lying on the floor
        fl = Q(s, [lwall(xa, 1.0), lwall(xb, 1.0), (xb + 520, lwall(xb, 1.0)[1] + 150), (xa + 640, lwall(xa, 1.0)[1] + 230)])
        s.lift(fl * floor, 0.22, soft=26, wob=6)

    # ---- back wall: shelves, the counter, the machine, a record player, the kitchen door
    door = s.rect(2470, 600, 2700, BY1)
    base(s, door, SEPIA, 1.15, wob=1.2, edge=0.4)
    s.wash(door, INKBLUE, 0.5, wob=2, bleed=12)
    cur = s.poly([(2470, 600), (2700, 600), (2690, 900), (2640, 1010), (2470, 1040)])
    base(s, cur, BURNT, 0.95, wob=2, edge=0.5, flow=0.5)
    for i in range(6):
        s.ink([(2490 + i * 38, 606), (2494 + i * 36, 820), (2486 + i * 30, 1020)], 1.5, SEPIA, 0.9, skip=0.2, clip=cur)
    path(s, [(2462, 592), (2708, 592), (2708, BY1), (2462, BY1)], 2.4, INK, 1.4, over=5, r=r)
    board = s.rect(1120, 470, 1640, 600)
    base(s, board, PAYNE, 1.15, wob=1.2, edge=0.4, flow=0.4)
    path(s, [(1112, 462), (1648, 462), (1648, 608), (1112, 608)], 3.0, UMBER, 1.4, closed=True, over=4, r=r)
    for j in range(4):                                   # chalk that says nothing
        for i in range(3):
            x0 = 1150 + i * 165
            s.lift(s.ribbon([(x0, 494 + j * 26), (x0 + 60 + 70 * r.random(), 494 + j * 26)], 5), 0.5, soft=1, wob=1.5)
    for sy, x0, x1 in ((640, 1100, 2330), (760, 1100, 2330)):
        sh = s.rect(x0, sy, x1, sy + 14)
        base(s, sh, UMBER, 1.1, wob=0.8, edge=0.4)
        contour(s, sh, 1.6, INK, 1.2)
        cast(s, sh, 4, 16, UMBER, 0.4, blur=7, clip=back)
        x = x0 + 26
        while x < x1 - 50:
            kind = r.random()
            if x > 1680 and sy == 640 and x < 1700:
                x += 30
            if kind < 0.45:                              # a cup, or two stacked
                for st in range(1 + int(r.random() * 2)):
                    cm = Q(s, [(x, sy - 30 - st * 22), (x + 40, sy - 30 - st * 22), (x + 34, sy - st * 22), (x + 6, sy - st * 22)])
                    base(s, cm, CREAM, 0.3, wob=0.6, edge=0.4)
                    s.wash(cm, [TEAL, RAIN, OCHRE][int(r.random() * 3)], 0.4, wob=0.6, soft=1.5, grad=s.hgrad(x, x + 40))
                    contour(s, cm, 1.3, INK, 1.2)
                x += 56
            elif kind < 0.75:                            # a jar
                h = 50 + 30 * r.random()
                jm = s.rect(x, sy - h, x + 36, sy)
                base(s, jm, [SIENNA, UMBER, MOSS, BURNT][int(r.random() * 4)], 0.85, wob=1, edge=0.5)
                s.lift(s.rect(x + 5, sy - h + 6, x + 10, sy - 8), 0.5, soft=1.5)
                lid = s.rect(x - 2, sy - h - 9, x + 38, sy - h)
                base(s, lid, OCHRE, 0.9, wob=0.6)
                contour(s, np.maximum(jm, lid), 1.3, INK, 1.2)
                x += 52
            else:                                        # a bottle
                h = 80 + 20 * r.random()
                bm = s.poly([(x + 8, sy - h), (x + 20, sy - h), (x + 20, sy - h + 26), (x + 28, sy - h + 44), (x + 28, sy), (x, sy), (x, sy - h + 44), (x + 8, sy - h + 26)], smooth=False)
                base(s, bm, [TEAL, UMBER, PRUSSIAN][int(r.random() * 3)], 0.9, wob=0.8, edge=0.5)
                contour(s, bm, 1.3, INK, 1.2)
                x += 46
    # counter
    ctop = Q(s, [(1040, 872), (2380, 872), (2410, 902), (1010, 902)])
    cfr = s.rect(1010, 902, 2410, BY1)
    cast(s, cfr, 30, 26, SEPIA, 0.5, blur=14, clip=floor)
    wood(s, cfr, UMBER, SEPIA, 1.0, ang=math.pi / 2, n=40, seed=8, wob=1)
    for x in range(1010, 2410, 140):
        path(s, [(x + 14, 924), (x + 126, 924), (x + 126, BY1 - 20), (x + 14, BY1 - 20)], 1.5, INK, 1.0, closed=True, over=3, r=r)
    wood(s, ctop, SIENNA, BURNT, 0.8, n=14, seed=9, wob=1)
    s.lift(Q(s, [(1500, 876), (2100, 876), (2110, 890), (1490, 890)]), 0.35, soft=5)
    contour(s, np.maximum(ctop, cfr), 2.4, INK, 1.4)
    seg(s, (1010, 902), (2410, 902), 1.8, INK, 1.2, r=r)
    # espresso machine
    mx0, my0, mx1, my1 = 1150, 690, 1500, 872
    mb = s.poly([(mx0, my0 + 30), (mx0 + 20, my0), (mx1 - 20, my0), (mx1, my0 + 30), (mx1, my1), (mx0, my1)], smooth=False)
    base(s, mb, MIST, 0.6, wob=1.2, edge=0.4, flow=0.4)
    s.wash(mb, SLATE, 0.6, wob=1, soft=3, grad=s.vgrad(my0 + 60, my1, 0.1, 1))
    s.wash(s.rect(mx0, my0 + 30, mx1, my0 + 66), TEAL, 1.0, wob=1, edge=0.4)
    s.lift(s.rect(mx0 + 30, my0 + 8, mx1 - 30, my0 + 18), 0.6, soft=3)
    contour(s, mb, 2.2, INK, 1.4)
    for i in range(3):
        gx = mx0 + 70 + i * 105
        grp = s.poly([(gx - 20, my0 + 96), (gx + 20, my0 + 96), (gx + 14, my0 + 126), (gx - 14, my0 + 126)], smooth=False)
        base(s, grp, PAYNE, 1.1, wob=0.8)
        contour(s, grp, 1.5, INK, 1.3)
        seg(s, (gx, my0 + 110), (gx + 44, my0 + 128), 4.0, SEPIA, 1.4)
        oval(s, gx, my0 + 80, 9, 9, 1.4, INK, 1.2)
    for i in range(4):                                   # cups warming on top
        cx_ = mx0 + 60 + i * 76
        cm = Q(s, [(cx_, my0 - 26), (cx_ + 44, my0 - 26), (cx_ + 38, my0), (cx_ + 6, my0)])
        base(s, cm, CREAM, 0.3, wob=0.6)
        contour(s, cm, 1.3, INK, 1.2)
    # cake under a glass dome
    dx, dy = 1720, 872
    stand = s.poly([(dx - 90, dy - 30), (dx + 90, dy - 30), (dx + 20, dy - 18), (dx + 34, dy), (dx - 34, dy), (dx - 20, dy - 18)], smooth=False)
    base(s, stand, CREAM, 0.35, wob=0.8)
    cake = s.rect(dx - 56, dy - 76, dx + 56, dy - 30)
    base(s, cake, SIENNA, 0.8, wob=1, edge=0.5)
    s.lift(s.rect(dx - 58, dy - 80, dx + 58, dy - 64), 0.8, soft=1.5)
    contour(s, cake, 1.4, INK, 1.2)
    contour(s, stand, 1.5, INK, 1.3)
    s.ink(ell(dx, dy - 30, 84, 96, math.pi, 2 * math.pi, 30), 1.8, SLATE, 1.1)
    s.lift(s.ribbon([(dx - 60, dy - 80), (dx - 40, dy - 112)], 6), 0.7, soft=2)
    oval(s, dx, dy - 128, 8, 6, 1.4, SLATE, 1.1)
    # record player (the page turns the record)
    px, py = 2130, 872
    deck = Q(s, [(px - 150, py - 40), (px + 150, py - 40), (px + 166, py), (px - 166, py)])
    wood(s, deck, BURNT, SEPIA, 0.9, n=8, seed=11, wob=1)
    contour(s, deck, 2.0, INK, 1.4)
    rec = s.ellipse(px - 30, py - 24, 104, 17)
    base(s, rec, SEPIA, 1.3, wob=0.8, edge=0.4)
    lab = s.ellipse(px - 30, py - 24, 32, 5.5)
    s.lift(lab, 1.0, soft=0.8)
    s.wash(lab, BURNT, 0.9, wob=0.5, body=1)
    oval(s, px - 30, py - 24, 104, 17, 1.6, INK, 1.3)
    seg(s, (px + 110, py - 44), (px + 30, py - 28), 3.0, MIST, 1.2)
    oval(s, px + 112, py - 44, 9, 6, 1.4, INK, 1.2)
    # pictures on the right wall, and a round mirror on the back wall (a circle that holds the room)
    mir = s.ellipse(2110, 520, 70, 70)
    base(s, mir, MIST, 0.45, wob=1, edge=0.4)
    s.wash(mir, OCHRE, 0.35, wob=2, bleed=10, grad=s.rgrad(2090, 500, 10, 90, 1, 0))
    oval(s, 2110, 520, 70, 70, 4.0, UMBER, 1.4, twice=True)
    for xa, xb, f0, f1 in ((2960, 3110, 0.22, 0.44), (3200, 3400, 0.18, 0.46)):
        q = [rwall(xa, f0), rwall(xb, f0), rwall(xb, f1), rwall(xa, f1)]
        m = Q(s, q)
        base(s, m, CREAM, 0.35, wob=1, edge=0.4)
        cx_, cy_ = (xa + xb) / 2, (q[0][1] + q[2][1]) / 2
        s.wash(s.ellipse(cx_, cy_, (xb - xa) * 0.26, (xb - xa) * 0.3), [BURNT, TEAL][int(xa > 3000)], 0.8, wob=3, edge=0.6, clip=m)
        path(s, q, 3.0, UMBER, 1.4, closed=True, over=4, r=r)
        cast(s, m, 10, 14, UMBER, 0.3, blur=8, clip=right * (1 - m))

    # ---- furniture: every table but one is empty
    order = sorted(TABLES, key=lambda t: t[1])
    tops = {}
    for (x, y, i) in order:
        sc = fsc(y)
        if i == 2:              # the corner seat: only the table and the far chair here; she and her coat are sprites
            small_chair(s, x + 150 * sc, y - 34 * sc, "F", i)
            tops[i] = small_table(s, x, y, i, bare=True)
            continue
        if i == 6:              # the nearest table is cropped by the frame: just its top and one chair back
            small_chair(s, x + 360, y - 120, "F", i)
            tops[i] = small_table(s, x, y, i)
            continue
        off = (-150, 150) if i % 2 == 0 else (30, -40)
        small_chair(s, x + off[0] * sc, y - 46 * sc, "F", i)
        tops[i] = small_table(s, x, y, i)
        small_chair(s, x + off[1] * sc, y + 58 * sc, "B", i)
    # a big plant by the first window
    px, py = 250, 1560
    pot = Q(s, [(px - 90, py - 150), (px + 90, py - 150), (px + 66, py), (px - 66, py)])
    cast(s, pot, 40, 12, SEPIA, 0.5, blur=14, clip=floor)
    for i in range(15):
        a = -math.pi / 2 + (i - 7) * 0.25 + (r.random() - 0.5) * 0.2
        Ln = 300 + 260 * r.random()
        tip = (px + math.cos(a) * Ln * 0.8, py - 160 + math.sin(a) * Ln)
        mid = (px + math.cos(a) * Ln * 0.35, py - 160 + math.sin(a) * Ln * 0.6)
        lf = s.ribbon([(px + (i - 7) * 7, py - 150), mid, tip], 60 + 30 * r.random(), taper=(0.25, 0.6))
        base(s, lf, MOSS, 0.8 + 0.4 * r.random(), wob=2, edge=0.5)
        s.wash(lf, TEAL, 0.45, wob=2, bleed=8, grad=s.hgrad(px - 250, px + 250, 0.8, 0))
        s.ink([(px + (i - 7) * 7, py - 150), mid, tip], 1.6, INKBLUE, 0.9, skip=0.1)
    base(s, pot, BURNT, 0.95, wob=2, edge=0.5, flow=0.4)
    s.wash(pot, UMBER, 0.5, wob=2, bleed=8, grad=s.hgrad(px - 10, px + 90))
    contour(s, pot, 2.2, INK, 1.3)

    # ---- the lamps' light, painted: pools on the walls and floor (the lamps themselves hang in front, as sprites)
    for (lx, ly, sc) in LAMPS:
        s.lift(s.rgrad(lx, ly + 230 * sc, 40 * sc, 420 * sc, 1, 0, sy=0.9) * (1 - floor), 0.16, soft=0, wob=0)
        fy = min(SH - 40, ly + 540 * sc)
        s.lift(s.rgrad(lx, fy, 30 * sc, 300 * sc, 1, 0, sy=0.28) * floor, 0.20, soft=0, wob=0)
    s.wash(s.full(), UMBER, 0.32, wob=0, soft=0, edge=0, gran=0.3, flow=0.3, grad=s.rgrad(VP[0], VP[1] + 150, 1100, 2300, 0, 1, sy=0.7))    # the corners of the room fall away
    s.save("sp_room", opaque=True, q=90, meta={"lamps": LAMPS, "wins": wins, "seat": SEAT, "tops": {str(k): [float(v[0]), float(v[1])] for k, v in tops.items()},
                                              "record": [2100, 848, 104, 17], "machine": [1325, 690], "vp": list(VP)})


ALL = {"shop_room": room}
