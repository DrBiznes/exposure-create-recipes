#!/usr/bin/env python3
"""
Mod icon and README banner, drawn in the style of Exposure's own page art (cream cards, enlarged
item sprites, a dark label plate with pixel lettering).

    python tools/branding.py     # writes docs/icon.png, docs/banner.png and the in-jar icon.png

The camera and film sprites come from tools/exposure_ref.py (MIT, mortuusars); the cogwheel is drawn here.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import textures  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ("forge-1.20.1", "neoforge-1.21.1")

CREAM = (236, 228, 219)
CREAM_EDGE = (222, 212, 201)
PLATE = (74, 66, 63)
INK = (69, 64, 61)
INK_SOFT = (104, 97, 92)

FONT = {  # 5x7 pixel letters for the label plate
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    " ": ("000",) * 7,
}


def sprite(px, scale, size=16):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for p, c in px.items():
        img.putpixel(p, tuple(c) + (255,))
    return img.resize((size * scale, size * scale), Image.NEAREST)


COG = 22  # the cogwheel is larger than an item sprite so its teeth stay readable
WOOD = textures.ramp("3f2c17 553a1f 5a4424 614b2e 70522e 7a5a34 82613a")  # Create's cogwheel texture
SHAFT = textures.ramp("56544d 77746b 9b978d b9b6ad")                       # andesite shaft end


def cog():
    """Create's wooden cogwheel seen face-on: plank teeth, a recessed hub and the shaft end."""
    mid = (COG - 1) / 2
    px = {}
    for y in range(COG):
        for x in range(COG):
            dx, dy = x - mid, y - mid
            d = math.hypot(dx, dy)
            off = (math.atan2(dy, dx) + math.pi / 8) % (math.pi / 4) - math.pi / 8
            tooth = abs(d * math.sin(off)) < 1.9  # 8 square teeth, on the axes and diagonals
            if d > (10.7 if tooth else 7.9):
                continue
            light = -(dx + dy) / 15  # -1 lower right .. 1 upper left
            grain = (x * 7 + y * 13) % 5 == 0
            if max(abs(dx), abs(dy)) < 2:      # shaft end
                i = 0 if max(abs(dx), abs(dy)) < 1 else 3 if light > 0.05 else 1 if light < -0.05 else 2
                c = SHAFT[i]
            elif d < 4.2:                      # recessed hub
                i = 1 if light > 0 else 2
            elif d < 6.4:                      # disc face
                i = 3 + (light > 0.2) - grain * (light <= 0.2)
            elif d <= 7.9:                     # raised rim
                i = 6 if light > 0.25 else 5 if light > -0.25 else 3
            else:                              # teeth
                i = 5 if light > 0.2 else 4 if light > -0.3 else 2
                i -= grain
            if max(abs(dx), abs(dy)) >= 2:
                c = WOOD[max(i, 0)]
            px[(x, y)] = c
    # dark lower-right outline, like the item sprites
    shape = set(px)
    for (x, y) in shape:
        lower = ((x + 1, y) not in shape) + ((x, y + 1) not in shape)
        upper = ((x - 1, y) not in shape) + ((x, y - 1) not in shape)
        if lower:
            px[(x, y)] = WOOD[2 - lower]
        elif upper:
            px[(x, y)] = WOOD[6]
    return px


def card(size, radius):
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=CREAM_EDGE)
    d.rounded_rectangle((3, 3, w - 4, h - 4), radius - 3, fill=CREAM)
    return img


def plate(img, text, center, scale):
    cx, cy = center
    width = (sum(len(FONT[c][0]) + 1 for c in text) - 1) * scale
    pad = 4 * scale
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - width // 2 - pad, cy - 7 * scale // 2 - pad + scale,
                         cx + width // 2 + pad, cy + 7 * scale // 2 + pad - scale), 2 * scale, fill=PLATE)
    x = cx - width // 2
    for ch in text:
        for j, row in enumerate(FONT[ch]):
            for i, bit in enumerate(row):
                if bit == "1":
                    x0, y0 = x + i * scale, cy - 7 * scale // 2 + j * scale
                    d.rectangle((x0, y0, x0 + scale - 1, y0 + scale - 1), fill=CREAM)
        x += (len(FONT[ch][0]) + 1) * scale
    return img


def emblem(img, origin, scale):
    """Cogwheel turning behind the camera. `scale` is the camera's pixel size."""
    x, y = origin
    img.alpha_composite(sprite(cog(), scale, COG), (x + 3 * scale, y - 6 * scale))
    img.alpha_composite(sprite(textures.ref("camera"), scale), (x, y))


def icon():
    img = card((512, 512), 40)
    emblem(img, (70, 130), 16)
    plate(img, "CREATE RECIPES", (256, 426), 4)
    return img


def font(bold, size):
    return ImageFont.truetype("segoeuib.ttf" if bold else "segoeui.ttf", size)


def chevron(img, x, y, s):
    d = ImageDraw.Draw(img)
    for i, off in enumerate((0, 1, 2, 1, 0)):
        d.rectangle((x + off * s, y + i * s, x + off * s + s - 1, y + i * s + s - 1), fill=INK_SOFT)


def banner():
    img = card((1570, 380), 28)
    img.alpha_composite(sprite(cog(), 11, COG), (54, 69))
    d = ImageDraw.Draw(img)
    d.text((350, 34), "Exposure: Create Recipes", font=font(True, 62), fill=INK)
    d.text((352, 122), "Exposure's cameras and film, built on the assembly line.", font=font(False, 33), fill=INK_SOFT)

    # sequenced assembly strip: every in-between camera sprite, then the finished camera
    steps = textures.camera_stages() + [textures.ref("camera")]
    x, y, s = 350, 220, 6
    for n, px in enumerate(steps):
        if n:
            chevron(img, x - 34, y + 34, 5)
        img.alpha_composite(sprite(px, s), (x, y))
        x += 16 * s + 50

    films = ("black_and_white_film", "high_sensitivity_black_and_white_film", "color_film",
             "high_sensitivity_color_film")
    for n, name in enumerate(films):
        img.alpha_composite(sprite(textures.ref(name), 10), (1228 + n * 52, 150 + (n % 2) * 14))
    return img


if __name__ == "__main__":
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    logo = icon()
    logo.save(docs / "icon.png")
    banner().save(docs / "banner.png")
    for target in TARGETS:
        logo.save(ROOT / target / "src/main/resources/icon.png")
