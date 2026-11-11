import re,os,json
from playwright.sync_api import sync_playwright
REPO='/home/claude/mrdoob/three.js/'
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg=b.new_page()
    pg.on('pageerror',lambda e:print('PE',e))
    def route(r):
        u=r.request.url; m=re.match(r'https://cdn\.jsdelivr\.net/npm/three@0\.160\.0/(.*)',u)
        if m and os.path.exists(REPO+m.group(1)): return r.fulfill(path=REPO+m.group(1),content_type='text/javascript',headers={'access-control-allow-origin':'*'})
        if 'localhost' in u: return r.continue_()
        return r.abort()
    pg.route('**/*',route); pg.goto('http://localhost:8123/kqx.html'); pg.wait_for_function('window.DONE',timeout=100000)
    json.dump(pg.evaluate('window.OUT'),open('kq_src.json','w')); b.close()
