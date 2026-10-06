#!/usr/bin/env python3
"""
Procedural art for the incomplete (sequenced assembly) items.

Every incomplete item gets one 16x16 sprite per assembly stage; the item model picks a stage from
Create's assembly progress (see ClientSetup.java and the model overrides written by generate.py).
The stage lists below follow the BASE recipe of each item step by step: with N steps there are
N-1 in-between states, so an item with K = N-1 stages shows exactly one sprite per finished step.
Recipes that share an item but have a different step count just spread over the same sprites.

    python tools/textures.py preview.png     # enlarged contact sheet of every sprite

Style follows Exposure's own item sprites (tools/exposure_ref.py): same palettes, top-left light,
dark lower-right rims. The last film stages and all camera stages are cut out of the finished
Exposure sprites so they line up with the item the assembly turns into.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exposure_ref import REF  # noqa: E402

CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(s):
    return [rgb(h) for h in s.split()]


def ref(name):
    """Reference sprite as {(x, y): (r, g, b)}."""
    pal, rows = REF[name]
    pal = ramp(pal)
    return {(x, y): pal[CHARS.index(c)] for y, row in enumerate(rows) for x, c in enumerate(row) if c != "."}


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def remap(px, colors):
    """Recolor a sprite onto a dark-to-light ramp by luminance, keeping its shading."""
    lo = min(lum(c) for c in px.values())
    hi = max(lum(c) for c in px.values())
    last = len(colors) - 1
    return {p: colors[round((lum(c) - lo) / (hi - lo) * last)] for p, c in px.items()}


# ---------------------------------------------------------------- palettes (sampled from Exposure)

IRON = ramp("151413 312f2c 524f48 7b766e a19f98 cfcec9 e4e3dd f2f2ee")      # B&W canister body
GOLD = ramp("191309 79470e 8d5d1d a8650f c88325 de9d40 f5cf74 ffeca1")      # color canister body
FILM_BW = ramp("1a1918 282726 373534 4c4947 77726e a6a09b")                 # B&W film tongue
FILM_COLOR = ramp("26140c 402718 5a3322 74442f ae7049 d29c69")              # color film tongue
PURPLE = ramp("2f2644 443764 524379 8063bd 916fd7")                         # high-sensitivity band
KELP = ramp("1b2315 2b381f 3c4c2a 51653a")                                  # dried kelp film base
BRASS = ramp("2e1c10 5c3a1e 8a5c2c b9853f dcb25a f3d98a")                   # Create brass
LENS = ramp("211f1d 2a2725 322f2d 383532 4a4643 8f8684 c3c0c0 eeedeb")      # camera lens barrel + glass
PRISMARINE = ramp("5f9c8f a5d6c6 e3f4ec")
WHITE = ramp("a19f98 cfcec9 f2f2ee")                                        # bone meal gelatin
HOLE = rgb("130f0d")

# Potion chemistry, as (matte, wet, glint). Muted to sit next to Exposure's warm greys.
SWIFTNESS = ramp("5b8ba6 86b9cf c9e6ee")
POISON = ramp("5f8a3c 8cb85a cfe59a")
WEAKNESS = ramp("6f6a68 9a9491 d6d2cf")
NIGHT_VISION = ramp("524379 8063bd c4b0f0")
SILVER = ramp("636157 8b877c b4b1a8")                                       # B&W silver-halide coat


# ---------------------------------------------------------------- film: coating stages (flat sheet)

PLATE_TOP, PLATE_BOTTOM, PLATE_W = 3, 11, 10
BAND = (6, 7, 8, 9)  # plate rows covered by the film base


def plate_x(y):
    return 5 - (y - PLATE_TOP) // 2  # sheared, like a sheet lying on the belt


def plate(metal, high_sensitivity):
    px = {}
    for y in range(PLATE_TOP, PLATE_BOTTOM + 1):
        x0 = plate_x(y)
        for i in range(PLATE_W):
            c = metal[4]
            if y == PLATE_TOP:
                c = metal[6]
            elif i == 0:
                c = metal[5]
            elif i == PLATE_W - 1 or y == PLATE_BOTTOM:
                c = metal[3]
            px[(x0 + i, y)] = c
    if high_sensitivity:  # Exposure marks high-sensitivity film with a purple band
        for i in range(PLATE_W):
            px[(plate_x(10) + i, 10)] = PURPLE[4] if i in (1, 2) else PURPLE[3]
            px[(plate_x(11) + i, 11)] = PURPLE[1] if i == PLATE_W - 1 else PURPLE[2]
    x0 = plate_x(PLATE_BOTTOM)
    for i in range(PLATE_W):  # thickness / drop shadow
        px[(x0 + i, PLATE_BOTTOM + 1)] = metal[0] if i else metal[1]
    return px


def band_row(px, y, colors, glossy=False):
    """One row of the film base. colors = (shade, body, glint)."""
    x0 = plate_x(y)
    for i in range(PLATE_W):
        c = colors[1]
        if i == PLATE_W - 1:
            c = colors[0]
        if glossy and i in (2, 3, 6):
            c = colors[2]
        px[(x0 + i, y)] = c


def kelp_base(px):
    for n, y in enumerate(BAND):
        band_row(px, y, (KELP[0], KELP[2 if n == 0 else 1], KELP[3]))
    band_row(px, BAND[-1], (KELP[0], KELP[0], KELP[0]))


def droplets(px, colors, spots):
    for x, y in spots:
        px[(x, y)] = colors[1]
    x, y = spots[0]
    px[(x, y)] = colors[2]


def crystals(px, spots):
    for n, (x, y) in enumerate(spots):
        px[(x, y)] = PRISMARINE[2 if n % 2 == 0 else 1]
        px[(x + 1, y + 1)] = PRISMARINE[0]


SPLASH_A = [(7, 4), (12, 5), (3, 10)]
SPLASH_B = [(10, 4), (6, 5), (9, 10)]


def bw_sheet(metal, hs, stage):
    """stage: prismarine | base | gelatin | emulsion | sensitizer | pressed"""
    px = plate(metal, hs)
    if stage == "prismarine":
        crystals(px, [(6, 5), (10, 7), (4, 9), (9, 4)])
        return px
    kelp_base(px)
    if stage == "gelatin":  # bone meal dusted over the base
        for y in BAND[:3]:
            x0 = plate_x(y)
            for i in range(PLATE_W):
                if (i * 3 + y * 5) % 4 != 0:
                    px[(x0 + i, y)] = WHITE[2] if (i + y) % 3 == 0 else WHITE[1]
    elif stage in ("emulsion", "sensitizer"):
        wet = SWIFTNESS if stage == "emulsion" else NIGHT_VISION
        for n, y in enumerate(BAND[:3]):
            band_row(px, y, (wet[0], wet[1] if n < 2 else wet[0], wet[2]), glossy=n == 0)
        droplets(px, wet, SPLASH_A if stage == "emulsion" else SPLASH_B)
    elif stage == "pressed":
        for n, y in enumerate(BAND[:3]):
            band_row(px, y, (SILVER[0], SILVER[2 if n == 0 else 1], SILVER[2]))
    return px


COLOR_LAYERS = (SWIFTNESS, POISON, WEAKNESS)


def color_sheet(metal, hs, done, wet=None):
    """done = emulsion layers already pressed; wet = potion just poured on top (not pressed yet)."""
    px = plate(metal, hs)
    if done < 0:
        crystals(px, [(6, 5), (10, 7), (4, 9), (9, 4)])
        return px
    kelp_base(px)
    for n in range(done):
        c = COLOR_LAYERS[n]
        band_row(px, BAND[n], (c[0], c[0] if n else c[1], c[1]))
    if wet:
        y = BAND[min(done, 2)]
        band_row(px, y, (wet[0], wet[1], wet[2]), glossy=True)
        droplets(px, wet, SPLASH_A if done % 2 == 0 else SPLASH_B)
    return px


# ---------------------------------------------------------------- film: cut + spooled stages

def film_roll(film, hs):
    """The slit strip wound up, before it has a canister: Exposure's film roll in unexposed colors."""
    px = remap(ref("developed_film"), film)
    if hs:
        for (x, y) in list(px):
            if x <= 6 and y in (9, 10):
                px[(x, y)] = PURPLE[3 if x in (2, 3) else 2] if 1 < x < 6 else PURPLE[1]
    return px


