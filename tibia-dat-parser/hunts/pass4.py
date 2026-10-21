# 1 passada no 1098.otbm: por andar, cor de minimapa + flag de andável + escadas
import struct, sys, time, numpy as np, pickle
sys.path.insert(0,'/tmp/claude-0/s/map')
from otb import walk, items_otb
from dat import parse_dat
from itemsxml import load as load_xml
otb=items_otb('/mnt/user-data/uploads/rd_project/Server/data/items/items.otb')
dat=parse_dat('/mnt/user-data/uploads/rd_project/otcv_8/data/things/1098/Tibia.dat')
names,fc=load_xml()
mm=np.full(65536,-1,np.int16); isg=np.zeros(65536,bool); isb=np.zeros(65536,bool)
for sid,cid in otb.items():
    a=dat.get(cid) if cid else None
    if not a: continue
    if 'minimap' in a: mm[sid]=a['minimap']
    if 'ground' in a: isg[sid]=True
    if 'block' in a: isb[sid]=True
isfc=np.zeros(65536,bool)
for s in fc: isfc[s]=True
for i,n in names.items():
    if n.lower() in ('ladder','rope'): isfc[i]=True
X0,Y0,X1,Y1=3780,3830,7020,6120
W,H=X1-X0,Y1-Y0
col=np.full((16,H,W),255,np.uint8); wk=np.zeros((16,H,W),np.uint8)  # 1 andável, 2 escada/buraco
gid=np.zeros((16,H,W),np.uint16)
d=open('/mnt/user-data/uploads/rd_project/Server/data/world/1098.otbm','rb').read()
stack=[]; area=None; cur=None; curpos=None
def flush():
    if curpos is None: return
    x,y,z=curpos
    if not (X0<=x<X1 and Y0<=y<Y1): return
    xx=x-X0; yy=y-Y0; c=-1; g=False; b=False; f=False; g0=0
    for i in cur:
        v=mm[i]
        if v>=0: c=v
        if isg[i]: g=True; g0=i
        if isb[i]: b=True
        if isfc[i]: f=True
    if c>=0: col[z,yy,xx]=c
    gid[z,yy,xx]=g0
    if f: wk[z,yy,xx]=2
    elif g and not b: wk[z,yy,xx]=1
t0=time.time()
for ev in walk(d):
    if ev[0]=='open':
        t,data=ev[1],ev[2]; stack.append(t)
        if t==4: area=struct.unpack_from('<HHB',data,0)
        elif t in (5,14):
            flush()
            curpos=(area[0]+data[0],area[1]+data[1],area[2]); p=2+(4 if t==14 else 0); cur=[]
            while p<len(data):
                at=data[p]; p+=1
                if at==3: p+=4
                elif at==9: cur.append(struct.unpack_from('<H',data,p)[0]); p+=2
                else: break
        elif t==6 and len(stack)>=2 and stack[-2] in (5,14):
            cur.append(struct.unpack_from('<H',data,0)[0])
    else:
        stack.pop()
flush()
print('s',time.time()-t0)
np.save('/tmp/claude-0/s/hunt/col.npy',col); np.save('/tmp/claude-0/s/hunt/wk.npy',wk); np.save('/tmp/claude-0/s/hunt/gid.npy',gid)
print('tiles per z',[int((wk[z]>0).sum()) for z in range(16)])
