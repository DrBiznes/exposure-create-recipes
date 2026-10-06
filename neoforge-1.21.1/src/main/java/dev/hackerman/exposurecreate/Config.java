package dev.hackerman.exposurecreate;

import net.neoforged.neoforge.common.ModConfigSpec;

/**
 * Common config (config/exposure_create-common.toml). Film, camera, camera stand and interplanar projector
 * recipes are always replaced; everything here is an optional extra. Changing a value needs a restart.
 */
public class Config {
    public static final ModConfigSpec SPEC;

    public static final ModConfigSpec.BooleanValue CONVERT_ALL;
    public static final ModConfigSpec.BooleanValue EXPOSURE_EXTRAS;
    public static final ModConfigSpec.BooleanValue EXPANDED_FILMS;
    public static final ModConfigSpec.BooleanValue EXPANDED_LENSES;
    public static final ModConfigSpec.BooleanValue EXPANDED_SLIDES;
    public static final ModConfigSpec.BooleanValue POLAROID_CAMERA;
    public static final ModConfigSpec.BooleanValue POLAROID_SLIDES;

    static {
        ModConfigSpec.Builder b = new ModConfigSpec.Builder();

        CONVERT_ALL = b.comment(
                "Master switch: turn EVERY optional recipe group below into Create recipes,",
                "regardless of the individual options. Groups for mods that are not installed stay off.")
                .define("convertAllRecipes", false);

        b.push("exposure");
        EXPOSURE_EXTRAS = b.comment(
                "Album, photograph frame, glass photograph frame and lightroom as Create (compacting) recipes.")
                .define("extras", false);
        b.pop();

        b.push("expanded");
        b.comment("Only used when Exposure Expanded is installed.");
        EXPANDED_FILMS = b.comment(
                "Expanded's films (hi-cap, hi-res, Gameboy, CGA, C64, NES) as Create sequenced assembly.",
                "On by default so they do not bypass the Create-gated base films.")
                .define("films", true);
        EXPANDED_LENSES = b.comment("Telescopic and panoramic lenses as Create sequenced assembly.")
                .define("lenses", false);
        EXPANDED_SLIDES = b.comment("Instant slides as Create mixing recipes. Also needs the Exposure Polaroid addon,", "which is what adds the slide items.")
                .define("slides", false);
        b.pop();

        b.push("polaroid");
        b.comment("Only used when the Exposure: Polaroid addon is installed. On by default so the instant camera",
                "and its slides do not bypass the Create-gated camera and films.");
        POLAROID_CAMERA = b.comment("Instant camera as Create sequenced assembly.")
                .define("camera", true);
        POLAROID_SLIDES = b.comment("Instant slides as Create mixing recipes (original ingredients plus potion fluid).")
                .define("slides", true);
        b.pop();

        SPEC = b.build();
    }
}
