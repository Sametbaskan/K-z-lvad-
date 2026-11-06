import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    pg.set_viewport_size({'width':800,'height':360}); pg.wait_for_timeout(1500)
    ev("window.__game.killPlayer()"); ev("window.SIM(30,.05)"); pg.wait_for_timeout(3500); shot('d_m1.png')
    pg.set_viewport_size({'width':390,'height':780}); pg.wait_for_timeout(1200); shot('d_m2.png')
run(fn)
