"""The one person in the film, never seen from the front: dark bobbed hair, a deep teal jumper, and (when it is not
keeping the other chair company) a long persimmon coat. Also the hands that do things."""
import math

import cv2
import numpy as np

from kit import *

HAIR = (0.20, 0.14, 0.13)


def hair(s, cx, cy, rx, ry, drop, seed=1):
    """A bob seen from behind: the skull, then the hair falling to `drop` below the centre and curling in."""
    r = rs(seed)
    P = [(cx - rx * 1.02, cy), (cx - rx * 0.93, cy - ry * 0.62), (cx - rx * 0.45, cy - ry * 0.97), (cx, cy - ry * 1.04), (cx + rx * 0.45, cy - ry * 0.97),
         (cx + rx * 0.93, cy - ry * 0.62), (cx + rx * 1.02, cy), (cx + rx * 1.08, cy + drop * 0.6), (cx + rx * 0.96, cy + drop), (cx + rx * 0.62, cy + drop * 0.93),
         (cx + rx * 0.3, cy + drop * 0.84), (cx - rx * 0.3, cy + drop * 0.84), (cx - rx * 0.62, cy + drop * 0.93), (cx - rx * 0.96, cy + drop), (cx - rx * 1.08, cy + drop * 0.6)]
    m = s.poly(P)
    base(s, m, HAIR, 1.25, wob=2, edge=0.5, flow=0.5, fs=rx * 0.8, gran=0.4)
    s.wash(m, INKBLUE, 0.5, wob=2, bleed=rx * 0.06, grad=s.hgrad(cx - rx, cx + rx * 0.3, 1, 0), edge=0.2)       # cool on the window side
    s.lift(s.poly([(cx + rx * 0.25, cy - ry * 0.55), (cx + rx * 0.72, cy - ry * 0.30), (cx + rx * 0.86, cy + ry * 0.05), (cx + rx * 0.70, cy + ry * 0.02), (cx + rx * 0.40, cy - ry * 0.30)]), 0.34, soft=rx * 0.05, wob=3)   # lamp sheen
    s.wash(s.poly([(cx + rx * 0.3, cy - ry * 0.5), (cx + rx * 0.75, cy - ry * 0.25), (cx + rx * 0.8, cy)]), SIENNA, 0.3, wob=3, bleed=rx * 0.05, clip=m)
    for i in range(int(18 + rx * 0.1)):       # strands from the crown
        a = -0.95 + 1.9 * (i + r.random() * 0.6) / (18 + rx * 0.1)
        x0, y0 = cx + math.sin(a) * rx * 0.12, cy - ry * 0.9
        x1, y1 = cx + math.sin(a) * rx * 1.02, cy + drop * (0.55 + 0.4 * math.cos(a))
        s.ink([(x0, y0), ((x0 + x1) / 2 + math.sin(a) * rx * 0.32, (y0 + y1) / 2 - ry * 0.1), (x1, y1)], max(1.2, rx * 0.011), INK, 0.8, skip=0.3, clip=m, tremor=0.8)
    contour(s, m, max(2.0, rx * 0.014), INK, 1.4, tremor=0.6)
    return m


def jumper(s, m, seed=1, ribs=None):
    base(s, m, TEAL, 1.05, wob=2.5, edge=0.5, flow=0.5, fs=180, gran=0.5)
    roi = s._roi(m, 0)
    x0, x1 = roi[1].start, roi[1].stop
    s.wash(m, PRUSSIAN, 0.75, wob=2, bleed=14, grad=s.hgrad(x0, x0 + (x1 - x0) * 0.55, 1, 0.05), edge=0.2)       # shade on the window side... the lamp is to the right
    s.lift(m * s.hgrad(x0 + (x1 - x0) * 0.62, x1, 0, 1), 0.22, soft=10, wob=2)


