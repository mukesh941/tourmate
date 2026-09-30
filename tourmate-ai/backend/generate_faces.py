import os
import sys
import random
import time
import json
import urllib.request
from PIL import Image, ImageDraw
import io

OUT_DIR = "../frontend/public/images/guides"
os.makedirs(OUT_DIR, exist_ok=True)

# Generate rainbow colors
rainbow_colors = [
    (228, 3, 3),    # Red
    (255, 140, 0),  # Orange
    (255, 237, 0),  # Yellow
    (0, 128, 38),   # Green
    (36, 64, 142),  # Blue
    (115, 41, 130)  # Purple
]

def add_rainbow_pin(img):
    draw = ImageDraw.Draw(img)
    # Draw a subtle rainbow pin on the bottom right corner (lapel area)
    width, height = img.size
    pin_width = int(width * 0.15)
    pin_height = int(height * 0.1)
    
    start_x = width - int(width * 0.25)
    start_y = height - int(height * 0.2)
    
    stripe_height = pin_height / len(rainbow_colors)
    
    # Draw white border
    border = 2
    draw.rectangle([start_x - border, start_y - border, start_x + pin_width + border, start_y + pin_height + border], fill=(255,255,255))
    
    for i, color in enumerate(rainbow_colors):
        y0 = start_y + i * stripe_height
        y1 = y0 + stripe_height
        draw.rectangle([start_x, y0, start_x + pin_width, y1], fill=color)
        
    return img

print("Fetching unique faces from randomuser.me...")
unique_urls = set()
while len(unique_urls) < 197:
    req = urllib.request.Request("https://randomuser.me/api/?nat=in&results=100", headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for user in data['results']:
                unique_urls.add(user['picture']['large'])
                if len(unique_urls) >= 197:
                    break
    except Exception as e:
        print("Failed to fetch:", e)
        time.sleep(2)
        continue
    print(f"Collected {len(unique_urls)}/197 unique faces...")

urls = list(unique_urls)

total = 197
for i in range(1, total + 1):
    file_path = os.path.join(OUT_DIR, f"guide-{i:03d}.webp")
    
    is_lgbtq = (i % 6 == 0)
    
    img_url = urls[i-1]
    
    try:
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            img_bytes = response.read()
            
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        if is_lgbtq:
            img = add_rainbow_pin(img)
            
        img.save(file_path, "WEBP", quality=90)
        print(f"Saved {file_path}")
    except Exception as e:
        print(f"Failed to save {file_path}: {e}")

print("Successfully replaced all images!")
