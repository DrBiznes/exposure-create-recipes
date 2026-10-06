# Development notes

Replaces [Exposure](https://github.com/mortuusars/Exposure)'s crafting recipes with
[Create](https://github.com/Creators-of-Create/Create) processing recipes (sequenced assembly, mechanical crafting,
compacting, mixing). Potions stand in for the photographic chemistry. Create and Exposure are required;
[Exposure Expanded](https://github.com/Sparkwave2/exposure-expanded) and
[Exposure: Polaroid](https://github.com/mortuusars/ExposurePolaroid) are optional.

## Targets

| Folder | Minecraft | Loader | Exposure | Create | Expanded | Polaroid |
|---|---|---|---|---|---|---|
| `forge-1.20.1/` | 1.20.1 | Forge 47.x | 1.9.x | 6.0.7+ | 1.1.0 | 1.1.4 |
| `neoforge-1.21.1/` | 1.21.1 | NeoForge 21.1.x | 1.9.x | 6.0.7+ | 1.0.1 | 1.1.6 |

Fabric is intentionally not supported (Create has no official 1.21.1 Fabric release, and Exposure's own Create
integration is Forge/NeoForge only).

## Layout

```
spec/recipes.py        single source of truth: every recipe, recipe group and incomplete item
tools/generate.py      spec -> per-target recipe JSON, packs, models, lang, textures
tools/textures.py      procedural pixel art for the incomplete items (one sprite per assembly stage)
tools/exposure_ref.py  Exposure / Exposure: Polaroid sprites the art is derived from (MIT, mortuusars)
tools/branding.py      mod icon and README banner (docs/, plus icon.png in both jars)
forge-1.20.1/          ForgeGradle project
neoforge-1.21.1/       ModDevGradle project (Java 21)
```

## How replacement works

Every recipe ships at the same id as the recipe it replaces (`exposure:camera`, `exposure_expanded:nes_film`, ...).

- **Base group**: normal mod data, always active. Both mods declare `ordering="AFTER"` on Exposure and Create so this
  mod's data loads last and wins.
- **Optional groups**: built-in data packs under `resourcepacks/<group>/` in the jar. `RecipePacks.java` force-enables
  them as top-priority data packs when the config asks. A group that is off leaves the original recipe untouched.
  Expanded groups are only registered when `exposure_expanded` is loaded.

## Config (`config/exposure_create-common.toml`, restart required)

```toml
convertAllRecipes = false   # master switch: every group below on (Expanded ones only if installed)
[exposure]
  extras = false            # album, frames, lightroom
[expanded]
  films  = true             # on by default if Expanded is installed (else they bypass Create-gated film)
  lenses = false
  slides = false            # also needs the Exposure Polaroid addon
[polaroid]                  # only used when Exposure: Polaroid is installed
  camera = true             # on by default so the instant camera does not bypass the Create-gated camera
  slides = true             # likewise for the instant slides
```

## Recipes

**Base (always on)**

| Item | Type | Summary |
|---|---|---|
| B&W film | sequenced | iron sheet; kelp, bone meal, Swiftness, press, cut, nugget |
| High-sensitivity B&W | sequenced | opens with prismarine; adds Night Vision sensitizer |
| Color film | sequenced | golden sheet; Swiftness / Poison / Weakness layers, pressed between |
| High-sensitivity color | sequenced | opens with prismarine; adds Night Vision |
| Camera | sequenced | brass casing, iron sheet, glass pane, precision mechanism, lever, button |
| Camera stand | mechanical crafting | 3x5 tripod: iron sheet, 6 sticks, 2 andesite alloy |
| Interplanar projector | mechanical crafting | 5x5 diamond: 4 brass sheets, 4 tinted glass, 4 electron tubes, ender eye |

**Optional**: `exposure_extras` (album, photograph frame, glass frame, lightroom: compacting);
`expanded_films` (hi-cap, hi-res, Gameboy, CGA, C64, NES: sequenced); `expanded_lenses` (telescopic, panoramic:
sequenced); `expanded_slides` (six instant slides: mixing with a Swiftness potion; needs the Exposure Polaroid addon too, which is what adds those items).

**Polaroid (on by default when installed)**

| Item | Type | Summary |
|---|---|---|
| Instant camera | sequenced | brass casing; opens with a Mechanical Crafter (the printer, replacing the vanilla crafter), then iron sheet, press, glass pane, flash, button |
| 4 instant slides | mixing | every original ingredient (3 per craft) plus a Swiftness potion; the high-sensitivity slides add Night Vision |

Potions are one bottle per fill step and are all renewable: sugar (Swiftness), spider eyes (Poison, Weakness),
golden carrots (Night Vision), redstone (the Long variants for hi-res film).

Create selects a sequenced assembly by its first step, so recipes sharing a start item must open differently
(the high-sensitivity films open with prismarine, hi-cap with kelp blocks, hi-res with redstone, vanity films with
their palette pigment). `generate.py` enforces this across all groups.

Left alone on purpose: film developing, photograph copying/aging and broken-projector repair. They use Exposure's own
data-carrying recipe types, which Create steps cannot reproduce without a mixin.

## Workflow

```bash
python tools/generate.py           # regenerate data/assets after editing spec/recipes.py
python tools/generate.py --check   # CI: fail if generated files are stale
```

Everything generated (`data/`, `resourcepacks/`, item models and textures) is committed; do not hand-edit it, the
generator wipes and rewrites those folders.

Adding an incomplete item: add it to `INCOMPLETE_ITEMS` in the spec, add `incomplete("...")` to both `ModItems.java`
files, and run the generator (it checks the Java and spec agree). Adding a group: add it to `GROUPS`, to both
`RecipePacks.java` lists, and to both `Config.java` files.

## Building

```bash
cd forge-1.20.1 && ./gradlew build        # jar in build/libs
cd neoforge-1.21.1 && ./gradlew build
```

Run Gradle on JDK 21 (the Forge project still compiles for Java 17 via `--release 17`). On Windows with a sandboxed
shell, Java may fail with "Unable to establish loopback connection"; set
`JAVA_TOOL_OPTIONS=-Djdk.net.unixdomain.tmpdir=<any writable dir>`.

## Incomplete item art

The incomplete items change sprite as the assembly advances (44 sprites over seven items). `tools/textures.py` draws
them in code, in Exposure's palette, and cuts the late stages out of the finished Exposure sprites so they line up
with the result. Each item's stage list follows its base recipe step by step; recipes sharing the item with a
different step count spread over the same sprites.

`ClientSetup.java` exposes Create's assembly progress as the `exposure_create:progress` item property and the
generated item models switch stage on it. To change the art, edit `tools/textures.py`, preview with
`python tools/textures.py preview.png`, then run the generator.