def back():
    """Head and shoulders from behind, large: the foreground of every shot that looks out of the window."""
    s = Sheet(1500, 1200, 61)
    r = rs(61)
    torso = s.poly([(100, 1210), (130, 840), (250, 660), (510, 560), (640, 520), (860, 520), (990, 560), (1250, 660), (1370, 840), (1400, 1210)])
    jumper(s, torso)
    for i in range(34):                    # knit: soft vertical ribs that follow the shoulders
        x = 150 + i * 37 + r.random() * 6
        yt = 560 + 0.00028 * (x - 750) ** 2
        s.ink([(x, yt + 30), (x + (x - 750) * 0.04, 900), (x + (x - 750) * 0.06, 1200)], 1.6, INKBLUE, 0.5, skip=0.4, clip=torso, tremor=1.2)
    neck = s.poly([(668, 380), (832, 380), (850, 540), (650, 540)])
    base(s, neck, SKIN, 0.65, wob=1.5, edge=0.3)
    s.wash(neck, BURNT, 0.4, wob=2, bleed=10, grad=s.hgrad(650, 800, 1, 0.1))
    s.wash(neck, UMBER, 0.35, wob=2, bleed=8, grad=s.vgrad(380, 470, 1, 0))            # under the hair
    collar = s.poly([(610, 548), (700, 500), (800, 500), (890, 548), (860, 590), (750, 610), (640, 590)])
    base(s, collar, TEAL, 1.2, wob=2, edge=0.6)
    s.wash(collar, PRUSSIAN, 0.5, wob=2, bleed=6, grad=s.hgrad(610, 800, 1, 0))
    for i in range(15):
        x = 625 + i * 18
        s.ink([(x, 520 + abs(x - 750) * 0.2), (x + (x - 750) * 0.06, 600 - abs(x - 750) * 0.1)], 1.5, INKBLUE, 0.8, clip=collar)
    contour(s, collar, 2.2, INKBLUE, 1.3)
    contour(s, torso, 2.6, INKBLUE, 1.4)
    hair(s, 750, 250, 205, 232, 215, 3)
    s.save("fig_back", crop=True, anchor=(750, 540))


def arm():
    """The right arm raised with the cup, from behind. Anchor at the shoulder; the page swings it up."""
    s = Sheet(1100, 900, 62)
    sh = (160, 700)
    sleeve = s.ribbon([sh, (330, 640), (520, 500), (640, 360)], 190, profile=lambda t: 1.0 - 0.38 * t)
    jumper(s, sleeve)
    r = rs(62)
    for i in range(16):
        u = i / 15
        x, y = 190 + u * 430, 690 - u * 320
        s.ink([(x - 50, y - 60), (x, y), (x + 46, y + 62)], 1.5, INKBLUE, 0.5, skip=0.35, clip=sleeve)
    contour(s, sleeve, 2.4, INKBLUE, 1.4)
    cuff = s.ribbon([(622, 392), (668, 318)], 136)
    base(s, cuff, TEAL, 1.25, wob=1.5, edge=0.6)
    contour(s, cuff, 2.0, INKBLUE, 1.3)
    # the hand round the cup, seen from the back: knuckles toward us
    palm = s.poly([(640, 330), (720, 250), (800, 250), (830, 320), (790, 400), (700, 410)])
    fs = [finger(s, [(720, 262), (760, 200), (800, 190)], 44), finger(s, [(760, 256), (806, 206), (846, 204)], 44),
          finger(s, [(790, 270), (842, 232), (876, 238)], 40), finger(s, [(806, 300), (854, 276), (884, 286)], 34)]
    hm = palm.copy()
    for f in fs:
        hm = np.maximum(hm, f)
    # the cup first (behind the fingers)
    prof = [(742, 150), (752, 230), (790, 296), (830, 328), (950, 328), (990, 296), (1028, 230), (1038, 150)]
    hdl = s.ribbon([(1026, 176), (1084, 170), (1112, 214), (1090, 262), (1040, 276), (1004, 268)], 26)
    base(s, hdl, CREAM, 0.30, wob=1, edge=0.4)
    contour(s, hdl, 2.0, SEPIA, 1.3)
    cup = s.poly(prof, smooth=True)
    base(s, cup, CREAM, 0.28, wob=1.5, edge=0.4)
    s.wash(cup, RAIN, 0.34, wob=2, bleed=12, grad=s.hgrad(742, 880, 1, 0))
    s.wash(cup, OCHRE, 0.26, wob=2, bleed=12, grad=s.hgrad(900, 1038, 0, 1))
    s.wash(cup * s.vgrad(176, 181) * (1 - s.vgrad(190, 195)), TEAL, 1.0, wob=0.8, soft=1, edge=0.3)
    rim = s.ellipse(890, 150, 148, 30)
    base(s, rim, CREAM, 0.2, wob=1)
    s.wash(s.ellipse(890, 153, 132, 22), COFFEE, 1.05, wob=1, edge=0.5)
    oval(s, 890, 150, 148, 30, 2.2, SEPIA, 1.4)
    s.ink(prof[:4], 2.2, SEPIA, 1.4)
    s.ink(prof[4:], 2.2, SEPIA, 1.4)
    base(s, hm, SKIN, 0.62, wob=1.5, edge=0.35)
    s.wash(hm, BURNT, 0.32, wob=2, bleed=8, grad=s.vgrad(250, 420, 0.1, 1))
    contour(s, hm, 2.0, SEPIA, 1.3)
    for f in fs[:3]:
        contour(s, f, 1.3, SEPIA, 0.7)
    s.save("fig_arm", crop=True, anchor=sh)


