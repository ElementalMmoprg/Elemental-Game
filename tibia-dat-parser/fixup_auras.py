import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from decode_spr import decode_tile
from PIL import Image

BASE = os.path.dirname(__file__)
SPR_PATH = None
for cand in [
    os.path.expanduser("~/mnt/Ravendawn Spr e Dat 8/export_10.98.spr"),
]:
    if os.path.exists(cand):
        SPR_PATH = cand
        break
if SPR_PATH is None:
    raise SystemExit("spr not found")

AURAS_DIR = os.path.expanduser("~/mnt/GitHub/Elemental_assets/assets/auras")

FIXUP = [(3,2394),(4,2407),(5,2424),(6,2410),(8,2386)]

effects = json.load(open(os.path.join(BASE, "effects_export1098_full.json")))

def compose_pattern0_phases(f, group):
    w, h = group['w'], group['h']
    layers = group.get('layers', 1)
    px = group.get('px', 1); py = group.get('py', 1); pz = group.get('pz', 1)
    phases = group.get('phases', 1)
    sprites = group['sprites']
    n_tiles = w * h
    pattern_count = px * py * pz * layers
    out = []
    for phase in range(phases):
        block_start = phase * pattern_count * n_tiles
        block = sprites[block_start:block_start + n_tiles]
        canvas = Image.new('RGBA', (w * 32, h * 32))
        idx = 0
        for yy in range(h):
            for xx in range(w):
                if idx >= len(block):
                    idx += 1
                    continue
                tile = decode_tile(f, block[idx])
                idx += 1
                canvas.paste(tile, (xx * 32, yy * 32))
        out.append(canvas)
    return out

results = {}
with open(SPR_PATH, 'rb') as f:
    for aid, cid in FIXUP:
        entry = effects[str(cid)]
        fg = entry['fg']
        frames = compose_pattern0_phases(f, fg)
        folder = os.path.join(AURAS_DIR, f"aura_{aid}")
        # delete old (incorrect) frames
        for fn in os.listdir(folder):
            if fn.startswith('f') and fn.endswith('.png'):
                os.remove(os.path.join(folder, fn))
        for i, im in enumerate(frames):
            im.save(os.path.join(folder, f"f{i:02d}.png"))
        results[aid] = {"clientid": cid, "frameCount": len(frames), "w": fg['w']*32, "h": fg['h']*32}
        print(f"aura_{aid} (clientid {cid}): {len(frames)} frames corrigidos")

with open(os.path.join(BASE, "fixup_results.json"), "w") as out:
    json.dump(results, out, indent=2)
