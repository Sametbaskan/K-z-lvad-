import re, os, sys
from playwright.sync_api import sync_playwright
REPO='/home/claude/mrdoob/three.js/'; T='/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/'
MOCK=T+'tools/auth_mock/'; out=T+'shots/'
CFG='export const firebaseConfig={apiKey:"x",authDomain:"x",projectId:"p",appId:"a"};'
def mkroute(configured=True):
    def route(r):
        u=r.request.url; m=re.match(r'https://cdn\.jsdelivr\.net/npm/three@0\.160\.0/(.*)',u)
        if m and os.path.exists(REPO+m.group(1)): return r.fulfill(path=REPO+m.group(1),content_type='text/javascript',headers={'access-control-allow-origin':'*'})
        g=re.match(r'https://www\.gstatic\.com/firebasejs/[\d.]+/firebase-(app|auth|firestore)\.js',u)
        if g: return r.fulfill(path=MOCK+{'app':'app.js','auth':'auth.js','firestore':'fs.js'}[g.group(1)],content_type='text/javascript',headers={'access-control-allow-origin':'*'})
        if configured and u.endswith('auth/firebase-config.js'): return r.fulfill(body=CFG,content_type='text/javascript')
        if 'localhost' in u: return r.continue_()
        return r.abort()
    return route
def session(fn,W=900,H=420,configured=True,ctx=None):
    with sync_playwright() as p:
        b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl'])
        c=ctx or b.new_context(viewport={'width':W,'height':H}); pg=c.new_page(); logs=[]
        pg.on('console',lambda m: logs.append(m.type+': '+m.text) if m.type in('error','warning') else None)
        pg.on('pageerror',lambda e: logs.append('PAGEERROR: '+str(e)))
        pg.route('**/*',mkroute(configured)); pg.goto('http://localhost:8123/test.html')
        pg.wait_for_selector('#a_card input, #a_card .amsg',timeout=90000)
        fn(pg,c,lambda n: pg.screenshot(path=out+n,timeout=150000))
        print('LOGS:','\n'.join(l for l in logs if 'ERR_FAILED' not in l)[:1500]); b.close()
