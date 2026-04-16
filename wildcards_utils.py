import os
import random
import re
import folder_paths

# Try to find common wildcard folders
WILDCARD_PATHS = []

custom_nodes_path = folder_paths.get_folder_paths("custom_nodes")[0]
possible_wildcard_folders = [
    os.path.join(folder_paths.base_path, "wildcards"),
    os.path.join(custom_nodes_path, "comfyui-impact-pack", "wildcards"),
    os.path.join(custom_nodes_path, "comfyui-dynamicprompts", "wildcards"),
]

for p in possible_wildcard_folders:
    if os.path.exists(p) and os.path.isdir(p):
        WILDCARD_PATHS.append(p)

def get_wildcard_list(wildcard_name):
    """Recursively search for the wildcard file and return its lines."""
    # wildcard_name could be something like "hair" or "colors/warm"
    # We search through all WILDCARD_PATHS
    search_name = wildcard_name.replace("\\", "/")
    
    for base_path in WILDCARD_PATHS:
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".txt") and file[:-4].replace("\\", "/") == search_name:
                    p = os.path.join(root, file)
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                            if lines:
                                return lines
                    except:
                        pass
                
                # Also fallback to matching the exact filename regardless of directory depth
                if file.endswith(".txt") and file[:-4] == search_name.split("/")[-1]:
                    p = os.path.join(root, file)
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                            if lines:
                                return lines
                    except:
                        pass
    return None

def replace_wildcards(text, seed=None):
    if seed is not None:
        random.seed(seed)
        
    print(f"\n[Phantom] Resolving wildcards for: {text}")
    
    def repl(match):
        w_name = match.group(1)
        lines = get_wildcard_list(w_name)
        if lines:
            choice = random.choice(lines)
            print(f"[Phantom] -> Found wildcard '__{w_name}__': {choice}")
            return choice
        print(f"[Phantom] -> Warning: wildcard '__{w_name}__' not found!")
        return f"__{w_name}__"

    # Support nested/recursive wildcard replacement
    max_iterations = 100
    for _ in range(max_iterations):
        new_text = re.sub(r'__([\w\-/]+)__', repl, text)
        if new_text == text:
            break
        text = new_text
        
    print(f"[Phantom] Resolved string: {text}\n")
    return text
