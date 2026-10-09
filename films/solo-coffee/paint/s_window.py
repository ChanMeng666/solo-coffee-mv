"""The window by the corner seat, from inside. Outside is painted wet-in-wet (it is out of focus, and the glass pass
fogs it further); the wall, the frame, the sill and the clock are in focus and carry the pen.
Sheet 2880x1620."""
import math

import cv2
import numpy as np

from kit import *

SW, SH = 2880, 1620
X0, X1, Y0, Y1 = 560, 2240, 140, 1150          # the window opening
MUL = (X0 + 560, X0 + 1120)                    # mullion centres
TRANSOM = 392
FR, MW = 46, 34                                # frame and mullion thickness
SILL_Y = 1150
PANES = []
for a, b in ((X0 + FR, MUL[0] - MW / 2), (MUL[0] + MW / 2, MUL[1] - MW / 2), (MUL[1] + MW / 2, X1 - FR)):
    PANES.append([a, Y0 + FR, b, TRANSOM - 15])
    PANES.append([a, TRANSOM + 15, b, Y1 - 8])
AWN_TIPS = [X0 - 150 + i * 170 + 85 for i in range(13)]
AWN_Y = 318
CLOCK = (2570, 520)


def outside():
    s = Sheet(SW, SH, 41)
    r = rs(41)
    # wet sky going down into mist
    s.glaze(RAIN, 0.75, grad=s.vgrad(0, SH * 0.6, 1, 0.5), flow=0.5, fs=500)
    s.glaze(INDIGO, 0.42, grad=s.vgrad(0, SH * 0.5, 1, 0.1), flow=0.5, fs=380)
    s.glaze(ROSE, 0.12, grad=s.vgrad(SH * 0.25, SH * 0.55, 0, 1) * s.vgrad(SH * 0.55, SH * 0.8, 1, 0), flow=0.3)
    # the buildings opposite: soft blocks, darker toward the street
    x = -80
    while x < SW + 100:
        w = 240 + r.random() * 330
        top = 250 + r.random() * 330
        col = [PAYNE, PRUSSIAN, SLATE, TEAL, VIOLET][int(r.random() * 5)]
        m = s.rect(x, top, x + w, 1120)
        s.wash(m, col, 0.55 + 0.4 * r.random(), wob=8, bleed=26, edge=0.25, ew=18, flow=0.5, fs=160, gran=0.5)
        s.wash(m, INDIGO, 0.3, wob=6, bleed=30, grad=s.vgrad(top, 1120, 0.1, 1), edge=0.1)
        # windows: most dark, a few lit
        for wy in np.arange(top + 60, 880, 96):
            for wx in np.arange(x + 36, x + w - 60, 84):
                if r.random() < 0.55:
                    continue
                mm = s.rect(wx, wy, wx + 44, wy + 60)
                if r.random() < 0.32:
                    s.lift(mm, 0.75, soft=7, wob=3)
                    s.wash(mm, OCHRE if r.random() < 0.7 else ROSE, 0.5, wob=3, bleed=9, edge=0.1)
                else:
                    s.wash(mm, INDIGO, 0.35, wob=3, bleed=8, edge=0.1)
        x += w + r.random() * 30 - 8
    # shop fronts at street level: smears of light
    for i in range(9):
        cx = 150 + i * 330 + r.random() * 120
        col = [AMBER, ROSE, OCHRE, TEAL, AMBER][i % 5]
        mm = s.rect(cx - 110, 930, cx + 110, 1090)
        s.lift(mm, 0.7, soft=22, wob=6)
        s.wash(mm, col, 0.55, wob=6, bleed=26, edge=0.1)
    # the street: dark wet, with every light pulled down into it
    road = s.rect(-10, 1110, SW + 10, SH + 10)
    s.wash(road, PRUSSIAN, 1.0, wob=5, bleed=22, edge=0.2, flow=0.5, fs=300, gran=0.5)
    s.wash(road, INDIGO, 0.5, wob=0, edge=0, grad=s.vgrad(1110, SH, 0.2, 1), flow=0.4)
    for i in range(16):
        cx = 60 + i * 190 + r.random() * 110
        mm = s.rect(cx - 16 - 24 * r.random(), 1120, cx + 16 + 24 * r.random(), 1300 + r.random() * 320)
        s.lift(mm, 0.45 + 0.3 * r.random(), soft=16, wob=9, bleed=20)
        if r.random() < 0.6:
            s.wash(mm, [AMBER, ROSE, OCHRE][i % 3], 0.3, wob=8, bleed=24, edge=0.1)
    # a street lamp and a bare tree, as soft dark verticals
    s.stroke([(1980, 1130), (1976, 700), (1990, 420), (2060, 380)], 16, INDIGO, 0.8, wob=3, bleed=6, taper=(0, 0.2))
    s.lift(s.ellipse(2070, 384, 60, 46), 0.85, soft=20)
    s.wash(s.ellipse(2070, 384, 46, 34), OCHRE, 0.4, wob=3, bleed=14)
    for (a, b, w) in (((700, 1130), (690, 760), 20), ((690, 760), (560, 520), 12), ((690, 760), (820, 560), 11), ((560, 520), (470, 400), 7), ((820, 560), (900, 430), 7), ((690, 880), (600, 700), 8)):
        s.stroke([a, ((a[0] + b[0]) / 2 + 12, (a[1] + b[1]) / 2), b], w, INDIGO, 0.7, wob=3, bleed=5, taper=(0, 0.3))
    s.save("wn_out", opaque=True, q=88)


