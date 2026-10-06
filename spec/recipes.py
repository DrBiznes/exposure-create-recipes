"""
Single source of truth for every recipe, recipe group and incomplete item in the mod.

tools/generate.py turns this into per-target JSON (1.20.1 Forge, 1.21.1 NeoForge).
Edit recipes HERE, then re-run `python tools/generate.py`. Never hand-edit the generated
files under <target>/src/main/resources/data, resourcepacks or generated assets.

GROUPS
    "base" is shipped as the mod's own data and is ALWAYS active.
    Every other group is a built-in data pack in resourcepacks/<group>/ that Java force-enables
    from the config (see GROUP_CONFIG in the README). Each recipe overrides the original mod's
    recipe with the same id, so a disabled group leaves the original recipe untouched.

SEQUENCED STEP KINDS
    ("deploy", "namespace:item")        Deployer holding an item
    ("deploy_tag", "namespace:tag")     Deployer holding anything in an item tag
    ("fill", "potion_id")               Spout, one bottle of that potion (see FILL_BOTTLES)
    ("press",)                          Mechanical Press
    ("cut",)                            Mechanical Saw

Create picks a sequenced assembly by the FIRST step, so any two recipes sharing the same `start`
item must open with different first steps (generate.py asserts this across ALL groups, because
every group can be enabled at once).
"""

MOD_ID = "exposure_create"

# Number of potion bottles consumed by every "fill" step.
FILL_BOTTLES = 1
# Fluid used by each mixing-recipe fluid input (one bottle's worth: 250 mB on Forge/NeoForge).
MIXING_FLUID_BOTTLES = 1

# group id -> (mods that must ALL be loaded for the group to register, human title).
# "base" is special-cased by the generator. Expanded's instant-slide items only exist when the
# Exposure Polaroid addon is installed, so the slides group needs both mods.
GROUPS = {
    "base": ([], "Exposure: Create Recipes (base)"),
    "exposure_extras": ([], "Exposure: Create Recipes (extras)"),
    "expanded_films": (["exposure_expanded"], "Exposure: Create Recipes (Expanded films)"),
    "expanded_lenses": (["exposure_expanded"], "Exposure: Create Recipes (Expanded lenses)"),
    "expanded_slides": (["exposure_expanded", "exposure_polaroid"], "Exposure: Create Recipes (Expanded slides)"),
    "polaroid_camera": (["exposure_polaroid"], "Exposure: Create Recipes (Polaroid camera)"),
    "polaroid_slides": (["exposure_polaroid"], "Exposure: Create Recipes (Polaroid slides)"),
}

# Transitional ("incomplete") items. Registered by Java, textured by placeholder art.
# Recipes of one family share an item (Create keys progress on recipe id, not on item).
INCOMPLETE_ITEMS = {
    "incomplete_black_and_white_film": "Incomplete Black & White Film",
    "incomplete_high_sensitivity_black_and_white_film": "Incomplete High-Sensitivity Black & White Film",
    "incomplete_color_film": "Incomplete Color Film",
    "incomplete_high_sensitivity_color_film": "Incomplete High-Sensitivity Color Film",
    "incomplete_camera": "Incomplete Camera",
    "incomplete_lens": "Incomplete Lens",
    "incomplete_instant_camera": "Incomplete Instant Camera",
}


# ------------------------------------------------------------------ recipe constructors

def seq(group, result, start, transitional, steps):
    return {"kind": "sequenced", "group": group, "result": result, "start": start,
            "transitional": transitional, "steps": steps}


def mech(group, result, pattern, key):
    """Mechanical crafting. `key` maps a pattern char to "ns:item" or "#ns:tag"."""
    return {"kind": "mechanical", "group": group, "result": result, "pattern": pattern, "key": key}


def compact(group, result, ingredients):
    """Press + basin. Repeat an ingredient to require several of it. "#ns:tag" for tags."""
    return {"kind": "compacting", "group": group, "result": result, "ingredients": ingredients}


def mix(group, result, ingredients, count=1, fluids=("water",)):
    """Mixer + basin (unheated). `fluids` (max 2) are "water" or a potion id such as "minecraft:swiftness"."""
    return {"kind": "mixing", "group": group, "result": result, "ingredients": ingredients,
            "count": count, "fluids": list(fluids)}


