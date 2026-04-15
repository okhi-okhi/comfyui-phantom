import folder_paths
import comfy.utils

class ApplyLoraStack:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
            },
            "optional": {
                "lora_stack": ("LORA_STACK",),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP")
    RETURN_NAMES = ("MODEL", "CLIP")
    FUNCTION = "apply_stack"
    CATEGORY = "Phantom"

    def apply_stack(self, model, clip, lora_stack=None):
        if not lora_stack:
            return (model, clip)

        for lora in lora_stack:
            lora_name = lora[0]
            strength_model = lora[1]
            strength_clip = lora[2]
            
            lora_path = folder_paths.get_full_path("loras", lora_name)
            if not lora_path:
                print(f"Warning: Lora {lora_name} not found.")
                continue
                
            lora_model = comfy.utils.load_torch_file(lora_path, safe_load=True)
            model, clip = comfy.sd.load_lora_for_models(model, clip, lora_model, strength_model, strength_clip)
            
        return (model, clip)
