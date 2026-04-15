from .nodes_prompt import A1111PromptParser
from .nodes_xy import AxisPrompt, AxisSteps, XYCrossMultiplier, XYGridBuilder
from .nodes_lora import ApplyLoraStack
from .nodes_saver import CivitaiImageSaver

NODE_CLASS_MAPPINGS = {
    "PhantomA1111PromptParser": A1111PromptParser,
    "PhantomAxisPrompt": AxisPrompt,
    "PhantomAxisSteps": AxisSteps,
    "PhantomXYCrossMultiplier": XYCrossMultiplier,
    "PhantomXYGridBuilder": XYGridBuilder,
    "PhantomApplyLoraStack": ApplyLoraStack,
    "PhantomCivitaiImageSaver": CivitaiImageSaver,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhantomA1111PromptParser": "Phantom A1111 Prompt Parser",
    "PhantomAxisPrompt": "Phantom Axis: Prompt",
    "PhantomAxisSteps": "Phantom Axis: Steps",
    "PhantomXYCrossMultiplier": "Phantom XY Cross Multiplier",
    "PhantomXYGridBuilder": "Phantom XY Grid Builder",
    "PhantomApplyLoraStack": "Phantom Apply LoRA Stack",
    "PhantomCivitaiImageSaver": "Phantom Civitai Image Saver",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