def sit():
    """Seated, from behind, about half the size of fig_back. Anchor at the middle of the seat."""
    s = Sheet(800, 1100, 63)
    r = rs(63)
    larm = s.poly([(205, 468), (158, 560), (146, 700), (188, 742), (246, 700), (250, 560)])
    rarm = s.poly([(596, 468), (652, 556), (676, 684), (634, 736), (572, 694), (552, 560)])
    for m in (larm, rarm):
        jumper(s, m)
        contour(s, m, 2.0, INKBLUE, 1.3)
    hips = s.poly([(214, 880), (586, 880), (600, 990), (200, 990)])
    base(s, hips, PAYNE, 1.1, wob=2, edge=0.5)
    s.wash(hips, INKBLUE, 0.5, wob=2, bleed=8, grad=s.hgrad(200, 420, 1, 0))
    contour(s, hips, 2.0, INKBLUE, 1.3)
    torso = s.poly([(200, 474), (232, 412), (330, 386), (470, 386), (568, 412), (600, 474), (586, 640), (560, 780), (584, 900), (216, 900), (240, 780), (214, 640)])
    jumper(s, torso)
    for i in range(20):
        x = 226 + i * 18.5
        s.ink([(x, 420 + abs(x - 400) * 0.1), (x + (x - 400) * 0.03, 660), (x + (x - 400) * 0.02, 896)], 1.3, INKBLUE, 0.5, skip=0.4, clip=torso, tremor=1.0)
    s.ink([(250, 870), (400, 884), (550, 870)], 3.0, INKBLUE, 0.9)                        # hem rib
    contour(s, torso, 2.2, INKBLUE, 1.4)
    neck = s.poly([(366, 318), (434, 318), (444, 400), (356, 400)])
    base(s, neck, SKIN, 0.65, wob=1, edge=0.3)
    s.wash(neck, UMBER, 0.4, wob=1, bleed=5, grad=s.vgrad(318, 370, 1, 0))
    collar = s.poly([(336, 404), (372, 378), (428, 378), (464, 404), (448, 424), (400, 434), (352, 424)])
    base(s, collar, TEAL, 1.2, wob=1.5, edge=0.6)
    contour(s, collar, 1.8, INKBLUE, 1.3)
    hair(s, 400, 250, 100, 112, 108, 5)
    s.save("fig_sit", crop=True, anchor=(400, 980))


