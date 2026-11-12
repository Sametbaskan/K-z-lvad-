import sys, json, re, os
from playwright.sync_api import sync_playwright
REPO='/home/claude/mrdoob/three.js/'
S='/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/'
os.makedirs(S+'savout',exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    pg=b.new_page(); pg.on('pageerror',lambda e:print('ERR',e)); pg.on('console',lambda m: print('LOG',m.text[:300]) if m.type in('error',) else 0)
    def route(r):
        u=r.request.url; m=re.match(r'https://cdn\.jsdelivr\.net/npm/three@0\.160\.0/(.*)',u)
        if m and os.path.exists(REPO+m.group(1)): return r.fulfill(path=REPO+m.group(1),content_type='text/javascript',headers={'access-control-allow-origin':'*'})
        return r.continue_() if 'localhost' in u else r.abort()
    pg.route('**/*',route); pg.goto('http://localhost:8123/nin_x.html'); pg.wait_for_timeout(1500)
    res=pg.evaluate("window.run().then(r=>JSON.stringify(r))")
    open(S+'savout/nin_raw.json','w').write(res); d=json.loads(res)
    print('\n'.join(d['log'])); print('bones',len(d['bones']),'size KB',len(res)//1024,[ (q['n'],len(q['pos'])//3) for q in d['parts']],d['meta'],'h',d['h'])
    b.close()
