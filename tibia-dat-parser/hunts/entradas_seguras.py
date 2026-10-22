# Entrada segura das caçadas: andar sem monstro (acima/subsolo) ou canto longe dos lures
import json, glob, base64, collections, sys
N8=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
rep={}
for f in sorted(glob.glob('/tmp/claude-0/s/ent/*.json')):
    j=json.load(open(f)); x0,y0,W,H=j['x0'],j['y0'],j['w'],j['h']
    walk=set()
    for z in j['floors']:
        b=base64.b64decode(j['walk'][str(z)])
        for i in range(W*H):
            if b[i>>3]&(1<<(i&7)): walk.add((x0+i%W,y0+i//W,z))
    ch={(a,b,c):(d,e,g) for a,b,c,d,e,g in j['changes']}
    def succ(u):
        X,Y,Z=u
        for dx,dy in N8:
            v=(X+dx,Y+dy,Z)
            if v not in walk: continue
            if dx and dy and not ((X+dx,Y,Z) in walk and (X+dx,Y,Z) not in ch and (X,Y+dy,Z) in walk and (X,Y+dy,Z) not in ch): continue
            if v in ch:
                d=ch[v]
                if d in walk: yield d
            else: yield v
    def bfs(s):
        D={s:0}; q=collections.deque([s])
        while q:
            u=q.popleft()
            for v in succ(u):
                if v not in D: D[v]=D[u]+1; q.append(v)
        return D
    lures=[tuple(l) for l in j['lures']]
    Dl=[bfs(l) for l in lures]
    lureZ=set(l[2] for l in lures)
    arrivals=set(ch.values())
    def opn(k,r=2):
        X,Y,Z=k; return sum(1 for a in range(-r,r+1) for b in range(-r,r+1) if (X+a,Y+b,Z) in walk and (X+a,Y+b,Z) not in ch)
    best=None
    for e in walk:
        if e in ch or e in arrivals: continue
        o=opn(e)
        if o<12: continue
        dmin=min(D.get(e,10**6) for D in Dl)
        if dmin>=10**6 or dmin<10 or dmin>45: continue
        other=e[2] not in lureZ
        if not other:
            if min(max(abs(e[0]-l[0]),abs(e[1]-l[1])) for l in lures if l[2]==e[2])<16: continue
        # longe de escada que leva direto pros monstros? (não precisa: monstro não usa escada)
        sc=(100 if other else 0)+o*0.6-abs(dmin-22)*0.8
        if best is None or sc>best[0]: best=(sc,e,dmin,other,o)
    if not best: print(j['id'],'SEM CANDIDATA'); continue
    sc,e,dmin,other,o=best
    De=bfs(e); first=min(range(len(lures)),key=lambda i:De.get(lures[i],10**6))
    newl=lures[first:]+lures[:first]
    # zona segura: raio 3 em volta da entrada (monstro não entra)
    safe={(e[0]+a,e[1]+b,e[2]) for a in range(-3,4) for b in range(-3,4)}&walk
    safe-=set(ch)
    sb=bytearray((W*H+7)//8)
    for (X,Y,Z) in safe:
        i=(Y-y0)*W+(X-x0); sb[i>>3]|=1<<(i&7)
    j2=dict(j); j2['entrance']=list(e); j2['lures']=[list(l) for l in newl]; j2['safe']={str(e[2]):base64.b64encode(bytes(sb)).decode()}
    j2['entranceInfo']={'floorWithoutMonsters':other,'stepsToFirstLure':De[newl[0]]}
    json.dump(j2,open('/tmp/claude-0/s/ent/out/'+j['id']+'.json','w'),separators=(',',':'))
    rep[j['id']]={'ent':e,'oldEnt':j['entrance'],'other':other,'steps':De[newl[0]],'open':o,'mainZ':j['mainZ'],'win':j['window']}
    print(j['id'],e,'outro andar' if other else 'mesmo andar','passos',De[newl[0]],'abertura',o,'(main',j['mainZ'],')')
json.dump(rep,open('/tmp/claude-0/s/ent/rep.json','w'),default=list)
