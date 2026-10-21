import re
def load(path='/mnt/user-data/uploads/rd_project/Server/data/items/items.xml'):
    s=open(path,encoding='latin1').read()
    names={}; fc={}
    for m in re.finditer(r'<item\s+([^>]*?)(/?)>(.*?)(?=<item\s|</items>)', s, re.S):
        attrs=m.group(1); body=m.group(3) if m.group(2)!='/' else ''
        a=dict(re.findall(r'(\w+)="([^"]*)"',attrs))
        if 'id' in a: ids=[int(a['id'])]
        elif 'fromid' in a: ids=list(range(int(a['fromid']),int(a['toid'])+1))
        else: continue
        f=re.search(r'key="floorchange"\s+value="(\w+)"',body)
        for i in ids:
            names[i]=a.get('name','')
            if f: fc[i]=f.group(1)
    return names,fc