def stand():
    """Standing, from behind, with the coat on and the umbrella furled in the right hand. Anchor between the feet."""
    s = Sheet(760, 1500, 64)
    r = rs(64)
    cx = 360
    # legs and shoes
    for x in (cx - 62, cx + 42):
        leg = s.poly([(x, 1150), (x + 62, 1150), (x + 54, 1400), (x + 8, 1400)], smooth=False)
        base(s, leg, PAYNE, 1.15, wob=1.5, edge=0.5)
        contour(s, leg, 2.0, INKBLUE, 1.3)
        shoe = s.poly([(x - 6, 1396), (x + 66, 1396), (x + 72, 1440), (x + 30, 1452), (x - 12, 1440)])
        base(s, shoe, SEPIA, 1.2, wob=1.5, edge=0.5)
        contour(s, shoe, 2.0, INK, 1.4)
    # umbrella, furled, hanging from the right hand
    um = s.ribbon([(560, 770), (590, 1000), (616, 1250)], 34, profile=lambda t: 1 - 0.75 * t)
    base(s, um, PRUSSIAN, 1.2, wob=1.2, edge=0.5)
    contour(s, um, 1.8, INKBLUE, 1.3)
    s.ink(spline([(560, 772), (548, 720), (572, 700), (592, 722)]), 5, SEPIA, 1.4, taper=(0, 0))
    # the coat
    lsl = s.poly([(178, 352), (138, 470), (120, 660), (126, 800), (182, 806), (206, 660), (226, 480)])
    rsl = s.poly([(542, 352), (584, 470), (602, 640), (592, 786), (540, 790), (520, 650), (498, 480)])
    body = s.poly([(180, 350), (236, 318), (310, 304), (410, 304), (486, 318), (540, 350), (548, 640), (566, 900), (590, 1180), (380, 1200), (360, 1196), (340, 1200), (130, 1180), (154, 900), (172, 640)], smooth=True)

    def cloth(m, deep=0.55):
        base(s, m, PERSIMMON, 1.05, wob=2.5, edge=0.5, flow=0.5, fs=160, gran=0.45)
        s.wash(m, BURNT, deep, wob=2, bleed=14, grad=s.hgrad(120, 380, 1, 0.05), edge=0.2)
        s.lift(m * s.hgrad(440, 600, 0, 1), 0.18, soft=10, wob=2)
    cloth(body)
    for (a, b, c, w, k) in (((cx, 330), (cx + 4, 760), (cx - 6, 1196), 3.0, 0.9), ((250, 700), (238, 950), (214, 1180), 2.0, 0.6), ((470, 700), (486, 950), (506, 1180), 2.0, 0.6)):
        s.ink([a, b, c], w, BURNT, k, skip=0.1, clip=body)
    for (a, b, c, w) in (((230, 700), (210, 940), (176, 1180), 60), ((470, 720), (492, 960), (540, 1180), 54), ((340, 760), (330, 980), (300, 1190), 40)):
        s.stroke([a, b, c], w, BURNT, 0.3, wob=3, bleed=10, clip=body, taper=(0.3, 0.0), edge=0.2)        # folds below the belt
    belt = s.poly([(168, 624), (552, 624), (556, 668), (166, 668)])
    base(s, belt, PERSIMMON, 1.2, wob=1.5, edge=0.6)
    s.wash(belt, BURNT, 0.5, wob=1, soft=2)
    contour(s, belt, 1.8, SEPIA, 1.2)
    contour(s, body, 2.4, SEPIA, 1.4)
    for m in (lsl, rsl):
        cloth(m, 0.4)
        contour(s, m, 2.2, SEPIA, 1.4)
    for (x, y) in ((154, 806), (566, 790)):
        hand = s.ellipse(x, y + 16, 30, 34)
        base(s, hand, SKIN, 0.62, wob=1.2, edge=0.4)
        contour(s, hand, 1.8, SEPIA, 1.2)
    collar = s.poly([(250, 322), (310, 286), (410, 286), (470, 322), (440, 350), (360, 362), (280, 350)])
    cloth(collar, 0.3)
    contour(s, collar, 2.0, SEPIA, 1.3)
    neck = s.poly([(330, 250), (392, 250), (398, 300), (324, 300)])
    base(s, neck, SKIN, 0.65, wob=1, edge=0.3)
    s.wash(neck, UMBER, 0.4, wob=1, bleed=5)
    hair(s, cx, 190, 92, 104, 100, 7)
    s.save("fig_stand", crop=True, anchor=(cx, 1450))


