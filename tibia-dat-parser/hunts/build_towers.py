# Gera os mapas REAIS das caçadas a partir de wtiles.pkl (pass5.py) + escolha (sel.json)
#  - servidor:  out/server/<id>.json   (walk por andar, escadas, 6 lures, entrada)
#  - cliente:   out/assets/<id>/meta.json + floor_<z>.json  (tiles g/o/t com índice no atlas)
#  - atlas:     out/jobs_hunts_atlas.json (sprites -> páginas 2048x2048, 64 por linha)
import sys, json, pickle, base64, collections, itertools, os, math
sys.path.insert(0,'/tmp/claude-0/s/map')
from dat import parse_dat
from otb import items_otb
from itemsxml import load as load_xml
otb=items_otb('/mnt/user-data/uploads/rd_project/Server/data/items/items.otb')
dat=parse_dat('/mnt/user-data/uploads/rd_project/otcv_8/data/things/1098/Tibia.dat')
names,fc=load_xml()
UP_USE=set(i for i,n in names.items() if n.lower() in ('ladder','rope'))
W1,B1,T1=pickle.load(open('/tmp/claude-0/s/hunt/wtiles.pkl','rb'))
W2,B2,T2=pickle.load(open('/tmp/claude-0/s/hunt/tower_wtiles.pkl','rb'))
sel=json.load(open(sys.argv[1]))
OUT='/tmp/claude-0/s/hunt/tout/'
os.makedirs(OUT+'server',exist_ok=True); os.makedirs(OUT+'assets',exist_ok=True)
N8=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
def thing(sid):
    cid=otb.get(sid); return dat.get(cid) if cid else None
def layer(a):
    if 'ground' in a: return 0
    o=a.get('order')
    if o==1: return 1
    if o==3: return 3
    return 2
