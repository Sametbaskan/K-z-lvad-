import sys, json, re, os
from playwright.sync_api import sync_playwright
REPO='/home/claude/mrdoob/three.js/'
out='/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/shots/'
W=int(os.environ.get('W',1000)); H=int(os.environ.get('H',560))
SIM=open('/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/tools/sim.js').read()
def run(fn):
    with sync_playwright() as p:
        b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl'])
        pg=b.new_page(viewport={'width':W,'height':H}); logs=[]
        pg.on('console',lambda m: logs.append(m.type+': '+m.text) if m.type in('error','warning') else None)
        pg.on('pageerror',lambda e: logs.append('PAGEERROR: '+str(e)))
        def route(r):
            u=r.request.url; m=re.match(r'https://cdn\.jsdelivr\.net/npm/three@0\.160\.0/(.*)',u)
            if m:
                f=REPO+m.group(1)
                if os.path.exists(f): return r.fulfill(path=f,content_type='text/javascript',headers={'access-control-allow-origin':'*'})
            if 'localhost' in u: return r.continue_()
            return r.abort()
        pg.route('**/*',route); pg.goto('http://localhost:8123/test.html')
        pg.wait_for_function('window.__game',timeout=60000); pg.evaluate("window.__game.enterGame({uid:'t',username:'t',character:{id:'1',name:'Yiğit',king:0}})"); pg.wait_for_timeout(1500); pg.evaluate(SIM)
        def ev(js): 
            r=pg.evaluate(js); return r
        def shot(n): pg.screenshot(path=out+n,timeout=150000)
        fn(pg,ev,shot)
        print('\n'.join(l for l in logs if 'ERR_FAILED' not in l)[:3000]); b.close()
