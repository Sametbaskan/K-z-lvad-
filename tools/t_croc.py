import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    ev("(()=>{window.__game.travelTo('forest')})()"); pg.wait_for_timeout(9000)
    print(ev("""(()=>{const g=window.__game;const m=g.mobs.find(m=>m.type==='croc');window.__m=m;const h=m.home;
      g.placePlayer(h.x-7,h.z-1,Math.PI/2); g.S.hp=9999; g.S.lvl=1; g.P.target=null; g.cam.dist=11; g.cam.pitch=.45; m.state='wander';
      return [m.lvl,m.hp,m.maxHp,m.home.x,m.home.z, g.CORE.mobDamage(m.lvl,m.T.atk,1,()=>1)]})()"""))
    seen=[]; hp0=ev("window.__game.S.hp")
    for i in range(40):
        ev("window.SIM(12,.05)"); st=ev("(()=>{const m=window.__m,g=window.__game;return [m.state,m.b.fx.cur,+m.group.position.y.toFixed(2),+g.lakeE(m.group.position.x,m.group.position.z).toFixed(1),Math.round(g.S.hp)]})()")
        if i%2==0 or st[1]!='walk': seen.append(st)
        if i==12: shot('cr_walk.png')
        if i==22: shot('cr_atk.png')
    print(seen[:40], 'hp lost', hp0-ev("window.__game.S.hp"))
    # hasar alma + ölüm + yeniden doğma
    ev("(()=>{const g=window.__game,m=window.__m; g.playerHit(m,1,false,false,0);})()"); ev("window.SIM(3,.05)"); print('hit:',ev("(()=>{const m=window.__m;return [m.b.fx.cur,m.hp,m.maxHp]})()")); shot('cr_hit.png')
    ev("(()=>{const g=window.__game,m=window.__m; g.killMob(m); m.respT=2;})()"); ev("window.SIM(8,.1)"); print('dead:',ev("(()=>{const m=window.__m;return [m.dead,m.b.fx.cur,m.b.fx.dead,m.b.root.rotation.x]})()")); shot('cr_dead.png')
    ev("window.SIM(60,.1)"); print('respawn:',ev("(()=>{const m=window.__m,g=window.__game;return [m.dead,m.hp,m.b.fx.cur,m.group.position.x.toFixed(1),m.group.position.z.toFixed(1),m.home.x,m.home.z,g.S.rp]})()"))
run(fn)