def open_canister(name, metal):
    """The finished Exposure canister with the spool cap still missing."""
    px = {p: c for p, c in ref(name).items() if p[1] > 3}
    for x in range(2, 8):
        px.pop((x, 4), None)
    px[(2, 4)] = metal[2]
    px[(3, 4)] = metal[0]
    px[(4, 4)] = metal[5]  # spool core poking out
    px[(5, 4)] = metal[0]
    px[(6, 4)] = metal[1]
    px[(4, 3)] = metal[4]
    return px


def film_stages(name):
    hs = "high_sensitivity" in name
    final = name.removeprefix("incomplete_")
    if "color" in name:
        metal, film = GOLD, FILM_COLOR
        s = [color_sheet(metal, hs, -1)] if hs else []
        s += [
            color_sheet(metal, hs, 0),
            color_sheet(metal, hs, 0, SWIFTNESS), color_sheet(metal, hs, 1),
            color_sheet(metal, hs, 1, POISON), color_sheet(metal, hs, 2),
            color_sheet(metal, hs, 2, WEAKNESS),
        ]
        if hs:
            s.append(color_sheet(metal, hs, 2, NIGHT_VISION))
        s += [color_sheet(metal, hs, 3), film_roll(film, hs), open_canister(final, metal)]
        return s
    metal = IRON
    order = ["base", "gelatin", "emulsion", "pressed"]
    if hs:
        order = ["prismarine", "base", "gelatin", "emulsion", "sensitizer", "pressed"]
    return [bw_sheet(metal, hs, st) for st in order] + [open_canister(final, metal)]


