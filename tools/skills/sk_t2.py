import sys,json; sys.path.insert(0,'tools'); from drive import *
BR=os.environ.get('BR','beden')
def f(pg,ev,shot):
    pg.wait_for_timeout(1500); ev("window.__freeze=false; document.querySelectorAll('#auth').forEach(e=>e.style.display='none')")
    G="window.__gear"; click=lambda sel: ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e) return 'YOK'; e.click(); return 'ok';}})()")
    ev(G+".S.lvl=40; "+G+".S.sp=9999; "+G+".S.hp=99999;"); click('[data-win="skw"]'); pg.wait_for_timeout(300)
    click('[data-skact="tab"][data-arg="%s"]'%BR); click('[data-skact="branch"]'); click('[data-skact="yes"]')
    ids=ev(G+".SK.filter(x=>x).map(x=>x.id)"); print('slots',ids)
    for k in ids:
        click(f'[data-sksel="{k}"]')
        for i in range(5): click(f'[data-skup="{k}"]')
    pg.wait_for_timeout(300); shot('sk_ui_%s.png'%BR); click('[data-close="mw"]')
    ev("(()=>{const g=window.__game,P=window.__gear.P; window.__ms=[]; for(let i=0;i<4;i++){ const a=(i-1.5)*.5; window.__ms.push(g.spawnMob('wolf',35,P.pos.x+Math.sin(P.yaw+a)*2.4,P.pos.z+Math.cos(P.yaw+a)*2.4,true)); } window.__gear.P.target=window.__ms[1]; })()"); pg.wait_for_timeout(500)
    hp=lambda: ev("window.__ms.map(m=>Math.round(m.hp)+(m.dead?'D':'')+(m.stunT>0?'S':'')+(m.slowT>0?'s':''))")
    S=lambda: ev("(()=>{const S=window.__gear.S,g=window.__gear; return JSON.stringify({atk:Math.round(g.atkPow()),buff:+S.buff.toFixed(1),bred:S.buffRed,aura:+S.auraT.toFixed(1),msw:+S.mswT.toFixed(1),fs:+S.fsT.toFixed(1),rage:+S.rageT.toFixed(1),hp:Math.round(S.hp),sp:Math.round(S.sp)})})()")
    print('base',S())
    slot={i:s for i,s in enumerate(ev(G+".SK.map(x=>x?x.id:null)")) if s}
    for i,name in slot.items():
        ev(G+".S.sp=9999"); b=hp(); ev(G+".useSlot(%d)"%i)
        try: pg.wait_for_function("window.__gear.P.atk&&window.__gear.P.atk.hit",timeout=25000)
        except Exception as e: print(name,'cast did not hit',ev("JSON.stringify(window.__gear.P.atk)"))
        pg.wait_for_timeout(250); shot('sk_fx_%s.png'%name); print(' at-hit',hp())
        try: pg.wait_for_function("!window.__gear.P.atk",timeout=25000)
        except Exception: pass
        pg.wait_for_timeout(1200); print(name,b,'->',hp(),'cd',round(ev(G+".cds[%d]"%i),1),S())
    ev(G+".saveGame()")
    sv=ev("JSON.stringify((()=>{const d=JSON.parse(localStorage.getItem(window.__gear.key)); return {sk:d.sk,skm:d.skm,skg:d.skg,skp:d.skp,br:d.br}})())"); print('SAVE',sv)
run(f)
