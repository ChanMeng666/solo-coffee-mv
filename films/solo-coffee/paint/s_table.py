"""The table from straight above: a round wooden top, the cup, and the small things one person puts down.
Sheet 3072x1728 (1.6x the frame) so the camera can go in close on the cup."""
import math

import cv2
import numpy as np

from kit import *

TW, TH = 3072, 1728
CUP = (1536, 880)          # cup centre on the sheet
CUP_R = 205                # outer rim radius
COF_R = 178                # coffee surface radius
SAUCER_R = 330


def table():
    s = Sheet(TW, TH, 11)
    r = rs(11)
    # the floor far below: cool, dark boards, out of focus
    s.glaze(PRUSSIAN, 1.0, flow=0.4, fs=500)
    s.glaze(PAYNE, 0.7, grad=s.rgrad(TW / 2, TH / 2, 600, 1800, 0.3, 1), flow=0.3)
    for i in range(9):
        x = -200 + i * 430 + r.random() * 30
        s.stroke([(x, -20), (x + 60, TH / 2), (x + 130, TH + 20)], 7, INKBLUE, 0.5, wob=3, bleed=6, taper=(0, 0))
    # the table top
    top = s.ellipse(TW / 2, TH / 2 + 40, 1450, 1010)
    cast(s, top, 50, 70, INKBLUE, 0.9, blur=45)
    wood(s, top, SIENNA, BURNT, 0.72, ang=0.05, n=120, seed=5, lw=1.5)
    s.wash(top, OCHRE, 0.30, wob=0, edge=0, grad=s.rgrad(CUP[0] - 120, CUP[1] - 160, 200, 1100, 1, 0), flow=0.3)     # lamp pool
    s.wash(top, UMBER, 0.55, wob=0, edge=0, grad=s.rgrad(CUP[0] - 60, CUP[1] - 80, 700, 1650, 0, 1), flow=0.4, gran=0.5)   # falloff
    s.wash(top * (1 - s.ellipse(TW / 2, TH / 2 + 40, 1420, 985)), UMBER, 0.7, wob=1, soft=3, edge=0.3)                # bevel
    oval(s, TW / 2, TH / 2 + 40, 1450, 1010, 3.2, SEPIA, 1.5, twice=True, tremor=1.4)
    oval(s, TW / 2, TH / 2 + 40, 1418, 984, 1.6, SEPIA, 0.9, tremor=1.2, skip=0.3)
    # a few old rings and scratches: other people's coffees
    for cx, cy, rr in ((640, 520, 150), (2380, 1250, 170), (2250, 420, 120)):
        s.ink(ell(cx, cy, rr, rr * 0.98, r.random() * 6, r.random() * 6 + 4.6, 50), 5, BURNT, 0.28, tremor=1.5, skip=0.35, dry=0.6)
    s.spatter(40, UMBER, 0.35, box=(300, 200, TW - 300, TH - 200), r=(1, 4))
    s.save("tt_bg", opaque=True, q=90)


def saucer():
    s = Sheet(900, 900, 12)
    c = 450
    m = s.ellipse(c, c, SAUCER_R, SAUCER_R)
    base(s, m, CREAM, 0.30, wob=1.2, edge=0.3, flow=0.3)
    s.wash(m, RAIN, 0.22, wob=0, edge=0, grad=s.rgrad(c + 150, c + 170, 60, 480, 1, 0))                 # cool side away from the lamp
    well = s.ellipse(c, c, SAUCER_R * 0.62, SAUCER_R * 0.62)
    s.wash(well, UMBER, 0.20, wob=2, bleed=7, edge=0.4)
    s.wash(m * (1 - s.ellipse(c - 10, c - 12, SAUCER_R * 0.97, SAUCER_R * 0.97)), SLATE, 0.5, wob=1, soft=2)
    oval(s, c, c, SAUCER_R, SAUCER_R, 2.8, SEPIA, 1.5, twice=True)
    oval(s, c, c, SAUCER_R * 0.63, SAUCER_R * 0.63, 1.5, SEPIA, 0.8, skip=0.3)
    s.save("tt_saucer", crop=True, anchor=(c, c))
    # its shadow on the table
    sh = Sheet(1100, 1100, 13)
    sh.wash(sh.ellipse(550 + 34, 550 + 44, SAUCER_R + 6, SAUCER_R + 6), SEPIA, 0.75, wob=2, bleed=16, edge=0.1)
    sh.save("tt_saucer_sh", crop=True, anchor=(550, 550))


