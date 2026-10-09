"""The cup at eye level: the chorus's hero. The room behind is out of focus (wet-in-wet, no pen): the window to the
left, the warm wall to the right. Sheet 2560x1440."""
import math

import cv2
import numpy as np

from kit import *

SW, SH = 2560, 1440
TABLE_Y = 930
SAUCER = (1330, 1160)
CUP_BASE = (1330, 1128)


def bg():
    s = Sheet(SW, SH, 71)
    r = rs(71)
    # the window: cool, bright, soft bars
    s.glaze(RAIN, 0.55, grad=s.hgrad(1300, 1750, 1, 0), flow=0.5, fs=500)
    s.glaze(PRUSSIAN, 0.30, grad=s.hgrad(1200, 1700, 1, 0) * s.vgrad(300, 950, 0.2, 1), flow=0.5, fs=300)
    for i in range(26):          # lights of the street, already half dissolved
        x, y = r.random() * 1500, 250 + r.random() * 600
        m = s.blob(x, y, 30 + 50 * r.random(), 30 + 50 * r.random(), 0.2)
        s.lift(m, 0.7, soft=18, wob=6)
        if r.random() < 0.75:
            s.wash(m, [AMBER, ROSE, OCHRE, TEAL][int(r.random() * 4)], 0.35, wob=6, bleed=22, edge=0.1)
    for x, w in ((430, 62), (1130, 58)):
        s.wash(s.rect(x, -10, x + w, TABLE_Y), UMBER, 0.95, wob=6, bleed=24, edge=0.15)
    s.wash(s.rect(-10, 250, 1560, 300), UMBER, 0.8, wob=6, bleed=22, edge=0.15)
    s.wash(s.rect(1490, -10, 1580, TABLE_Y), UMBER, 1.0, wob=6, bleed=26, edge=0.15)        # the window's right jamb
    # the wall: warm
    wall = s.rect(1560, -10, SW + 10, TABLE_Y)
    s.wash(wall, OCHRE, 0.75, wob=8, bleed=40, edge=0.1, flow=0.5, fs=300)
    s.wash(wall, SIENNA, 0.35, wob=8, bleed=40, grad=s.rgrad(2150, 420, 200, 900, 0, 1), edge=0.1)
    s.wash(s.rect(1560, 700, SW + 10, TABLE_Y), TEAL, 0.9, wob=8, bleed=30, edge=0.15)       # wainscot
    dome = s.poly([(1960, 60), (2340, 60), (2420, 250), (1880, 250)])
    s.wash(dome, PRUSSIAN, 1.0, wob=6, bleed=22, edge=0.2)
    s.wash(s.rect(2140, -10, 2160, 70), SEPIA, 0.8, wob=2, bleed=6)
    s.lift(s.ellipse(2150, 270, 230, 40), 0.9, soft=24)
    # sill
    s.wash(s.rect(-10, 850, 1560, TABLE_Y), UMBER, 0.85, wob=5, bleed=20, edge=0.2)
    # the table: wood, sharper toward us
    top = s.rect(-10, TABLE_Y, SW + 10, SH + 10)
    wood(s, top, SIENNA, BURNT, 0.78, ang=0.0, n=70, seed=6, lw=1.5)
    s.wash(top, OCHRE, 0.25, wob=0, edge=0, grad=s.rgrad(1500, 1150, 200, 1100, 1, 0, sy=0.4))
    s.wash(top, UMBER, 0.5, wob=0, edge=0, grad=s.rgrad(1400, 1100, 700, 1700, 0, 1, sy=0.5), flow=0.4)
    s.lift(s.rect(-10, TABLE_Y, 1500, TABLE_Y + 46), 0.4, soft=14, wob=4)                # the window lying on the varnish
    s.wash(s.rect(-10, TABLE_Y - 6, SW + 10, TABLE_Y + 10), SEPIA, 0.7, wob=2, bleed=4)
    s.save("cs_bg", opaque=True, q=90)


