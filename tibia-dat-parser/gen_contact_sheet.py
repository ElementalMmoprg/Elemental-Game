import json
import sys
from PIL import Image, ImageDraw

SPR_PATH = sys.argv[1]
OUTFITS_JSON = sys.argv[2]
START = int(sys.argv[3])
END = int(sys.argv[4])
OUT = sys.argv[5]

sys.path.insert(0, '.')
from decode_spr import decode_tile

with open(OUTFITS_JSON) as f:
    outfits = json.load(f)

with open('/tmp/candidates.json') as f:
    cand = json.load(f)

batch = cand[START:END]
n = len(batch)
cols = 10
rows = (n + cols - 1) // cols
cell = 70
canvas = Image.new('RGB', (cols * cell, rows * cell), (30, 30, 30))
draw = ImageDraw.Draw(canvas)

with open(SPR_PATH, 'rb') as f:
    for i, outfit_id in enumerate(batch):
        entry = outfits[str(outfit_id)]
        g0 = entry['groups'][0]
        sprite_id = g0['sprites'][0]
        tile = decode_tile(f, sprite_id)
        tile_big = tile.resize((64, 64), Image.NEAREST)
        r, c = divmod(i, cols)
        x, y = c * cell, r * cell
        bg = Image.new('RGB', (64, 64), (60, 60, 60))
        bg.paste(tile_big, (0, 0), tile_big)
        canvas.paste(bg, (x + 3, y + 3))
        draw.text((x + 3, y + 55), str(outfit_id), fill=(255, 255, 0))

canvas.save(OUT)
print('saved', OUT, canvas.size, 'n=', n)