def passers():
    """People going by outside, as soft dark shapes: a pair under one umbrella, and the same pair smaller."""
    def person(s, cx, top, h, lean=0.0, col=INDIGO):
        head = s.ellipse(cx + lean * 20, top + h * 0.07, h * 0.055, h * 0.065)
        body = s.poly([(cx - h * 0.10 + lean * 14, top + h * 0.14), (cx + h * 0.10 + lean * 14, top + h * 0.14), (cx + h * 0.13, top + h * 0.62), (cx + h * 0.07, top + h), (cx - h * 0.07, top + h), (cx - h * 0.13, top + h * 0.62)])
        m = np.maximum(head, body)
        s.wash(m, col, 1.1, wob=5, bleed=9, edge=0.3, body=0.85)
        return m
    s = Sheet(900, 1000, 44)
    person(s, 380, 330, 600, 0.3, INDIGO)
    person(s, 520, 300, 640, -0.3, PAYNE)
    um = s.poly([(160, 330), (240, 200), (450, 130), (660, 200), (740, 330), (600, 300), (450, 318), (300, 300)])
    s.wash(um, PRUSSIAN, 1.2, wob=4, bleed=8, edge=0.4, body=0.9)
    s.stroke([(450, 130), (452, 520)], 7, INKBLUE, 0.9, wob=1, bleed=2, taper=(0, 0))
    s.wash(s.ellipse(450, 940, 260, 22), INDIGO, 0.5, wob=3, bleed=14)       # their reflection on the wet ground
    s.save("wn_pair", crop=True, anchor=(450, 930))
    s = Sheet(700, 1000, 45)
    person(s, 350, 320, 620, 0.1, PAYNE)
    um = s.poly([(120, 330), (190, 210), (350, 150), (510, 210), (580, 330), (460, 300), (350, 316), (240, 300)])
    s.wash(um, SLATE, 1.0, wob=4, bleed=8, edge=0.4, body=0.9)
    s.stroke([(350, 150), (352, 520)], 7, INKBLUE, 0.9, wob=1, bleed=2, taper=(0, 0))
    s.wash(s.ellipse(350, 950, 200, 20), INDIGO, 0.5, wob=3, bleed=14)
    s.save("wn_single", crop=True, anchor=(350, 940))


def awning():
    """The awning's valance seen from under it: scallops, wet, dripping."""
    s = Sheet(SW, 420, 46)
    for i in range(13):
        x = X0 - 150 + i * 170
        m = s.poly([(x, 0), (x + 170, 0), (x + 170, 240), (x + 150, 290), (x + 85, 318), (x + 20, 290), (x, 240)])
        base(s, m, BURNT if i % 2 else CREAM, 0.9 if i % 2 else 0.45, wob=3, edge=0.5, flow=0.5, fs=90, gran=0.5)
        s.wash(m, UMBER, 0.45, wob=3, bleed=12, grad=s.vgrad(0, 200, 1, 0.1))
        s.wash(m, PRUSSIAN, 0.25, wob=3, bleed=10, grad=s.vgrad(200, 318, 0, 1))          # wet lower edge
        s.ink([(x, 240), (x + 20, 290), (x + 85, 318), (x + 150, 290), (x + 170, 240)], 2.4, SEPIA, 1.2, tremor=1.2)
        seg(s, (x, 0), (x, 240), 1.6, SEPIA, 0.8, skip=0.2)
    s.save("wn_awn", meta={"tips": AWN_TIPS, "tip_y": AWN_Y})


