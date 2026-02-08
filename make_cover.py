
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import os

# Configuration
# 尝试自动找到 D十一 文件夹下的图片
SEARCH_DIR = 'D十一'
OUTPUT_FILE = 'cover.png'
TEXT_CONTENT = "哈仔十一关系图"
CANVAS_SIZE = (1920, 1080)
FONT_PATH = 'C:/Windows/Fonts/msyh.ttc'

def get_image_path():
    if os.path.exists(SEARCH_DIR):
        for f in os.listdir(SEARCH_DIR):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                return os.path.join(SEARCH_DIR, f)
    return None

def create_cover():
    img_path = get_image_path()
    if not img_path:
        print(f"No image found in {SEARCH_DIR}")
        return

    print(f"Using image: {img_path}")
    
    try:
        original_img = Image.open(img_path).convert('RGBA')
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Create background (blurred version of original stretched)
    # This is a nice value-add for vertical images on 16:9
    base_img = Image.new('RGB', CANVAS_SIZE, (0,0,0))
    
    # Method 1: Fit (Crop) - might cut off head
    # Method 2: Blur background + Fit center
    
    # Let's use Method 2 which is safer for varying aspect ratios
    bg = original_img.resize(CANVAS_SIZE, Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    
    # Resize original to fit inside height or width
    ratio_w = CANVAS_SIZE[0] / original_img.width
    ratio_h = CANVAS_SIZE[1] / original_img.height
    scale = min(ratio_w, ratio_h)
    
    # If the image is close to 16:9, just fill. 
    # If it's very vertical, fit inside.
    # User said "弄成16:9", usually implies filling the screen.
    # Let's try ImageOps.fit for a full bleed look first, it usually looks better for covers.
    
    final_img = ImageOps.fit(original_img, CANVAS_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    
    # Draw Text
    draw = ImageDraw.Draw(final_img)
    
    # Font
    try:
        font = ImageFont.truetype(FONT_PATH, 150)
    except:
        font = ImageFont.load_default()
        
    text = TEXT_CONTENT
    
    # Calculate text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (CANVAS_SIZE[0] - text_w) // 2
    # Place text at bottom area
    y = CANVAS_SIZE[1] - text_h - 100
    
    # Shadow/Stroke
    stroke_width = 10
    stroke_color = (0, 0, 0)
    text_color = (255, 255, 0)
    
    # Draw stroke
    for off_x in range(-stroke_width, stroke_width+1):
        for off_y in range(-stroke_width, stroke_width+1):
            draw.text((x+off_x, y+off_y), text, font=font, fill=stroke_color)
            
    # Draw main text
    draw.text((x, y), text, font=font, fill=text_color)
    
    final_img.save(OUTPUT_FILE)
    print(f"Cover saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    create_cover()
