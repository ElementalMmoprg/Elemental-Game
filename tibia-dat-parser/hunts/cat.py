import numpy as np, sys, collections
sys.path.insert(0,'/tmp/claude-0/s/map')
from itemsxml import load
names,fc=load()
CATN=['none','grass','forest','jungle','dried','sand','snow','swamp','rock','wood','stone','sandstone','water','lava','dirt']
M={'grass':1,'lush grass':1,'flowers':1,'forest floor':2,'mossy floor':2,'jungle grass':3,'dried grass':4,'sand':5,'sand tile':5,
'snow':6,'ice':6,'swamp':7,'brown swamp ground':7,'mud':7,'dirt mud':7,'muddy floor':7,'rock soil':8,'gravel':8,'dirt floor':8,'rock':8,'mountain':8,
'wooden floor':9,'grimy wooden plank':9,'wooden planks':9,'parquet floor':9,'timber floor':9,'wooden boards':9,'bridge':9,
'stone floor':10,'stone tile':10,'black marble floor':10,'white marble floor':10,'tiled floor':10,'cobbled pavement':10,'cobblestone':10,'pavement':10,
'sandstone tile':11,'sandstone floor':11,'sandstone':11,'shallow water':12,'dirty water':12,'lava':13,'tar':13,'basalt floor':13,'dirt':14,'earth':14}
gid=np.load('gid.npy',mmap_mode='r'); col=np.load('col.npy',mmap_mode='r')
lut=np.zeros(65536,np.uint8)
for i,n in names.items():
    if n.lower() in M: lut[i]=M[n.lower()]
# cor de minimapa -> categoria (aprendida dos chão com nome)
votes=np.zeros((256,15),np.int64)
for z in range(16):
    g=np.asarray(gid[z]); c=np.asarray(col[z]); k=lut[g]
    m=k>0
    np.add.at(votes,(c[m],k[m]),1)
colcat=votes.argmax(1).astype(np.uint8); colcat[votes.sum(1)==0]=0
cat=np.zeros(gid.shape,np.uint8)
for z in range(16):
    g=np.asarray(gid[z]); c=np.asarray(col[z]); k=lut[g]
    unk=(k==0)&(g>0)
    k[unk]=colcat[c[unk]]
    cat[z]=k
np.save('cat.npy',cat)
for z in (7,8,9):
    u,n=np.unique(cat[z],return_counts=True); print(z,{CATN[a]:int(b) for a,b in zip(u,n)})