def cup():
    """The cup seen from above: thick ceramic rim, inner wall, the coffee. The page draws the moving surface over it."""
    s = Sheet(760, 760, 14)
    c = 380
    sh = s.ellipse(c + 26, c + 34, CUP_R + 4, CUP_R + 4)
    s.wash(sh, SEPIA, 0.55, wob=2, bleed=12, edge=0.1)
    # handle, pointing right and a little down
    hp = [(c + 170, c + 52), (c + 262, c + 86), (c + 318, c + 122), (c + 306, c + 170), (c + 244, c + 150), (c + 176, c + 104)]
    hm = s.poly(hp)
    base(s, hm, CREAM, 0.34, wob=1)
    s.wash(hm, SLATE, 0.35, wob=1, soft=2, grad=s.vgrad(c + 90, c + 180))
    s.ink(hp + [hp[0]], 2.4, SEPIA, 1.5)
    m = s.ellipse(c, c, CUP_R, CUP_R)
    base(s, m, CREAM, 0.26, wob=1.0, edge=0.3)
    s.wash(m, RAIN, 0.25, wob=0, edge=0, grad=s.rgrad(c + 120, c + 130, 40, 300, 1, 0))
    inner = s.ellipse(c, c, COF_R + 8, COF_R + 8)
    s.wash(inner, UMBER, 0.45, wob=1, soft=1.5, edge=0.5)                  # inner wall in shade
    cof = s.ellipse(c, c, COF_R, COF_R)
    s.lift(cof, 1.0, soft=0.8, wob=1)
    s.wash(cof, COFFEE, 1.15, wob=1.5, edge=0.7, ew=9, flow=0.3, fs=90, gran=0.5, body=1)
    s.wash(cof, BURNT, 0.5, wob=0, edge=0, grad=s.rgrad(c - 50, c - 60, 20, 190, 1, 0), flow=0.5, fs=60)
    oval(s, c, c, CUP_R, CUP_R, 2.8, SEPIA, 1.6, twice=True)
    oval(s, c, c, COF_R + 6, COF_R + 6, 1.8, SEPIA, 1.1, skip=0.15)
    s.save("tt_cup", crop=True, anchor=(c, c))
    # the rim alone (drawn over the animated coffee so the surface stays inside the cup)
    k = Sheet(760, 760, 15)
    ring = k.ellipse(c, c, CUP_R + 60, CUP_R + 60) * 0
    k.wash(k.ellipse(c, c, COF_R + 14, COF_R + 14) * (1 - k.ellipse(c + 14, c + 18, COF_R + 2, COF_R + 2)), SEPIA, 0.55, wob=1, soft=5, edge=0)   # rim's shadow on the coffee
    k.save("tt_cup_in", crop=True, anchor=(c, c))


def spoon():
    """A teaspoon lying along +x: bowl at the origin end, handle to the right. Anchor = centre of the bowl."""
    s = Sheet(760, 240, 16)
    cy = 120
    bowl = s.ellipse(110, cy, 70, 46)
    handle = s.poly([(165, cy - 12), (420, cy - 9), (640, cy - 16), (700, cy - 12), (712, cy), (700, cy + 12), (640, cy + 16), (420, cy + 9), (165, cy + 12)])
    m = np.maximum(bowl, handle)
    base(s, m, MIST, 0.55, wob=0.8, edge=0.4)
    s.wash(bowl, SLATE, 0.6, wob=1, soft=2, grad=s.rgrad(96, cy - 8, 6, 62, 0, 1))
    s.lift(s.ellipse(92, cy - 12, 24, 10, -20), 0.85, soft=2)
    s.wash(handle, SLATE, 0.5, wob=0.6, soft=1.5, grad=s.vgrad(cy - 4, cy + 16))
    s.lift(Q(s, [(200, cy - 6), (660, cy - 9), (660, cy - 5), (200, cy - 2)]), 0.7, soft=1.5)
    s.ink(ell(110, cy, 70, 46, 0.25, 2 * math.pi - 0.25, 40), 2.2, SEPIA, 1.5)
    s.ink([(170, cy - 13), (420, cy - 10), (640, cy - 17), (702, cy - 12), (714, cy), (702, cy + 12), (640, cy + 17), (420, cy + 10), (170, cy + 13)], 2.0, SEPIA, 1.5)
    s.save("tt_spoon", crop=True, anchor=(110, cy))


