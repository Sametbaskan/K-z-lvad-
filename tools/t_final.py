import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    print('village:',ev("(()=>{const g=window.__game;return [g.MAP.id,g.npcs.length,g.guards.length,g.mobs.length]})()"))
    t=ev("(async()=>{const g=window.__game;const t0=performance.now();await g.travelTo('forest');return Math.round(performance.now()-t0)})()"); print('forest build+travel ms',t)
    print(ev("""(()=>{const g=window.__game;const L=m=>g.lakeE(m.group.position.x,m.group.position.z);
      const lake=g.mobs.filter(m=>L(m)<16&&(m.type==='wolf'||m.type==='croc'));
      let gap=1e9; for(let i=0;i<lake.length;i++) for(let j=i+1;j<lake.length;j++) gap=Math.min(gap,Math.hypot(lake[i].group.position.x-lake[j].group.position.x,lake[i].group.position.z-lake[j].group.position.z));
      const per={}; for(const m of g.mobs) per[m.type]=(per[m.type]||0)+1;
      const inWater=g.mobs.filter(m=>L(m)<1).length;
      const gy=g.mobs.map(m=>Math.abs(m.group.position.y-g.hAt(m.group.position.x,m.group.position.z))).reduce((a,b)=>Math.max(a,b),0);
      return {map:g.MAP.id,per,lakeFrogs:lake.filter(m=>m.type==='wolf').length,lakeCrocs:lake.filter(m=>m.type==='croc').length,minGapLake:+gap.toFixed(1),inWater,maxYerr:gy,
        frogLv:lake.filter(m=>m.type==='wolf').map(m=>m.lvl),crocLv:lake.filter(m=>m.type==='croc').map(m=>m.lvl),
        frogStat:(()=>{const f=lake.find(m=>m.type==='wolf');return [f.maxHp,g.CORE.mobDamage(f.lvl,f.T.atk,1,()=>1),g.CORE.mobExp(f.lvl,f.T.exp)]})(),
        crocStat:(()=>{const f=lake.find(m=>m.type==='croc');return [f.maxHp,g.CORE.mobDamage(f.lvl,f.T.atk,1,()=>1),g.CORE.mobExp(f.lvl,f.T.exp),g.rankReward('croc',f.lvl)]})(),
        zoneLake:g.zoneAt(13,-31).name+' '+g.zoneAt(13,-31).l0+'-'+g.zoneAt(13,-31).l1, zoneCroc:g.zoneAt(48,-40).name+' '+g.zoneAt(48,-40).l0+'-'+g.zoneAt(48,-40).l1, stats:g.LAKE_STATS,
        existing:{mage:per.mage,orc:per.orc,fboss:per.fboss,mboss:per.mboss,boss:per.boss,stone:per.stone}}})()"""))
    # oyuncu derin suya giremez
    print('wade:',ev("""(()=>{const g=window.__game;g.placePlayer(14,-38,1.57);g.P.dest=null;let r=[];for(let i=0;i<5;i++){ g.P.pos.x+=3; g.updatePlayer(.05); r.push([Math.round(g.P.pos.x*10)/10,+g.lakeE(g.P.pos.x,g.P.pos.z).toFixed(1),+(g.hAt(g.P.pos.x,g.P.pos.z)-g.LAKE_WL).toFixed(2)]); } return r})()"""))
    print('back:',ev("(async()=>{const g=window.__game;await g.travelTo('village');return [g.MAP.id,g.npcs.length,g.mobs.length]})()"))
    print('again:',ev("(async()=>{const g=window.__game;await g.travelTo('forest');const m=g.mobs;return [g.MAP.id,m.length,m.filter(x=>x.type==='croc').length,g.LAKE_MOBS]})()"))
run(fn)