def frame():
    s = Sheet(SW, SH, 42)
    r = rs(42)
    panes = s.zeros()
    for p in PANES:
        panes = np.maximum(panes, s.rect(*p))
    wall = 1 - panes
    hard = (wall > 0.5).astype(np.float32)
    # plaster: warm, uneven, a pool of lamp light upper left, cooler near the glass
    s.wash(wall, CREAM, 0.55, wob=0, soft=0, edge=0, flow=0.45, fs=420, gran=0.4, body=1)
    s.wash(wall, OCHRE, 0.42, wob=0, soft=0, edge=0, grad=s.rgrad(330, 240, 200, 1500, 0.25, 1), flow=0.5, fs=300)
    s.wash(wall, SIENNA, 0.22, wob=0, soft=0, edge=0, grad=s.noise(260, 3) * s.vgrad(900, 1400, 0.2, 1))
    s.wash(wall, RAIN, 0.20, wob=0, soft=0, edge=0, grad=s.rgrad((X0 + X1) / 2, (Y0 + Y1) / 2, 900, 1300, 1, 0, sy=0.62))
    for _ in range(7):
        s.wash(s.blob(r.random() * SW, r.random() * 1250, 200 + 200 * r.random(), 90 + 80 * r.random(), 0.3) * hard, OCHRE, 0.10, wob=6, bleed=30, edge=0.5, ew=14)
    # wainscot below the dado rail
    DADO = 1335
    wm = s.rect(-10, DADO, SW + 10, SH + 10)
    base(s, wm, TEAL, 1.05, wob=2, edge=0.3, flow=0.5, fs=260, gran=0.5)
    s.wash(wm, PRUSSIAN, 0.6, wob=0, edge=0, grad=s.vgrad(DADO, SH, 0.2, 1), flow=0.4)
    for x in range(40, SW, 205):
        seg(s, (x + r.random() * 6, DADO + 22), (x + r.random() * 6, SH), 2.0, INKBLUE, 1.0, skip=0.15, r=r)
        s.wash(s.rect(x + 4, DADO + 20, x + 22, SH), INKBLUE, 0.25, wob=1, soft=4)
    rail = s.rect(-10, DADO - 16, SW + 10, DADO + 12)
    base(s, rail, OCHRE, 0.9, wob=1, edge=0.5)
    s.wash(rail, BURNT, 0.5, wob=1, soft=2, grad=s.vgrad(DADO - 4, DADO + 12))
    seg(s, (0, DADO - 16), (SW, DADO - 15), 2.0, SEPIA, 1.2, r=r)
    seg(s, (0, DADO + 12), (SW, DADO + 13), 2.2, SEPIA, 1.4, r=r)
    # the frame: dark umber wood
    def member(x0, y0, x1, y1, seed, ang=0.0):
        m = s.rect(x0, y0, x1, y1)
        wood(s, m, UMBER, SEPIA, 1.0, ang=ang, n=10, seed=seed, lw=1.2, wob=0.8)
        s.wash(m, SEPIA, 0.35, wob=1, soft=3, grad=s.hgrad(x0, x1, 0.2, 1) if ang else s.vgrad(y0, y1, 0.2, 1))
        path(s, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 2.0, INK, 1.3, closed=True, over=5, r=r)
        return m
    member(X0, Y0, X1, Y0 + FR, 1)
    member(X0, Y0, X0 + FR, Y1, 2, math.pi / 2)
    member(X1 - FR, Y0, X1, Y1, 3, math.pi / 2)
    member(X0, TRANSOM - 15, X1, TRANSOM + 15, 4)
    for i, mx in enumerate(MUL):
        member(mx - MW / 2, Y0, mx + MW / 2, Y1, 5 + i, math.pi / 2)
    member(X0, Y1 - 8, X1, Y1 + 6, 8)
    # lit inner edges where the daylight catches the frame
    for p in PANES:
        s.lift(s.rect(p[0] - 5, p[1], p[0] + 2, p[3]), 0.35, soft=1.5)
        s.lift(s.rect(p[0], p[1] - 5, p[2], p[1] + 2), 0.3, soft=1.5)
    # sill and apron
    sill = Q(s, [(X0 - 70, SILL_Y + 6), (X1 + 70, SILL_Y + 6), (X1 + 96, SILL_Y + 62), (X0 - 96, SILL_Y + 62)])
    wood(s, sill, SIENNA, BURNT, 0.8, ang=0.0, n=30, seed=9)
    s.lift(Q(s, [(X0, SILL_Y + 10), (X1, SILL_Y + 10), (X1 + 10, SILL_Y + 30), (X0 - 10, SILL_Y + 30)]), 0.35, soft=8)       # window light on the sill
    front = s.rect(X0 - 96, SILL_Y + 62, X1 + 96, SILL_Y + 96)
    wood(s, front, UMBER, SEPIA, 0.95, n=8, seed=10)
    path(s, [(X0 - 70, SILL_Y + 6), (X1 + 70, SILL_Y + 6), (X1 + 96, SILL_Y + 62), (X1 + 96, SILL_Y + 96), (X0 - 96, SILL_Y + 96), (X0 - 96, SILL_Y + 62)], 2.4, INK, 1.4, closed=True, over=5, r=r)
    seg(s, (X0 - 96, SILL_Y + 62), (X1 + 96, SILL_Y + 62), 1.8, INK, 1.1, r=r)
    cast(s, front, 10, 46, UMBER, 0.5, blur=18, clip=hard)
    # shadow of the frame on the wall, away from the lamp
    shade(s, s.rect(X1, Y0 + 20, X1 + 40, Y1) * hard, UMBER, 0.3, bleed=12)
    # a linen curtain drawn back at the left
    cp = [(250, 96), (560, 90), (548, 400), (470, 760), (440, 1150), (400, 1215), (268, 1215), (300, 760), (262, 400)]
    cm = s.poly(cp)
    base(s, cm, CREAM, 0.42, wob=3, edge=0.4, flow=0.5, fs=120)
    for i in range(7):
        x = 285 + i * 38
        s.stroke([(x, 110), (x + 12, 420), (x - 20 + i * 8, 780), (300 + i * 16, 1200)], 20, SIENNA, 0.22, wob=3, bleed=7, clip=cm, taper=(0, 0), edge=0.2)
        s.ink([(x + 8, 110), (x + 20, 420), (x - 12 + i * 8, 780), (308 + i * 16, 1200)], 1.5, SEPIA, 0.8, skip=0.3, clip=cm)
    s.wash(cm, RAIN, 0.28, wob=2, bleed=14, grad=s.hgrad(380, 560))
    s.ink(spline(cp, True), 2.0, SEPIA, 1.2, smooth=False, skip=0.05)
    tie = s.poly([(290, 740), (480, 742), (486, 790), (296, 792)])
    base(s, tie, BURNT, 0.9, wob=2)
    s.ink(spline([(290, 740), (480, 742), (486, 790), (296, 792)], True), 1.8, SEPIA, 1.2, smooth=False)
    rod = s.rect(200, 84, 640, 100)
    base(s, rod, OCHRE, 0.9, wob=1)
    seg(s, (200, 84), (640, 84), 1.8, SEPIA, 1.2)
    seg(s, (200, 100), (640, 100), 1.8, SEPIA, 1.2)
    # on the sill: a pot of something green, two books
    px, py = 800, SILL_Y + 20
    pot = Q(s, [(px - 62, py - 110), (px + 62, py - 110), (px + 46, py), (px - 46, py)])
    cast(s, pot, 34, 10, UMBER, 0.5, blur=10)
    for i in range(13):
        a = -math.pi / 2 + (i - 6) * 0.26 + (r.random() - 0.5) * 0.2
        L = 150 + 110 * r.random()
        tip = (px + math.cos(a) * L, py - 120 + math.sin(a) * L)
        midp = (px + math.cos(a) * L * 0.5 + 16 * math.cos(a + 1.5), py - 120 + math.sin(a) * L * 0.55)
        lf = s.ribbon([(px + (i - 6) * 5, py - 112), midp, tip], 34 + 16 * r.random(), taper=(0.3, 0.6))
        base(s, lf, MOSS, 0.75 + 0.4 * r.random(), wob=2, edge=0.5)
        s.wash(lf, TEAL, 0.35, wob=2, bleed=5, grad=s.hgrad(px - 150, px + 150))
        s.ink([(px + (i - 6) * 5, py - 112), midp, tip], 1.5, INKBLUE, 0.9, skip=0.1)
    base(s, pot, BURNT, 0.95, wob=2, edge=0.5, flow=0.4)
    s.wash(pot, UMBER, 0.5, wob=2, bleed=8, grad=s.hgrad(px - 10, px + 62))
    path(s, [(px - 62, py - 110), (px + 62, py - 110), (px + 46, py), (px - 46, py)], 2.2, INK, 1.3, closed=True, over=4, r=r)
    seg(s, (px - 66, py - 92), (px + 66, py - 92), 1.6, INK, 1.0)
    bx, by = 1960, SILL_Y + 22
    for i, (col, w, h, dx) in enumerate(((PRUSSIAN, 250, 40, 0), (BURNT, 220, 34, 18), (CREAM, 236, 30, -6))):
        y1 = by - sum((40, 34, 30)[:i])
        bm = Q(s, [(bx + dx, y1 - h), (bx + dx + w, y1 - h - 3), (bx + dx + w + 4, y1 - 2), (bx + dx + 2, y1)])
        if i == 0:
            cast(s, bm, 30, 8, UMBER, 0.5, blur=9)
        base(s, bm, col, 0.9 if col != CREAM else 0.4, wob=1.5, edge=0.5)
        path(s, [(bx + dx, y1 - h), (bx + dx + w, y1 - h - 3), (bx + dx + w + 4, y1 - 2), (bx + dx + 2, y1)], 2.0, INK, 1.3, closed=True, over=3, r=r)
        seg(s, (bx + dx + 30, y1 - h + 6), (bx + dx + 30, y1 - 5), 1.2, INK, 0.8)
    s.save("wn_frame", meta={"panes": PANES, "opening": [X0, Y0, X1, Y1], "sill_y": SILL_Y, "clock": list(CLOCK), "dado_y": DADO})


