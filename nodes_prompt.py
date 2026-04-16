import re
from .wildcards_utils import replace_wildcards
from .nodes_lora import ApplyLoraStack

class A1111PromptParser:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "wildcard_text": ("STRING", {"multiline": True, "dynamicPrompts": False}),
                "populated_text": ("STRING", {"multiline": True, "dynamicPrompts": False}),
                "mode": (["populate", "fixed"], {"default": "populate"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "CONDITIONING", "STRING")
    RETURN_NAMES = ("model", "clip", "conditioning", "populated_text")
    FUNCTION = "parse"
    CATEGORY = "Phantom"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(s, model, clip, wildcard_text, populated_text, mode, seed):
        # Force re-execution if seed changes, but also if mode evaluates wildcard dynamically
        return float("NaN") if mode == "populate" else populated_text

    def parse(self, model, clip, wildcard_text, populated_text, mode, seed):
        print(f"\n[Phantom] Parse triggered - Mode: {mode}, Seed: {seed}")
        
        if mode == "populate":
            text = replace_wildcards(wildcard_text, seed)
            
            # Simple combinatorics {} resolution directly to match Impact pack if needed
            # For this node, we use the standard {a|b|c} resolver for dynamic prompts natively
            def repl_opts(match):
                import random
                options = match.group(1).split('|')
                return random.choice(options).strip()
            
            # resolve {{A|B}|C} up to 100 times to prevent infinite loops
            for _ in range(100):
                new_text = re.sub(r'\{([^\{\}]+)\}', repl_opts, text)
                if new_text == text:
                    break
                text = new_text
        else:
            text = populated_text

        # Extract LoRAs <lora:name:weight_model:weight_clip>
        lora_stack = []
        
        def extract_lora(m):
            name = m.group(1).strip()
            # clean the < > and split
            parts = m.group(0).strip("<>").split(":")
            
            weight_model = float(parts[2]) if len(parts) > 2 else 1.0
            weight_clip = float(parts[3]) if len(parts) > 3 else weight_model
            
            import folder_paths
            available_loras = folder_paths.get_filename_list("loras")
            
            best_match = name
            for av in available_loras:
                # Find an exact fallback if safetensors omitted
                if av == f"{name}.safetensors" or av == f"{name}.pt":
                    best_match = av
                    break
                elif av.startswith(name) or name in av:
                    best_match = av
                    
            print(f"[Phantom LOG] Caught LoRA '{name}' -> matching to '{best_match}' with M:{weight_model} C:{weight_clip}")
            lora_stack.append((best_match, weight_model, weight_clip))
            return "" # Strip the <lora...> string from the text output!

        # Use re.sub just to execute extract_lora while keeping the matched original string via return m.group(0)
        # Or simply use re.findall to populate lora_stack
        text = re.sub(r'<lora:([^:>]+)[^>]*>', extract_lora, text)
        
        # Resolve embeddings like embedding:lazypos -> embedding:exact_filename.safetensors
        def extract_embedding(m):
            name = m.group(1).strip()
            
            import folder_paths
            available_embs = folder_paths.get_filename_list("embeddings")
            
            best_match = name
            for av in available_embs:
                if av == f"{name}.safetensors" or av == f"{name}.pt" or av == f"{name}.bin":
                    best_match = av
                    break
                elif name.lower() in av.lower():
                    best_match = av
                    
            print(f"[Phantom LOG] Caught Embedding '{name}' -> matching to '{best_match}'")
            return f"embedding:{best_match}"
            
        text = re.sub(r'embedding:([^\s,\:]+)', extract_embedding, text, flags=re.IGNORECASE)

        # Clean up double spaces
        text = re.sub(r'  +', ' ', text).strip()
        
        # Apply LoRAs to the model and clip
        lora_node = ApplyLoraStack()
        model, clip = lora_node.apply_stack(model, clip, lora_stack)
        
        # Encode the text using the CLIP provided (like CLIPTextEncode)
        tokens = clip.tokenize(text)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        conditioning = [[cond, {"pooled_output": pooled}]]
        
        # UI feedback for Node: update the populated_text widget and the wildcard_text incoming stream
        return {"ui": {"string": [text], "wildcard": [wildcard_text]}, "result": (model, clip, conditioning, text)}
