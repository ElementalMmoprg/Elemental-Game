# Extrai os itens de cada tile das janelas candidatas (todas os andares), 1 passada no otbm.
import struct, sys, time, json, pickle
sys.path.insert(0,'/tmp/claude-0/s/map')
from otb import walk
MARGIN=12
win=json.load(open(sys.argv[1] if len(sys.argv)>1 else '/tmp/claude-0/s/hunt/windows.json'))
# win: {nome: [x,y,S]}  (janela andável; recorte = janela + margem)
boxes={k:(x-MARGIN,y-MARGIN,x+S+MARGIN,y+S+MARGIN) for k,(x,y,S) in win.items()}
# índice espacial grosso (blocos de 256) pra não testar todas as caixas por tile
grid={}
for k,(a,b,c,d) in boxes.items():
    for gx in range(a>>8,(c>>8)+1):
        for gy in range(b>>8,(d>>8)+1): grid.setdefault((gx,gy),[]).append(k)
out={k:{} for k in win}
d=open('/mnt/user-data/uploads/rd_project/Server/data/world/1098.otbm','rb').read()
stack=[]; area=None; curs=None
t0=time.time()
for ev in walk(d):
    if ev[0]=='open':
        t,data=ev[1],ev[2]; stack.append(t)
        if t==4: area=struct.unpack_from('<HHB',data,0)
        elif t in (5,14):
            x=area[0]+data[0]; y=area[1]+data[1]; z=area[2]; curs=None
            ks=grid.get((x>>8,y>>8))
            if ks:
                hit=[k for k in ks if boxes[k][0]<=x<boxes[k][2] and boxes[k][1]<=y<boxes[k][3]]
                if hit:
                    p=2+(4 if t==14 else 0); ids=[]
                    while p<len(data):
                        at=data[p]; p+=1
                        if at==3: p+=4
                        elif at==9: ids.append(struct.unpack_from('<H',data,p)[0]); p+=2
                        else: break
                    for k in hit: out[k][(x,y,z)]=ids
                    curs=ids
        elif t==6 and curs is not None and len(stack)>=2 and stack[-2] in (5,14):
            curs.append(struct.unpack_from('<H',data,0)[0])
    else:
        t=stack.pop()
        if t in (5,14): curs=None
print('s',time.time()-t0,{k:len(v) for k,v in out.items()})
pickle.dump((win,boxes,out),open('/tmp/claude-0/s/hunt/wtiles.pkl','wb'))