def saucer():
    s = Sheet(1200, 420, 72)
    cx, cy = 600, 200
    s.wash(s.ellipse(cx + 40, cy + 34, 500, 104), SEPIA, 0.6, wob=3, bleed=22, edge=0.1)
    m = s.ellipse(cx, cy, 480, 100)
    base(s, m, CREAM, 0.28, wob=1.2, edge=0.3)
    s.wash(m, RAIN, 0.3, wob=2, bleed=16, grad=s.hgrad(cx - 480, cx, 1, 0))
    s.wash(m, OCHRE, 0.2, wob=2, bleed=16, grad=s.hgrad(cx, cx + 480, 0, 1))
    s.wash(m * (1 - s.ellipse(cx, cy - 12, 470, 90)), SLATE, 0.55, wob=1, soft=3)         # the lip nearest us
    s.wash(s.ellipse(cx + 20, cy + 6, 250, 44), UMBER, 0.4, wob=2, bleed=12)              # the cup's shadow in the well
    oval(s, cx, cy, 480, 100, 2.8, SEPIA, 1.5, twice=True)
    oval(s, cx, cy - 8, 300, 56, 1.5, SEPIA, 0.8, skip=0.3)
    # a little biscuit that comes with it
    b = s.poly([(cx - 400, cy - 14), (cx - 300, cy - 34), (cx - 250, cy - 8), (cx - 330, cy + 22), (cx - 400, cy + 12)])
    base(s, b, SIENNA, 0.8, wob=1.5, edge=0.5, gran=0.6)
    s.wash(b, BURNT, 0.4, wob=2, bleed=5, grad=s.vgrad(cy - 10, cy + 22))
    contour(s, b, 1.8, SEPIA, 1.2)
    s.spatter(8, UMBER, 0.6, box=(cx - 390, cy - 26, cx - 270, cy + 14), r=(1, 2.5))
    s.save("cs_saucer", crop=True, anchor=(cx, cy))


def cup():
    """Anchor at the middle of the foot. The rim centre is 330 px above it."""
    s = Sheet(1100, 760, 73)
    cx, ry_, by = 480, 150, 480
    prof = [(cx - 300, ry_), (cx - 292, ry_ + 110), (cx - 250, ry_ + 220), (cx - 190, ry_ + 296), (cx - 150, ry_ + 330), (cx + 150, ry_ + 330), (cx + 190, ry_ + 296), (cx + 250, ry_ + 220), (cx + 292, ry_ + 110), (cx + 300, ry_)]
    body = s.poly(prof, smooth=True)
    # handle (behind the body's edge)
    hp = [(cx + 280, ry_ + 60), (cx + 400, ry_ + 40), (cx + 460, ry_ + 110), (cx + 430, ry_ + 210), (cx + 330, ry_ + 262), (cx + 240, ry_ + 250)]
    ho = s.ribbon(hp, 50, profile=lambda t: 1 - 0.25 * t)
    base(s, ho, CREAM, 0.30, wob=1, edge=0.4)
    s.wash(ho, SLATE, 0.4, wob=1, soft=3, grad=s.vgrad(ry_ + 120, ry_ + 270))
    s.wash(ho, OCHRE, 0.25, wob=1, soft=3, grad=s.hgrad(cx + 380, cx + 470))
    contour(s, ho, 2.4, SEPIA, 1.4)
    base(s, body, CREAM, 0.26, wob=1.2, edge=0.3)
    s.wash(body, RAIN, 0.40, wob=2, bleed=24, grad=s.hgrad(cx - 300, cx - 40, 1, 0))                   # window side
    s.wash(body, SLATE, 0.30, wob=2, bleed=20, grad=s.hgrad(cx - 120, cx + 60, 0, 1) * s.hgrad(cx + 60, cx + 200, 1, 0))  # the turn of the form
    s.wash(body, OCHRE, 0.32, wob=2, bleed=22, grad=s.hgrad(cx + 120, cx + 300, 0, 1))                 # lamp side
    s.wash(body, UMBER, 0.28, wob=2, bleed=14, grad=s.vgrad(ry_ + 240, ry_ + 330, 0, 1))
    s.lift(s.poly([(cx - 236, ry_ + 60), (cx - 200, ry_ + 60), (cx - 176, ry_ + 230), (cx - 206, ry_ + 230)]), 0.7, soft=7)   # the window in the glaze
    band = body * s.vgrad(ry_ + 52, ry_ + 60) * (1 - s.vgrad(ry_ + 76, ry_ + 84))
    s.wash(band, TEAL, 1.0, wob=1, soft=1, edge=0.3)
    # rim and the coffee inside
    rim = s.ellipse(cx, ry_, 300, 60)
    base(s, rim, CREAM, 0.20, wob=1, edge=0.3)
    inner = s.ellipse(cx, ry_ + 2, 284, 50)
    s.wash(inner, UMBER, 0.5, wob=1, soft=2)
    cof = s.ellipse(cx, ry_ + 10, 268, 40) * inner
    s.lift(cof, 1.0, soft=1)
    s.wash(cof, COFFEE, 1.15, wob=1.2, edge=0.7, ew=6, flow=0.3, gran=0.5, body=1)
    s.wash(cof, BURNT, 0.45, wob=1, soft=3, grad=s.rgrad(cx + 90, ry_ + 6, 20, 200, 1, 0, sy=0.3))
    oval(s, cx, ry_, 300, 60, 2.8, SEPIA, 1.5, twice=True)
    oval(s, cx, ry_ + 3, 283, 49, 1.6, SEPIA, 1.0, skip=0.15)
    s.ink(prof[:5], 2.6, SEPIA, 1.5)
    s.ink(prof[5:], 2.6, SEPIA, 1.5)
    s.ink(ell(cx, ry_ + 330, 150, 20, 0.15, math.pi - 0.15, 20), 2.4, SEPIA, 1.4)
    s.save("cs_cup", crop=True, anchor=(cx, ry_ + 340), meta={"rim": [0, -340], "handle": [370, -190], "mouth": [0, -330, 268, 40]})


