import sys,os,json; sys.path.insert(0,'tools'); from drive import *
from PIL import Image
ONLY=os.environ.get('ONLY','cut,spin,body,roar,quake').split(','); TIER=os.environ.get('TIER','')
def f(pg,ev,shot):
    G="window.__gear"; click=lambda sel: ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e) return 'YOK'; e.click(); return 'ok';}})()")
    pg.wait_for_timeout(1500); ev("window.__freeze=false; document.querySelectorAll('#auth').forEach(e=>e.style.display='none')")
    ev(G+".S.lvl=60; "+G+".S.sp=9999; "+G+".S.hp=99999;"); click('[data-win="skw"]'); pg.wait_for_timeout(200)
    click('[data-skact="tab"][data-arg="beden"]'); click('[data-skact="branch"]'); click('[data-skact="yes"]')
    for k in ['cut','spin','body','roar','quake']:
        click(f'[data-sksel="{k}"]')
        for i in range(5): click(f'[data-skup="{k}"]')
    if TIER: ev("(()=>{const S=window.__gear.S,t=%s; for(const k of ['cut','spin','body','roar','quake']){ S.sk[k]=20; S.skm[k]=t>=1?10:0; if(t>=1)S.skm[k]=t>=2?10:5; S.skg[k]=t>=2?(t>=3?10:5):0; S.skp[k]=t>=3?1:0; } })()"%TIER)
    click('[data-close="mw"]'); ev("document.querySelectorAll('.winwrap,#mw').forEach(e=>e.style&&0)")
    ev("(()=>{const g=window.__game,P=window.__gear.P; P.pos.set(-4,g.hAt(-4,33),33); P.yaw=0; P.yawGoal=0; window.__ms=[]; for(let i=0;i<4;i++){ const a=(i-1.5)*.55; window.__ms.push(g.spawnMob('wolf',35,P.pos.x+Math.sin(a)*2.6,P.pos.z+Math.cos(a)*2.6,true)); } P.target=window.__ms[1]; g.cam.yaw=Math.PI*(+(window.CY||.18)); g.cam.pitch=.7; g.cam.dist=8; })()"); pg.wait_for_timeout(2500)
    slot={s:i for i,s in enumerate(ev(G+".SK.map(x=>x?x.id:null)")) if s}
    for name in ONLY:
        i=slot[name]; ev(G+".S.sp=9999; "+G+".cds[%d]=0"%i)
        ev("(()=>{const g=window.__game; for(const m of window.__ms){ if(m.dead){} } })()")
        ev(G+".useSlot(%d)"%i); pg.wait_for_timeout(50)
        info=ev("(()=>{const a=window.__gear.P.atk,s=window.__gear.P.spin; return JSON.stringify({hit:a?a.hitAt:null,dur:a?a.dur:null,t1:s&&s.t1,t2:s&&s.t2})})()"); d=json.loads(info); print(name,d)
        if name=='spin': ts=[d['t1']+.15,(d['t1']+d['t2'])/2,d['t2']-.04,d['dur']-.15]
        else: h=d['hit']; ts=[h+.03,h+.18,h+.45]
        tiles=[]
        for j,t in enumerate(ts):
            ok=ev("new Promise(r=>{ const iv=setInterval(()=>{ const a=window.__gear.P.atk; if(!a||a.t>=%f){ window.__freeze=true; clearInterval(iv); r(!!a); } },5); setTimeout(()=>{clearInterval(iv);r('to')},60000); })"%t)
            pg.wait_for_timeout(120); shot('tmp.png'); ev("window.__freeze=false")
            im=Image.open('shots/tmp.png'); w,hh=im.size; tiles.append(im.crop((int(w*.25),int(hh*.08),int(w*.75),int(hh*.85))))
        W2,H2=tiles[0].size; o=Image.new('RGB',(W2*len(tiles),H2)); [o.paste(t,(k*W2,0)) for k,t in enumerate(tiles)]; o.save('shots/bv3_%s%s.png'%(name,TIER))
        try: pg.wait_for_function("!window.__gear.P.atk",timeout=30000)
        except Exception: pass
        pg.wait_for_timeout(1500)
run(f)
