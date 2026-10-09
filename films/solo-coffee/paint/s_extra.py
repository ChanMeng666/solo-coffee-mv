"""Late additions: her walk (in profile, two drawings), the milk jug, the cup when it is empty."""
import math

import cv2
import numpy as np

from kit import *
from s_figure import HAIR
from s_table import CUP_R, COF_R


def cloth(s, m, deep=0.5, x0=250, x1=560):
    base(s, m, PERSIMMON, 1.05, wob=2.5, edge=0.5, flow=0.5, fs=160, gran=0.45)
    s.wash(m, BURNT, deep, wob=2, bleed=14, grad=s.hgrad(x0, x1, 0.05, 1), edge=0.2)       # the lamp is behind her now: shade toward her back
    s.lift(m * s.hgrad(x0, x0 + 90, 1, 0), 0.16, soft=10, wob=2)


def walk(frame):
    """She walks to the left, coat on, umbrella furled in her hand. frame 0: legs apart (contact); frame 1: legs passing.
    Anchor between the feet. Hair hides the face: a bob in profile, a line for the brow, nose and chin and nothing else."""
    s = Sheet(820, 1500, 101 + frame)
    cx, gy = 410, 1450
    k = 1 if frame == 0 else 0
    # --- legs and shoes (far leg first)
    def leg(hip, knee, foot, far):
        m = s.ribbon([hip, knee, foot], 62, profile=lambda t: 1.0 - 0.32 * t)
        base(s, m, PAYNE, 1.2 if far else 1.1, wob=1.5, edge=0.5)
        if far:
            s.wash(m, INKBLUE, 0.5, wob=1, soft=2)
        contour(s, m, 2.0, INKBLUE, 1.3)
        sh = s.poly([(foot[0] + 26, foot[1] - 22), (foot[0] + 30, foot[1] + 14), (foot[0] - 58, foot[1] + 16), (foot[0] - 66, foot[1] + 2), (foot[0] - 30, foot[1] - 14)])
        base(s, sh, SEPIA, 1.2, wob=1.2, edge=0.5)
        contour(s, sh, 1.8, INK, 1.4)
    if frame == 0:
        leg((cx + 30, 1120), (cx + 96, 1280), (cx + 150, gy - 34), True)        # back leg, pushing off
        leg((cx - 10, 1120), (cx - 70, 1280), (cx - 120, gy - 10), False)       # front leg, heel down
    else:
        leg((cx + 20, 1120), (cx + 50, 1270), (cx + 70, gy - 70), True)         # swinging through, foot lifted
        leg((cx + 4, 1120), (cx + 6, 1290), (cx + 10, gy - 10), False)          # standing leg
    # --- far arm (behind the body), swinging opposite to the near one
    fa = [(cx + 30, 372), (cx + 60 - 90 * k, 560), (cx + 80 - 170 * k, 740)]
    fm = s.ribbon(fa, 84, profile=lambda t: 1.0 - 0.25 * t)
    cloth(s, fm, 0.75)
    contour(s, fm, 2.0, SEPIA, 1.3)
    # --- the coat, in profile: straight front, the back swinging out with the stride
    sw = 34 * k
    body = s.poly([(cx - 70, 322), (cx - 20, 306), (cx + 50, 310), (cx + 96, 350), (cx + 110, 640), (cx + 128 + sw, 920), (cx + 150 + sw * 1.6, 1180), (cx + 20, 1198), (cx - 112 - sw * 0.8, 1176), (cx - 96, 900), (cx - 84, 640), (cx - 92, 420)], smooth=True)
    cloth(s, body)
    for (a, b, c_, w) in (((cx + 40, 700), (cx + 70 + sw * 0.5, 950), (cx + 104 + sw * 1.3, 1180), 56), ((cx - 30, 720), (cx - 44, 960), (cx - 70 - sw * 0.6, 1176), 44)):
        s.stroke([a, b, c_], w, BURNT, 0.3, wob=3, bleed=10, clip=body, taper=(0.3, 0.0), edge=0.2)
    s.ink([(cx - 78, 430), (cx - 84, 640), (cx - 96, 900), (cx - 110 - sw * 0.8, 1170)], 2.0, BURNT, 0.8, skip=0.1)           # the front edge, doubled
    belt = s.poly([(cx - 88, 626), (cx + 112, 626), (cx + 114, 668), (cx - 90, 668)], smooth=False) * (body > 0.5)
    base(s, belt, PERSIMMON, 1.2, wob=1.5, edge=0.6)
    s.wash(belt, BURNT, 0.5, wob=1, soft=2)
    contour(s, belt, 1.8, SEPIA, 1.2)
    contour(s, body, 2.4, SEPIA, 1.4)
    # --- near arm with the furled umbrella
    hand = (cx - 60 + 150 * k, 760)
    na = [(cx + 10, 366), (cx - 10 + 60 * k, 560), hand]
    # the umbrella hangs from the hand, tip forward and down
    tip = (hand[0] - 120 + 40 * k, 1230)
    um = s.ribbon([(hand[0] + 6, hand[1] - 10), ((hand[0] + tip[0]) / 2, (hand[1] + tip[1]) / 2 + 10), tip], 38, profile=lambda t: 1 - 0.78 * t)
    base(s, um, PERSIMMON, 1.25, wob=1.2, edge=0.6)
    s.wash(um, BURNT, 0.7, wob=1, soft=2)
    contour(s, um, 1.8, SEPIA, 1.3)
    s.ink(spline([(hand[0] + 8, hand[1] - 8), (hand[0] + 30, hand[1] - 50), (hand[0] + 4, hand[1] - 66), (hand[0] - 14, hand[1] - 46)]), 5, SEPIA, 1.4, taper=(0, 0))
    nm = s.ribbon(na, 92, profile=lambda t: 1.0 - 0.25 * t)
    cloth(s, nm, 0.4)
    contour(s, nm, 2.2, SEPIA, 1.4)
    hm = np.maximum(s.ellipse(hand[0], hand[1] + 16, 26, 30), finger(s, [(hand[0] - 6, hand[1] + 6), (hand[0] - 26, hand[1] + 26), (hand[0] - 16, hand[1] + 44)], 22))
    base(s, hm, SKIN, 0.62, wob=1.2, edge=0.4)
    contour(s, hm, 1.7, SEPIA, 1.2)
    for q in range(3):
        s.ink([(hand[0] - 10 + q * 12, hand[1] + 22), (hand[0] - 6 + q * 12, hand[1] + 42)], 1.2, BURNT, 0.8)
    collar = s.poly([(cx - 80, 330), (cx - 30, 292), (cx + 50, 290), (cx + 86, 330), (cx + 40, 356), (cx - 30, 360)])
    cloth(s, collar, 0.3)
    contour(s, collar, 2.0, SEPIA, 1.3)
    # --- head: skin first (a narrow strip of profile), then the bob over it
    neck = s.poly([(cx - 30, 250), (cx + 36, 250), (cx + 40, 304), (cx - 36, 304)])
    base(s, neck, SKIN, 0.65, wob=1, edge=0.3)
    s.wash(neck, UMBER, 0.4, wob=1, bleed=5)
    hx, hy = cx - 4, 190
    face = s.poly([(hx - 70, hy - 44), (hx - 92, hy - 6), (hx - 104, hy + 20), (hx - 90, hy + 30), (hx - 94, hy + 54), (hx - 78, hy + 78), (hx - 40, hy + 86), (hx - 20, hy - 44)])
    base(s, face, SKIN, 0.62, wob=1.2, edge=0.3)
    s.wash(face, ROSE, 0.14, wob=2, bleed=8)
    s.ink([(hx - 78, hy - 34), (hx - 94, hy - 4), (hx - 104, hy + 20), (hx - 90, hy + 30), (hx - 94, hy + 54), (hx - 78, hy + 78), (hx - 44, hy + 86)], 1.9, SEPIA, 1.2)
    hair = s.poly([(hx - 84, hy - 30), (hx - 70, hy - 80), (hx - 10, hy - 108), (hx + 60, hy - 92), (hx + 100, hy - 30), (hx + 108, hy + 50), (hx + 92, hy + 104), (hx + 40, hy + 96), (hx - 6, hy + 84),
                   (hx - 34, hy + 92), (hx - 44, hy + 40), (hx - 40, hy - 14), (hx - 62, hy - 26)])
    base(s, hair, HAIR, 1.25, wob=2, edge=0.5, flow=0.5, fs=80, gran=0.4)
    s.lift(s.poly([(hx + 10, hy - 70), (hx + 60, hy - 50), (hx + 84, hy), (hx + 66, hy - 4), (hx + 30, hy - 40)]), 0.32, soft=5, wob=3)
    r = rs(5)
    for i in range(16):
        a = -0.5 + 1.9 * (i + r.random() * 0.6) / 16
        s.ink([(hx + 10 + math.sin(a) * 12, hy - 96), (hx + 10 + math.sin(a) * 66, hy - 10), (hx + 14 + math.sin(a) * 84, hy + 92)], 1.3, INK, 0.8, skip=0.3, clip=hair, tremor=0.8)
    contour(s, hair, 2.0, INK, 1.4)
    s.save(f"fig_walk{frame}", crop=True, anchor=(cx, gy))


