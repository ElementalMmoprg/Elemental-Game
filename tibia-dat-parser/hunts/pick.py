import numpy as np, json, pickle
cat=np.load('cat.npy',mmap_mode='r'); wk=np.load('wk.npy',mmap_mode='r')
X0,Y0=3780,3830
S=72; STEP=8
CAT={'grass':1,'forest':2,'jungle':3,'dried':4,'sand':5,'snow':6,'swamp':7,'rock':8,'wood':9,'stone':10,'sandstone':11,'water':12,'lava':13,'dirt':14}
THEMES={
 'meadow':({'grass':1},'s',{}),'trail':({'forest':1},'s',{}),'boar':({'dried':2,'grass':.5},'s',{}),
 'bear':({'forest':1,'grass':.4},'s',{}),'wolf':({'snow':1},'s',{}),'blaze':({'lava':4,'rock':1},'u',{}),
 'bog':({'swamp':1},'a',{}),'brotherhood':({'dirt':1,'wood':.8,'grass':.2},'s',{}),
 'captain':({'sand':1},'s',{'water':.3}),'cave':({'rock':1},'u',{}),'coldstone':({'snow':1},'a',{}),
 'dwarf':({'rock':1,'wood':1.5},'u',{}),'anglerfish_bat':({'rock':1},'u',{'water':1.5}),
 'battlehog_chewacabra':({'jungle':1},'s',{}),'coal_contraption_arachnowalker':({'stone':1,'dirt':.5,'rock':.3},'s',{}),
 'trunk':({'forest':1},'s',{}),'dreadknought':({'wood':1,'sand':.2},'a',{'water':.4}),
 'chainwraith':({'stone':1},'u',{}),'gazer':({'rock':1,'dirt':.5},'u',{}),
 'blademaster_djinn_blizzard_beast':({'snow':1,'stone':1.5,'wood':.5},'a',{}),
 'contagious_sporewalker_cragglehide':({'swamp':1,'forest':.3},'a',{}),'astor':({'stone':1,'sandstone':.5},'a',{}),
 'crow_matriarch_crowman':({'dried':1,'dirt':.5},'s',{}),'direhorn_drake_dusk_crawler':({'rock':1},'s',{}),
 'duskling_dunewalker_jackal':({'sand':1,'sandstone':.5},'s',{}),'draconic':({'lava':4,'sandstone':.5,'rock':.3},'a',{}),
}
def integ(a): return np.pad(a.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
def boxsum(I,ys,xs): return I[ys+S,xs+S]-I[ys,xs+S]-I[ys+S,xs]+I[ys,xs]
H,W=cat.shape[1:]
ys=np.arange(0,H-S,STEP); xs=np.arange(0,W-S,STEP); YY,XX=np.meshgrid(ys,xs,indexing='ij')
cands={t:[] for t in THEMES}
for z in range(3,13):
    c=np.asarray(cat[z]); w=(np.asarray(wk[z])==1)
    if w.sum()<2000: continue
    Iw=integ(w); walkc=boxsum(Iw,YY,XX)
    Ik={k:integ(w&(c==v)) for k,v in CAT.items()}
    Iwat=integ(c==12)
    # estrutura: tile andável vizinho de bloqueio (árvore/parede/pedra) -> área com obstáculos, não campo vazio
    wb=np.zeros_like(w); wb[1:-1,1:-1]=w[1:-1,1:-1]&~(w[:-2,1:-1]&w[2:,1:-1]&w[1:-1,:-2]&w[1:-1,2:])
    Iedge=integ(wb)
    sk={k:boxsum(I,YY,XX) for k,I in Ik.items()}
    wat=boxsum(Iwat,YY,XX)/(S*S)
    town=(sk['wood']+sk['stone'])/np.maximum(walkc,1)
    edge=boxsum(Iedge,YY,XX)/np.maximum(walkc,1)
    wfrac=walkc/(S*S)
    for t,(wts,fl,extra) in THEMES.items():
        if fl=='s' and z>7: continue
        if fl=='u' and z<8: continue
        sc=sum(wt*sk[k] for k,wt in wts.items())/np.maximum(walkc,1)
        if 'water' in extra: sc=sc+extra['water']*np.minimum(wat,0.5)*2
        if not any(k in wts for k in ('wood','stone')): sc=sc-0.6*town
        sc=sc*np.minimum(1,walkc/2000)
        sc=sc*(0.55+np.minimum(edge,0.45))          # premia obstáculos
        sc=sc-np.maximum(0,wfrac-0.62)*1.5          # campo aberto demais = vazio
        sc[walkc<1300]=-9
        # fora de Ravencrest
        gx=XX+X0; gy=YY+Y0
        sc[(gx+S>4990)&(gx<5230)&(gy+S>4990)&(gy<5250)]=-9
        idx=np.argsort(sc.ravel())[::-1][:400]
        for i in idx:
            if sc.ravel()[i]<=0: break
            cands[t].append((float(sc.ravel()[i]),int(XX.ravel()[i]+X0),int(YY.ravel()[i]+Y0),z,int(walkc.ravel()[i])))
# escolha gulosa: hunts com menos opções primeiro, sem sobrepor
order=sorted(THEMES,key=lambda t:len([c for c in cands[t] if c[0]>0.3]))
chosen={}
def overl(a,b): return abs(a[1]-b[1])<S+10 and abs(a[2]-b[2])<S+10
for t in order:
    for c in sorted(cands[t],reverse=True):
        if any(overl(c,o) for o in chosen.values()): continue
        chosen[t]=c; break
for t in THEMES: print(t, chosen.get(t))
json.dump(chosen,open('chosen.json','w'))
# top-3 distintos por tema (pra prévia)
top={}
for t in THEMES:
    L=[]
    for c in sorted(cands[t],reverse=True):
        if any(overl(c,o) for o in L): continue
        L.append(c)
        if len(L)==3: break
    top[t]=L
json.dump(top,open('top3.json','w'))
pickle.dump(cands,open('cands.pkl','wb'))
