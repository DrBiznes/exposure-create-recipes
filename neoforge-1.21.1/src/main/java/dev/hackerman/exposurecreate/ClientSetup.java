package dev.hackerman.exposurecreate;

import com.simibubi.create.content.processing.sequenced.SequencedAssemblyItem;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.registries.DeferredHolder;

/**
 * Exposes Create's assembly progress (0..1) as the "exposure_create:progress" item property, which the generated
 * item models use to pick a per-stage sprite (see tools/generate.py and tools/textures.py).
 */
@EventBusSubscriber(modid = ExposureCreate.MOD_ID, value = Dist.CLIENT)
public class ClientSetup {
    private static final ResourceLocation PROGRESS = ResourceLocation.fromNamespaceAndPath(ExposureCreate.MOD_ID, "progress");

    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> {
            for (DeferredHolder<Item, ? extends Item> entry : ModItems.ITEMS.getEntries()) {
                if (entry.get() instanceof SequencedAssemblyItem item) {
                    ItemProperties.register(item, PROGRESS, (stack, level, entity, seed) -> item.getProgress(stack));
                }
            }
        });
    }
}