def jug():
    """A small milk jug from above. Anchor at the tip of its spout (which points left)."""
    s = Sheet(520, 420, 111)
    cx, cy, R = 300, 210, 108
    s.wash(s.ellipse(cx + 22, cy + 30, R + 6, R + 6), SEPIA, 0.55, wob=2, bleed=12, edge=0.1)
    hp = [(cx + 80, cy - 46), (cx + 150, cy - 60), (cx + 196, cy - 10), (cx + 176, cy + 56), (cx + 96, cy + 60)]
    ho = s.ribbon(hp, 34)
    base(s, ho, CREAM, 0.30, wob=1, edge=0.4)
    s.wash(ho, SLATE, 0.35, wob=1, soft=2, grad=s.vgrad(cy - 20, cy + 60))
    contour(s, ho, 2.2, SEPIA, 1.4)
    body = np.maximum(s.ellipse(cx, cy, R, R), s.poly([(cx - 70, cy - 60), (cx - 150, cy - 14), (cx - 168, cy), (cx - 150, cy + 14), (cx - 70, cy + 60)]))
    base(s, body, CREAM, 0.26, wob=1.0, edge=0.3)
    s.wash(body, RAIN, 0.25, wob=0, edge=0, grad=s.rgrad(cx + 70, cy + 80, 30, 200, 1, 0))
    inner = np.maximum(s.ellipse(cx, cy, R - 16, R - 16), s.poly([(cx - 66, cy - 40), (cx - 140, cy - 8), (cx - 150, cy), (cx - 140, cy + 8), (cx - 66, cy + 40)]))
    s.wash(inner, UMBER, 0.28, wob=1, soft=2, edge=0.5)
    milk = np.maximum(s.ellipse(cx, cy, R - 24, R - 24), s.poly([(cx - 60, cy - 30), (cx - 132, cy - 5), (cx - 138, cy), (cx - 132, cy + 5), (cx - 60, cy + 30)]))
    s.lift(milk, 1.0, soft=1.5, wob=1)
    s.wash(milk, CREAM, 0.10, wob=1, edge=0.4, body=1)
    s.wash(milk, RAIN, 0.14, wob=2, bleed=8, grad=s.rgrad(cx + 40, cy + 40, 10, 120, 1, 0))
    contour(s, body, 2.6, SEPIA, 1.5)
    contour(s, inner, 1.5, SEPIA, 0.9, skip=0.15)
    s.save("tt_jug", crop=True, anchor=(cx - 166, cy), meta={"handle": [344, 0]})


