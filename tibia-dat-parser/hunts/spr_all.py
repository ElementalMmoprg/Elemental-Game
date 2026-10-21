import sys, json, pickle
sys.path.insert(0,'/tmp/claude-0/s/map')
from dat import parse_dat
from otb import items_otb
otb=items_otb('/mnt/user-data/uploads/rd_project/Server/data/items/items.otb')
dat=parse_dat('/mnt/user-data/uploads/rd_project/otcv_8/data/things/1098/Tibia.dat')
win,boxes,wt=pickle.load(open('wtiles.pkl','rb'))
S=set(); cache={}
for k,tiles in wt.items():
    for (X,Y,Z),ids in tiles.items():
        for sid in ids:
            key=(sid,X%4,Y%4,Z%4)
            cid=otb.get(sid); a=dat.get(cid) if cid else None
            if not a: continue
            px,py,pz=a['px'],a['py'],a['pz']; xp=X%px; yp=Y%py; zp=Z%pz
            for hh in range(a['h']):
                for ww in range(a['w']):
                    idx=((((zp*py+yp)*px+xp)*a['L']+0)*a['h']+hh)*a['w']+ww
                    s=a['spr'][idx] if idx<len(a['spr']) else 0
                    if s: S.add(s)
S=sorted(S); print(len(S))
json.dump(S,open('master_order.json','w'))
PER=4096; jobs=[]
for p in range(0,len(S),PER):
    ch=S[p:p+PER]
    jobs.append({'out':f'master/atlas_{p//PER}.png','w':2048,'h':((len(ch)+63)//64)*32,'tiles':[[s,(i%64)*32,(i//64)*32] for i,s in enumerate(ch)]})
json.dump(jobs,open('/mnt/user-data/outputs/rdmapa/jobs_master.json','w'))
print(len(jobs))
