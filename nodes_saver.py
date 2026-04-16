import folder_paths
import os
import json
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np

class CivitaiImageSaver:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(s):
        import comfy.samplers
        return {
            "required": {
                "images": ("IMAGE", ),
                "positive": ("STRING", {"forceInput": True}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000, "forceInput": True}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "forceInput": True}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS, {"forceInput": True}),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS, {"forceInput": True}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "forceInput": True}),
                "model_name": ("STRING", {"default": "checkpoint.safetensors"}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "optional": {
                "negative": ("STRING", {"forceInput": True, "default": ""}),
                "lora_stack": ("LORA_STACK", ),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Phantom/Saver"

    def save_images(self, images, positive, steps, cfg, sampler_name, scheduler, seed, model_name, filename_prefix="Phantom", negative="", lora_stack=None, prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        
        # Build strict A1111 EXIF formatted string
        a1111_string = f"{positive}\nNegative prompt: {negative}\nSteps: {steps}, Sampler: {sampler_name}, CFG scale: {cfg}, Seed: {seed}, Size: {images[0].shape[1]}x{images[0].shape[0]}, Model: {model_name}"
        
        if lora_stack and isinstance(lora_stack, list):
            # A1111 sometimes writes Lora hashes if configured, but keeping the tags in the prompt is sufficient
            # We already left the `<lora:name:weight>` string un-extracted in the text!
            pass
        
        metadata = PngInfo()
        metadata.add_text("parameters", a1111_string)
        if extra_pnginfo is not None:
            metadata.add_text("workflow", json.dumps(extra_pnginfo))
        if prompt is not None:
            metadata.add_text("prompt", json.dumps(prompt))

        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            file = f"{filename}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=4)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return { "ui": { "images": results } }
