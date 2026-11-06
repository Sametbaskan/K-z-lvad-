import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    ev("(()=>{window.__game.travelTo('forest')})()"); pg.wait_for_timeout(9000)
    print(ev("""(()=>{const g=window.__game;const f=g.mobs.filter(m=>m.type==='wolf'&&g.lakeE(m.group.position.x,m.group.position.z)<20),c=g.mobs.filter(m=>m.type==='croc');
      return {map:g.MAP.id,mobs:g.LAKE_MOBS,frogs:f.map(m=>[Math.round(m.group.position.x),Math.round(m.group.position.z),m.lvl,+g.lakeE(m.group.position.x,m.group.position.z).toFixed(1)]),crocs:c.map(m=>[Math.round(m.group.position.x),Math.round(m.group.position.z),m.lvl,+g.lakeE(m.group.position.x,m.group.position.z).toFixed(1)])}})()"""))
    ev("(()=>{const g=window.__game;g.placePlayer(33,-18,0);g.cam.dist=14;g.cam.pitch=.42;g.cam.yaw=Math.PI;})()"); pg.wait_for_timeout(3000); shot('lk_e.png')
    ev("(()=>{const g=window.__game;g.placePlayer(60,-34,1.57);g.cam.dist=14;g.cam.pitch=.4;g.cam.yaw=-1.57;})()"); pg.wait_for_timeout(3000); shot('lk_f.png')
run(fn)
