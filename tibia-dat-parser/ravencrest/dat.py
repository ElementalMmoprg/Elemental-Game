import struct
def parse_dat(path):
    d=open(path,'rb').read(); p=0
    def u8():
        nonlocal p; v=d[p]; p+=1; return v
    def u16():
        nonlocal p; v=struct.unpack_from('<H',d,p)[0]; p+=2; return v
    def u32():
        nonlocal p; v=struct.unpack_from('<I',d,p)[0]; p+=4; return v
    sig=u32(); ni=u16(); no=u16(); ne=u16(); nm=u16()
    items={}
    for cid in range(100, ni+1):
        a={}
        while True:
            at=u8()
            if at==0xFF: break
            if at==0: a['ground']=u16()
            elif at in (1,2,3): a['order']=at
            elif at in (8,9): u16()
            elif at==22: u16(); u16()
            elif at==25: a['disp']=(u16(),u16())
            elif at==26: a['elev']=u16()
            elif at==29: a['minimap']=u16()
            elif at==30: u16()
            elif at==33: u16()
            elif at==34: u16();u16();u16(); l=u16(); p+=l; u16();u16()
            elif at==35: u16()
            elif at in (4,5,6,7,10,11,12,13,14,15,16,17,18,19,20,21,23,24,27,28,31,32,36,37,38,254):
                if at==12: a['block']=1
                if at==31: a['full']=1
            else: raise Exception(f'attr {at} at item {cid} p={p}')
        w=u8(); h=u8()
        if w>1 or h>1: u8()
        L=u8(); px=u8(); py=u8(); pz=u8(); ph=u8()
        if ph>1:
            u8(); u32(); u8(); p+=8*ph
        n=w*h*L*px*py*pz*ph
        spr=list(struct.unpack_from('<%dI'%n,d,p)); p+=4*n
        a.update(w=w,h=h,L=L,px=px,py=py,pz=pz,ph=ph,spr=spr)
        items[cid]=a
    return items
if __name__=='__main__':
    it=parse_dat('/mnt/user-data/uploads/rd_project/otcv_8/data/things/1098/Tibia.dat')
    print(len(it), it[102] if 102 in it else None)
    print(sum(1 for v in it.values() if 'minimap' in v), sum(1 for v in it.values() if 'ground' in v))
