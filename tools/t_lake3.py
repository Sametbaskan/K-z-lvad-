import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    ev("(()=>{window.__game.travelTo('forest')})()"); pg.wait_for_timeout(9000)
    print(ev("(()=>{const g=window.__game; g.updateHUD(); g.drawMini(); return [g.MAP.id, document.getElementById('zone').textContent]})()"))
    for name,(x,z,yaw,dist,pitch) in {'lk_g':(30,-18,3.14,32,.75),'lk_h':(12,-38,1.57,12,.35),'lk_i':(48,-52,-1.57,11,.35)}.items():
        ev(f"(()=>{{const g=window.__game;g.placePlayer({x},{z},{yaw});g.cam.dist={dist};g.cam.pitch={pitch};}})()"); pg.wait_for_timeout(3500); shot(name+'.png')
run(fn)