def cup_empty():
    """The cup from above when she has finished: cream china, the rings each sip left, a last brown coin at the bottom."""
    s = Sheet(760, 760, 112)
    c = 380
    r = rs(112)
    sh = s.ellipse(c + 26, c + 34, CUP_R + 4, CUP_R + 4)
    s.wash(sh, SEPIA, 0.55, wob=2, bleed=12, edge=0.1)
    hp = [(c + 170, c + 52), (c + 262, c + 86), (c + 318, c + 122), (c + 306, c + 170), (c + 244, c + 150), (c + 176, c + 104)]
    hm = s.poly(hp)
    base(s, hm, CREAM, 0.34, wob=1)
    s.wash(hm, SLATE, 0.35, wob=1, soft=2, grad=s.vgrad(c + 90, c + 180))
    s.ink(hp + [hp[0]], 2.4, SEPIA, 1.5)
    m = s.ellipse(c, c, CUP_R, CUP_R)
    base(s, m, CREAM, 0.26, wob=1.0, edge=0.3)
    s.wash(m, RAIN, 0.25, wob=0, edge=0, grad=s.rgrad(c + 120, c + 130, 40, 300, 1, 0))
    inner = s.ellipse(c, c, COF_R + 8, COF_R + 8)
    s.wash(inner, UMBER, 0.34, wob=1, soft=1.5, edge=0.5)
    well = s.ellipse(c, c, COF_R, COF_R)
    s.lift(well, 0.9, soft=1.5, wob=1)
    s.wash(well, CREAM, 0.34, wob=1.5, edge=0.4, flow=0.4, fs=80, gran=0.5, body=1)
    s.wash(well, SLATE, 0.5, wob=0, edge=0, grad=s.rgrad(c - 30, c - 40, COF_R * 0.45, COF_R, 0, 1))             # the wall of the cup, in its own shadow
    s.wash(well, OCHRE, 0.22, wob=0, edge=0, grad=s.rgrad(c + 40, c + 50, 10, 150, 1, 0))                        # the lamp, in the glaze
    for i, rr in enumerate((166, 146, 121, 92)):                                                                 # tide marks
        a0 = r.random() * 6.28
        s.ink(ell(c + 3 * i, c + 4 * i, rr, rr * 0.98, a0, a0 + 3.2 + 1.8 * r.random(), 60), 3.2 + 2.5 * r.random(), BURNT, 0.5 + 0.2 * r.random(), tremor=1.4, skip=0.25, dry=0.5)
        s.wash(s.ellipse(c + 3 * i, c + 4 * i, rr, rr) * (1 - s.ellipse(c + 3 * i, c + 4 * i, rr - 9, rr - 9)), BURNT, 0.16, wob=2, bleed=4, edge=0.6)
    dreg = s.blob(c + 16, c + 22, 62, 54, 0.22, seed=7)
    s.wash(dreg, COFFEE, 1.0, wob=2, edge=0.9, ew=5, gran=0.6, flow=0.5, fs=30)
    s.wash(s.blob(c + 16, c + 22, 92, 80, 0.25, seed=9), BURNT, 0.22, wob=3, bleed=10, edge=0.4)
    s.spatter(18, COFFEE, 0.6, box=(c - 110, c - 110, c + 120, c + 120), r=(0.8, 2.6))
    oval(s, c, c, CUP_R, CUP_R, 2.8, SEPIA, 1.6, twice=True)
    oval(s, c, c, COF_R + 6, COF_R + 6, 1.8, SEPIA, 1.1, skip=0.15)
    s.save("tt_cup_empty", crop=True, anchor=(c, c))


ALL = {"walk0": lambda: walk(0), "walk1": lambda: walk(1), "jug": jug, "cup_empty": cup_empty}