def hand():
    """A right hand from above, coming in from the lower right, fingers pinched round a spoon handle.
    Anchor = the pinch point. The sleeve is the deep teal jumper."""
    s = Sheet(1500, 1300, 17)
    px, py = 300, 300                       # pinch point
    # forearm / sleeve runs to the lower right corner
    sl = [(520, 430), (700, 380), (1500, 900), (1500, 1300), (1150, 1300), (470, 640)]
    sm = s.poly(sl, smooth=False)
    base(s, sm, TEAL, 1.0, wob=3, edge=0.5, flow=0.5, fs=120, gran=0.5)
    s.wash(sm, PRUSSIAN, 0.8, wob=2, bleed=14, grad=s.hgrad(500, 1300) * s.vgrad(500, 1250), edge=0.2)
    r = rs(3)
    for i in range(46):                     # knit ribs
        u = i / 45
        a = (540 + u * 900, 420 + u * 590)
        b = (430 + u * 900, 640 + u * 590)
        s.ink([a, ((a[0] + b[0]) / 2 + 10, (a[1] + b[1]) / 2 + 6), b], 1.6, INKBLUE, 0.55, tremor=1.2, skip=0.35, clip=sm)
    cuff = s.poly([(455, 470), (560, 380), (690, 372), (720, 430), (520, 660), (440, 650)], smooth=True)
    base(s, cuff, TEAL, 1.15, wob=2, edge=0.6)
    s.wash(cuff, PRUSSIAN, 0.6, wob=2, bleed=6, grad=s.vgrad(480, 660))
    for i in range(9):
        u = i / 8
        s.ink([(470 + u * 215, 468 - u * 88), (452 + u * 80, 640 + u * 10)], 1.6, INKBLUE, 0.7, tremor=1, skip=0.2, clip=cuff)
    s.ink(spline([(455, 470), (560, 380), (690, 372), (720, 430), (520, 660), (440, 650)], True), 2.4, INKBLUE, 1.4, closed=False, smooth=False)
    # back of the hand; the fingers curl down and in toward the pinch, the thumb comes round to meet them
    palm = s.poly([(360, 372), (450, 318), (560, 336), (628, 430), (590, 560), (492, 628), (400, 588), (332, 480)])
    fs = [finger(s, [(420, 350), (352, 296), (312, 286), (300, 308)], 70), finger(s, [(376, 420), (300, 372), (262, 356), (250, 382)], 68),
          finger(s, [(356, 492), (286, 456), (250, 436), (240, 462)], 62), finger(s, [(370, 556), (318, 536), (284, 518), (274, 540)], 52)]
    thumb = finger(s, [(520, 330), (440, 262), (360, 250), (308, 284)], 72, tip=0.74)
    allm = np.maximum(palm, thumb)
    for f in fs:
        allm = np.maximum(allm, f)
    base(s, allm, SKIN, 0.62, wob=1.5, edge=0.35, flow=0.3)
    s.wash(allm, BURNT, 0.30, wob=2, bleed=12, grad=s.hgrad(300, 620, 0.1, 1) * 0.7 + s.vgrad(300, 620) * 0.5, edge=0.2)
    s.wash(allm, ROSE, 0.16, wob=2, bleed=10, grad=s.rgrad(300, 320, 20, 170, 1, 0))
    contour(s, allm, 2.2, SEPIA, 1.3)
    for f in fs:
        contour(s, f, 1.4, SEPIA, 0.8)
    contour(s, thumb, 1.4, SEPIA, 0.8)
    for kx, ky in ((408, 352), (366, 420), (352, 490), (368, 552)):     # knuckles
        s.ink([(kx - 5, ky - 12), (kx + 8, ky - 2), (kx + 2, ky + 12)], 1.4, BURNT, 0.8)
    s.save("tt_hand", crop=True, anchor=(px, py))
    sh = Sheet(1500, 1300, 18)
    sh.wash(cv2.warpAffine(np.maximum(allm, np.maximum(sm, cuff)), np.float32([[1, 0, 40], [0, 1, 54]]), (1500, 1300)), SEPIA, 0.6, wob=2, bleed=18, edge=0.1)
    sh.save("tt_hand_sh", crop=True, anchor=(px, py))


