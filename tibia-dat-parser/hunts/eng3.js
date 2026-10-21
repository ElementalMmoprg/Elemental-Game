const dir=process.env.SRV||'/home/claude/srv'; process.chdir(dir);
const he=require(dir+'/huntEngine.js');
const [huntId, diff, minutes]=[process.argv[2], process.argv[3]||'cauteloso', +(process.argv[4]||5)];
const all=new Map();
const st=he.createPlayerState({username:'u0',characterId:'c0',nick:'P0',progress:{}});
st.level=90; st.hpMax=st.hp=999999; st.stamina.current=1e12; st.sqmDistance=1; all.set('u0',st);
let T=Date.now(); Date.now=()=>T;
const r=he.startHunt(st,huntId,diff); if(!r.ok){console.log(huntId,diff,'ERRO',r.reason);process.exit(0);}
let lastKill=T, maxGap=0, k0=st.huntStats.kills, hold=0, gaps=[];
const ticks=minutes*60*30;
for(let k=0;k<ticks;k++){
  T+=33; st.hp=st.hpMax; st.mp=st.mpMax;
  const kb=st.huntStats.kills;
  he.tickPlayer(st,0.033,all,T);
  if(st.huntStats.kills>kb){ const g=(T-lastKill)/1000; gaps.push(g); if(g>maxGap) maxGap=g; lastKill=T; }
  if(st.hunt.holding) hold++;
}
const g=(T-lastKill)/1000; if(g>maxGap) maxGap=g;
const kills=st.huntStats.kills-k0;
gaps.sort((a,b)=>a-b);
const p90=gaps.length?gaps[Math.floor(gaps.length*0.9)]:0;
console.log(`${huntId.padEnd(34)} ${diff.padEnd(9)} pontos ${String(st.hunt.lurePoints.length).padStart(2)} | mortes ${String(kills).padStart(3)} | maior tempo sem matar ${maxGap.toFixed(0).padStart(3)}s | 90% das mortes em até ${p90.toFixed(0)}s | lutando ${Math.round(hold/ticks*100)}%`);