# ---------------------------------------------------------------- camera

CAMERA_TOP_ROWS = range(0, 5)
LENS_GLASS = "DEGHIJK"   # palette chars of the glass in the reference sprite
PANEL = [(x, y) for y in (5, 6, 7) for x in (9, 10, 11)]  # shutter housing, right of the lens
GEAR = ["313", "404", "313"]


def camera_stages():
    pal, rows = REF["camera"]
    base = ref("camera")
    glass = {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c in LENS_GLASS}
    body = {p: c for p, c in base.items() if p[1] not in CAMERA_TOP_ROWS}

    def build(brass_body, lens, panel):
        px = dict(base)
        if brass_body:  # bare brass casing, only the plated top is iron so far
            px.update(remap(body, BRASS[:5]))
        if not lens:
            for p in glass:
                px[p] = HOLE
            px[(3, 10)] = LENS[1]
        elif brass_body is False and lens == "bare":
            pass
        for n, p in enumerate(PANEL):
            if panel == "open":
                px[p] = HOLE if n not in (0, 1, 2) else LENS[0]
            elif panel == "gear" or (panel == "half" and p[0] > 9):
                px[p] = BRASS[int(GEAR[p[1] - 5][p[0] - 9])]
        if panel == "gear":
            px[(10, 6)] = BRASS[0]
        return px

    return [
        build(True, False, "open"),    # iron sheet deployed on the brass casing
        build(False, False, "open"),   # pressed into the body
        build(False, True, "open"),    # glass pane: lens
        build(False, True, "gear"),    # precision mechanism: shutter
        build(False, True, "half"),    # lever: film advance, housing half closed
    ]


# ---------------------------------------------------------------- instant camera (Exposure: Polaroid)

INSTANT_TRAY_ROWS = range(9, 14)   # print tray: the mechanical crafter
INSTANT_FLASH = (10, 4)
INSTANT_BUTTON = (3, 7)