def clock():
    """A round regulator clock: face above, a little glazed case below where the pendulum swings. The page draws the hands."""
    s = Sheet(520, 900, 47)
    cx, cy, Rr = 260, 250, 190
    # case
    case = Q(s, [(cx - 92, cy + 150), (cx + 92, cy + 150), (cx + 78, cy + 500), (cx, cy + 560), (cx - 78, cy + 500)])
    cast(s, np.maximum(case, s.ellipse(cx, cy, Rr, Rr)), 26, 30, UMBER, 0.45, blur=16)
    wood(s, case, UMBER, SEPIA, 1.0, ang=math.pi / 2, n=10, seed=3)
    glass = Q(s, [(cx - 62, cy + 190), (cx + 62, cy + 190), (cx + 52, cy + 480), (cx, cy + 520), (cx - 52, cy + 480)])
    s.lift(glass, 0.9, soft=1.5)
    s.wash(glass, SEPIA, 0.9, wob=1, edge=0.4, body=1)
    s.wash(glass, PRUSSIAN, 0.3, wob=1, soft=3)
    path(s, [(cx - 92, cy + 150), (cx + 92, cy + 150), (cx + 78, cy + 500), (cx, cy + 560), (cx - 78, cy + 500)], 2.4, INK, 1.4, closed=True, over=4)
    path(s, [(cx - 62, cy + 190), (cx + 62, cy + 190), (cx + 52, cy + 480), (cx, cy + 520), (cx - 52, cy + 480)], 1.6, INK, 1.1, closed=True, over=3)
    rim = s.ellipse(cx, cy, Rr, Rr)
    wood(s, rim, UMBER, SEPIA, 1.05, ang=0.4, n=12, seed=4, lines=False)
    face = s.ellipse(cx, cy, Rr - 30, Rr - 30)
    base(s, face, CREAM, 0.38, wob=1, edge=0.4)
    s.wash(face, OCHRE, 0.25, wob=2, bleed=10, grad=s.rgrad(cx + 40, cy + 50, 30, 190, 0, 1))
    s.wash(face * (1 - s.ellipse(cx - 6, cy - 8, Rr - 34, Rr - 34)), UMBER, 0.5, wob=1, soft=3)      # the rim's shadow on the face
    oval(s, cx, cy, Rr, Rr, 2.8, INK, 1.5, twice=True)
    oval(s, cx, cy, Rr - 30, Rr - 30, 2.0, INK, 1.2)
    for i in range(12):
        a = i * math.pi / 6
        r0, r1 = (Rr - 62, Rr - 40) if i % 3 else (Rr - 74, Rr - 40)
        seg(s, (cx + math.sin(a) * r0, cy - math.cos(a) * r0), (cx + math.sin(a) * r1, cy - math.cos(a) * r1), 3.4 if i % 3 == 0 else 1.8, INK, 1.5, bow=0)
    s.save("wn_clock", crop=True, anchor=(cx, cy), meta={"face_r": Rr - 30, "pivot": [0, 200], "glass": [-62, 190, 62, 520]})
    # pendulum: rod and brass bob, anchor at the pivot
    p = Sheet(200, 420, 48)
    seg(p, (100, 20), (100, 300), 3.0, SEPIA, 1.5, bow=0)
    bob = p.ellipse(100, 320, 40, 40)
    base(p, bob, OCHRE, 1.0, wob=1, edge=0.5)
    p.wash(bob, BURNT, 0.5, wob=1, soft=3, grad=p.rgrad(86, 306, 6, 50, 0, 1))
    p.lift(p.ellipse(86, 306, 12, 9), 0.8, soft=3)
    oval(p, 100, 320, 40, 40, 2.0, INK, 1.4)
    p.save("wn_pend", crop=True, anchor=(100, 20))


