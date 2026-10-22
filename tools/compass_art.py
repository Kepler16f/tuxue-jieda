# -*- coding: utf-8 -*-
"""圆规图标绘制的共享逻辑：make_icon.py 与 make_android_icons.py 共用。"""
import math


def draw_compass(d, cx, cy, s, white=(255, 255, 255, 255)):
    """cx,cy=画布中心, s=缩放（1 = 1024 画布标称）。绘制圆规+弧线。"""
    lw = max(2, int(58 * s))
    hinge = (cx, cy - int(170 * s))
    tipL = (cx - int(186 * s), cy + int(235 * s))
    tipR = (cx + int(186 * s), cy + int(235 * s))
    # 顶部手柄
    d.line([hinge[0], cy - int(300 * s), hinge[0], hinge[1] - int(30 * s)],
           fill=white, width=max(2, int(40 * s)))
    r34 = int(34 * s)
    if r34 >= 2:
        d.ellipse([hinge[0] - r34, cy - int(334 * s), hinge[0] + r34, cy - int(266 * s)], fill=white)
    # 两腿
    d.line([hinge, tipL], fill=white, width=lw)
    d.line([hinge, tipR], fill=white, width=lw)
    # 铰链圆环
    r = max(2, int(64 * s))
    d.ellipse([hinge[0] - r, hinge[1] - r, hinge[0] + r, hinge[1] + r],
              outline=white, width=lw)
    # 左脚尖（针）
    r2 = max(1, int(26 * s))
    d.ellipse([tipL[0] - r2, tipL[1] - r2, tipL[0] + r2, tipL[1] + r2], fill=white)
    # 右脚尖（铅芯）
    d.line([tipR[0], tipR[1] - int(78 * s), tipR[0], tipR[1] + int(30 * s)],
           fill=white, width=max(2, int(56 * s)))
    # 弧线
    ra = math.hypot(186 * s, 405 * s)
    box = [cx - ra, cy - 170 * s - ra, cx + ra, cy - 170 * s + ra]
    d.arc(box, start=62, end=118, fill=white, width=max(1, int(46 * s)))