def instant_camera_stages():
    pal, rows = REF["instant_camera"]
    base = ref("instant_camera")
    face = base[(4, 8)]
    glass = {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c in "jk"}
    tray = {p: c for p, c in base.items() if p[1] in INSTANT_TRAY_ROWS and p[0] < 13}
    top = {p: c for p, c in base.items() if p[1] not in INSTANT_TRAY_ROWS and p[0] < 13}

    def build(body, lens, flash):
        px = dict(base)
        if body != "final":  # the crafter stays bare brass until the plating is pressed around it
            px.update(remap(tray, BRASS[:5]))
            px.update(remap(top, BRASS[:5] if body == "brass" else IRON[1:6]))
        if not lens:
            for p in glass:
                px[p] = HOLE
            px[(5, 5)] = LENS[1]
        if not flash:
            px[INSTANT_FLASH] = px[(9, 4)]
        px[INSTANT_BUTTON] = px[(3, 6)] if body != "final" else face
        return px

    return [
        build("brass", False, False),   # mechanical crafter deployed on the brass casing
        build("iron", False, False),    # iron sheet: body plating
        build("final", False, False),   # pressed
        build("final", True, False),    # glass pane: lens
        build("final", True, True),     # flash; only the shutter button is missing
    ]


# ---------------------------------------------------------------- lens (spyglass being re-ground)

def lens_stage(gem):
    """A short lens barrel pointing up-right. gem=False: empty front cell; True: amethyst element."""
    fx, fy, fr = 6.0, 9.5, 4.9      # front rim
    bx, by, br = 10.5, 5.0, 3.9     # back of the barrel
    length = math.hypot(bx - fx, by - fy)
    ax, ay = (bx - fx) / length, (by - fy) / length
    px = {}
    for y in range(16):
        for x in range(16):
            along = ((x - fx) * ax + (y - fy) * ay) / length      # 0 at the front rim, 1 at the back
            across = (x - fx) * ay - (y - fy) * ax                # > 0 on the lit (upper-left) side
            df = math.hypot(x - fx, y - fy)
            if df <= fr:                                           # front face
                lit = (x - fx) + (y - fy) < -1
                if df > fr - 1.3:
                    c = LENS[4] if lit else LENS[1]                # rim
                elif df > fr - 2.3:
                    c = GOLD[5] if lit else GOLD[3]                # spyglass retainer ring
                else:
                    c = HOLE
            elif 0 <= along <= 1 and abs(across) <= fr + (br - fr) * along                     or math.hypot(x - bx, y - by) <= br:           # barrel
                side = across / (fr + (br - fr) * min(max(along, 0), 1))
                shade = LENS if not 0.4 < along < 0.7 else [GOLD[1], GOLD[1], GOLD[3], GOLD[4], GOLD[6]]
                c = shade[4] if side > 0.35 else shade[3] if side > -0.3 else shade[1]
                if side < -0.8 or along > 1.25:
                    c = LENS[0]
            else:
                continue
            px[(x, y)] = c
    if gem:
        shard = {(4, 9): 3, (5, 8): 4, (6, 8): 4, (7, 8): 2, (5, 9): 4, (6, 9): 3, (7, 9): 3, (4, 10): 2,
                 (5, 10): 3, (6, 10): 2, (7, 10): 1, (5, 11): 2, (6, 11): 1, (7, 11): 0}
        for p, i in shard.items():
            if px.get(p) == HOLE:
                px[p] = PURPLE[i]
        px[(5, 8)] = LENS[7]
    else:
        px[(5, 9)] = LENS[1]
    return px


# ---------------------------------------------------------------- public API

def stages(name):
    if name == "incomplete_camera":
        return camera_stages()
    if name == "incomplete_instant_camera":
        return instant_camera_stages()
    if name == "incomplete_lens":
        return [lens_stage(False), lens_stage(True)]
    return film_stages(name)


def to_image(px):
    from PIL import Image

    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x, y), c in px.items():
        img.putpixel((x, y), tuple(c) + (255,))
    return img


def preview(names, out, scale=10):
    from PIL import Image

    rows = [[to_image(px) for px in stages(n)] for n in names]
    cell = 16 * scale + 8
    sheet = Image.new("RGBA", (max(len(r) for r in rows) * cell, len(rows) * cell), (58, 58, 68, 255))
    for j, row in enumerate(rows):
        for i, img in enumerate(row):
            big = img.resize((16 * scale, 16 * scale), Image.NEAREST)
            sheet.alpha_composite(big, (i * cell + 4, j * cell + 4))
    sheet.save(out)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spec"))
    import recipes

    preview(list(recipes.INCOMPLETE_ITEMS), sys.argv[1] if len(sys.argv) > 1 else "preview.png")