def hand():
    """The right hand through the cup's handle, from the side; the sleeve runs off to the right. Anchor at the handle."""
    s = Sheet(1300, 760, 74)
    ax, ay = 330, 400
    sleeve = s.poly([(720, 300), (1300, 250), (1300, 600), (730, 540)], smooth=False)
    base(s, sleeve, TEAL, 1.05, wob=2.5, edge=0.5, flow=0.5, fs=180, gran=0.5)
    s.wash(sleeve, PRUSSIAN, 0.7, wob=2, bleed=14, grad=s.vgrad(380, 600, 0.05, 1), edge=0.2)
    for i in range(30):
        x = 740 + i * 19
        s.ink([(x, 300 - (x - 720) * 0.086), (x + 6, 420), (x - 2, 540 + (x - 730) * 0.105)], 1.5, INKBLUE, 0.5, skip=0.35, clip=sleeve, tremor=1.1)
    contour(s, sleeve, 2.4, INKBLUE, 1.4)
    cuff = s.poly([(650, 300), (760, 286), (770, 556), (656, 540)])
    base(s, cuff, TEAL, 1.25, wob=1.5, edge=0.6)
    for i in range(12):
        s.ink([(660 + i * 9, 300 + i * 1), (664 + i * 9, 546)], 1.4, INKBLUE, 0.8, clip=cuff)
    contour(s, cuff, 2.0, INKBLUE, 1.3)
    palm = s.poly([(430, 318), (660, 306), (690, 420), (660, 536), (470, 530), (400, 430)])
    fs = [finger(s, [(470, 350), (370, 356), (318, 388), (330, 420)], 62), finger(s, [(460, 410), (360, 420), (310, 452), (326, 482)], 60),
          finger(s, [(466, 468), (380, 484), (340, 512), (356, 536)], 54), finger(s, [(486, 512), (420, 534), (396, 556)], 44)]
    thumb = finger(s, [(560, 324), (450, 276), (360, 282), (310, 306)], 66, tip=0.72)
    hm = np.maximum(palm, thumb)
    for f in fs:
        hm = np.maximum(hm, f)
    base(s, hm, SKIN, 0.62, wob=1.5, edge=0.35, flow=0.3)
    s.wash(hm, BURNT, 0.32, wob=2, bleed=12, grad=s.vgrad(300, 560, 0.05, 1), edge=0.2)
    s.wash(hm, ROSE, 0.16, wob=2, bleed=10, grad=s.rgrad(340, 420, 20, 160, 1, 0))
    contour(s, hm, 2.2, SEPIA, 1.3)
    for f in fs:
        contour(s, f, 1.4, SEPIA, 0.8)
    contour(s, thumb, 1.4, SEPIA, 0.8)
    s.save("cs_hand", crop=True, anchor=(ax, ay))


ALL = {"cup_bg": bg, "cup_saucer": saucer, "cup_cup": cup, "cup_hand": hand}
