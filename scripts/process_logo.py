import os
from PIL import Image, ImageChops
import numpy as np

def process_and_crop():
    input_path = "backend/data/ea1d220a280be38853d3b8d056d7b89d.jpg"
    output_dir = "frontend/public"
    os.makedirs(output_dir, exist_ok=True)
    
    output_png = os.path.join(output_dir, "sda_logo.png")
    
    print(f"Loading logo from {input_path}...")
    img = Image.open(input_path).convert("RGBA")
    
    # 1. Background Removal
    # We'll treat very light colors as background
    data = np.array(img)
    r, g, b, a = data.T
    
    # White floor threshold (adjust if needed)
    white_areas = (r > 240) & (g > 240) & (b > 240)
    data[..., 3][white_areas.T] = 0 # Set alpha to 0 for white areas
    
    img = Image.fromarray(data)
    
    # 2. Cropping
    bg = Image.new(img.mode, img.size, (0,0,0,0))
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    
    if bbox:
        img = img.crop(bbox)
        print(f"Logo cropped to {bbox}")
    
    img.save(output_png)
    print(f"Saved transparent cropped logo to {output_png}")

    # 3. Simple SVG Wrapper (Embedding the processed logo)
    # This is more reliable for map markers than a complex trace
    output_svg = os.path.join(output_dir, "sda_logo.svg")
    width, height = img.size
    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image xlink:href="sda_logo.png" width="{width}" height="{height}" />
</svg>'''
    
    with open(output_svg, "w") as f:
        f.write(svg_content)
    print(f"Generated SVG wrapper at {output_svg}")

if __name__ == "__main__":
    process_and_crop()
