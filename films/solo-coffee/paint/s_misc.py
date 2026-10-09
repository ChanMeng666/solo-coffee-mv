"""Things that belong to no one set: the sheet of paper the whole film is printed on, the brush stroke under the lyric."""
import math

import numpy as np

from kit import *


def paper():
    paper_tile(512, 3)


def band():
    """A dry-brushed stroke of coffee: the lyric sits on it. Stretched to the line's width by the page."""
    s = Sheet(1600, 220, 31)
    r = rs(31)
    pts = [(60, 112), (400, 104), (800, 114), (1200, 106), (1540, 112)]
    s.stroke(pts, 118, COFFEE, 1.25, taper=(0.05, 0.10), dry=0.16, edge=0.5, wob=3, flow=0.5, fs=200, gran=0.5,
             profile=lambda t: 0.82 + 0.18 * np.sin(t * 9 + 1) * np.sin(t * 3.1))
    s.stroke([(90, 118), (800, 122), (1500, 116)], 78, SEPIA, 0.85, taper=(0.08, 0.14), dry=0.30, edge=0.3, wob=2)
    s.stroke([(1380, 100), (1500, 108), (1590, 104)], 60, COFFEE, 0.6, taper=(0.0, 0.5), dry=0.62, edge=0.1)       # the brush running dry
    s.spatter(16, COFFEE, 0.7, box=(1420, 40, 1600, 190), r=(1, 4))
    s.save("ly_band", crop=True)


ALL = {"paper": paper, "band": band}
