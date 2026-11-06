import sys; sys.path.insert(0,'/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/tools')
from auth_test import *
def t(pg,c,shot):
    txt=lambda: pg.inner_text('#a_card')
    print('1 view:',pg.inner_text('#a_card h2')); shot('au_login.png')
    # boş giriş
    pg.click('#a_go'); print('2 empty:',pg.inner_text('#a_msg'))
    # olmayan kullanıcı
    pg.fill('#a_id','nobody'); pg.fill('#a_pw','abc12345'); pg.click('#a_go'); pg.wait_for_timeout(300); print('3 nouser:',pg.inner_text('#a_msg'))
    # kayıt
    pg.click('[data-v=register]'); shot('au_reg.png')
    pg.fill('#a_user','ab'); pg.fill('#a_mail','x@y.com'); pg.fill('#a_pw','abc12345'); pg.fill('#a_pw2','abc12345'); pg.click('#a_go'); print('4 shortuser:',pg.inner_text('#a_msg'))
    pg.fill('#a_user','Samet_1'); pg.fill('#a_mail','bad'); pg.click('#a_go'); print('5 bademail:',pg.inner_text('#a_msg'))
    pg.fill('#a_mail','samet@test.com'); pg.fill('#a_pw','abcdefgh'); pg.fill('#a_pw2','abcdefgh'); pg.click('#a_go'); print('6 weak:',pg.inner_text('#a_msg'))
    pg.fill('#a_pw','abc12345'); pg.fill('#a_pw2','abc12346'); pg.click('#a_go'); print('7 mismatch:',pg.inner_text('#a_msg'))
    pg.fill('#a_pw2','abc12345'); pg.click('#a_go'); pg.wait_for_selector('#a_cn',timeout=5000); print('8 reg ok ->',pg.inner_text('#a_card h2'),'|',pg.inner_text('#a_msg')); shot('au_create.png')
    # karakter oluştur
    pg.fill('#a_cn','x'); pg.click('#a_go'); print('9 badchar:',pg.inner_text('#a_msg'))
    pg.fill('#a_cn','Kaan'); pg.click('input[name=a_king][value="1"]',force=True); pg.click('#a_go')
    pg.wait_for_function('window.__game && document.getElementById("auth").classList.contains("gone")',timeout=20000); pg.wait_for_timeout(800)
    print('10 in game; hud hidden?',pg.evaluate('document.getElementById("hud").classList.contains("hidden")'),'name',pg.evaluate('document.getElementById("meName").textContent'))
    shot('au_game.png')
    # yenile → oturum korunmalı
    pg.reload(); pg.wait_for_selector('#a_card .clist',timeout=90000); print('11 after reload:',pg.inner_text('#a_card h2'),'|',pg.inner_text('.cslot')); shot('au_chars.png')
    # ikinci hesap: aynı e-posta / aynı kullanıcı adı
    pg.click('#a_out',no_wait_after=True); pg.wait_for_selector('#a_id',timeout=90000)
    pg.click('[data-v=register]'); pg.fill('#a_user','Baska'); pg.fill('#a_mail','SAMET@test.com'); pg.fill('#a_pw','abc12345'); pg.fill('#a_pw2','abc12345'); pg.click('#a_go'); pg.wait_for_timeout(400); print('12 dup email:',pg.inner_text('#a_msg'))
    pg.fill('#a_user','samet_1'); pg.fill('#a_mail','b@b.com'); pg.click('#a_go'); pg.wait_for_timeout(400); print('13 dup user:',pg.inner_text('#a_msg'))
    # giriş: yanlış şifre / kullanıcı adı ile / e-posta ile
    pg.click('[data-v=login]'); pg.fill('#a_id','samet_1'); pg.fill('#a_pw','wrongpass1'); pg.click('#a_go'); pg.wait_for_timeout(400); print('14 wrongpw:',pg.inner_text('#a_msg'))
    pg.fill('#a_pw','abc12345'); pg.click('#a_go'); pg.wait_for_selector('.cslot',timeout=5000); print('15 login by username ->',pg.inner_text('#a_card h2'))
    # şifre değiştir
    pg.click('[data-v=pass]'); pg.fill('#a_old','nope1234'); pg.fill('#a_pw','newpass99'); pg.fill('#a_pw2','newpass99'); pg.click('#a_go'); pg.wait_for_timeout(300); print('16 changepw wrongold:',pg.inner_text('#a_msg'))
    pg.fill('#a_old','abc12345'); pg.click('#a_go'); pg.wait_for_timeout(300); print('17 changepw ok:',pg.inner_text('#a_msg'))
    pg.click('[data-v=chars]'); pg.wait_for_selector('.cslot'); pg.click('#a_out',no_wait_after=True); pg.wait_for_selector('#a_id',timeout=90000)
    pg.fill('#a_id','samet@test.com'); pg.fill('#a_pw','abc12345'); pg.click('#a_go'); pg.wait_for_timeout(400); print('18 old pw rejected:',pg.inner_text('#a_msg'))
    pg.fill('#a_pw','newpass99'); pg.uncheck('#a_rem',force=True); pg.click('#a_go'); pg.wait_for_selector('.cslot',timeout=5000); print('19 login by email w/ new pw OK')
    # forgot
    pg.click('#a_out',no_wait_after=True); pg.wait_for_selector('#a_id',timeout=90000); pg.click('[data-v=forgot]'); pg.fill('#a_mail','samet@test.com'); pg.click('#a_go'); pg.wait_for_timeout(300); print('20 forgot:',pg.inner_text('#a_msg')); print('   mail log:',pg.evaluate('localStorage.getItem("__mock_mail")'))
session(t)
