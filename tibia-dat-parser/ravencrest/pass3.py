import struct, sys, time, pickle, collections
sys.path.insert(0,'/tmp/claude-0/s/map')
from otb import walk
X0,Y0,X1,Y1=5015,5010,5205,5235
d=open('/mnt/user-data/uploads/rd_project/Server/data/world/1098.otbm','rb').read()
tiles={}; tele={}
stack=[]; area=None; cur=None; curpos=None
def item_attrs(data,p):
    res={}
    try:
        while p<len(data):
            at=data[p]; p+=1
            if at in (4,5,10,22): p+=2
            elif at in (6,7,19): ln=struct.unpack_from('<H',data,p)[0]; p+=2+ln
            elif at==8: res['tele']=struct.unpack_from('<HHB',data,p); p+=5
            elif at in (14,15,17): p+=1
            elif at in (16,18,20,21): p+=4
            else: break
    except Exception: pass
    return res
t0=time.time()
for ev in walk(d):
    if ev[0]=='open':
        t,data=ev[1],ev[2]; stack.append(t)
        if t==4: area=struct.unpack_from('<HHB',data,0)
        elif t in (5,14):
            x=area[0]+data[0]; y=area[1]+data[1]; z=area[2]; cur=None
            if X0<=x<=X1 and Y0<=y<=Y1:
                p=2+(4 if t==14 else 0); ids=[]
                while p<len(data):
                    at=data[p]; p+=1
                    if at==3: p+=4
                    elif at==9: ids.append(struct.unpack_from('<H',data,p)[0]); p+=2
                    else: break
                cur=ids; curpos=(x,y,z); tiles[curpos]=ids
        elif t==6 and cur is not None and len(stack)>=2 and stack[-2] in (5,14):
            cur.append(struct.unpack_from('<H',data,0)[0])
            a=item_attrs(data,2)
            if 'tele' in a: tele[curpos]=a['tele']
    else:
        t=stack.pop()
        if t in (5,14): cur=None
print('s',time.time()-t0, len(tiles), collections.Counter(k[2] for k in tiles), 'tele',len(tele), list(tele.items())[:10])
pickle.dump((tiles,tele),open('/tmp/claude-0/s/map/rc_tiles.pkl','wb'))