# ------------------------------------------------------------------ shared step lists

# Color chemistry: three emulsion layers (cyan / green / grey), all spider-farm + sugar-cane tier.
COLOR_LAYERS = [
    ("fill", "minecraft:swiftness"), ("press",),
    ("fill", "minecraft:poison"), ("press",),
    ("fill", "minecraft:weakness"), ("press",),
]
COLOR_FINISH = [("cut",), ("deploy", "minecraft:lapis_lazuli"), ("deploy", "minecraft:gold_nugget")]
# "Fine grain" chemistry for Expanded hi-res film: extended (redstone) potions.
LONG_COLOR_LAYERS = [
    ("fill", "minecraft:long_swiftness"), ("press",),
    ("fill", "minecraft:long_poison"), ("press",),
    ("fill", "minecraft:long_weakness"), ("press",),
]


def vanity_film(result, opener, extra_after_first=None):
    """Palette film = color film chemistry, opened by its palette pigment."""
    steps = [("deploy", opener), ("deploy", "minecraft:dried_kelp")]
    layers = list(COLOR_LAYERS)
    if extra_after_first:  # insert a second pigment after the first layer's press
        layers[2:2] = [("deploy", extra_after_first)]
    return seq("expanded_films", result, "create:golden_sheet", "incomplete_color_film",
               steps + layers + COLOR_FINISH)


# ------------------------------------------------------------------ the recipes

