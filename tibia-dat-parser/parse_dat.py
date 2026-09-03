import struct, json, sys, os

def read_u8(buf, pos): return buf[pos], pos+1
def read_u16(buf, pos): return struct.unpack_from('<H', buf, pos)[0], pos+2
def read_u32(buf, pos): return struct.unpack_from('<I', buf, pos)[0], pos+4
def read_s8(buf, pos): return struct.unpack_from('<b', buf, pos)[0], pos+1
def read_s32(buf, pos): return struct.unpack_from('<i', buf, pos)[0], pos+4
def read_string(buf, pos):
    ln, pos = read_u16(buf, pos)
    if ln > 500: raise Desync('string too long, likely desync')
    s = buf[pos:pos+ln].decode('latin1')
    return s, pos+ln

class Desync(Exception): pass

FLAG_NAMES = {
 0:'ground',1:'groundBorder',2:'onBottom',3:'onTop',4:'container',5:'stackable',
 6:'forceUse',7:'multiUse',8:'writable',9:'writableOnce',10:'fluidContainer',
 11:'splash',12:'notWalkable',13:'notMoveable',14:'blockProjectile',15:'notPathable',
 16:'pickupable',17:'hangable',18:'hookSouth',19:'hookEast',20:'rotateable',
 21:'light',22:'dontHide',23:'translucent',24:'displacement',25:'elevation',
 26:'lyingCorpse',27:'animateAlways',28:'minimapColor',29:'lensHelp',30:'fullGround',
 31:'look',32:'cloth',33:'market',34:'usable',35:'wrapable',36:'unwrapable',37:'topEffect',
 100:'opacity',101:'notPreWalkable',252:'floorChange',253:'noMoveAnimation',254:'chargeable'
}
U16_PAYLOAD_ATTRS = {0,8,9,25,28,29,32,34}

def parse_attributes(buf, pos):
    flags = []
    data = {}
    n = 0
    while True:
        n += 1
        if n > 600: raise Desync('too many attributes (runaway) at pos %d' % pos)
        if pos >= len(buf): raise Desync('ran off end of buffer in attribute loop')
        opcode, pos = read_u8(buf, pos)
        if opcode == 255:
            break
        name = FLAG_NAMES.get(opcode, 'unknown_%d' % opcode)
        if opcode == 24:
            x, pos = read_u16(buf, pos); y, pos = read_u16(buf, pos)
            data['displacement'] = [x,y]
        elif opcode == 21:
            intensity, pos = read_u16(buf, pos); color, pos = read_u16(buf, pos)
            data['light'] = {'intensity':intensity,'color':color}
        elif opcode == 33:
            category, pos = read_u16(buf, pos)
            tradeAs, pos = read_u16(buf, pos)
            showAs, pos = read_u16(buf, pos)
            name_str, pos = read_string(buf, pos)
            restrictVocation, pos = read_u16(buf, pos)
            requiredLevel, pos = read_u16(buf, pos)
            data['market'] = {'category':category,'tradeAs':tradeAs,'showAs':showAs,'name':name_str,'restrictVocation':restrictVocation,'requiredLevel':requiredLevel}
        elif opcode in U16_PAYLOAD_ATTRS:
            val, pos = read_u16(buf, pos)
            data[name] = val
        else:
            # unknown/unlisted opcode: treated as a bare flag (no payload) -- matches
            # otclient's generic 'default' handling for boolean attributes.
            flags.append(name)
    return flags, data, pos

def parse_single_frame_group(buf, pos, extended_sprites=True, max_sprites=50000):
    width, pos = read_u8(buf, pos)
    height, pos = read_u8(buf, pos)
    if width == 0 or height == 0:
        raise Desync('degenerate width/height %d/%d'%(width,height))
    real_size = None
    if width > 1 or height > 1:
        real_size, pos = read_u8(buf, pos)
    layers, pos = read_u8(buf, pos)
    px, pos = read_u8(buf, pos)
    py, pos = read_u8(buf, pos)
    pz, pos = read_u8(buf, pos)
    phases, pos = read_u8(buf, pos)
    if layers==0 or px==0 or py==0 or pz==0 or phases==0:
        raise Desync('degenerate frame group field')
    animator = None
    if phases > 1:
        async_flag, pos = read_u8(buf, pos)
        loop_count, pos = read_s32(buf, pos)
        start_phase, pos = read_s8(buf, pos)
        durations = []
        for _ in range(phases):
            mn, pos = read_u32(buf, pos)
            mx, pos = read_u32(buf, pos)
            durations.append([mn,mx])
        animator = {'async': async_flag==0, 'loopCount': loop_count, 'startPhase': start_phase, 'durations': durations}
    total_sprites = width*height*layers*px*py*pz*phases
    if total_sprites > max_sprites: raise Desync('total_sprites too large %d'%total_sprites)
    if pos + total_sprites*4 > len(buf): raise Desync('sprite id list runs off buffer')
    sprite_ids = []
    for _ in range(total_sprites):
        if extended_sprites:
            sid, pos = read_u32(buf, pos)
        else:
            sid, pos = read_u16(buf, pos)
        sprite_ids.append(sid)
    return {
        'width':width,'height':height,'realSize':real_size,'layers':layers,
        'patternX':px,'patternY':py,'patternZ':pz,'phases':phases,
        'animator':animator,'spriteIds':sprite_ids
    }, pos

def parse_frame_section_auto(buf, pos, extended_sprites=True):
    """Try single-group layout first; if degenerate, retry as multi-group (groupCount + per-group type)."""
    try:
        fg, newpos = parse_single_frame_group(buf, pos, extended_sprites)
        return {'multi': False, 'frameGroup': fg}, newpos
    except Desync:
        p = pos
        group_count, p = read_u8(buf, p)
        if group_count == 0 or group_count > 8:
            raise Desync('bad group_count %d (fallback also failed)' % group_count)
        groups = {}
        for g in range(group_count):
            group_type, p = read_u8(buf, p)
            fg, p = parse_single_frame_group(buf, p, extended_sprites)
            groups[group_type] = fg
        return {'multi': True, 'frameGroups': groups}, p

def parse_thing(buf, pos, extended_sprites=True):
    flags, data, pos = parse_attributes(buf, pos)
    frame_info, pos = parse_frame_section_auto(buf, pos, extended_sprites)
    result = {'flags': flags, 'data': data}
    result.update(frame_info)
    return result, pos
