import pickle, json, base64
floors,walk,changes,sprites,W,H,X0,Y0=pickle.load(open('/tmp/claude-0/s/map/rc_built.pkl','rb'))
out='/mnt/user-data/outputs/ravencrest/'
meta={'version':3,'name':'Ravencrest','source':'rd_project 1098.otbm (Ravendawn), Tibia.dat/spr 10.98',
 'x0':X0,'y0':Y0,'w':W,'h':H,'floors':sorted(floors.keys()),'mainZ':6,
 'spawn':{'x':5132,'y':5092,'z':6},'teleport':{'x':5132,'y':5103,'z':6},
 'dummies':[{'x':x,'y':y,'z':6} for x,y in [(5114,5102),(5116,5102),(5118,5102),(5120,5102),(5122,5102),(5124,5102)]],
 'atlas':{'pages':['atlas_0.png','atlas_1.png'],'perRow':64,'perPage':4096,'cell':32},
 'changes':[[x,y,z,a,b,c] for (x,y,z),(a,b,c) in sorted(changes.items())]}
for d in [meta['spawn'],meta['teleport']]:
    assert walk.get((d['x'],d['y'],d['z'])), d
json.dump(meta,open(out+'city.json','w'),separators=(',',':'))
for z,F in floors.items():
    bits=bytearray((W*H+7)//8)
    for (x,y,zz),w in walk.items():
        if zz==z and w:
            i=(y-Y0)*W+(x-X0); bits[i>>3]|=1<<(i&7)
    tl=[[i,g,o,t] for i,(g,o,t) in sorted(F.items())]
    open(out+f'floor_{z}.json','w').write(json.dumps({'z':z,'walk':base64.b64encode(bytes(bits)).decode(),'tiles':tl},separators=(',',':')))
print('ok')
