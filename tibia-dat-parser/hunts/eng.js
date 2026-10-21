// teste do MOTOR real (huntEngine.js) nos mapas reais: solo e PT
process.chdir('/home/claude/srv');
const he=require('/home/claude/srv/huntEngine.js'); const hm=he.huntMaps;
const [huntId, nPlayers, minutes]=[process.argv[2]||'cave', +(process.argv[3]||1), +(process.argv[4]||10)];
const all=new Map(); const ps=[];
for(let i=0;i<nPlayers;i++){
  const st=he.createPlayerState({username:'u'+i,characterId:'c'+i,nick:'P'+i,progress:{}});
  st.level=90; st.hpMax=st.hp=999999; st.mpMax=st.mp=99999; st.stamina.current=1e12;
  all.set(st.username,st); ps.push(st);
}
let T=Date.now(); const realNow=Date.now; Date.now=()=>T;
if(nPlayers>1){
  const r=he.createParty(ps[0]); 
  for(let i=1;i<nPlayers;i++) he.joinParty(ps[0].party.id, ps[i], all);
  const g=he.partyGo(ps[0], huntId, Object.keys(he.DIFFICULTIES)[0], all); console.log('partyGo',g.ok,g.reason||'',g.teleported);
} else { const r=he.startHunt(ps[0],huntId,Object.keys(he.DIFFICULTIES)[0]); console.log('start',r); }
const m=hm.loadRealMap(huntId);
const band=s=>Math.floor((Math.round(s.x/34)-hm.REAL_BASE)/m.stride);
const last=ps.map(s=>({band:band(s),idx:s.hunt.currentIndex}));
let maxStuck=0; let laps=ps.map(()=>0), crosses=ps.map(()=>0), maxSpread=0, waitTicks=0, stuck=ps.map(()=>0), lastPos=ps.map(s=>s.x+','+s.y), kills0=ps.map(s=>s.stats? s.stats.kills:0);
const ticks=minutes*60*30;
for(let k=0;k<ticks;k++){
  T+=33;
  for(const s of ps){ s.hp=s.hpMax; s.mp=s.mpMax; he.tickPlayer(s,0.033,all,T); }
  ps.forEach((s,i)=>{
    const b=band(s); if(b!==last[i].band){crosses[i]++; last[i].band=b;}
    if(s.hunt.currentIndex!==last[i].idx){ if(s.hunt.currentIndex===0) laps[i]++; last[i].idx=s.hunt.currentIndex; }
    const p=s.x+','+s.y; if(p===lastPos[i]) {stuck[i]++; if(stuck[i]>maxStuck) maxStuck=stuck[i];} else {stuck[i]=0; lastPos[i]=p;}
  });
  if(nPlayers>1){ const bs=new Set(ps.map(band)); if(bs.size>1) waitTicks++; }
  if(k%(30*60)===0){ console.log(`t=${k/30|0}s`, ps.map((s,i)=>`P${i}[idx ${s.hunt.currentIndex} andar ${m.src.floors[band(s)]} voltas ${laps[i]} esc ${crosses[i]} parado ${(stuck[i]/30)|0}s${s.hunt.waitingParty?' ESPERANDO':''}]`).join(' '), 'mons', s0());}
}
function s0(){ return m && ps[0].hunt.lurePoints.reduce((a,p)=>a+p.monsters.length,0); }
console.log('FIM', huntId, ps.map((s,i)=>`P${i}: voltas=${laps[i]} trocas_andar=${crosses[i]} xp=${s.xp}`).join(' | '), 'ticks c/ PT separada', waitTicks, 'maior_parado_s', (maxStuck/30)|0, 'lure_final', ps[0].hunt.currentIndex);
