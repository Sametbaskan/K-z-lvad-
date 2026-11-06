import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/tools')
from auth_test import *
def t(pg,c,shot):
    pg.click('[data-v=register]'); pg.fill('#a_user','Sel_2'); pg.fill('#a_mail','s2@s.com'); pg.fill('#a_pw','abc12345'); pg.fill('#a_pw2','abc12345'); pg.click('#a_go')
    pg.wait_for_selector('#a_cn',timeout=8000); print('1 first-time -> create view')
    pg.fill('#a_cn','Bora'); pg.click('#a_go'); pg.wait_for_selector('#c_sel .cpanel',state='visible',timeout=8000); pg.wait_for_timeout(2000); shot('v4_sel.png'); print('2 sel:',pg.inner_text('#c_name'),pg.inner_text('#c_king'),pg.inner_text('#c_pt'))
    pg.reload(); pg.wait_for_selector('#c_sel .cpanel',state='visible',timeout=120000); print('3 session kept after reload ->',pg.inner_text('#c_cls'))
    pg.click('#c_del'); pg.fill('#c_mi','bora'); pg.click('#c_md'); pg.wait_for_selector('#a_cn',timeout=1) if False else pg.wait_for_timeout(500); print('4 deleted msg:',pg.inner_text('#c_msg'),'| ok btn:',pg.inner_text('#c_ok'))
    pg.click('#c_ok'); pg.wait_for_selector('#a_cn',timeout=5000); pg.fill('#a_cn','Bora'); pg.click('#a_go'); pg.wait_for_selector('#c_sel .cpanel',state='visible',timeout=8000); print('5 same name reusable after delete')
    pg.click('#c_ok'); pg.wait_for_function('document.getElementById("auth").classList.contains("gone")',timeout=20000); pg.wait_for_function('document.getElementById("meName").textContent!=="Savaşçı"',timeout=20000); print('6 in game, name:',pg.evaluate('document.getElementById("meName").textContent'),'hero visible:',pg.evaluate('window.__game&&1'))
session(t,W=900,H=420)
