import sys, pickle, json, collections, os
sys.path.insert(0,'/tmp/claude-0/s/map')
from dat import parse_dat
from otb import items_otb
from itemsxml import load as load_xml
otb=items_otb('/mnt/user-data/uploads/rd_project/Server/data/items/items.otb')
dat=parse_dat('/mnt/user-data/uploads/rd_project/otcv_8/data/things/1098/Tibia.dat')
names,fc=load_xml()
tiles,tele=pickle.load(open('/tmp/claude-0/s/map/rc_tiles.pkl','rb'))
X0,Y0,X1,Y1=5015,5010,5205,5235
W,H=X1-X0+1,Y1-Y0+1
UP_USE=set(i for i,n in names.items() if n.lower() in ('ladder','rope'))  # escada de mão / corda: sobe (x, y+1, z-1)
def thing(sid):
    cid=otb.get(sid)
    return dat.get(cid) if cid else None
def layer(a):
    if 'ground' in a: return 0
    o=a.get('order')
    if o==1: return 1
    if o==3: return 3
    return 2
sprite_index={}; sprites=[]
import json as _j
try:
    for _job in _j.load(open('/mnt/user-data/outputs/rdmapa/jobs_ravencrest_atlas.json')):
        for _t in _job['tiles']:
            sprite_index[_t[0]]=len(sprites); sprites.append(_t[0])
except FileNotFoundError: pass
def sidx(s):
    if s not in sprite_index: sprite_index[s]=len(sprites); sprites.append(s)
    return sprite_index[s]
floors=collections.defaultdict(dict)  # z -> idx -> (g,o,t,walk)
fcflags={}  # (x,y,z)->set of flags
for (x,y,z),ids in tiles.items():
    fl=set()
    for sid in ids:
        if sid in fc: fl.add(fc[sid])
        if sid in UP_USE: fl.add('ladder')
    if fl: fcflags[(x,y,z)]=fl
changes={}
for (x,y,z),fl in fcflags.items():
    if 'down' in fl:
        dx,dy,dz=x,y,z+1
        f2=fcflags.get((dx,dy,dz),set())
        if 'north' in f2: dy+=1
        if 'south' in f2: dy-=1
        if 'southalt' in f2: dy-=2
        if 'east' in f2: dx-=1
        if 'eastalt' in f2: dx-=2
        if 'west' in f2: dx+=1
        changes[(x,y,z)]=(dx,dy,dz)
    elif 'ladder' in fl:
        changes[(x,y,z)]=(x,y+1,z-1)
    elif fl & {'north','south','east','west','southalt','eastalt'}:
        dx,dy,dz=x,y,z-1
        if 'north' in fl: dy-=1
        if 'south' in fl: dy+=1
        if 'southalt' in fl: dy+=2
        if 'east' in fl: dx+=1
        if 'eastalt' in fl: dx+=2
        if 'west' in fl: dx-=1
        changes[(x,y,z)]=(dx,dy,dz)
walkgrid={}
for (x,y,z),ids in tiles.items():
    things=[]
    for i,sid in enumerate(ids):
        a=thing(sid)
        if a: things.append((layer(a),i,a))
    things.sort(key=lambda t:(t[0],t[1]))
    hasGround=any('ground' in a for _,_,a in things)
    blocked=any('block' in a for _,_,a in things)
    walk = hasGround and not blocked
    if (x,y,z) in changes: walk = True
    g=[];o=[];t=[]
    elev=0
    for L,_,a in things:
        W_,H_,Lr,px,py,pz=a['w'],a['h'],a['L'],a['px'],a['py'],a['pz']
        xp=x%px; yp=y%py; zp=z%pz
        ddx,ddy=a.get('disp',(0,0))
        out = g if L<=1 else (t if L==3 else o)
        for hh in range(H_):
            for ww in range(W_):
                idx=((((zp*py+yp)*px+xp)*Lr+0)*H_+hh)*W_+ww
                s=a['spr'][idx] if idx<len(a['spr']) else 0
                if not s: continue
                out += [sidx(s), -ww*32-ddx-elev, -hh*32-ddy-elev]
        if 'elev' in a: elev=min(24, elev+a['elev'])
    if not (g or o or t) and not walk: continue
    floors[z][(y-Y0)*W+(x-X0)]=(g,o,t)
    walkgrid[(x,y,z)]=walk
json.dump({'sprites':sprites},open('/tmp/claude-0/s/map/rc_sprites.json','w'))
pickle.dump((floors,walkgrid,changes,sprites,W,H,X0,Y0),open('/tmp/claude-0/s/map/rc_built.pkl','wb'))
print('sprites',len(sprites),'tiles',sum(len(v) for v in floors.values()),'changes',len(changes))
print({z:len(v) for z,v in sorted(floors.items())})
print('temple walk', walkgrid.get((5132,5092,6)), [ (k,v) for k,v in list(changes.items())[:8]])
