package dev.hackerman.exposurecreate;

import com.mojang.logging.LogUtils;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackSource;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.common.ModConfigSpec;
import net.neoforged.neoforge.event.AddPackFindersEvent;
import org.slf4j.Logger;

import java.util.List;

/**
 * Registers the optional recipe groups (resourcepacks/&lt;dir&gt; inside this jar) as forced-on, top-priority data packs
 * when the config enables them. Each pack overrides the original mod's recipe with the same id, so a disabled group
 * leaves the original recipe untouched. Group names must match GROUPS in spec/recipes.py (generate.py checks).
 */
public class RecipePacks {
    private static final Logger LOGGER = LogUtils.getLogger();

    /** dir = folder under resourcepacks/, requiredMods = mods that must ALL be loaded. */
    private record Group(String dir, String title, List<String> requiredMods, ModConfigSpec.BooleanValue option) {
        boolean enabled() {
            for (String mod : requiredMods) {
                if (!ModList.get().isLoaded(mod)) {
                    return false;
                }
            }
            if (!Config.SPEC.isLoaded()) {
                LOGGER.warn("Config not loaded yet while registering recipe pack '{}'; using its default", dir);
                return option.getDefault();
            }
            return Config.CONVERT_ALL.get() || option.get();
        }
    }

    private static final List<Group> GROUPS = List.of(
            new Group("exposure_extras", "Exposure: Create Recipes (extras)", List.of(), Config.EXPOSURE_EXTRAS),
            new Group("expanded_films", "Exposure: Create Recipes (Expanded films)", List.of("exposure_expanded"), Config.EXPANDED_FILMS),
            new Group("expanded_lenses", "Exposure: Create Recipes (Expanded lenses)", List.of("exposure_expanded"), Config.EXPANDED_LENSES),
            new Group("expanded_slides", "Exposure: Create Recipes (Expanded slides)", List.of("exposure_expanded", "exposure_polaroid"), Config.EXPANDED_SLIDES),
            new Group("polaroid_camera", "Exposure: Create Recipes (Polaroid camera)", List.of("exposure_polaroid"), Config.POLAROID_CAMERA),
            new Group("polaroid_slides", "Exposure: Create Recipes (Polaroid slides)", List.of("exposure_polaroid"), Config.POLAROID_SLIDES)
    );

    public static void onAddPackFinders(AddPackFindersEvent event) {
        if (event.getPackType() != PackType.SERVER_DATA) {
            return;
        }
        for (Group group : GROUPS) {
            if (!group.enabled()) {
                continue;
            }
            LOGGER.info("Enabling Create recipe group '{}'", group.dir());
            event.addPackFinders(
                    ResourceLocation.fromNamespaceAndPath(ExposureCreate.MOD_ID, "resourcepacks/" + group.dir()),
                    PackType.SERVER_DATA, Component.literal(group.title()), PackSource.BUILT_IN,
                    true, Pack.Position.TOP);
        }
    }
}
