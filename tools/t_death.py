import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    ev("(()=>{window.__game.travelTo('forest')})()"); pg.wait_for_timeout(8000)
    ev("(()=>{const g=window.__game;g.placePlayer(20,-20,1);})()"); pg.wait_for_timeout(500)
    S="(()=>{const g=window.__game,d=document.getElementById('death');return [g.S.dead,Math.round(g.S.hp),Math.round(g.S.sp),d.className,g.DEATH.count,+g.P.pos.x.toFixed(1),+g.P.pos.z.toFixed(1),g.P.anim]})()"
    print('start',ev(S))
    ev("(()=>{const g=window.__game;g.S.hp=1;g.S.lvl=1;})()")
    ev("(()=>{const g=window.__game;g.damagePlayer(500,null);g.damagePlayer(500,null);g.killPlayer();})()")   # birden çok tetik: tek ölüm
    ev("window.SIM(6,.05)"); shot('d_1.png'); print('dead',ev(S))
    ev("window.SIM(40,.05)"); pg.wait_for_timeout(1500); shot('d_2.png')
    ev("window.SIM(20,.05)"); pg.wait_for_timeout(2500); shot('d_3.png'); print('buttons',ev(S))
    # ölüyken hasar / hareket / saldırı
    print('dead-hit',ev("(()=>{const g=window.__game;const h=g.S.hp;g.damagePlayer(50,null);g.keys&&0;const x=g.P.pos.x;g.useSlot&&g.useSlot(0);return [h,g.S.hp,g.P.atk]})()"))
    pg.click('#reHere'); pg.wait_for_timeout(1800); ev("window.SIM(10,.05)"); print('here',ev(S)); shot('d_4.png')
    # grace
    print('grace-hit',ev("(()=>{const g=window.__game;const h=g.S.hp;g.damagePlayer(50,null);return [h,g.S.hp]})()"))
    ev("window.SIM(80,.05)"); print('after grace hit',ev("(()=>{const g=window.__game;const h=g.S.hp;g.damagePlayer(10,null);return [h,g.S.hp]})()"))
    # şehir
    ev("(()=>{const g=window.__game;g.S.hp=1;g.damagePlayer(999,null);})()"); ev("window.SIM(10,.05)"); pg.wait_for_timeout(2500)
    print('dead2',ev(S)); pg.click('#reCity'); pg.wait_for_timeout(1800); ev("window.SIM(10,.05)"); print('city',ev(S), 'spawn',ev("(()=>{const s=window.__game.MAPS?window.__game.MAPS.forest.spawn:null;return s})()"))
    # köyde ölüm -> şehir
    ev("(async()=>{await window.__game.travelTo('village')})()"); pg.wait_for_timeout(3000)
    ev("(()=>{const g=window.__game;g.placePlayer(30,20,1);g.S.hp=1;g.damagePlayer(999,null);})()"); ev("window.SIM(10,.05)"); pg.wait_for_timeout(2500)
    pg.click('#reCity'); pg.wait_for_timeout(1800); ev("window.SIM(10,.05)"); print('village city',ev(S))
    # mobil görünüm
    ev("(()=>{const g=window.__game;g.S.hp=1;g.damagePlayer(999,null);})()"); pg.set_viewport_size({'width':800,'height':360}); pg.wait_for_timeout(4000); shot('d_m1.png')
    pg.set_viewport_size({'width':390,'height':780}); pg.wait_for_timeout(800); shot('d_m2.png')
run(fn)
