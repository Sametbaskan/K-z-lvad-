import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/tools')
from auth_test import *
def t(pg,c,shot):
    pg.click('[data-v=register]'); pg.fill('#a_user','Sel_1'); pg.fill('#a_mail','s@s.com'); pg.fill('#a_pw','abc12345'); pg.fill('#a_pw2','abc12345'); pg.click('#a_go')
    pg.wait_for_selector('#a_cn',timeout=8000); pg.fill('#a_cn','Kaan'); pg.click('#a_go'); pg.wait_for_selector('#c_sel .cpanel',state='visible',timeout=8000); pg.wait_for_timeout(2500)
    print('sel shown; msg:',pg.inner_text('#c_msg')); shot('v3_sel.png')
    pg.click('#c_r'); pg.wait_for_timeout(600); print('class:',pg.inner_text('#c_cls'),'| ok disabled:',pg.evaluate('document.getElementById("c_ok").disabled')); shot('v3_locked.png')
    pg.click('#c_r'); pg.click('#c_r'); pg.click('#c_r'); pg.wait_for_timeout(400); print('back to:',pg.inner_text('#c_cls'))
    pg.click('#c_del'); pg.fill('#c_mi','xx'); pg.click('#c_md'); print('del mismatch:',pg.inner_text('#c_mm')); shot('v3_del.png')
    pg.click('#c_mc'); pg.click('#c_ok'); pg.wait_for_function('document.getElementById("auth").classList.contains("gone")',timeout=20000); pg.wait_for_timeout(1500)
    print('entered game; hero visible:',pg.evaluate('1'))
session(t,W=900,H=420)
