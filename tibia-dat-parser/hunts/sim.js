const hm=require('./huntMaps.js'); const fs=require('fs');
const ids=fs.readdirSync(__dirname+'/data/huntmaps').map(f=>f.replace('.json',''));
let ok=0;
for(const id of ids){
  const t0=Date.now(); const m=hm.loadRealMap(id); const tBuild=Date.now()-t0;
  if(!m){console.log(id,'FALHOU load');continue;}
  let x=m.entrance.x,y=m.entrance.y, steps=0, cross=0, bands=new Set([hm.realFloorOf(m,x)]), bad=null;
  const legs=[];
  const order=[0,1,2,3,4,5,0];
  for(const li of order){
    const [gx,gy]=m.lures[li]; let n=0;
    while(Math.max(Math.abs(x-gx),Math.abs(y-gy))>1){
      const st=hm.realRouteStep(m,li,x,y,null);
      if(!st){bad=`sem passo no lure ${li} em ${x},${y}`;break;}
      x=st[0];y=st[1]; n++;
      const l=m.links.get(x+','+y); if(l){x=l[0];y=l[1];cross++;bands.add(hm.realFloorOf(m,x));}
      if(n>20000){bad=`loop no lure ${li}`;break;}
    }
    if(bad)break; legs.push(n); steps+=n;
  }
  if(!bad) ok++;
  console.log(id.padEnd(36), bad?('ERRO '+bad):`ok passos=${steps} escadas=${cross} andares=${[...bands].join(',')} pernas=${legs.join('/')} build=${tBuild}ms`);
}
console.log('OK',ok,'de',ids.length);
