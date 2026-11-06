import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    ev("(()=>{window.__game.travelTo('forest')})()"); pg.wait_for_timeout(9000)
    ev("""(()=>{const g=window.__game;const m=g.mobs.find(m=>m.type==='croc'&&m.lvl===9);window.__m=m;const h=m.home;
      for(const o of g.mobs) if(o!==m&&o.type==='croc'){ o.group.position.set(0,0,0); o.state='dead'; o.dead=true; o.respT=9999; o.group.visible=false; }
      g.S.lvl=30; g.S.hp=99999; g.S.vit=50;
      g.placePlayer(h.x-4.5,h.z+.5,Math.PI/2); g.cam.dist=7; g.cam.pitch=1.15; m.state='wander';})()""")
    for i in range(30):
        ev("window.SIM(5,.05)"); st=ev("(()=>{const m=window.__m;return m.b.fx.cur})()")
        if i==3: shot('cc_1.png')
        if st=='attack':
            ev("window.SIM(4,.05)"); shot('cc_atk.png'); ev("window.SIM(4,.05)"); shot('cc_atk2.png'); break
    ev("(()=>{const g=window.__game;g.playerHit(window.__m,1,false,false,0);})()"); ev("window.SIM(2,.05)"); shot('cc_hit.png')
    ev("(()=>{const g=window.__game,m=window.__m; g.killMob(m); m.respT=2;})()"); ev("window.SIM(12,.1)"); shot('cc_dead.png')
    ev("(()=>{const g=window.__game;g.placePlayer(10,-10,0);})()"); ev("window.SIM(60,.1)"); print('respawn:',ev("(()=>{const m=window.__m;return [m.dead,m.hp,m.b.fx.cur,m.group.position.x.toFixed(1),m.group.position.z.toFixed(1),m.home.x,m.home.z]})()"))
run(fn)
