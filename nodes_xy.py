import re
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from torchvision.utils import make_grid

def combine_axes(axis_x, axis_y):
    combinations_x = []
    combinations_y = []

    for y in axis_y['values']:
        for x in axis_x['values']:
            combinations_x.append(x)
            combinations_y.append(y)
            
    grid_data = {
        "x_title": axis_x['name'],
        "y_title": axis_y['name'],
        "x_labels": axis_x.get('labels', []),
        "y_labels": axis_y.get('labels', []),
        "cols": len(axis_x['values']),
        "rows": len(axis_y['values'])
    }
            
    return combinations_x, combinations_y, grid_data

class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False
ANY = AnyType("*")

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
    RETURN_NAMES = ("x_axis",)
    FUNCTION = "generate"
    CATEGORY = "Phantom"

    def generate(self, text, axis_name):
        values = []
        labels = []
        matches = list(re.finditer(r'\{(.*?)\}', text))
        
        if matches:
            opts_list = [m.group(1).split('|') for m in matches]
            # Assumes combinations are zipped together
            max_opts = max(len(o) for o in opts_list)
            
            for i in range(max_opts):
                val = text
                diff_label = []
                
                # Check for each block variation
                for m_idx, m in enumerate(matches):
                    opt = opts_list[m_idx][i % len(opts_list[m_idx])].strip()
                    val = val.replace(m.group(0), opt)
                    
                    # Discover context backwards if it's within a LoRA tag <lora:NAME:{opt}>
                    start = m.start()
                    lora_match = re.search(r'<lora:([^:>]+)[^>]*?$', text[:start])
                    if lora_match and text[start:m.end()+1].endswith('>'):
                        diff_label.append(f"{lora_match.group(1)}:{opt}")
                    else:
                        diff_label.append(opt)
                        
                values.append(val)
                labels.append(", ".join(diff_label))
        else:
            # newline delimited fallback
            values = [v.strip() for v in text.split('\n') if v.strip()]
            labels = values
            
        return ({"name": axis_name, "values": values, "labels": labels},)

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
    RETURN_NAMES = ("y_axis",)
    FUNCTION = "generate"
    CATEGORY = "Phantom"

    def generate(self, steps, axis_name):
        values = [int(v.strip()) for v in steps.split(',') if v.strip().isdigit()]
        labels = [str(v) for v in values]
        return ({"name": axis_name, "values": values, "labels": labels, "type": "int"},)

class AxisFloat:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "floats": ("STRING", {"default": "6.0, 7.0, 8.0"}),
                "axis_name": ("STRING", {"default": "CFG"}),
            }
        }
    
    RETURN_TYPES = ("AXIS",)
    RETURN_NAMES = ("cfgs",)
    FUNCTION = "generate"
    CATEGORY = "Phantom"

    def generate(self, floats, axis_name):
        def is_float(v):
            try:
                float(v)
                return True
            except ValueError:
                return False
        values = [float(v.strip()) for v in floats.split(',') if is_float(v.strip())]
        labels = [str(v) for v in values]
        return ({"name": axis_name, "values": values, "labels": labels, "type": "float"},)

