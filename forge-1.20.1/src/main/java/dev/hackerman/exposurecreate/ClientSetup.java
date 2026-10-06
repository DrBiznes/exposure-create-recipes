package dev.hackerman.exposurecreate;

import com.simibubi.create.content.processing.sequenced.SequencedAssemblyItem;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.registries.RegistryObject;

/**
 * Exposes Create's assembly progress (0..1) as the "exposure_create:progress" item property, which the generated
 * item models use to pick a per-stage sprite (see tools/generate.py and tools/textures.py).
 */
@Mod.EventBusSubscriber(modid = ExposureCreate.MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public class ClientSetup {
    private static final ResourceLocation PROGRESS = new ResourceLocation(ExposureCreate.MOD_ID, "progress");

    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> {
            for (RegistryObject<Item> entry : ModItems.ITEMS.getEntries()) {
                if (entry.get() instanceof SequencedAssemblyItem item) {
                    ItemProperties.register(item, PROGRESS, (stack, level, entity, seed) -> item.getProgress(stack));
                }
            }
        });
    }
}
