import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    ev("(()=>{window.__game.travelTo('forest')})()"); pg.wait_for_timeout(9000)
    print(ev("""(()=>{const g=window.__game;const f=g.mobs.filter(m=>m.type==='wolf'),c=g.mobs.filter(m=>m.type==='croc');
      const inLake=g.mobs.filter(m=>g.lakeE(m.group.position.x,m.group.position.z)<0.5).length;
      return {stats:g.LAKE_STATS,mobs:g.LAKE_MOBS,frogs:f.length,crocs:c.length,inLake,crocLv:c.map(m=>m.lvl),crocE:c.map(m=>+g.lakeE(m.group.position.x,m.group.position.z).toFixed(1)),crocPos:c.map(m=>[Math.round(m.group.position.x),Math.round(m.group.position.z)]),hasCroc:!!g.CROC,fx:c[0]&&Object.keys(c[0].b.fx.acts),obst:g.obstacles.length,forest:g.FOREST_STATS}})()"""))
    for i,(x,z,yaw,name) in enumerate([(8,-30,-1.57,'lk_a'),(30,-62,3.14,'lk_b'),(55,-40,1.57,'lk_c'),(30,-16,0,'lk_d')]):
        ev(f"(()=>{{const g=window.__game;g.placePlayer({x},{z},{yaw});g.cam.dist=13;g.cam.pitch=.5;}})()"); pg.wait_for_timeout(2500); shot(name+'.png')
run(fn)
