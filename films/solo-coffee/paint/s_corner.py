"""The corner seat, wide, from behind her: the wall she faces, the window to her left, the room's corner to the right.
The chairs, the coat and she herself are sprites from other modules; this paints the room and the table.
Sheet 2880x1620."""
import math

import cv2
import numpy as np

from kit import *

SW, SH = 2880, 1620
DADO, SKIRT, CORNER = 930, 1262, 2540
WX0, WX1, WY0, WY1 = 170, 1090, 160, 850
PANES = [[WX0 + 40, WY0 + 40, 615, 330], [645, WY0 + 40, WX1 - 40, 330], [WX0 + 40, 360, 615, WY1 - 10], [645, 360, WX1 - 40, WY1 - 10]]
PLACE = {"fig": [1320, 1420, 1.0], "table": [1770, 1470], "top": [1770, 1092], "far": [2075, 1030, 0.62], "lamp": [1770, 430, 0.72], "cup": [1700, 1086, 0.2]}


def bg():
    s = Sheet(SW, SH, 91)
    r = rs(91)
    # plaster
    wall = s.rect(-10, -10, SW + 10, DADO)
    s.wash(wall, CREAM, 0.55, wob=0, edge=0, flow=0.45, fs=420, gran=0.4)
    s.wash(wall, OCHRE, 0.45, wob=0, edge=0, grad=s.rgrad(1770, 560, 150, 1500, 0.2, 1), flow=0.5, fs=300)
    s.wash(wall, SIENNA, 0.25, wob=0, edge=0, grad=s.noise(300, 3) * s.vgrad(300, DADO, 0.3, 1))
    s.wash(wall, RAIN, 0.22, wob=0, edge=0, grad=s.rgrad(630, 500, 500, 1100, 1, 0))                 # cool by the window
    for _ in range(8):
        s.wash(s.blob(r.random() * SW, r.random() * 900, 200 + 200 * r.random(), 90 + 80 * r.random(), 0.3) * wall, OCHRE, 0.10, wob=6, bleed=30, edge=0.5, ew=14)
    # the adjoining wall, in shade
    side = Q(s, [(CORNER, -10), (SW + 10, -10), (SW + 10, DADO + 46), (CORNER, DADO)])
    s.wash(side, UMBER, 0.42, wob=1, edge=0.2, flow=0.4, gran=0.5)
    s.wash(side, PRUSSIAN, 0.14, wob=0, edge=0)
    # wainscot
    wm = s.rect(-10, DADO, SW + 10, SKIRT)
    base(s, wm, TEAL, 1.05, wob=1.5, edge=0.3, flow=0.5, fs=260, gran=0.5)
    s.wash(wm, PRUSSIAN, 0.6, wob=0, edge=0, grad=s.vgrad(DADO, SKIRT, 0.2, 1), flow=0.4)
    s.wash(s.rect(CORNER, DADO, SW + 10, SKIRT), INKBLUE, 0.45, wob=1, soft=3)
    for x in range(30, SW, 168):
        if x < CORNER:
            seg(s, (x, DADO + 18), (x + r.random() * 4, SKIRT - 6), 1.8, INKBLUE, 1.0, skip=0.15, r=r)
            s.wash(s.rect(x + 3, DADO + 16, x + 18, SKIRT - 6), INKBLUE, 0.22, wob=1, soft=4)
    rail = s.rect(-10, DADO - 14, SW + 10, DADO + 10)
    base(s, rail, OCHRE, 0.9, wob=1, edge=0.5)
    s.wash(rail, BURNT, 0.5, wob=1, soft=2, grad=s.vgrad(DADO - 2, DADO + 10))
    seg(s, (0, DADO - 14), (SW, DADO - 13), 1.9, SEPIA, 1.2, r=r)
    seg(s, (0, DADO + 10), (SW, DADO + 11), 2.1, SEPIA, 1.4, r=r)
    sk = s.rect(-10, SKIRT - 30, SW + 10, SKIRT + 6)
    base(s, sk, UMBER, 1.1, wob=1, edge=0.4)
    seg(s, (0, SKIRT - 30), (SW, SKIRT - 29), 1.8, INK, 1.2, r=r)
    seg(s, (0, SKIRT + 6), (SW, SKIRT + 7), 2.2, INK, 1.4, r=r)
    seg(s, (CORNER, 0), (CORNER + 2, SKIRT), 2.4, INK, 1.3, r=r)
    # floor: dark herringbone, with the window's light lying across it and the lamp's pool under the table
    fl = s.rect(-10, SKIRT + 6, SW + 10, SH + 10)
    base(s, fl, UMBER, 0.95, wob=1, edge=0.2, flow=0.5, fs=300, gran=0.5)
    s.wash(fl, SEPIA, 0.55, wob=0, edge=0, grad=s.vgrad(SKIRT, SH, 0.2, 1) * (0.6 + 0.4 * s.noise(260, 3)), flow=0.4)
    vp = (1500, 700)
    for i in range(-30, 31):
        x1 = vp[0] + i * 210
        a = (vp[0] + (x1 - vp[0]) * (SKIRT + 6 - vp[1]) / (SH - vp[1]), SKIRT + 6)
        seg(s, a, (x1, SH + 10), 1.6, SEPIA, 0.9, skip=0.2, r=r, clip=fl)
    for j in range(8):
        y = SKIRT + 20 + (SH - SKIRT) * (j / 8) ** 1.5
        k = (y - vp[1]) / (SH - vp[1])
        for i in range(-30, 31):
            xa, xb = vp[0] + i * 210 * k, vp[0] + (i + 1) * 210 * k
            if r.random() < 0.4:
                continue
            dy = 22 * k * (1 if (i + j) % 2 else -1)
            s.ink([(xa + 4, y - dy), (xb - 4, y + dy)], 1.5, SEPIA, 0.6, skip=0.25, clip=fl, taper=(0.1, 0.1))
    s.lift(Q(s, [(200, SKIRT + 10), (1080, SKIRT + 10), (1500, SH), (500, SH)]) * fl, 0.20, soft=30, wob=8)
    s.wash(Q(s, [(200, SKIRT + 10), (1080, SKIRT + 10), (1500, SH), (500, SH)]) * fl, RAIN, 0.14, wob=6, bleed=30)
    s.lift(s.ellipse(1770, 1470, 520, 120) * fl, 0.22, soft=40)
    # the window, with the wet street soft behind it
    op = s.rect(WX0, WY0, WX1, WY1)
    s.lift(op, 1.0, soft=0.8, wob=0.8)
    s.wash(op, RAIN, 0.75, wob=1, edge=0.1, flow=0.5, fs=300, body=1)
    s.wash(op, INDIGO, 0.42, wob=0, edge=0, grad=s.vgrad(WY0, WY1, 0.5, 0.1))
    x = WX0
    while x < WX1:
        w = 120 + r.random() * 160
        top = WY0 + 150 + r.random() * 200
        m = s.rect(x, top, x + w, WY1) * op
        s.wash(m, [PAYNE, PRUSSIAN, SLATE, TEAL][int(r.random() * 4)], 0.6 + 0.3 * r.random(), wob=6, bleed=18, edge=0.2, clip=op)
        for _ in range(4):
            bx, by = x + r.random() * w, top + 40 + r.random() * (WY1 - top - 60)
            bm = s.blob(bx, by, 14 + 14 * r.random(), 16 + 14 * r.random(), 0.2) * op
            s.lift(bm, 0.7, soft=7)
            s.wash(bm, [AMBER, ROSE, OCHRE][int(r.random() * 3)], 0.4, wob=3, bleed=9, clip=op)
        x += w
    s.wash(s.rect(WX0, WY1 - 130, WX1, WY1) * op, PRUSSIAN, 0.8, wob=4, bleed=16, clip=op)

    def member(x0, y0, x1, y1, seed, ang=0.0):
        m = s.rect(x0, y0, x1, y1)
        wood(s, m, UMBER, SEPIA, 1.0, ang=ang, n=8, seed=seed, lw=1.2, wob=0.8)
        path(s, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 1.9, INK, 1.3, closed=True, over=5, r=r)
    member(WX0, WY0, WX1, WY0 + 40, 1)
    member(WX0, WY0, WX0 + 40, WY1, 2, math.pi / 2)
    member(WX1 - 40, WY0, WX1, WY1, 3, math.pi / 2)
    member(WX0, 330, WX1, 360, 4)
    member(615, WY0, 645, WY1, 5, math.pi / 2)
    member(WX0, WY1 - 10, WX1, WY1 + 4, 6)
    sill = Q(s, [(WX0 - 50, WY1 + 4), (WX1 + 50, WY1 + 4), (WX1 + 70, WY1 + 46), (WX0 - 70, WY1 + 46)])
    wood(s, sill, SIENNA, BURNT, 0.8, n=18, seed=7, wob=1)
    front = s.rect(WX0 - 70, WY1 + 46, WX1 + 70, WY1 + 72)
    wood(s, front, UMBER, SEPIA, 0.95, n=6, seed=8, wob=1)
    contour(s, np.maximum(sill, front), 2.2, INK, 1.4)
    seg(s, (WX0 - 70, WY1 + 46), (WX1 + 70, WY1 + 46), 1.6, INK, 1.1, r=r)
    cast(s, front, 8, 34, UMBER, 0.45, blur=14, clip=wall)
    shade(s, s.rect(WX1, WY0 + 20, WX1 + 34, WY1) * wall, UMBER, 0.3, bleed=10)
    # a small plant on the sill
    px, py = 330, WY1 + 14
    for i in range(11):
        a = -math.pi / 2 + (i - 5) * 0.28 + (r.random() - 0.5) * 0.2
        Ln = 100 + 80 * r.random()
        tip = (px + math.cos(a) * Ln, py - 86 + math.sin(a) * Ln)
        lf = s.ribbon([(px + (i - 5) * 4, py - 80), (px + math.cos(a) * Ln * 0.5, py - 86 + math.sin(a) * Ln * 0.55), tip], 24 + 12 * r.random(), taper=(0.3, 0.6))
        base(s, lf, MOSS, 0.8 + 0.4 * r.random(), wob=1.5, edge=0.5)
        s.ink([(px + (i - 5) * 4, py - 80), tip], 1.3, INKBLUE, 0.8, skip=0.1)
    pot = Q(s, [(px - 44, py - 80), (px + 44, py - 80), (px + 32, py), (px - 32, py)])
    base(s, pot, BURNT, 0.95, wob=1.5, edge=0.5)
    contour(s, pot, 2.0, INK, 1.3)
    # pictures: two circles, each alone in its frame
    for (x0, y0, x1, y1, col, rot) in ((2130, 330, 2330, 590, BURNT, -1.2), (2370, 420, 2500, 590, TEAL, 1.6)):
        cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
        M = cv2.getRotationMatrix2D((cxp, cyp), rot, 1)
        q = [tuple(M @ np.array([px_, py_, 1.0])) for px_, py_ in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        m = Q(s, q)
        cast(s, m, 10, 16, UMBER, 0.35, blur=9, clip=wall * (1 - m))
        base(s, m, CREAM, 0.30, wob=1, edge=0.4)
        s.wash(s.ellipse(cxp, cyp, (x1 - x0) * 0.27, (x1 - x0) * 0.27), col, 0.85, wob=3, edge=0.7, ew=6, flow=0.5, fs=40, gran=0.5)
        path(s, q, 4.0, UMBER, 1.4, closed=True, over=4, r=r)
        path(s, q, 1.6, INK, 1.2, closed=True, over=6, r=r)
    # the lamp's pool on the wall behind the far chair
    s.lift(s.rgrad(1900, 640, 80, 620, 1, 0, sy=0.8) * wall, 0.18, soft=0, wob=0)
    s.wash(s.full(), UMBER, 0.28, wob=0, soft=0, edge=0, gran=0.3, flow=0.3, grad=s.rgrad(1700, 800, 1100, 2000, 0, 1, sy=0.7))
    s.save("cn_bg", opaque=True, q=90, meta={"panes": PANES, "place": PLACE, "dado_y": DADO, "floor_y": SKIRT, "corner_x": CORNER})


def table():
    """The corner table seen from her side: top at eye-below height, single pedestal. Anchor at the foot."""
    s = Sheet(900, 700, 92)
    x, y = 450, 600
    h, rx, ry = 378, 300, 66
    s.wash(s.ellipse(x + 50, y + 16, 300, 60), SEPIA, 0.55, wob=3, bleed=22, edge=0.1)
    foot = s.ellipse(x, y, 130, 34)
    base(s, foot, UMBER, 1.1, wob=1.2, edge=0.5)
    oval(s, x, y, 130, 34, 2.4, INK, 1.3)
    ped = s.poly([(x - 22, y - h + 10), (x + 22, y - h + 10), (x + 16, y - 120), (x + 40, y - 10), (x - 40, y - 10), (x - 16, y - 120)], smooth=False)
    base(s, ped, UMBER, 1.15, wob=1, edge=0.5)
    s.wash(ped, SEPIA, 0.5, wob=1, soft=3, grad=s.hgrad(x - 6, x + 40))
    contour(s, ped, 2.2, INK, 1.3)
    rim = s.ellipse(x, y - h + 24, rx, ry)
    base(s, rim, UMBER, 1.1, wob=1, edge=0.4)
    s.ink(ell(x, y - h + 24, rx, ry, 0.08, math.pi - 0.08, 30), 2.2, INK, 1.3)
    top = s.ellipse(x, y - h, rx, ry)
    wood(s, top, SIENNA, BURNT, 0.75, ang=0.0, n=22, seed=3, lw=1.3, wob=1.2)
    s.lift(s.ellipse(x - 20, y - h - 6, rx * 0.62, ry * 0.5), 0.5, soft=14, wob=2)
    oval(s, x, y - h, rx, ry, 2.8, INK, 1.4, twice=True)
    s.save("cn_table", crop=True, anchor=(x, y), meta={"top": [0, -h]})


ALL = {"corner_bg": bg, "corner_table": table}
