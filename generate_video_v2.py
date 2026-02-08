
import re
import os
from PIL import Image, ImageDraw, ImageFont
import subprocess
import glob

# Configuration
RELATIONS_FILE = 'Relations.md'
FRAMES_DIR = 'frames'
OUTPUT_VIDEO = 'output.mp4'
FONT_PATH = 'C:/Windows/Fonts/msyh.ttc'  # Microsoft YaHei
CANVAS_SIZE = (1920, 1080)
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
AVATAR_MAX_SIZE = (500, 500)
FRAME_DURATION = 3  # Seconds

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except IOError:
        try:
            return ImageFont.truetype("simhei.ttf", size)
        except IOError:
            return ImageFont.load_default()

def parse_node_content(content):
    # Regex to split Name and Title based on Gender marker [MFU] followed by [-:]
    # Example: 十一M-哈士奇... -> Name: 十一, Title: 哈士奇...
    # Example: 疯婆娘F:原始股东 -> Name: 疯婆娘, Title: 原始股东
    match = re.search(r"^(.*?)([MFU])([-:])(.*)$", content, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        title = match.group(4).strip()
        return name, title
    
    # Fallback/Other cases
    # Example: 猪罗纪 -> Name: 猪罗纪, Title: ""
    return content.strip(), ""

def parse_node_str(node_str):
    # Extracts ID and Content from A[Content]
    match = re.match(r"^([A-Z0-9]+)[\[\{\(](.*)[\]\}\)]$", node_str)
    if match:
        return match.group(1), match.group(2)
    return "", ""

def parse_relations(file_path):
    relationships = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('style') or line.startswith('%%') or line.startswith('graph') or line.startswith('```'):
                continue

            # Match Line: Node1 Arrow Node2
            # Node pattern: ID[Content] or ID{Content} or ID(Content)
            # Find the two nodes. The text between is the arrow.
            
            # This regex looks for two groups that look like nodes, separated by something.
            # Node regex: ([A-Z0-9]+[\[\{\(].*?[\]\}\)])
            node_pattern = r"([A-Z0-9]+[\[\{\(].*?[\]\}\)])"
            
            # Find all nodes in the line
            nodes = [m.group(0) for m in re.finditer(node_pattern, line)]
            
            if len(nodes) == 2:
                # We have exactly two nodes.
                node1_str = nodes[0]
                node2_str = nodes[1]
                
                # Split line by these nodes to find the middle part (relation)
                # Escape them for regex 
                # Doing simple string split might be safer if unique
                parts = line.split(node1_str)
                if len(parts) > 1:
                    rest = parts[1]
                    parts2 = rest.split(node2_str)
                    relation_raw = parts2[0].strip()
                    
                    # Parse Node 1
                    id1, content1 = parse_node_str(node1_str)
                    name1, title1 = parse_node_content(content1)
                    
                    # Parse Node 2
                    id2, content2 = parse_node_str(node2_str)
                    name2, title2 = parse_node_content(content2)
                    
                    # Parse Relation
                    # Arrow examples: -->, -- 骑 -->, -- is 小弟 of-->
                    # Extract text inside arrow
                    # Remove starting - and ending > and -
                    # Usually arrow is -- TEXT --> or -->
                    arrow_text = ""
                    # Regex to extract text inside arrow
                    # Look for something between -- and -->
                    arrow_match = re.search(r"-+\s*(.*?)\s*-+>", relation_raw)
                    if arrow_match:
                        arrow_text = arrow_match.group(1).strip()
                    
                    relationships.append({
                        'left': {'id': id1, 'name': name1, 'title': title1},
                        'right': {'id': id2, 'name': name2, 'title': title2},
                        'relation': arrow_text
                    })
    return relationships

def find_avatar_path(id_val, name):
    # Expect folder named {ID}{Name} e.g. D十一
    # Sometimes ID and Name might be concatenated differently or spacing?
    # Based on workspace, it is ID+Name (no space).
    # Check for exact match first
    
    target_folder = f"{id_val}{name}"
    
    # workspace root is current dir
    for item in os.listdir('.'):
        if os.path.isdir(item):
            if item == target_folder:
                 # Find first image in this folder
                 folder_path = item
                 for file in os.listdir(folder_path):
                     if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                         return os.path.join(folder_path, file)
    
    # Fallback: Maybe folder name is slightly different?
    # Try searching for folder starting with ID
    # Risk: A and AA, B and AB.
    # So matching ID+Name is safest.
    
    return None

def draw_text_wrapped(draw, text, font, color, cx, y, max_width):
    lines = []
    # If text contains slashes, treat as newlines? User used / in title.
    # e.g. 原始股东/雪橇犬选美2nd/头狗
    # Let's replace / with newline for better formatting if it helps, or wrap properly.
    # The prompt doesn't specify, but lists "哈士奇:原始股东/雪橇犬选美2nd/头狗" as a title line.
    
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w > max_width:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    lines.append(current_line)
    
    current_y = y
    for line in lines:
        draw.text((cx, current_y), line, font=font, fill=color, anchor="mt")
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        current_y += h + 10

def draw_person(img, draw, person, avatar_path, align, name_font, title_font):
    # Layout parameters
    col_width = CANVAS_SIZE[0] // 3
    center_x = col_width // 2 if align == 'left' else (CANVAS_SIZE[0] - col_width // 2)
    center_y = CANVAS_SIZE[1] // 2
    
    # Avatar
    # Place avatar above center
    # Avatar area center: y = center_y - 150
    avatar_cy = center_y - 150
    
    if avatar_path and os.path.exists(avatar_path):
        try:
            avatar = Image.open(avatar_path)
            # Resize preserving aspect ratio to fit in AVATAR_MAX_SIZE
            avatar.thumbnail(AVATAR_MAX_SIZE, Image.Resampling.LANCZOS)
            
            w, h = avatar.size
            pos = (center_x - w // 2, avatar_cy - h // 2)
            img.paste(avatar, pos)
        except Exception as e:
            print(f"Error loading avatar for {person['name']}: {e}")
            pass
    # No "else text" because if no avatar, we just show text below.

    # Name text below avatar area
    text_base_y = center_y + 150
    
    draw.text((center_x, text_base_y), person['name'], font=name_font, fill=TEXT_COLOR, anchor="mt")
    
    # Title text below name
    if person['title']:
        draw_text_wrapped(draw, person['title'], title_font, TEXT_COLOR, center_x, text_base_y + 80, col_width - 40)

def create_frame(idx, rel):
    img = Image.new('RGB', CANVAS_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Font setup
    name_font = get_font(60)
    title_font = get_font(40)
    rel_font = get_font(50)
    
    # --- Left Person ---
    left = rel['left']
    avatar_path1 = find_avatar_path(left['id'], left['name'])
    draw_person(img, draw, left, avatar_path1, align='left', name_font=name_font, title_font=title_font)
    
    # --- Right Person ---
    right = rel['right']
    avatar_path2 = find_avatar_path(right['id'], right['name'])
    draw_person(img, draw, right, avatar_path2, align='right', name_font=name_font, title_font=title_font)
    
    # --- Middle Relation ---
    cx, cy = CANVAS_SIZE[0] // 2, CANVAS_SIZE[1] // 2
    rel_text = rel['relation']
    display_text = f"{rel_text} ->" if rel_text else "->"
    
    # Draw text centered
    bbox = draw.textbbox((0, 0), display_text, font=rel_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    draw.text((cx - text_w // 2, cy - text_h // 2), display_text, font=rel_font, fill=TEXT_COLOR)
    
    # Save
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)
    img.save(f"{FRAMES_DIR}/frame_{idx:04d}.png")
    print(f"Generated frame {idx}: {left['name']} {display_text} {right['name']}")


def find_bgm():
    music_dir = 'Music'
    if os.path.exists(music_dir):
        for file in os.listdir(music_dir):
            if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
                return os.path.join(music_dir, file)
    return None

def main():
    if not os.path.exists(FRAMES_DIR):
        os.makedirs(FRAMES_DIR)
        
    relations = parse_relations(RELATIONS_FILE)
    print(f"Found {len(relations)} relations.")
    
    for i, rel in enumerate(relations):
        create_frame(i, rel)
    
    bgm_path = find_bgm()
    print(f"Background music found: {bgm_path}")

    # FFmpeg command
    # -y overwrite output
    # -framerate 1/3 -> Each image lasts 3 seconds
    # -i frames/frame_%04d.png -> Input pattern
    # -stream_loop -1 -i bgm -> Loop music
    # -c:v libx264 -> Video Codec
    # -c:a aac -> Audio Codec
    # -shortest -> Finish when shortest stream (video) ends
    
    cmd = [
        'ffmpeg', '-y',
        '-framerate', f'1/{FRAME_DURATION}',
        '-i', f'{FRAMES_DIR}/frame_%04d.png'
    ]
    
    if bgm_path:
        # Add looped audio input
        cmd.extend(['-stream_loop', '-1', '-i', bgm_path])
    
    cmd.extend([
        '-c:v', 'libx264',
        '-r', '30',
        '-pix_fmt', 'yuv420p'
    ])
    
    if bgm_path:
        cmd.extend(['-c:a', 'aac', '-shortest'])
        
    cmd.append(OUTPUT_VIDEO)
    
    print("Running FFmpeg: " + " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Video saved to {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