def pointer():
    """The back of the right hand, index finger out: it draws on the fogged glass. Anchor at the fingertip."""
    s = Sheet(900, 1200, 65)
    tip = (300, 120)
    sleeve = s.poly([(430, 760), (640, 700), (900, 1100), (900, 1200), (560, 1200)], smooth=False)
    jumper(s, sleeve)
    r = rs(65)
    for i in range(22):
        u = i / 21
        s.ink([(450 + u * 330, 760 + u * 440), (640 + u * 250, 700 + u * 400)], 1.5, INKBLUE, 0.5, skip=0.35, clip=sleeve)
    contour(s, sleeve, 2.4, INKBLUE, 1.4)
    cuff = s.poly([(404, 720), (600, 640), (660, 720), (470, 810)])
    base(s, cuff, TEAL, 1.25, wob=1.5, edge=0.6)
    for i in range(9):
        u = i / 8
        s.ink([(414 + u * 190, 716 - u * 74), (474 + u * 186, 800 - u * 80)], 1.4, INKBLUE, 0.8, clip=cuff)
    contour(s, cuff, 2.0, INKBLUE, 1.3)
    palm = s.poly([(330, 470), (430, 410), (540, 430), (600, 540), (590, 680), (480, 760), (400, 730), (340, 620)])
    idx = finger(s, [(390, 470), (340, 300), tip], 78, tip=0.7)
    others = [finger(s, [(460, 450), (458, 404), (480, 430), (486, 474)], 72), finger(s, [(520, 462), (528, 420), (548, 450), (544, 504)], 66),
              finger(s, [(566, 506), (590, 474), (604, 506), (590, 560)], 58)]
    thumb = finger(s, [(370, 640), (280, 560), (200, 480), (140, 440)], 84, tip=0.7)      # out to the side, so the pointing finger is plainly the first one
    hm = np.maximum(np.maximum(palm, idx), thumb)
    for f in others:
        hm = np.maximum(hm, f)
    base(s, hm, SKIN, 0.62, wob=1.5, edge=0.35, flow=0.3)
    s.wash(hm, BURNT, 0.30, wob=2, bleed=12, grad=s.hgrad(330, 620, 0.1, 1) * s.vgrad(200, 760, 0.3, 1), edge=0.2)
    s.wash(hm, ROSE, 0.18, wob=2, bleed=10, grad=s.rgrad(tip[0] + 10, tip[1] + 40, 10, 130, 1, 0))
    contour(s, hm, 2.2, SEPIA, 1.3)
    for f in others:
        contour(s, f, 1.4, SEPIA, 0.8)
    s.ink([(372, 300), (356, 290), (338, 296)], 1.4, BURNT, 0.8)       # knuckle creases
    s.ink([(402, 420), (384, 404), (362, 410)], 1.4, BURNT, 0.8)
    s.ink(ell(tip[0] + 6, tip[1] + 30, 22, 26, 3.6, 5.9, 12), 1.3, BURNT, 0.8)   # the nail
    s.save("fig_point", crop=True, anchor=tip)


def palm():
    """The flat of the hand, from behind, fingers together: it wipes the glass. Anchor at the middle of the palm."""
    s = Sheet(900, 1200, 66)
    sleeve = s.poly([(360, 800), (600, 800), (700, 1200), (300, 1200)], smooth=False)
    jumper(s, sleeve)
    for i in range(14):
        u = i / 13
        s.ink([(372 + u * 220, 804), (316 + u * 370, 1196)], 1.5, INKBLUE, 0.5, skip=0.35, clip=sleeve)
    contour(s, sleeve, 2.4, INKBLUE, 1.4)
    cuff = s.poly([(340, 740), (620, 740), (630, 830), (330, 830)])
    base(s, cuff, TEAL, 1.25, wob=1.5, edge=0.6)
    for i in range(12):
        s.ink([(352 + i * 23, 744), (350 + i * 23.5, 826)], 1.4, INKBLUE, 0.8, clip=cuff)
    contour(s, cuff, 2.0, INKBLUE, 1.3)
    pm = s.poly([(350, 470), (600, 450), (630, 600), (600, 760), (370, 760), (330, 620)])
    fs = [finger(s, [(380, 480), (350, 300), (340, 190)], 70), finger(s, [(448, 470), (440, 250), (438, 120)], 74),
          finger(s, [(516, 466), (528, 260), (536, 150)], 72), finger(s, [(580, 480), (610, 330), (626, 240)], 62)]
    thumb = finger(s, [(350, 660), (250, 560), (200, 450)], 76, tip=0.75)
    hm = np.maximum(pm, thumb)
    for f in fs:
        hm = np.maximum(hm, f)
    base(s, hm, SKIN, 0.62, wob=1.5, edge=0.35, flow=0.3)
    s.wash(hm, BURNT, 0.30, wob=2, bleed=12, grad=s.vgrad(300, 780, 0.1, 1), edge=0.2)
    contour(s, hm, 2.2, SEPIA, 1.3)
    for (a, b) in (((412, 470), (398, 300)), ((482, 462), (486, 280)), ((550, 470), (566, 320))):
        s.ink([a, ((a[0] + b[0]) / 2 + 3, (a[1] + b[1]) / 2), b], 1.5, SEPIA, 1.0, taper=(0.3, 0.1))
    for (x, y) in ((364, 330), (440, 290), (526, 300), (606, 366), (366, 480), (446, 468), (520, 466), (584, 484)):
        s.ink([(x - 12, y - 3), (x, y + 3), (x + 12, y - 2)], 1.3, BURNT, 0.8)
    s.save("fig_palm", crop=True, anchor=(480, 610))


ALL = {"fig_back": back, "fig_arm": arm, "fig_sit": sit, "fig_point": pointer, "fig_palm": palm}        # stand() is kept for reference but not built
