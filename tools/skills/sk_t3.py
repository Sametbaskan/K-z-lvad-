import sys,json; sys.path.insert(0,'tools'); from drive import *
def f(pg,ev,shot):
    G="window.__gear"; click=lambda sel: ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e) return 'YOK'; e.click(); return 'ok';}})()")
    st=lambda: ev(f"(()=>{{const g={G},S=g.S,nz=o=>Object.fromEntries(Object.entries(o).filter(e=>e[1])); return JSON.stringify({{br:S.br,lvl:S.lvl,pts:g.skPoints(),sk:nz(S.sk),m:nz(S.skm),g:nz(S.skg),p:nz(S.skp),slots:g.SK.filter(x=>x).map(x=>x.id),it:['skbook','soulst','pseal','forget'].map(g.itemCount)}})}})()")
    def reenter():
        pg.reload(); pg.wait_for_function('window.__game',timeout=400000); pg.evaluate("window.__game.enterGame({uid:'t',username:'t',character:{id:'1',name:'Yiğit',king:0}})"); pg.wait_for_timeout(2500); ev("window.__freeze=false; document.querySelectorAll('#auth').forEach(e=>e.style.display='none')")
    pg.wait_for_timeout(1500); ev("window.__freeze=false; document.querySelectorAll('#auth').forEach(e=>e.style.display='none')")
    ev(G+".S.lvl=40;"); click('[data-win="skw"]'); click('[data-skact="tab"][data-arg="beden"]'); click('[data-skact="branch"]'); click('[data-skact="yes"]')
    ev(G+".addItem('skbook',5)"); click('[data-sksel="cut"]')
    for i in range(23): click('[data-skup="cut"]')
    click('[data-sksel="roar"]'); [click('[data-skup="roar"]') for i in range(7)]
    ev(G+".saveGame()"); print('1 before reload',st())
    reenter(); print('2 after reload ',st())
    # kurcalanmış kayıt: fazla puan + geçersiz aşamalar + diğer dal
    ev("(()=>{const k=window.__gear.key,d=JSON.parse(localStorage.getItem(k)); d.sk={cut:20,spin:20,body:20,roar:20,quake:20,soul:20}; d.skm={cut:10,spin:99,soul:5}; d.skg={cut:3,spin:9,roar:4}; d.skp={cut:1,spin:1}; localStorage.setItem(k,JSON.stringify(d)); window.__noSave=1;})()")
    ev("window.__gear.saveGame=()=>{}")   # sayfa kapanırken üstüne yazmasın diye değil: aşağıda doğrudan reload
    pg.evaluate("(()=>{const k=window.__gear.key,v=localStorage.getItem(k); window.addEventListener('pagehide',()=>localStorage.setItem(k,v)); window.addEventListener('beforeunload',()=>localStorage.setItem(k,v));})()")
    reenter(); print('3 tampered    ',st(),'earned',ev(G+".S.lvl-4"))
    click('[data-win="skw"]'); pg.wait_for_timeout(200)
    print('reset without scroll:',click('[data-skact="reset"]'), 'confirm shown:',ev("!!document.querySelector('.m4cf')"))
    ev(G+".addItem('forget',1)"); click('[data-skact="reset"]'); pg.wait_for_timeout(200); shot('sk_reset_confirm.png'); print('confirm shown:',ev("!!document.querySelector('.m4cf')")); click('[data-skact="yes"]'); print('4 after reset  ',st())
    click('[data-skact="tab"][data-arg="zihin"]'); click('[data-skact="branch"]'); click('[data-skact="yes"]'); click('[data-sksel="aura"]'); [click('[data-skup="aura"]') for i in range(4)]
    ev(G+".saveGame()"); print('5 zihin        ',st()); reenter(); print('6 after reload ',st())
run(f)
