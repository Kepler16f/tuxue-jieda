# -*- coding: utf-8 -*-
"""生成 Android 各密度启动图标 + splash，覆盖 Capacitor 模板默认图标。

  ic_launcher.png            传统图标(蓝渐变圆角+圆规)
  ic_launcher_round.png      圆形版
  ic_launcher_foreground.png 自适应前景(透明底+缩放的圆规)
  splash.png (port/land xxxhdpi) 蓝底居中图案
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from PIL import Image, ImageDraw

from compass_art import draw_compass

RES = pathlib.Path(__file__).resolve().parent.parent / "android" / "app" / "src" / "main" / "res"
TOP = (24, 116, 208)
BOT = (8, 68, 138)

LEGACY = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FOREGROUND = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}


def grad_bg(size):
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(TOP[i] + (BOT[i] - TOP[i]) * t) for i in range(3)) + (255,)
        d.line([(0, y), (size, y)], fill=c)
    return img


def legacy(size, round_):
    S = size * 4
    img = grad_bg(S)
    m = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    draw_compass(d, S // 2, S // 2 + int(10 * S / 1024), S / 1024)
    img = Image.alpha_composite(img, m)
    mask = Image.new("L", (S, S), 0)
    dm = ImageDraw.Draw(mask)
    if round_:
        dm.ellipse([0, 0, S - 1, S - 1], fill=255)
    else:
        dm.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.218), fill=255)
    img.putalpha(mask)
    return img.resize((size, size), Image.LANCZOS)


def foreground(size):
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = S / 1024 * 0.62
    draw_compass(d, S // 2, S // 2 + int(10 * k), k)
    return img.resize((size, size), Image.LANCZOS)


def main():
    made = 0
    for dens, px in LEGACY.items():
        d = RES / f"mipmap-{dens}"
        if not d.exists():
            print(f"skip missing {d}")
            continue
        legacy(px, False).save(d / "ic_launcher.png")
        legacy(px, True).save(d / "ic_launcher_round.png")
        foreground(FOREGROUND[dens]).save(d / "ic_launcher_foreground.png")
        made += 3

    # splash
    for d, w, h in [("drawable-port-xxxhdpi", 1280, 1920),
                    ("drawable-land-xxxhdpi", 1920, 1280)]:
        p = RES / d / "splash.png"
        if not p.exists():
            continue
        img = Image.new("RGB", (w, h), BOT)
        dr = ImageDraw.Draw(img)
        for y in range(h):
            t = y / (h - 1)
            c = tuple(int(TOP[i] + (BOT[i] - TOP[i]) * t) for i in range(3))
            dr.line([(0, y), (w, y)], fill=c)
        draw_compass(dr, w // 2, h // 2, min(w, h) / 1024 * 0.9)
        img.save(p)
    print(f"[icons] {made} files + 2 splash across {len(LEGACY)} densities")


if __name__ == "__main__":
    main()
