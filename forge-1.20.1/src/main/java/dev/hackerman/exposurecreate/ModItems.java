package dev.hackerman.exposurecreate;

import com.simibubi.create.content.processing.sequenced.SequencedAssemblyItem;
import net.minecraft.world.item.Item;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * Transitional items for our sequenced assembly recipes. Names must match INCOMPLETE_ITEMS in spec/recipes.py.
 * They intentionally have no creative tab entry, like Create's own incomplete items.
 */
public class ModItems {
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, ExposureCreate.MOD_ID);

    public static final RegistryObject<Item> INCOMPLETE_BLACK_AND_WHITE_FILM = incomplete("incomplete_black_and_white_film");
    public static final RegistryObject<Item> INCOMPLETE_HIGH_SENSITIVITY_BLACK_AND_WHITE_FILM = incomplete("incomplete_high_sensitivity_black_and_white_film");
    public static final RegistryObject<Item> INCOMPLETE_COLOR_FILM = incomplete("incomplete_color_film");
    public static final RegistryObject<Item> INCOMPLETE_HIGH_SENSITIVITY_COLOR_FILM = incomplete("incomplete_high_sensitivity_color_film");
    public static final RegistryObject<Item> INCOMPLETE_CAMERA = incomplete("incomplete_camera");
    public static final RegistryObject<Item> INCOMPLETE_LENS = incomplete("incomplete_lens");
    public static final RegistryObject<Item> INCOMPLETE_INSTANT_CAMERA = incomplete("incomplete_instant_camera");

    private static RegistryObject<Item> incomplete(String name) {
        return ITEMS.register(name, () -> new SequencedAssemblyItem(new Item.Properties()));
    }
}
