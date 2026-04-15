import os
import random
import re
import folder_paths

# Try to find common wildcard folders
WILDCARD_PATHS = []

custom_nodes_path = folder_paths.get_folder_paths("custom_nodes")[0]
possible_wildcard_folders = [
    os.path.join(folder_paths.base_path, "wildcards"),
    os.path.join(custom_nodes_path, "ComfyUI-Impact-Pack", "wildcards"),
    os.path.join(custom_nodes_path, "comfyui-dynamicprompts", "wildcards"),
]

for p in possible_wildcard_folders:
    if os.path.exists(p) and os.path.isdir(p):
        WILDCARD_PATHS.append(p)

def replace_wildcards(text, seed=None):
    if seed is not None:
        random.seed(seed)
    
    def repl(match):
        w_name = match.group(1)
        # Search in wildcard paths
        w_file = f"{w_name}.txt"
        
        for bp in WILDCARD_PATHS:
            p = os.path.join(bp, w_file)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                if lines:
                    return random.choice(lines)
        # If not found, return the wildcard as is
        return f"__{w_name}__"

    text = re.sub(r'__([\w-]+)__', repl, text)
    return text
