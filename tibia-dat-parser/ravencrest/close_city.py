import pickle, collections, sys
sys.path.insert(0,'/tmp/claude-0/s/map')
from reach import reach, succ, N8
floors,walk,changes,sprites,W,H,X0,Y0=pickle.load(open('/tmp/claude-0/s/map/rc_built.pkl','rb'))
S=(5132,5092,6)
YARD=(5100,5128,5171,5188)
# componentes do z7 andando só no z7 (sem escadas)
w7={k for k,v in walk.items() if v and k[2]==7}
comp={}; sizes={}
for k in w7:
    if k in comp: continue
    cid=len(sizes); st=[k]; comp[k]=cid; n=0
    while st:
        u=st.pop(); n+=1
        for dx,dy in N8:
            v=(u[0]+dx,u[1]+dy,7)
            if v in w7 and v not in comp: comp[v]=cid; st.append(v)
    sizes[cid]=n
def allowed_tile(k):
    x,y,z=k
    if z==7:
        if YARD[0]<=x<=YARD[1] and YARD[2]<=y<=YARD[3]: return True
        return sizes[comp[k]]<250   # porões/poços pequenos debaixo da cidade
    if z>7: return x<5160
    return 5040<=x<=5180
allowed={k for k,v in walk.items() if v and allowed_tile(k)}
ch={k:v for k,v in changes.items() if k in allowed}
for it in range(10):
    R=reach(S,walk,ch,allowed)
    # quem consegue voltar pro spawn
    pred=collections.defaultdict(set)
    for u in R:
        for v in succ(u,walk,ch,allowed): pred[v].add(u)
    B={S}; st=[S]
    while st:
        v=st.pop()
        for u in pred[v]:
            if u not in B: B.add(u); st.append(u)
    K=R&B
    bad=R-K
    # escadas que levam pra fora de K viram parede
    nch={k:v for k,v in ch.items() if v in K and k in allowed}
    nallowed={k for k in allowed if k in K or (k in nch)}
    print('iter',it,'R',len(R),'K',len(K),'trap',len(bad),'changes',len(nch))
    if len(nch)==len(ch) and nallowed==allowed: break
    ch=nch; allowed=nallowed
final_walk=set(k for k in allowed if k in K or k in ch)
print('final walk',len(final_walk),collections.Counter(k[2] for k in final_walk),'changes',len(ch))
for z in sorted(set(k[2] for k in final_walk)):
    xs=[k[0] for k in final_walk if k[2]==z]; ys=[k[1] for k in final_walk if k[2]==z]
    print(z,min(xs),max(xs),min(ys),max(ys))
print('yard dummies standing', [(x,5173,7) in final_walk for x in (5117,5119,5121,5123)])
pickle.dump((final_walk,ch,K),open('/tmp/claude-0/s/map/closed.pkl','wb'))
pickle.dump(K,open('/tmp/claude-0/s/map/K.pkl','wb'))
