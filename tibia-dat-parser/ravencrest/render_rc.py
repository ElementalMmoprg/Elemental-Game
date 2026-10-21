import pickle, sys
from PIL import Image, ImageDraw
floors,walk,changes,sprites,W,H,X0,Y0=pickle.load(open('/tmp/claude-0/s/map/rc_built.pkl','rb'))
A=[Image.open(f'/mnt/user-data/uploads/rd_project/pacote_elemental/mapa/ravencrest/atlas_{i}.png').convert('RGBA') for i in (0,1)]
cache={}
def spr(i):
    if i not in cache:
        p=A[i>>12]; j=i&4095; cache[i]=p.crop(((j%64)*32,(j//64)*32,(j%64)*32+32,(j//64)*32+32))
    return cache[i]
def render(cx,cy,pz,rw=40,rh=26,out='r.png',walkov=False):
    img=Image.new('RGBA',(rw*32,rh*32),(0,0,0,255))
    x0=cx-rw//2; y0=cy-rh//2
    zs=[z for z in range(7 if pz<=7 else pz, pz-1, -1)]
    # floors acima: só se não coberto
    for zu in range(pz-1,-1,-1):
        k=(cy+(pz-zu)-Y0)*W+(cx+(pz-zu)-X0)
        if zu in floors and k in floors[zu]: break
        zs.append(zu)
    for z in zs:
        off=(z-pz)
        F=floors.get(z,{})
        for y in range(y0-off-3, y0-off+rh+3):
            for x in range(x0-off-3, x0-off+rw+3):
                t=F.get((y-Y0)*W+(x-X0))
                if not t: continue
                bx=(x+off-x0)*32; by=(y+off-y0)*32
                for arr in t:
                    for q in range(0,len(arr),3):
                        img.alpha_composite(spr(arr[q]),(0,0) ,) if False else None
                        dx=bx+arr[q+1]; dy=by+arr[q+2]
                        if -32<dx<rw*32 and -32<dy<rh*32:
                            s=spr(arr[q]); 
                            img.paste(s,(dx,dy),s)
    if walkov:
        d=ImageDraw.Draw(img,'RGBA')
        for y in range(y0,y0+rh):
            for x in range(x0,x0+rw):
                w=walk.get((x,y,pz))
                if w is None: continue
                c=(0,255,0,50) if w else (255,0,0,60)
                if (x,y,pz) in changes: c=(255,255,0,120)
                d.rectangle([(x-x0)*32,(y-y0)*32,(x-x0)*32+31,(y-y0)*32+31],fill=c)
    img.save(out); return img
if __name__=='__main__':
    render(5132,5092,6,48,30,'/tmp/claude-0/s/map/rc_temple.png')
    render(5132,5092,6,48,30,'/tmp/claude-0/s/map/rc_temple_walk.png',True)