RECIPES = [
    # ============================================================ BASE (always on)
    # --- Black & white film: one cheap emulsion (Swiftness / sugar) ---
    seq("base", "exposure:black_and_white_film", "create:iron_sheet", "incomplete_black_and_white_film", [
        ("deploy", "minecraft:dried_kelp"),     # film base
        ("deploy", "minecraft:bone_meal"),      # gelatin binder
        ("fill", "minecraft:swiftness"),        # silver-halide emulsion
        ("press",),                             # coat evenly
        ("cut",),                               # slit to width
        ("deploy", "minecraft:iron_nugget"),    # spool cap
    ]),
    # --- High-sensitivity B&W: prismarine first, plus a Night Vision sensitizer ---
    seq("base", "exposure:high_sensitivity_black_and_white_film", "create:iron_sheet",
        "incomplete_high_sensitivity_black_and_white_film", [
        ("deploy", "minecraft:prismarine_crystals"),  # distinguishing first step
        ("deploy", "minecraft:dried_kelp"),
        ("deploy", "minecraft:bone_meal"),
        ("fill", "minecraft:swiftness"),
        ("fill", "minecraft:night_vision"),     # low-light sensitizer
        ("press",),
        ("cut",),
        ("deploy", "minecraft:iron_nugget"),
    ]),
    # --- Color film ---
    seq("base", "exposure:color_film", "create:golden_sheet", "incomplete_color_film",
        [("deploy", "minecraft:dried_kelp")] + COLOR_LAYERS + COLOR_FINISH),
    seq("base", "exposure:high_sensitivity_color_film", "create:golden_sheet",
        "incomplete_high_sensitivity_color_film", [
        ("deploy", "minecraft:prismarine_crystals"),  # distinguishing first step
        ("deploy", "minecraft:dried_kelp"),
        ("fill", "minecraft:swiftness"), ("press",),
        ("fill", "minecraft:poison"), ("press",),
        ("fill", "minecraft:weakness"),
        ("fill", "minecraft:night_vision"),     # low-light sensitizer
        ("press",),
    ] + COLOR_FINISH),
    # --- Camera: brass casing body, precision-mechanism shutter ---
    seq("base", "exposure:camera", "create:brass_casing", "incomplete_camera", [
        ("deploy", "create:iron_sheet"),        # body plating
        ("press",),
        ("deploy", "minecraft:glass_pane"),     # lens
        ("deploy", "create:precision_mechanism"),  # shutter
        ("deploy", "minecraft:lever"),          # film advance
        ("deploy_tag", "minecraft:buttons"),    # shutter release
    ]),
    # --- Camera stand: tall tripod, mechanical crafter ---
    mech("base", "exposure:camera_stand", [
        " I ",
        " S ",
        "SSS",
        "S S",
        "B B",
    ], {"I": "create:iron_sheet", "S": "minecraft:stick", "B": "create:andesite_alloy"}),
    # --- Interplanar projector: 5x5 diamond, electron tubes instead of redstone ---
    mech("base", "exposure:interplanar_projector", [
        "  B  ",
        " PTP ",
        "BTETB",
        " PTP ",
        "  B  ",
    ], {"B": "create:brass_sheet", "P": "minecraft:tinted_glass",
        "T": "create:electron_tube", "E": "minecraft:ender_eye"}),

    # ============================================================ EXPOSURE EXTRAS (off by default)
    compact("exposure_extras", "exposure:album", ["minecraft:writable_book", "minecraft:phantom_membrane"]),
    compact("exposure_extras", "exposure:photograph_frame",
            ["minecraft:item_frame"] + ["#minecraft:planks"] * 4 + ["minecraft:stick"] * 4),
    compact("exposure_extras", "exposure:glass_photograph_frame",
            ["exposure:photograph_frame"] + ["minecraft:glass_pane"] * 4),
    compact("exposure_extras", "exposure:lightroom",
            ["minecraft:iron_trapdoor", "minecraft:redstone_torch"] + ["#minecraft:planks"] * 4),

    # ============================================================ EXPOSURE EXPANDED: films (on by default if installed)
    seq("expanded_films", "exposure_expanded:hicap_black_and_white_film", "create:iron_sheet",
        "incomplete_black_and_white_film", [
        ("deploy", "minecraft:dried_kelp_block"),   # distinguishing first step (high capacity)
        ("deploy", "minecraft:dried_kelp_block"),
        ("deploy", "minecraft:bone_meal"),
        ("fill", "minecraft:swiftness"),
        ("press",),
        ("cut",),
        ("deploy", "minecraft:iron_nugget"),
    ]),
    seq("expanded_films", "exposure_expanded:hicap_color_film", "create:golden_sheet",
        "incomplete_color_film",
        [("deploy", "minecraft:dried_kelp_block"), ("deploy", "minecraft:dried_kelp_block")]
        + COLOR_LAYERS + COLOR_FINISH),
    seq("expanded_films", "exposure_expanded:hires_black_and_white_film", "create:iron_sheet",
        "incomplete_black_and_white_film", [
        ("deploy", "minecraft:redstone"),           # distinguishing first step (fine grain)
        ("deploy", "minecraft:dried_kelp"),
        ("deploy", "minecraft:bone_meal"),
        ("fill", "minecraft:long_swiftness"),
        ("press",),
        ("cut",),
        ("deploy", "minecraft:iron_nugget"),
    ]),
    seq("expanded_films", "exposure_expanded:hires_color_film", "create:golden_sheet",
        "incomplete_color_film",
        [("deploy", "minecraft:redstone"), ("deploy", "minecraft:dried_kelp")]
        + LONG_COLOR_LAYERS + COLOR_FINISH),
    vanity_film("exposure_expanded:gameboy_film", "minecraft:green_dye"),
    vanity_film("exposure_expanded:cga_film", "minecraft:cyan_dye", extra_after_first="minecraft:magenta_dye"),
    vanity_film("exposure_expanded:c64_film", "minecraft:emerald"),
    vanity_film("exposure_expanded:nes_film", "minecraft:red_mushroom"),

    # ============================================================ EXPOSURE EXPANDED: lenses (off by default)
    seq("expanded_lenses", "exposure_expanded:telescopic_lens", "minecraft:spyglass", "incomplete_lens", [
        ("deploy", "minecraft:amethyst_shard"),
        ("deploy", "minecraft:amethyst_shard"),
    ]),
    seq("expanded_lenses", "exposure_expanded:panoramic_lens", "minecraft:spyglass", "incomplete_lens", [
        ("press",),                                 # flatten wide; distinguishes it from the telescopic lens
        ("deploy", "minecraft:amethyst_shard"),
        ("deploy", "minecraft:amethyst_shard"),
    ]),

    # ============================================================ EXPOSURE EXPANDED: instant slides (off by default)
    mix("expanded_slides", "exposure_expanded:instant_c64_slide", [
        "minecraft:lapis_lazuli", "minecraft:black_dye", "minecraft:emerald", "minecraft:cyan_dye",
        "minecraft:magenta_dye", "minecraft:yellow_dye"] + ["minecraft:paper"] * 3, count=3, fluids=["minecraft:swiftness"]),
    mix("expanded_slides", "exposure_expanded:instant_cga_slide",
        ["minecraft:lapis_lazuli"] * 2 + ["minecraft:magenta_dye"] * 2 + ["minecraft:cyan_dye"] * 2
        + ["minecraft:paper"] * 3, count=3, fluids=["minecraft:swiftness"]),
    mix("expanded_slides", "exposure_expanded:instant_gameboy_slide",
        ["minecraft:lapis_lazuli"] * 2 + ["minecraft:black_dye"] + ["minecraft:green_dye"] * 3
        + ["minecraft:paper"] * 3, count=3, fluids=["minecraft:swiftness"]),
    mix("expanded_slides", "exposure_expanded:instant_hires_black_and_white_slide", [
        "minecraft:bone_meal", "minecraft:black_dye", "minecraft:redstone"] + ["minecraft:paper"] * 3, count=3, fluids=["minecraft:swiftness"]),
    mix("expanded_slides", "exposure_expanded:instant_hires_color_slide", [
        "minecraft:lapis_lazuli", "minecraft:black_dye", "minecraft:redstone", "minecraft:cyan_dye",
        "minecraft:magenta_dye", "minecraft:yellow_dye"] + ["minecraft:paper"] * 3, count=3, fluids=["minecraft:swiftness"]),
    mix("expanded_slides", "exposure_expanded:instant_nes_slide", [
        "minecraft:lapis_lazuli", "minecraft:black_dye", "minecraft:red_mushroom", "minecraft:cyan_dye",
        "minecraft:magenta_dye", "minecraft:yellow_dye"] + ["minecraft:paper"] * 3, count=3, fluids=["minecraft:swiftness"]),

    # ============================================================ POLAROID (on by default if installed)
    # Instant camera: the vanilla crafter/crafting table becomes a Mechanical Crafter (the printer). Opens with it,
    # so it cannot be confused with the base camera (also brass casing, but opening with an iron sheet).
    seq("polaroid_camera", "exposure_polaroid:instant_camera", "create:brass_casing", "incomplete_instant_camera", [
        ("deploy", "create:mechanical_crafter"),    # printer unit; distinguishing first step
        ("deploy", "create:iron_sheet"),            # body plating
        ("press",),
        ("deploy", "minecraft:glass_pane"),         # lens
        ("deploy_tag", "exposure:flashes"),         # built-in flash
        ("deploy_tag", "minecraft:buttons"),        # shutter release
    ]),
    # Instant slides: every original ingredient, plus the film chemistry as potion fluid
    # (Swiftness emulsion; Night Vision sensitizer on the high-sensitivity ones). Three slides per craft.
    mix("polaroid_slides", "exposure_polaroid:instant_black_and_white_slide", [
        "minecraft:bone_meal", "minecraft:bone_meal", "minecraft:black_dye"] + ["minecraft:paper"] * 3,
        count=3, fluids=["minecraft:swiftness"]),
    mix("polaroid_slides", "exposure_polaroid:high_sensitivity_instant_black_and_white_slide", [
        "minecraft:bone_meal", "minecraft:black_dye", "minecraft:prismarine_crystals"] + ["minecraft:paper"] * 3,
        count=3, fluids=["minecraft:swiftness", "minecraft:night_vision"]),
    mix("polaroid_slides", "exposure_polaroid:instant_color_slide", [
        "minecraft:lapis_lazuli", "minecraft:lapis_lazuli", "minecraft:black_dye", "minecraft:cyan_dye",
        "minecraft:magenta_dye", "minecraft:yellow_dye"] + ["minecraft:paper"] * 3,
        count=3, fluids=["minecraft:swiftness"]),
    mix("polaroid_slides", "exposure_polaroid:high_sensitivity_instant_color_slide", [
        "minecraft:lapis_lazuli", "minecraft:black_dye", "minecraft:prismarine_crystals", "minecraft:cyan_dye",
        "minecraft:magenta_dye", "minecraft:yellow_dye"] + ["minecraft:paper"] * 3,
        count=3, fluids=["minecraft:swiftness", "minecraft:night_vision"]),
]
