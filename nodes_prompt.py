import re
from .wildcards_utils import replace_wildcards

class A1111PromptParser:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }
    
    RETURN_TYPES = ("STRING", "LORA_STACK")
    RETURN_NAMES = ("clean_prompt", "lora_stack")
    FUNCTION = "parse"
    CATEGORY = "Phantom"
    OUTPUT_NODE = True

    def parse(self, text, seed):
        # 1. Replace Wildcards
        text = replace_wildcards(text, seed)
        
        # 2. Extract LoRAs <lora:name:weight_model:weight_clip> or <lora:name:weight>
        lora_stack = []
        
        def extract_lora(m):
            name = m.group(1)
            parts = m.group(0).strip("<>").split(":")
            
            weight_model = float(parts[2]) if len(parts) > 2 else 1.0
            weight_clip = float(parts[3]) if len(parts) > 3 else weight_model
            
            # format of lora_stack item is usually exactly what ComfyUI expects:
            # (lora_name, weight_model, weight_clip)
            # Ensure name resolves correctly if possible, usually by default `name.safetensors`
            
            # Find closest matching Lora if .safetensors is omitted
            import folder_paths
            available_loras = folder_paths.get_filename_list("loras")
            
            # find an exact or fuzzy match
            best_match = name
            for av in available_loras:
                if av.startswith(name) or name in av:
                    best_match = av
                    break
                    
            lora_stack.append((best_match, weight_model, weight_clip))
            return ""

        text = re.sub(r'<lora:([^:>]+)[^>]*>', extract_lora, text)
        
        # 3. Clean up double spaces left by removal
        text = re.sub(r'  +', ' ', text).strip()
        
        return {"ui": {"text": [text]}, "result": (text, lora_stack)}
