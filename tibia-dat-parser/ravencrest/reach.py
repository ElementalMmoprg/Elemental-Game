import pickle, collections
floors,walk,changes,sprites,W,H,X0,Y0=pickle.load(open('/tmp/claude-0/s/map/rc_built.pkl','rb'))
N8=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
def succ(u, walk, changes, allowed=None):
    x,y,z=u
    for dx,dy in N8:
        v=(x+dx,y+dy,z)
        if not walk.get(v): continue
        if dx and dy:  # diagonal: precisa de um dos ortogonais livre (evita atravessar quina)
            if not (walk.get((x+dx,y,z)) or walk.get((x,y+dy,z))): continue
        if allowed is not None and v not in allowed: continue
        if v in changes:
            d=changes[v]
            yield d
        else: yield v
def reach(start, walk, changes, allowed=None):
    seen={start}; q=collections.deque([start])
    while q:
        u=q.popleft()
        for v in succ(u,walk,changes,allowed):
            if v not in seen: seen.add(v); q.append(v)
    return seen
def build_pred(walk,changes,allowed=None):
    pred=collections.defaultdict(set)
    nodes=set(k for k,w in walk.items() if w)|set(changes.values())
    for u in nodes:
        for v in succ(u,walk,changes,allowed): pred[v].add(u)
    return pred
if __name__=='__main__':
    S=(5132,5092,6)
    R=reach(S,walk,changes)
    print('R',len(R),collections.Counter(z for _,_,z in R))
    edge=[p for p in R if p[0] in (X0,X0+W-1) or p[1] in (Y0,Y0+H-1)]
    print('touch border',len(edge),edge[:20])
    for z in sorted(set(p[2] for p in R)):
        xs=[p[0] for p in R if p[2]==z]; ys=[p[1] for p in R if p[2]==z]
        print(z,min(xs),max(xs),min(ys),max(ys))
    pickle.dump(R,open('/tmp/claude-0/s/map/R.pkl','wb'))
