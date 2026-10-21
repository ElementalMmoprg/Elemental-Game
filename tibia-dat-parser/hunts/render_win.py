import sys, json, pickle
sys.path.insert(0,'/tmp/claude-0/s/map')
from PIL import Image
from dat import parse_dat
from otb import items_otb
otb=items_otb('/mnt/user-data/uploads/rd_project/Server/data/items/items.otb')
dat=parse_dat('/mnt/user-data/uploads/rd_project/otcv_8/data/things/1098/Tibia.dat')
order=json.load(open('/tmp/claude-0/s/hunt/master_order.json')); IDX={s:i for i,s in enumerate(order)}
A=[Image.open(f'/mnt/user-data/uploads/rd_project/pacote_elemental/mapa/cacas/master/atlas_{i}.png').convert('RGBA') for i in range(7)]
cache={}
def spr(s):
    if s not in cache:
        i=IDX.get(s)
        if i is None: cache[s]=None
        else:
            p=A[i>>12]; j=i&4095; cache[s]=p.crop(((j%64)*32,(j//64)*32,(j%64)*32+32,(j//64)*32+32))
    return cache[s]
def layer(a):
    if 'ground' in a: return 0
    o=a.get('order')
    return 1 if o==1 else (3 if o==3 else 2)
def tile_sprites(X,Y,Z,ids):
    th=[]
    for i,sid in enumerate(ids):
        cid=otb.get(sid); a=dat.get(cid) if cid else None
        if a: th.append((layer(a),i,a))
    th.sort(key=lambda t:(t[0],t[1])); out=[]; elev=0
    for L,_,a in th:
        px,py,pz=a['px'],a['py'],a['pz']; xp=X%px; yp=Y%py; zp=Z%pz; dx,dy=a.get('disp',(0,0))
        for hh in range(a['h']):
            for ww in range(a['w']):
                idx=((((zp*py+yp)*px+xp)*a['L']+0)*a['h']+hh)*a['w']+ww
                s=a['spr'][idx] if idx<len(a['spr']) else 0
                if s: out.append((s,-ww*32-dx-elev,-hh*32-dy-elev))
        if 'elev' in a: elev=min(24,elev+a['elev'])
    return out
def render(tiles,x0,y0,w,h,pz,scale=4,walk=None):
    img=Image.new('RGBA',(w*32,h*32),(0,0,0,255))
    zs=list(range(7 if pz<=7 else min(15,pz+1),pz,-1))+[pz]
    for z in zs:
        off=z-pz
        for y in range(y0-off-2,y0-off+h+2):
            for x in range(x0-off-2,x0-off+w+2):
                ids=tiles.get((x,y,z))
                if not ids: continue
                bx=(x+off-x0)*32; by=(y+off-y0)*32
                for s,ox,oy in tile_sprites(x,y,z,ids):
                    im=spr(s)
                    if im is None: continue
                    X=bx+ox; Y=by+oy
                    if -32<X<w*32 and -32<Y<h*32: img.paste(im,(X,Y),im)
    if walk is not None:
        from PIL import ImageDraw
        ov=Image.new('RGBA',img.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
        for (X,Y,Z),c in walk.items():
            if Z==pz: d.rectangle([(X-x0)*32,(Y-y0)*32,(X-x0)*32+31,(Y-y0)*32+31],fill=c)
        img.alpha_composite(ov)
    if scale!=32: img=img.resize((w*scale,h*scale),Image.LANCZOS)
    return img.convert('RGB')
if __name__=='__main__':
    win,boxes,wt=pickle.load(open('/tmp/claude-0/s/hunt/wtiles.pkl','rb'))
    meta=json.load(open('/tmp/claude-0/s/hunt/windows_meta.json'))
    from PIL import ImageDraw
    names=sys.argv[1].split(',') if len(sys.argv)>1 else list(win)
    for n in names:
        a,b,c,d=boxes[n]; z=meta[n]['c'][2]
        im=render(wt[n],a,b,c-a,d-b,z,4)
        dr=ImageDraw.Draw(im); dr.text((4,4),f"{n} z{z} "+' '.join(t for t,_ in meta[n]['themes'])[:70],fill=(255,255,0))
        im.save(f'/tmp/claude-0/s/hunt/prev/{n}.png')
        print(n,flush=True)
