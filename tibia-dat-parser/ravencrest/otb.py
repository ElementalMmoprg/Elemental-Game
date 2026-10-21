import re, struct
SPECIAL=re.compile(rb'[\xfd\xfe\xff]')
def walk(d, start=4):
    """Itera eventos ('open', type, data_bytes) / ('close',). data já sem escape."""
    i=start; n=len(d)
    stack=[]  # list of [type, bytearray]
    pending=None
    pos=i
    for m in SPECIAL.finditer(d, i):
        j=m.start()
        if j<pos: continue  # byte escapado já consumido
        b=d[j]
        if stack and j>pos: stack[-1][1]+=d[pos:j]
        if b==0xFD:
            if stack: stack[-1][1].append(d[j+1])
            pos=j+2; continue
        if b==0xFE:
            if stack and not stack[-1][2]:
                yield ('open', stack[-1][0], bytes(stack[-1][1])); stack[-1][2]=True
            # novo nó: tipo é o byte seguinte (pode ser escapado? tipo nunca é especial)
            stack.append([d[j+1], bytearray(), False]); pos=j+2; continue
        if b==0xFF:
            top=stack.pop()
            if not top[2]: yield ('open', top[0], bytes(top[1]))
            yield ('close', top[0]); pos=j+1; continue
def items_otb(path):
    d=open(path,'rb').read()
    m={}
    depth=0
    for ev in walk(d):
        if ev[0]=='open':
            depth+=1
            if depth==2:
                data=ev[2]; p=4; sid=cid=None
                while p+3<=len(data):
                    at=data[p]; ln=struct.unpack_from('<H',data,p+1)[0]; v=data[p+3:p+3+ln]; p+=3+ln
                    if at==0x10: sid=struct.unpack_from('<H',v)[0]
                    elif at==0x11: cid=struct.unpack_from('<H',v)[0]
                if sid: m[sid]=cid
        else: depth-=1
    return m
if __name__=='__main__':
    m=items_otb('/mnt/user-data/uploads/rd_project/Server/data/items/items.otb')
    print(len(m), list(m.items())[:5], max(m))