# atlas POR caçada (montado aqui a partir do atlas mestre extraído no PC)
from PIL import Image
MORD=json.load(open('/tmp/claude-0/s/hunt/master_order.json')); MIDX={s:i for i,s in enumerate(MORD)}
MPAGES=[Image.open(f'/mnt/user-data/uploads/rd_project/pacote_elemental/mapa/cacas/master/atlas_{i}.png').convert('RGBA') for i in range(7)]
def mcrop(s):
    i=MIDX[s]; p=MPAGES[i>>12]; j=i&4095; return p.crop(((j%64)*32,(j//64)*32,(j%64)*32+32,(j//64)*32+32))
sprite_index={}; sprites=[]
def sidx(s):
    if s not in sprite_index: sprite_index[s]=len(sprites); sprites.append(s)
    return sprite_index[s]
report={}
for hid,cfg in sel.items():
    sprite_index.clear(); sprites.clear()
    wname=cfg['win']; zmain=cfg['z']
    src=(W2,B2,T2) if wname in W2 else (W1,B1,T1)
    tiles=src[2][wname]
    if 'rect' in cfg: x,y,SW,SH=cfg['rect']
    else: x,y,SW=src[0][wname]; SH=SW
    bx0,by0,bx1,by1=x-12,y-12,x+SW+12,y+SH+12
    W,H=bx1-bx0,by1-by0
    S=SW
    inwin=lambda X,Y: x<=X<x+SW and y<=Y<y+SH
    tiles={k:v for k,v in tiles.items() if bx0<=k[0]<bx1 and by0<=k[1]<by1}
    # escadas
    fcf={}
    for k,ids in tiles.items():
        fl=set()
        for s in ids:
            if s in fc: fl.add(fc[s])
            if s in UP_USE: fl.add('ladder')
        if fl: fcf[k]=fl
    changes={}
    for (X,Y,Z),fl in fcf.items():
        if 'down' in fl:
            dx,dy,dz=X,Y,Z+1; f2=fcf.get((dx,dy,dz),set())
            if 'north' in f2: dy+=1
            if 'south' in f2: dy-=1
            if 'southalt' in f2: dy-=2
            if 'east' in f2: dx-=1
            if 'eastalt' in f2: dx-=2
            if 'west' in f2: dx+=1
            changes[(X,Y,Z)]=(dx,dy,dz)
        elif 'ladder' in fl: changes[(X,Y,Z)]=(X,Y+1,Z-1)
        elif fl & {'north','south','east','west','southalt','eastalt'}:
            dx,dy,dz=X,Y,Z-1
            if 'north' in fl: dy-=1
            if 'south' in fl: dy+=1
            if 'southalt' in fl: dy+=2
            if 'east' in fl: dx+=1
            if 'eastalt' in fl: dx+=2
            if 'west' in fl: dx-=1
            changes[(X,Y,Z)]=(dx,dy,dz)
    # andável + desenho
    walk={}; floors=collections.defaultdict(dict)
    for (X,Y,Z),ids in tiles.items():
        th=[]
        for i,s in enumerate(ids):
            a=thing(s)
            if a: th.append((layer(a),i,a))
        th.sort(key=lambda t:(t[0],t[1]))
        hasG=any('ground' in a for _,_,a in th); blk=any('block' in a for _,_,a in th)
        w=hasG and not blk
        if (X,Y,Z) in changes: w=True
        if w and inwin(X,Y): walk[(X,Y,Z)]=True
        g=[];o=[];t=[]; elev=0
        for L,_,a in th:
            W_,H_,Lr,px,py,pz=a['w'],a['h'],a['L'],a['px'],a['py'],a['pz']
            xp=X%px; yp=Y%py; zp=Z%pz
            ddx,ddy=a.get('disp',(0,0))
            out=g if L<=1 else (t if L==3 else o)
            for hh in range(H_):
                for ww in range(W_):
                    idx=((((zp*py+yp)*px+xp)*Lr+0)*H_+hh)*W_+ww
                    s=a['spr'][idx] if idx<len(a['spr']) else 0
                    if not s: continue
                    out+=[s,-ww*32-ddx-elev,-hh*32-ddy-elev]
            if 'elev' in a: elev=min(24,elev+a['elev'])
        if g or o or t: floors[Z][(Y-by0)*W+(X-bx0)]=(g,o,t)
    # grafo do jogador (igual ao motor): pisar em escada = ir pro destino
    def succ(u):
        X,Y,Z=u
        for dx,dy in N8:
            v=(X+dx,Y+dy,Z)
            if not walk.get(v): continue
            if dx and dy and not ((X+dx,Y,Z) in walk and (X+dx,Y,Z) not in changes and (X,Y+dy,Z) in walk and (X,Y+dy,Z) not in changes): continue
            if v in changes:
                d=changes[v]
                if d in walk or d in changes: yield d
            else: yield v
    # semente: tile mais aberto perto do centro no andar principal
    def openness(k):
        X,Y,Z=k; return sum(1 for a in range(-3,4) for b in range(-3,4) if (X+a,Y+b,Z) in walk and (X+a,Y+b,Z) not in changes)
    cx,cy=(cfg['seed'][0],cfg['seed'][1]) if 'seed' in cfg else (x+SW//2,y+SH//2)
    seeds=sorted([k for k in walk if k[2]==zmain and k not in changes], key=lambda k:(-(openness(k)>=30), abs(k[0]-cx)+abs(k[1]-cy)))
    best=None
    for sd in seeds[:40]:
        R={sd}; st=[sd]
        while st:
            u=st.pop()
            for v in succ(u):
                if v not in R: R.add(v); st.append(v)
        pred=collections.defaultdict(list)
        for u in R:
            for v in succ(u): pred[v].append(u)
        B={sd}; st=[sd]
        while st:
            v=st.pop()
            for u in pred[v]:
                if u not in B: B.add(u); st.append(u)
        K=R&B
        if best is None or len(K)>len(best[1]): best=(sd,K)
        if len(K)>800: break
    sd,K=best
    used_changes={k:v for k,v in changes.items() if v in K and any(((k[0]+dx,k[1]+dy,k[2]) in K) for dx,dy in N8)}
    fwalk={k for k in K if k not in changes}|set(used_changes)
    zs=sorted(set(k[2] for k in fwalk))
    # lures: espaços abertos, bem espalhados
    def bfs(src):
        D={src:0}; q=collections.deque([src])
        while q:
            u=q.popleft()
            for v in succ(u):
                if v not in D: D[v]=D[u]+1; q.append(v)
        return D
    # lures: só em espaços abertos de verdade (não dentro de casa/sótão) e só
    # nos andares "grandes" da área (>= 35% do aberto do andar principal)
    opn={k:openness(k) for k in K if k not in changes}
    perz=collections.Counter(k[2] for k,v in opn.items() if v>=36)
    okz={z for z,n in perz.items() if n>=0.35*max(1,perz.get(zmain,0))} or {zmain}
    cand=[k for k,v in opn.items() if v>=40 and k[2] in okz]
    if len(cand)<40: cand=[k for k,v in opn.items() if v>=33 and k[2] in okz]
    if len(cand)<20: cand=[k for k,v in opn.items() if v>=24]
    first=min(cand,key=lambda k:(k[2]!=zmain, abs(k[0]-cx)+abs(k[1]-cy)))
    # 21/10/2026: pontos de spawn/lure espalhados pela área inteira (antes eram
    # só 6 e sobrava muito chão sem monstro). Amostragem do ponto mais longe
    # até ficarem a no máximo ~SPACING passos uns dos outros.
    SPACING=cfg.get('spacing',12); MAXP=16; MINP=8
    lures=[first]; Dl=[bfs(first)]
    while len(lures)<MAXP:
        nxt=max(cand,key=lambda k:min(D.get(k,0) for D in Dl))
        far=min(D.get(nxt,0) for D in Dl)
        if len(lures)>=MINP and far<SPACING: break
        lures.append(nxt); Dl.append(bfs(nxt))
    if 'lures' in cfg:
        lures=[tuple(l) for l in cfg['lures']]; Dl=[bfs(l) for l in lures]
    n=len(lures)
    M=[[Dl[i].get(lures[j],10**6) for j in range(n)] for i in range(n)]
    # circuito: vizinho mais próximo + 2-opt (volta curta passando por todos)
    order=[0]; left=set(range(1,n))
    while left:
        c=order[-1]; nx=min(left,key=lambda j:M[c][j]); order.append(nx); left.remove(nx)
    def tour_len(o): return sum(M[o[i]][o[(i+1)%n]] for i in range(n))
    improved=True
    while improved:
        improved=False
        for i in range(1,n-1):
            for j in range(i+1,n):
                o2=order[:i]+order[i:j+1][::-1]+order[j+1:]
                if tour_len(o2)<tour_len(order): order=o2; improved=True
    best_ord=(tour_len(order),order)
    lures=[lures[i] for i in order]
    # entrada: ~5 tiles do 1º lure, no mesmo andar
    D0=bfs(lures[0])
    ent=min([k for k in D0 if k[2]==lures[0][2] and k not in changes], key=lambda k:(abs(D0[k]-5), -openness(k)))
    if 'entrance' in cfg: ent=tuple(cfg['entrance'])
    De=bfs(ent)
    if 'exit' in cfg: ext=tuple(cfg['exit'])
    else:
        ext=max([k for k in De if k not in changes and openness(k)>=20], key=lambda k:De[k])
    assert ent in K and ext in K, ('ent/exit fora',ent,ext)
    safe=set()
    if 'safeY' in cfg: safe={k for k in fwalk if k[1]>=cfg['safeY'] and k not in used_changes}
    # escrita — servidor
    bits={}
    for z in zs:
        b=bytearray((SW*SH+7)//8)
        for (X,Y,Z) in fwalk:
            if Z==z:
                i=(Y-y)*SW+(X-x); b[i>>3]|=1<<(i&7)
        bits[z]=base64.b64encode(bytes(b)).decode()
    sbits={}
    for z in zs:
        b=bytearray((S*S+7)//8) if False else bytearray((SW*SH+7)//8)
        for (X,Y,Z) in safe:
            if Z==z:
                i=(Y-y)*SW+(X-x); b[i>>3]|=1<<(i&7)
        if safe: sbits[str(z)]=base64.b64encode(bytes(b)).decode()
    srv={'exit':list(ext),'safe':sbits,'id':hid,'source':'rd_project 1098.otbm','window':wname,'x0':x,'y0':y,'w':SW,'h':SH,'floors':zs,'walk':{str(z):bits[z] for z in zs},
         'changes':[[a,b,c,d,e,f] for (a,b,c),(d,e,f) in sorted(used_changes.items())],'lures':[list(l) for l in lures],'entrance':list(ent),'mainZ':zmain}
    json.dump(srv,open(OUT+f'server/{hid}.json','w'),separators=(',',':'))
    # escrita — cliente (desenho do recorte inteiro com margem, todos os andares)
    d=OUT+f'assets/{hid}/'; os.makedirs(d,exist_ok=True)
    # só os andares que aparecem na tela: superfície = 0..7 + os andáveis;
    # subsolo = os andáveis com 1 de folga em cima/baixo
    if min(zs)<=7: keepz=set(range(0,8))|set(zs)
    else: keepz=set(range(min(zs)-1,max(zs)+2))
    fl_draw=sorted(z for z in floors.keys() if z in keepz)
    meta={'version':1,'id':hid,'x0':bx0,'y0':by0,'w':W,'h':H,'win':[x,y,SW,SH],'floors':fl_draw,'walkFloors':zs,'mainZ':zmain}
    json.dump(meta,open(d+'meta.json','w'),separators=(',',':'))
    for z in fl_draw:
        tl=[[i,[v if q%3 else sidx(v) for q,v in enumerate(g)],[v if q%3 else sidx(v) for q,v in enumerate(o)],[v if q%3 else sidx(v) for q,v in enumerate(t)]] for i,(g,o,t) in sorted(floors[z].items())]
        json.dump({'z':z,'tiles':tl},open(d+f'floor_{z}.json','w'),separators=(',',':'))
    pages=[]
    for p in range(0,len(sprites),4096):
        ch=sprites[p:p+4096]; im=Image.new('RGBA',(2048,((len(ch)+63)//64)*32),(0,0,0,0))
        for i,sp in enumerate(ch):
            if sp in MIDX: im.paste(mcrop(sp),((i%64)*32,(i//64)*32))
        nm=f'atlas_{p//4096}.png'; im.save(d+nm,optimize=True); pages.append(nm)
    meta['atlas']={'pages':pages,'perRow':64,'perPage':4096,'cell':32,'count':len(sprites)}
    json.dump(meta,open(d+'meta.json','w'),separators=(',',':'))
    loop=best_ord[0]
    report[hid]={'ent':ent,'exit':ext,'safe':len(safe),'win':wname,'K':len(K),'floors':zs,'lures':lures,'loop':loop,'changes':len(used_changes)}
    print(hid, report[hid])
json.dump(report,open(OUT+'report.json','w'),default=list)
