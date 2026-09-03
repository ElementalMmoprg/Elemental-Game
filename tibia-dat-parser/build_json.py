import sys, json, time
from parse_dat import read_u32, read_u16, parse_thing

COLLISION_FLAGS = {'notWalkable','notMoveable','blockProjectile','notPathable','pickupable','stackable','container','fluidContainer','hangable','rotateable','onTop','onBottom','groundBorder','fullGround'}

def compact_frame_group(fg):
    out = {'w':fg['width'],'h':fg['height'],'layers':fg['layers'],
           'px':fg['patternX'],'py':fg['patternY'],'pz':fg['patternZ'],
           'phases':fg['phases'],'sprites':fg['spriteIds']}
    if fg['realSize'] is not None: out['realSize'] = fg['realSize']
    return out

def compact_thing(thing, is_item):
    out = {}
    flags = thing['flags']
    if is_item:
        coll = [f for f in flags if f in COLLISION_FLAGS]
        if coll: out['flags'] = coll
        if 'ground' in thing['data']: out['groundSpeed'] = thing['data']['ground']
    else:
        if flags: out['flags'] = flags
    if thing.get('multi'):
        out['groups'] = {str(k): compact_frame_group(v) for k,v in thing['frameGroups'].items()}
    else:
        out['fg'] = compact_frame_group(thing['frameGroup'])
    return out

def main():
    dat_path = sys.argv[1]
    out_path = sys.argv[2]
    with open(dat_path,'rb') as f:
        buf = f.read()
    filesize = len(buf)
    pos = 0
    signature, pos = read_u32(buf, pos)
    item_count, pos = read_u16(buf, pos)
    outfit_count, pos = read_u16(buf, pos)
    effect_count, pos = read_u16(buf, pos)
    missile_count, pos = read_u16(buf, pos)

    items = {}
    for i in range(item_count):
        thing, pos = parse_thing(buf, pos)
        items[100+i] = compact_thing(thing, True)
    items_end_pos = pos
    print('items parsed, end pos=', pos, file=sys.stderr)

    outfits = {}
    for i in range(outfit_count):
        thing, pos = parse_thing(buf, pos)
        outfits[i+1] = compact_thing(thing, False)
    outfits_end_pos = pos
    print('outfits parsed, end pos=', pos, file=sys.stderr)

    # effects/missiles: parse for validation + basic sprite refs, but keep compact (many are simple)
    effects = {}
    for i in range(effect_count):
        thing, pos = parse_thing(buf, pos)
        effects[i+1] = compact_thing(thing, False)
    print('effects parsed, end pos=', pos, file=sys.stderr)

    real_missile_count = 0
    missiles = {}
    for i in range(missile_count):
        if pos >= filesize:
            print('stopping missiles early at index', i, '(header claimed', missile_count, ') pos==filesize', file=sys.stderr)
            break
        thing, pos = parse_thing(buf, pos)
        missiles[i+1] = compact_thing(thing, False)
        real_missile_count += 1
    print('missiles parsed:', real_missile_count, 'end pos=', pos, 'filesize=', filesize, 'EXACT_EOF=', pos==filesize, file=sys.stderr)

    out = {
        'meta': {
            'source': 'tibia.dat (Dezembro 16, 2025 update_7)',
            'itemCount': item_count, 'outfitCount': outfit_count,
            'effectCount': effect_count, 'missileCountHeader': missile_count,
            'missileCountActual': real_missile_count,
            'spriteIdWidth': 32, 'extendedSprites': True,
            'note': 'flags[] on items are collision/placement-relevant only (full attribute list not preserved). sprites[] are raw tibia.spr sprite IDs (32x32 tiles); use them to look up frames once tibia.spr is decoded.'
        },
        'items': items,
        'outfits': outfits,
    }
    with open(out_path, 'w') as f:
        json.dump(out, f, separators=(',',':'))
    import os
    print('wrote', out_path, 'size=', os.path.getsize(out_path), 'bytes', file=sys.stderr)

if __name__ == '__main__':
    main()