class XYCrossMultiplier:
    @classmethod
    def INPUT_TYPES(s):
        return {    
            "required": {
                "x_axis": ("AXIS",),
                "y_axis": ("AXIS",),
            }
        }
    
    RETURN_TYPES = (ANY, ANY, "STRING", "GRID_LABELS")
    RETURN_NAMES = ("x_values", "y_values", "combined_prompt", "grid_labels")
    OUTPUT_IS_LIST = (True, True, True, False)  # Output matched flat lists, block grid labels to pass as one chunk
    FUNCTION = "multiply"
    CATEGORY = "Phantom"

    def multiply(self, x_axis, y_axis):
        x_vals, y_vals, labels = combine_axes(x_axis, y_axis)
        
        # Automatically generate combined prompts if both axes are used for prompts/LoRAs
        combined = []
        for i in range(len(x_vals)):
            x = x_vals[i]
            y = y_vals[i]
            
            p_parts = []
            if x_axis.get('type') in ['prompt', 'string', None] and isinstance(x, str):
                p_parts.append(x)
            
            if y_axis.get('type') in ['prompt', 'string', None] and isinstance(y, str):
                p_parts.append(y)
                
            combined.append(", ".join(p_parts) if p_parts else "")
            
        return (x_vals, y_vals, combined, labels)

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
        grid_data = grid_labels[0]
        x_labels = grid_data["x_labels"]
        y_labels = grid_data["y_labels"]
        x_title = grid_data["x_title"]
        y_title = grid_data["y_title"]
        cols = grid_data["cols"]
        rows = grid_data["rows"]
        
        pil_images = []
        for img_tensor in images:
            if len(img_tensor.shape) == 4:
                img_tensor = img_tensor.squeeze(0)
            np_img = (255. * img_tensor.cpu().numpy()).astype(np.uint8)
            pil_images.append(Image.fromarray(np.clip(np_img, 0, 255)))
            
        # 1. Resize smaller by factor max(cols, rows)
        scale_factor = max(1, max(cols, rows))
        if scale_factor > 1:
            pil_images = [img.resize((img.width // scale_factor, img.height // scale_factor), Image.Resampling.LANCZOS) for img in pil_images]
            
        img_w, img_h = pil_images[0].size
        
        header_h = 100
        side_w = 150
        
        total_w = side_w + cols * img_w
        total_h = header_h + rows * img_h
        
        canvas = Image.new('RGB', (total_w, total_h), color='white')
        draw = ImageDraw.Draw(canvas)
        
        def load_font(size):
            try:
                return ImageFont.truetype("arial.ttf", size)
            except IOError:
                try:
                    return ImageFont.truetype("LiberationSans-Regular.ttf", size)
                except IOError:
                    try:
                        return ImageFont.load_default(size=size)
                    except TypeError:
                        return ImageFont.load_default()

        font = load_font(16)
        title_font = load_font(20)

        # Helper for handling line breaks based on image width/height boundaries
        def draw_multiline(draw, txt, x_center, y_center, f, max_w):
            words = txt.split(' ')
            lines = []
            cur_line = ""
            for w in words:
                try:
                    w_w = draw.textbbox((0,0), cur_line + w, font=f)[2]
                except AttributeError:
                    w_w = draw.textsize(cur_line + w, font=f)[0]
                if w_w < max_w:
                    cur_line += w + " "
                else:
                    lines.append(cur_line.strip())
                    cur_line = w + " "
            if cur_line:
                lines.append(cur_line.strip())
                
            try:
                box = draw.textbbox((0,0), "A", font=f)
                line_height = box[3] - box[1]
            except AttributeError:
                line_height = draw.textsize("A", font=f)[1]
                
            y_start = y_center - (len(lines) * line_height) // 2
            for line in lines:
                try:
                    box = draw.textbbox((0,0), line, font=f)
                    t_w = box[2] - box[0]
                    offset_x = box[0]
                    offset_y = box[1]
                except AttributeError:
                    t_w = draw.textsize(line, font=f)[0]
                    offset_x = 0
                    offset_y = 0
                    
                draw.text((x_center - t_w//2 - offset_x, y_start - offset_y), line, fill="black", font=f)
                y_start += line_height + 6

        # Draw X Header Titles
        for c in range(cols):
            x_pos = side_w + c * img_w + (img_w // 2)
            y_pos = header_h // 2
            txt = f"{x_title}\n{x_labels[c]}" if c < len(x_labels) else f"{x_title}\nUnknown"
            draw_multiline(draw, txt, x_pos, y_pos, font, img_w - 20)
            
        # Draw Y Header Titles
        for r in range(rows):
            x_pos = side_w // 2
            y_pos = header_h + r * img_h + (img_h // 2)
            txt = f"{y_title}\n{y_labels[r]}" if r < len(y_labels) else f"{y_title}\nUnknown"
            draw_multiline(draw, txt, x_pos, y_pos, font, side_w - 20)
            
        # Paste Images
        for i, img in enumerate(pil_images):
            c = i % cols
            r = i // cols
            canvas.paste(img, (side_w + c * img_w, header_h + r * img_h))

        new_np = np.array(canvas).astype(np.float32) / 255.0
        new_tensor = torch.from_numpy(new_np).unsqueeze(0)
        
        return (new_tensor,)
