from PIL import Image, ImageDraw, ImageFont

# Create a new image
width, height = 128, 128  # 4x4 grid of 32x32 tiles
tile_size = 32
image = Image.new('RGB', (width, height), color='black')
draw = ImageDraw.Draw(image)

# Try to load a monospaced font; fallback to default if not available
try:
    font = ImageFont.truetype("DejaVuSansMono.ttf", 16)
except IOError:
    font = ImageFont.load_default()

# Define symbols and their positions (row, col)
symbols = [
    ("╔", 0, 0), ("═", 0, 1), ("═", 0, 2), ("╗", 0, 3),
    ("║", 1, 0), ("·", 1, 1), ("·", 1, 2), ("║", 1, 3),
    ("║", 2, 0), ("·", 2, 1), ("·", 2, 2), ("║", 2, 3),
    ("╚", 3, 0), ("═", 3, 1), ("═", 3, 2), ("╝", 3, 3),
]

for symbol, row, col in symbols:
    x0 = col * tile_size
    y0 = row * tile_size
    x1 = x0 + tile_size
    y1 = y0 + tile_size
    # Get bounding box of the text to center it
    bbox = draw.textbbox((x0, y0), symbol, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = x0 + (tile_size - w) // 2
    y = y0 + (tile_size - h) // 2
    draw.text((x, y), symbol, font=font, fill='white')

# Save the image
image.save('/home/danny/Code/DarkDelve/assets/tilesets/new_tileset.png')
print("New tileset saved to /home/danny/Code/DarkDelve/assets/tilesets/new_tileset.png")