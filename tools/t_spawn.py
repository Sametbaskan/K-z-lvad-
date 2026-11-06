import sys; sys.path.insert(0,'tools')
from drive import run
def fn(pg,ev,shot):
    res=[]
    for i in range(6):
        res.append(ev("(async()=>{const g=window.__game;await g.travelTo('forest');const r=[g.LAKE_MOBS.frogs,g.LAKE_MOBS.crocs];await g.travelTo('village');return r})()"))
    print(res)
run(fn)
