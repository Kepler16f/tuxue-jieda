# -*- coding: utf-8 -*-
"""应用图标生成：圆规绘图主题（工程图学）。

输出（site/assets/icon.svg + _tuxue_web/assets/*.png）：
  icon-only.png / icon-foreground.png / icon-background.png (1024, 供网页与参考)
绘制 4x 超采样再缩小，保证边缘平滑。
"""
import math
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "site" / "assets"
OUT = ROOT / "assets"
OUT.mkdir(parents=True, exist_ok=True)

TOP = (24, 116, 208)      # 渐变上
BOT = (8, 68, 138)        # 渐变下
WHITE = (255, 255, 255, 255)


def gradient_bg(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(TOP[i] + (BOT[i] - TOP[i]) * t) for i in range(3)) + (255,)
        ImageDraw.Draw(img).line([(0, y), (size, y)], fill=c)
    return img


def mask_rounded(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def mask_circle(size):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    return m


def draw_compass(d, cx, cy, s):
    """cx,cy=画布中心，s=缩放系数(1 对应 1024 画布的标称尺寸)。"""
    lw = int(58 * s)
    hinge = (cx, cy - int(170 * s))
    tipL = (cx - int(186 * s), cy + int(235 * s))
    tipR = (cx + int(186 * s), cy + int(235 * s))
    # 顶部手柄
    d.line([hinge[0], cy - int(300 * s), hinge[0], hinge[1] - int(30 * s)],
           fill=WHITE, width=int(40 * s))
    d.ellipse([hinge[0] - int(34 * s), cy - int(334 * s),
               hinge[0] + int(34 * s), cy - int(266 * s)], fill=WHITE)
    #  d.line([hinge, tipL], fill=WHITE, width=lw)
    d.line([hinge, tipR], fill=WHITE, width=lw)
    # 铰链圆环
    r = int(64 * s)
    d.ellipse([hinge[0] - r, hinge[1] - r, hinge[0] + r, hinge[1] + r],
              outline=WHITE, width=lw)
    # 针脚尖（左）：实心小圆点
    r2 = int(26 * s)
    d.ellipse([tipL[0] - r2, tipL[1] - r2, tipL[0] + r2, tipL[1] + r2], fill=WHITE)
    # 铅芯脚（右）：短粗笔尖
    d.line([tipR[0], tipR[1] - int(78 * s), tipR[0], tipR[1] + int(30 * s)],
           fill=WHITE, width=int(56 * s))
    # 弧线（过两脚尖）
    ra = math.hypot(186 * s, 405 * s)
    box = [cx - ra, cy - 170 * s - ra, cx + ra, cy - 170 * s + ra]
    d.arc(box, start=62, end=118, fill=WHITE, width=int(46 * s))


def make(size, shape):
    """size=最终像素, shape: 'rounded' | 'circle' | 'flat'(背景块)"""
    S = size * 4
    bg = gradient_bg(S)
    motif = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(motif)
    draw_compass(d, S // 2, S // 2 + int(10 * (S / 1024)), S / 1024)
    img = Image.alpha_composite(bg, motif)
    if shape == "rounded":
        img.putalpha(mask_rounded(S, int(S * 0.218)))
    elif shape == "circle":
        img.putalpha(mask_circle(S))
    return img.resize((size, size), Image.LANCZOS)


def make_foreground(size):
    """自适应图标前景：透明底，图案占中心 ~60%。"""
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = S / 1024 * 0.62
    draw_compass(d, S // 2, S // 2 + int(10 * k), k)
    return img.resize((size, size), Image.LANCZOS)


def main():
    S = 1024
    make(S, "rounded").save(OUT / "icon-only.png")
    make_foreground(S).save(OUT / "icon-foreground.png")
    bg = Image.new("RGBA", (S, S), BOT + (255,))
    bg.save(OUT / "icon-background.png")
    # 网页 favicon 用的 svg（简化同 motif）
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#1874D0"/><stop offset="1" stop-color="#08448A"/></linearGradient></defs>'
        '<rect width="192" height="192" rx="42" fill="url(#g)"/>'
        '<g stroke="#fff" fill="#fff" stroke-linecap="round">'
        '<line x1="96" y1="30" x2="96" y2="58" stroke-width="8"/>'
        '<circle cx="96" cy="26" r="7" stroke="none"/>'
        '<line x1="96" y1="66" x2="61" y2="112" stroke-width="11"/>'
        '<line x1="96" y1="66" x2="131" y2="112" stroke-width="11"/>'
        '<circle cx="96" cy="66" r="12" fill="none" stroke-width="11"/>'
        '<circle cx="61" cy="112" r="5" stroke="none"/>'
        '<line x1="131" y1="102" x2="131" y2="120" stroke-width="12"/>'
        '<path d="M52 108 A 44 44 0 0 0 140 108" fill="none" stroke-width="9"/>'
        '</g></svg>'
    )
    (WEB / "icon.svg").write_text(svg, encoding="utf-8")
    for n in ("icon-only", "icon-foreground", "icon-background"):
        p = OUT / (n + ".png")
        print(f"{p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
