import sys,json; sys.path.insert(0,'tools'); from drive import *
def f(pg,ev,shot):
    G="window.__gear"; pg.wait_for_timeout(1000)
    nz="const nz=o=>Object.fromEntries(Object.entries(o).filter(e=>e[1]));"
    print('war',ev(G+".isWar()"),'slots',ev(G+".SK.map(x=>x?x.id:0)"))
    r=ev("(()=>{"+nz+"const g=window.__gear,S=g.S; S.lvl=40; S.br='beden'; g.sanitizeSkills({cut:20,spin:20,body:20,roar:20,quake:20,soul:20},{skm:{cut:10,spin:99,soul:5,roar:3},skg:{cut:3,spin:9,roar:4},skp:{cut:1,spin:1}}); return JSON.stringify({sum:Object.values(S.sk).reduce((a,b)=>a+b,0),sk:nz(S.sk),m:nz(S.skm),g:nz(S.skg),p:nz(S.skp),pts:g.skPoints()})})()")
    print('tamper(lvl40,beden):',r)
    r=ev("(()=>{"+nz+"const g=window.__gear,S=g.S; S.lvl=99; S.br='beden'; g.sanitizeSkills({cut:20,spin:20,roar:20},{skm:{cut:10,spin:10,roar:10},skg:{cut:10,spin:10,roar:4},skp:{cut:1,spin:0,roar:1}}); return JSON.stringify({sk:nz(S.sk),m:nz(S.skm),g:nz(S.skg),p:nz(S.skp),lab:['cut','spin','roar'].map(g.skLab)})})()")
    print('valid(lvl99):',r)
    r=ev("(()=>{"+nz+"const g=window.__gear,S=g.S; S.lvl=30; S.br=''; g.sanitizeSkills({cut:10,fire:8,heal:5},{}); return JSON.stringify({sk:nz(S.sk),br:S.br,pts:g.skPoints(),slots:g.SK.filter(x=>x).map(x=>x.id)})})()")
    print('old save, no branch:',r)
run(f)
