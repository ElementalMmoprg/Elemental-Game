import numpy as np, json
cat=np.load('cat.npy',mmap_mode='r'); wk=np.load('wk.npy',mmap_mode='r')
X0,Y0=3780,3830; S=56; STEP=8
CAT={'grass':1,'forest':2,'jungle':3,'dried':4,'sand':5,'snow':6,'swamp':7,'rock':8,'wood':9,'stone':10,'sandstone':11,'water':12,'lava':13,'dirt':14}
# tema: (pesos de chão, zs permitidos, extra água/lava (bloqueado próximo))
TH={
 'fogo':  ({'lava':3,'rock':.6},range(8,15),{'lava_any':2}),
 'agua':  ({'sand':.6,'rock':.6,'stone':.4},range(3,15),{'water_any':2.5}),
 'terra': ({'rock':1,'dirt':1},range(8,15),{}),
 'ar':    ({'rock':1,'grass':.3,'snow':.6},range(0,6),{}),
 'luz':   ({'sandstone':1.5,'stone':.6},range(3,15),{}),
 'trevas':({'stone':1,'swamp':.6},range(8,15),{}),
 'central':({'stone':1,'wood':.3},range(3,8),{}),
}
used=json.load(open('sel.json')); win=json.load(open('windows.json'))
usedbox=[(win[v['win']][0],win[v['win']][1]) for v in used.values()]
def integ(a): return np.pad(a.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
def box(I,ys,xs): return I[ys+S,xs+S]-I[ys,xs+S]-I[ys+S,xs]+I[ys,xs]
H,W=cat.shape[1:]; ys=np.arange(0,H-S,STEP); xs=np.arange(0,W-S,STEP); YY,XX=np.meshgrid(ys,xs,indexing='ij')
cands={t:[] for t in TH}
for z in range(0,15):
    c=np.asarray(cat[z]); w=(np.asarray(wk[z])==1)
    if w.sum()<1500: continue
    Iw=integ(w); walkc=box(Iw,YY,XX)
    sk={k:box(integ(w&(c==v)),YY,XX) for k,v in CAT.items()}
    lava=box(integ(c==13),YY,XX)/(S*S); wat=box(integ(c==12),YY,XX)/(S*S)
    wb=np.zeros_like(w); wb[1:-1,1:-1]=w[1:-1,1:-1]&~(w[:-2,1:-1]&w[2:,1:-1]&w[1:-1,:-2]&w[1:-1,2:])
    edge=box(integ(wb),YY,XX)/np.maximum(walkc,1); wfrac=walkc/(S*S)
    for t,(wts,zs,ex) in TH.items():
        if z not in zs: continue
        sc=sum(wt*sk[k] for k,wt in wts.items())/np.maximum(walkc,1)
        if 'lava_any' in ex: sc=sc+ex['lava_any']*np.minimum(lava,.25)*4
        if 'water_any' in ex: sc=sc+ex['water_any']*np.minimum(wat,.3)*3
        sc=sc*(0.55+np.minimum(edge,0.45)); sc=sc-np.maximum(0,wfrac-0.6)*1.5
        sc[walkc<900]=-9
        gx=XX+X0; gy=YY+Y0
        sc[(gx+S>4990)&(gx<5230)&(gy+S>4990)&(gy<5250)]=-9
        for (ux,uy) in usedbox: sc[(gx+S>ux)&(gx<ux+96)&(gy+S>uy)&(gy<uy+96)]=-9
        idx=np.argsort(sc.ravel())[::-1][:300]
        for i in idx:
            if sc.ravel()[i]<=0.05: break
            cands[t].append((round(float(sc.ravel()[i]),3),int(XX.ravel()[i]+X0),int(YY.ravel()[i]+Y0),z,int(walkc.ravel()[i])))
def ov(a,b): return abs(a[1]-b[1])<S and abs(a[2]-b[2])<S
top={}
for t in TH:
    L=[]
    for c in sorted(cands[t],reverse=True):
        if any(ov(c,o) for o in L): continue
        L.append(c)
        if len(L)==4: break
    top[t]=L; print(t,L)
json.dump(top,open('tower_top.json','w'))
