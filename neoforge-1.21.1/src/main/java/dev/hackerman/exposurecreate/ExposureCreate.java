package dev.hackerman.exposurecreate;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;

@Mod(ExposureCreate.MOD_ID)
public class ExposureCreate {
    public static final String MOD_ID = "exposure_create";

    public ExposureCreate(IEventBus modEventBus, ModContainer container) {
        ModItems.ITEMS.register(modEventBus);
        container.registerConfig(ModConfig.Type.COMMON, Config.SPEC);
        modEventBus.addListener(RecipePacks::onAddPackFinders);
    }
}