def pendant():
    """The café's lamp: an enamel dome on a cord. Anchor at the bulb. Used over every table in the film."""
    s = Sheet(700, 1300, 49)
    cx, top, by = 350, 0, 1040
    seg(s, (cx, top), (cx, by - 250), 3.2, INK, 1.6, bow=0.001)
    cap = Q(s, [(cx - 34, by - 260), (cx + 34, by - 260), (cx + 48, by - 200), (cx - 48, by - 200)])
    base(s, cap, OCHRE, 0.9, wob=1, edge=0.5)
    path(s, [(cx - 34, by - 260), (cx + 34, by - 260), (cx + 48, by - 200), (cx - 48, by - 200)], 2.0, INK, 1.3, closed=True, over=3)
    dome = s.poly([(cx - 46, by - 200), (cx + 46, by - 200), (cx + 170, by - 110), (cx + 250, by + 6), (cx + 262, by + 40), (cx - 262, by + 40), (cx - 250, by + 6), (cx - 170, by - 110)])
    base(s, dome, TEAL, 1.1, wob=2, edge=0.5, flow=0.5, fs=120, gran=0.5)
    s.wash(dome, PRUSSIAN, 0.7, wob=2, bleed=14, grad=s.hgrad(cx - 40, cx + 262), edge=0.2)
    s.lift(s.poly([(cx - 150, by - 96), (cx - 90, by - 150), (cx - 60, by - 150), (cx - 170, by - 20), (cx - 210, by - 10)]), 0.45, soft=8)       # sheen
    s.ink(spline([(cx - 46, by - 200), (cx - 170, by - 110), (cx - 250, by + 6), (cx - 262, by + 40)]), 2.4, INKBLUE, 1.5)
    s.ink(spline([(cx + 46, by - 200), (cx + 170, by - 110), (cx + 250, by + 6), (cx + 262, by + 40)]), 2.4, INKBLUE, 1.5)
    # the cream inside of the shade, seen from slightly below, and the bulb
    lip = s.ellipse(cx, by + 40, 262, 34)
    base(s, lip, CREAM, 0.30, wob=1, edge=0.4)
    s.wash(lip, OCHRE, 0.5, wob=1, soft=3, grad=s.rgrad(cx, by + 40, 40, 262, 0, 1))
    oval(s, cx, by + 40, 262, 34, 2.2, INKBLUE, 1.4)
    bulb = s.ellipse(cx, by + 44, 46, 30)
    s.lift(bulb, 1.0, soft=3)
    s.wash(bulb, OCHRE, 0.18, wob=1, soft=2, body=1)
    s.save("lamp_pendant", crop=True, anchor=(cx, by + 44))


ALL = {"win_out": outside, "win_passers": passers, "win_awning": awning, "win_frame": frame, "win_clock": clock, "pendant": pendant}