def sugar():
    # a small bowl of sugar cubes
    s = Sheet(520, 520, 19)
    c = 260
    s.wash(s.ellipse(c + 22, c + 28, 172, 172), SEPIA, 0.6, wob=2, bleed=12, edge=0.1)
    m = s.ellipse(c, c, 168, 168)
    base(s, m, CREAM, 0.30, wob=1, edge=0.3)
    s.wash(m, TEAL, 0.8, wob=1, soft=1.5, edge=0.4, grad=1 - s.ellipse(c, c, 140, 140))        # a glazed rim
    s.wash(s.ellipse(c, c, 140, 140), UMBER, 0.30, wob=1, bleed=5, edge=0.5)
    r = rs(4)
    for i in range(9):
        a = r.random() * 6.28
        d = r.random() * 78
        x, y, q = c + math.cos(a) * d, c + math.sin(a) * d, r.random() * 1.5
        pts = [(x + 34 * math.cos(q + j * math.pi / 2), y + 34 * math.sin(q + j * math.pi / 2)) for j in range(4)]
        cm = Q(s, pts)
        base(s, cm, CREAM, 0.10, wob=0.6, edge=0.2)
        s.wash(cm, RAIN, 0.18, wob=0.5, soft=1, grad=s.rgrad(x + 14, y + 16, 4, 44, 1, 0))
        path(s, pts, 1.6, SEPIA, 1.1, closed=True, over=2)
    oval(s, c, c, 168, 168, 2.6, SEPIA, 1.5, twice=True)
    oval(s, c, c, 141, 141, 1.5, SEPIA, 0.9, skip=0.2)
    s.save("tt_sugar", crop=True, anchor=(c, c))
    # single cubes for dropping, three turns
    for i, q in enumerate((0.2, 0.7, 1.2)):
        k = Sheet(160, 160, 20 + i)
        pts = [(80 + 46 * math.cos(q + j * math.pi / 2), 80 + 46 * math.sin(q + j * math.pi / 2)) for j in range(4)]
        cm = Q(k, pts)
        base(k, cm, CREAM, 0.10, wob=0.6, edge=0.25)
        k.wash(cm, RAIN, 0.22, wob=0.5, soft=1, grad=k.rgrad(96, 100, 4, 60, 1, 0))
        k.spatter(14, UMBER, 0.25, box=(50, 50, 110, 110), r=(0.5, 1.2))
        path(k, pts, 1.8, SEPIA, 1.2, closed=True, over=2)
        k.save(f"tt_cube{i}", crop=True, anchor=(80, 80))


