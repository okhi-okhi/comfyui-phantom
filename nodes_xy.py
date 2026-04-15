import re

def combine_axes(axis_x, axis_y):
    combinations_x = []
    combinations_y = []
    grid_labels = []

    for y in axis_y['values']:
        for x in axis_x['values']:
            combinations_x.append(x)
            combinations_y.append(y)
            grid_labels.append(f"{axis_x['name']}: {x} | {axis_y['name']}: {y}")
            
    return combinations_x, combinations_y, grid_labels

class AxisPrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "axis_name": ("STRING", {"default": "Prompt"}),
            }
        }
    
    RETURN_TYPES = ("AXIS",)
    RETURN_NAMES = ("X_AXIS",)
    FUNCTION = "generate"
    CATEGORY = "Phantom"

    def generate(self, text, axis_name):
        # We handle A1111 '{A|B|C}' format or simple line splits if no `{...}` found
        values = []
        if '{' in text and '}' in text:
            # simple combinatorics - just extracts the first block to axis
            match = re.search(r'\{(.*?)\}', text)
            if match:
                inner = match.group(1)
                options = inner.split('|')
                for opt in options:
                    values.append(text.replace(match.group(0), opt.strip()))
        else:
            # otherwise assume newline delimited list
            values = [v.strip() for v in text.split('\n') if v.strip()]
            
        return ({"name": axis_name, "values": values},)

class AxisSteps:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "steps": ("STRING", {"default": "20, 30, 40"}),
                "axis_name": ("STRING", {"default": "Steps"}),
            }
        }
    
    RETURN_TYPES = ("AXIS",)
    RETURN_NAMES = ("Y_AXIS",)
    FUNCTION = "generate"
    CATEGORY = "Phantom"

    def generate(self, steps, axis_name):
        # comma delimited ints
        values = [int(v.strip()) for v in steps.split(',') if v.strip().isdigit()]
        return ({"name": axis_name, "values": values},)

class XYCrossMultiplier:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "x_axis": ("AXIS",),
                "y_axis": ("AXIS",),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "GRID_LABELS")
    RETURN_NAMES = ("STRING_VALUES", "INT_VALUES", "GRID_LABELS")
    OUTPUT_IS_LIST = (True, True, False)  # Output matched flat lists, block grid labels to pass as one chunk
    FUNCTION = "multiply"
    CATEGORY = "Phantom"

    def multiply(self, x_axis, y_axis):
        x_vals, y_vals, labels = combine_axes(x_axis, y_axis)
        return (x_vals, y_vals, labels)

class XYGridBuilder:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "grid_labels": ("GRID_LABELS",),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    INPUT_IS_LIST = True
    FUNCTION = "build_grid"
    CATEGORY = "Phantom"

    def build_grid(self, images, grid_labels):
        # The simple version just stacks PyTorch tensors.
        # This will be refined. Images input is a list of Tensors [1, H, W, 3].
        import torch
        from math import ceil
        
        # Determine cols by X_AXIS size if possible... wait, how to know X axis size?
        # A simple hack: we use the number of unique X values.
        # But for now, let's just create a horizontal strip or generic square
        n = len(images)
        cols = ceil(n ** 0.5)
        # Using basic torch view/cat to form grid
        # Assuming all images are same size
        # A more robust grid builder is usually standard in ComfyUI or ImageBatch
        batch = torch.cat(images, dim=0)
        # TODO: Implement proper 2D layout based on axis size. 
        # For simplicity, returning batch. To make actual grid 2D image, use torchvision make_grid
        from torchvision.utils import make_grid
        batch = batch.permute(0, 3, 1, 2)
        grid = make_grid(batch, nrow=cols)
        grid = grid.permute(1, 2, 0).unsqueeze(0)
        
        return (grid,)
