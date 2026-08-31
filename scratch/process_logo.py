import os
from PIL import Image, ImageDraw

src = r'C:\Users\shrey\.gemini\antigravity-ide\brain\e57b4fa8-bbea-45ea-a8fe-d1e7aec69b1f\.user_uploaded\media_1788193375485.jpg'
img = Image.open(src).convert('RGBA')
w, h = img.size
print(f"Original image size: {w}x{h}")

# The logo is a circle in the center. Let's find the circle bounds.
# Let's inspect along the center horizontal line to find the outer edge of the colored ring.
center_y = h // 2
center_x = w // 2

# Scan from left to find first non-black pixel
left_edge = 0
for x in range(w):
    r, g, b, a = img.getpixel((x, center_y))
    if r > 25 or g > 25 or b > 25:
        left_edge = x
        break

# Scan from right to find last non-black pixel
right_edge = w - 1
for x in range(w - 1, -1, -1):
    r, g, b, a = img.getpixel((x, center_y))
    if r > 25 or g > 25 or b > 25:
        right_edge = x
        break

# Scan from top to find first non-black pixel
top_edge = 0
for y in range(h):
    r, g, b, a = img.getpixel((center_x, y))
    if r > 25 or g > 25 or b > 25:
        top_edge = y
        break

# Scan from bottom to find last non-black pixel
bottom_edge = h - 1
for y in range(h - 1, -1, -1):
    r, g, b, a = img.getpixel((center_x, y))
    if r > 25 or g > 25 or b > 25:
        bottom_edge = y
        break

print(f"Detected bounds: Left={left_edge}, Right={right_edge}, Top={top_edge}, Bottom={bottom_edge}")

cx = (left_edge + right_edge) / 2.0
cy = (top_edge + bottom_edge) / 2.0
rx = (right_edge - left_edge) / 2.0
ry = (bottom_edge - top_edge) / 2.0
radius = min(rx, ry)
print(f"Center: ({cx}, {cy}), Radius: {radius}")

# Create high-resolution anti-aliased mask
# Super-sample by 4x for smooth anti-aliased circular edge
scale = 4
mask_size = (w * scale, h * scale)
mask = Image.new('L', mask_size, 0)
draw = ImageDraw.Draw(mask)

draw.ellipse([
    (cx - radius) * scale,
    (cy - radius) * scale,
    (cx + radius) * scale,
    (cy + radius) * scale
], fill=255)

# Downsample mask with high-quality resampling
mask = mask.resize((w, h), Image.Resampling.LANCZOS)

# Apply mask to image
result = Image.new('RGBA', (w, h), (0, 0, 0, 0))
result.paste(img, (0, 0), mask)

# Crop closely to the circular emblem
bbox = (int(cx - radius), int(cy - radius), int(cx + radius), int(cy + radius))
cropped = result.crop(bbox)

# Save transparent PNG to assets
output_paths = [
    r'a:\SHREYAS\RAILWAY BLOCK AI\frontend\assets\railopt_logo.png',
    r'a:\SHREYAS\RAILWAY BLOCK AI\frontend\assets\logo.png',
    r'a:\SHREYAS\RAILWAY BLOCK AI\frontend\assets\10_indian_railways_official_logo_ad892ab5.png'
]

for p in output_paths:
    cropped.save(p, 'PNG', optimize=True)
    print(f"Saved: {p} ({cropped.size[0]}x{cropped.size[1]})")

print("Processing complete!")