def phone():
    """Two faces of the same phone: screen up (dark glass; the page lights it) and face down."""
    for name, back in (("tt_phone", False), ("tt_phone_back", True)):
        s = Sheet(460, 800, 24)
        x0, y0, x1, y1 = 60, 60, 400, 740
        body = s.poly([(x0 + 30, y0), (x1 - 30, y0), (x1, y0 + 30), (x1, y1 - 30), (x1 - 30, y1), (x0 + 30, y1), (x0, y1 - 30), (x0, y0 + 30)], smooth=True, step=2)
        s.wash(cv2.warpAffine(body, np.float32([[1, 0, 16], [0, 1, 22]]), (460, 800)), SEPIA, 0.6, wob=2, bleed=10, edge=0.1)
        if back:
            base(s, body, SLATE, 0.75, wob=1, edge=0.4, flow=0.4, fs=120)
            s.wash(body, PAYNE, 0.4, wob=0, edge=0, grad=s.vgrad(200, 760))
            cam = s.ellipse(x0 + 70, y0 + 70, 34, 34)
            s.wash(cam, INKBLUE, 0.9, wob=0.6, edge=0.5)
            oval(s, x0 + 70, y0 + 70, 34, 34, 1.8, INKBLUE, 1.3)
            oval(s, x0 + 70, y0 + 70, 16, 16, 1.4, INKBLUE, 1.2)
        else:
            base(s, body, PAYNE, 1.1, wob=1, edge=0.4)
            scr = s.poly([(x0 + 26, y0 + 22), (x1 - 26, y0 + 22), (x1 - 16, y0 + 32), (x1 - 16, y1 - 32), (x1 - 26, y1 - 22), (x0 + 26, y1 - 22), (x0 + 16, y1 - 32), (x0 + 16, y0 + 32)], smooth=True, step=2)
            s.wash(scr, INKBLUE, 1.3, wob=0.8, edge=0.3, flow=0.3, fs=100)
            s.lift(Q(s, [(x0 + 40, y0 + 40), (x0 + 150, y0 + 40), (x0 + 60, y0 + 330), (x0 + 40, y0 + 330)]), 0.18, soft=8)    # a window reflected in the glass
        s.ink(spline([(x0 + 30, y0), (x1 - 30, y0), (x1, y0 + 30), (x1, y1 - 30), (x1 - 30, y1), (x0 + 30, y1), (x0, y1 - 30), (x0, y0 + 30)], True), 2.4, INKBLUE, 1.5, smooth=False)
        s.save(name, crop=True, anchor=(230, 400))


def napkin():
    s = Sheet(640, 560, 26)
    pts = [(70, 110), (520, 60), (575, 430), (120, 490)]
    m = Q(s, pts)
    s.wash(cv2.warpAffine(m, np.float32([[1, 0, 14], [0, 1, 18]]), (640, 560)), SEPIA, 0.45, wob=2, bleed=8, edge=0.1)
    base(s, m, CREAM, 0.12, wob=1.5, edge=0.3, flow=0.4)
    s.wash(m, RAIN, 0.15, wob=2, bleed=14, grad=s.hgrad(200, 600))
    path(s, pts, 1.8, SEPIA, 1.1, closed=True, over=3)
    seg(s, (300, 86), (345, 462), 1.2, SLATE, 0.7, skip=0.3)                     # the fold
    for i in range(5):                                                         # an embossed border
        seg(s, (100 + i * 4, 140 + i * 60), (130 + i * 3, 150 + i * 60), 1.0, SLATE, 0.5)
    s.save("tt_napkin", crop=True, anchor=(320, 280))


def ring():
    """The stain a cup leaves: the last circle in the film."""
    s = Sheet(560, 560, 27)
    c = 280
    m = s.ellipse(c, c, 186, 186) * (1 - s.ellipse(c + 3, c + 2, 168, 170))
    s.wash(m, UMBER, 0.75, wob=2.5, edge=0.9, ew=4, gran=0.6, flow=0.6, fs=60)
    s.wash(s.ellipse(c, c, 170, 170), BURNT, 0.07, wob=3, bleed=10, edge=0.3)
    s.spatter(7, UMBER, 0.5, box=(c + 150, c + 60, c + 240, c + 190), r=(1.5, 6))
    s.save("tt_ring", crop=True, anchor=(c, c))


ALL = {"table": table, "saucer": saucer, "cup": cup, "spoon": spoon, "hand": hand, "sugar": sugar, "phone": phone, "napkin": napkin, "ring": ring}
