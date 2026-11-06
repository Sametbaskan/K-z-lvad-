/* VALKOR — Giriş / kayıt / karakter seçimi arayüzü (oyun motorundan bağımsız).
   Kullanım: mountAuth({ root, onEnter({uid,username,character}) }) */
import * as A from './auth-service.js';

const CLASSES = [{ id: 'warrior', name: 'Savaşçı', ready: true }, { id: 'ninja', name: 'Ninja' }, { id: 'shaman', name: 'Şaman' }, { id: 'sura', name: 'Sura' }];
const KINGS = [['Kızıl', '#d33'], ['Altın', '#e3b52b'], ['Mavi', '#3a7be0']];
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const EYE = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z"/><circle cx="12" cy="12" r="3"/></svg>';
const IC = {
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="8" r="3.6"/><path d="M4.5 20c.6-4 3.6-6 7.5-6s6.9 2 7.5 6"/></svg>',
  mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="5.5" width="18" height="13" rx="1.5"/><path d="m3.5 7 8.5 6.5L20.5 7"/></svg>',
  lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="5" y="10.5" width="14" height="10" rx="1.5"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/></svg>',
  sword: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M5 19 17 7l2-4 2 2-4 2L5 19zM4 20l2-2M7 17l-3 3"/></svg>'
};
function fld(id, icon, ph, { type = 'text', ac = 'off', max = 80, mode = '', cap = 'off' } = {}) {
  const pwd = type === 'password';
  return `<div class="fld"><div class="fi">${IC[icon]}<input id="${id}" type="${type}" placeholder="${ph}" aria-label="${ph}" autocomplete="${ac}" maxlength="${max}" autocapitalize="${cap}" spellcheck="false"${mode ? ` inputmode="${mode}"` : ''}>${pwd ? `<button type="button" class="eye" data-eye="${id}" aria-label="Şifreyi göster/gizle">${EYE}</button>` : ''}</div></div>`;
}
const B = h => `<div class="abody">${h}</div>`;
const VIEWS = {
  login: () => `<h2><span>Hesap Girişi</span></h2>` + B(`
    ${fld('a_id', 'user', 'Kullanıcı adı veya e-posta', { ac: 'username' })}
    ${fld('a_pw', 'lock', 'Şifre', { type: 'password', ac: 'current-password', max: 64 })}
    <label class="rem"><input type="checkbox" id="a_rem" checked><span></span>Beni hatırla</label>
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Giriş Yap</i></button>`) +
    `<div class="alinks"><a href="#" data-v="register">Hesap Oluştur</a><a href="#" data-v="forgot">Şifremi Unuttum</a></div>`,
  register: () => `<h2><span>Hesap Oluştur</span></h2>` + B(`
    ${fld('a_user', 'user', 'Kullanıcı adı (3-16: harf, rakam, _)', { ac: 'username', max: 16 })}
    ${fld('a_mail', 'mail', 'E-posta', { type: 'email', ac: 'email', mode: 'email' })}
    ${fld('a_pw', 'lock', 'Şifre (8+ karakter, harf + rakam)', { type: 'password', ac: 'new-password', max: 64 })}
    <div class="meter" id="a_meter"><i></i></div>
    ${fld('a_pw2', 'lock', 'Şifre (tekrar)', { type: 'password', ac: 'new-password', max: 64 })}
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Hesap Oluştur</i></button>`) +
    `<div class="alinks"><a href="#" data-v="login">← Girişe dön</a></div>`,
  forgot: () => `<h2><span>Şifremi Unuttum</span></h2>` + B(`<p class="asub">Hesabına bağlı e-posta adresini yaz; şifre sıfırlama bağlantısı gönderelim.</p>
    ${fld('a_mail', 'mail', 'E-posta', { type: 'email', ac: 'email', mode: 'email' })}
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Bağlantı Gönder</i></button>`) +
    `<div class="alinks"><a href="#" data-v="login">← Girişe dön</a></div>`,
  pass: () => `<h2><span>Şifre Değiştir</span></h2>` + B(`
    ${fld('a_old', 'lock', 'Mevcut şifre', { type: 'password', ac: 'current-password', max: 64 })}
    ${fld('a_pw', 'lock', 'Yeni şifre (8+ karakter, harf + rakam)', { type: 'password', ac: 'new-password', max: 64 })}
    ${fld('a_pw2', 'lock', 'Yeni şifre (tekrar)', { type: 'password', ac: 'new-password', max: 64 })}
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Şifreyi Değiştir</i></button>`) +
    `<div class="alinks"><a href="#" data-v="chars">← Karakterlere dön</a></div>`,
  create: () => `<h2><span>Karakter Oluştur</span></h2>` + B(`
    ${fld('a_cn', 'sword', 'Karakter adı', { max: 14, cap: 'words' })}
    <div class="kings2">${KINGS.map((k, i) => `<label><input type="radio" name="a_king" value="${i}"${i ? '' : ' checked'}><b style="background:${k[1]}"></b>${k[0]}</label>`).join('')}</div>
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Karakteri Oluştur</i></button>`) +
    `<div class="alinks" id="a_back"><a href="#" data-v="chars">← Geri</a></div>`
};

/* Ateş kıvılcımları (canvas): yukarı süzülen, titreşen, sönen kor parçacıkları */
function sparks(cv, host) {
  const ctx = cv.getContext('2d'); let W = 0, H = 0, dpr = 1, last = 0, burstT = 2;
  const reduce = matchMedia('(prefers-reduced-motion:reduce)').matches, N = reduce ? 24 : 150;
  const spr = [[255, 240, 190], [255, 170, 60], [255, 80, 30]].map(c => { const s = document.createElement('canvas'); s.width = s.height = 32; const g = s.getContext('2d'), r = g.createRadialGradient(16, 16, 0, 16, 16, 16); r.addColorStop(0, `rgba(${c},1)`); r.addColorStop(.14, `rgba(${c},1)`); r.addColorStop(.4, `rgba(${c},.35)`); r.addColorStop(1, `rgba(${c},0)`); g.fillStyle = r; g.fillRect(0, 0, 32, 32); return s; });
  const size = () => { dpr = Math.min(2, devicePixelRatio || 1); W = cv.clientWidth; H = cv.clientHeight; cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); };
  const P = Array.from({ length: N }, () => ({}));
  const spawn = (p, init, x, boost) => { p.x = x != null ? x + (Math.random() - .5) * 40 : Math.random() * W; p.y = init ? Math.random() * H : H + 8; p.vy = -(35 + Math.random() * 95) * (boost || 1); p.vx = (Math.random() - .5) * 20; p.r = .9 + Math.random() * 3; p.t = 0; p.max = 3 + Math.random() * 5; p.ph = Math.random() * 6.28; p.sw = 8 + Math.random() * 28; p.c = Math.random() < .25 ? 0 : Math.random() < .6 ? 1 : 2; };
  size(); P.forEach(p => spawn(p, true)); addEventListener('resize', size);
  function frame(t) {
    requestAnimationFrame(frame);
    if (host.classList.contains('gone') || host.classList.contains('pre') || document.hidden) { last = t; return; }
    const dt = Math.min(.05, (t - last) / 1000 || .016); last = t; if (!W) size();
    ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter';
    burstT -= dt; if (burstT <= 0 && !reduce) { burstT = 2.5 + Math.random() * 3; const bx = Math.random() * W; let k = 0; for (const p of P) { if (p.t > p.max * .6 && k < 14) { spawn(p, false, bx, 1.5); k++; } } }
    for (const p of P) {
      p.t += dt; if (p.t > p.max || p.y < -20) { spawn(p, false); continue; }
      p.x += (p.vx + Math.sin(p.t * 2 + p.ph) * p.sw) * dt; p.y += p.vy * dt; p.vy *= 1 - .06 * dt;
      const a = Math.sin(Math.PI * p.t / p.max) * (.65 + .35 * Math.sin(p.t * 17 + p.ph));
      ctx.globalAlpha = Math.max(0, a); const s = p.r * 5.5; ctx.drawImage(spr[p.c], p.x - s / 2, p.y - s / 2, s, s);
    }
    ctx.globalAlpha = 1;
  }
  requestAnimationFrame(frame);
}

export async function mountAuth({ root, onEnter, preview = () => {}, info = () => ({ lvl: 1, guild: '' }), purge = () => {} }) {
  let state = { user: null, name: '', chars: [], ci: 0 }, view = 'login', busy = false, booted = false, registering = false;
  root.innerHTML = `<div class="abg"><i class="aimg"></i><i class="aglow"></i><i class="avig"></i><canvas class="asp"></canvas></div>
  <div class="ascroll"><div class="awrap"><div class="alogo"><svg class="awing l" viewBox="0 0 200 70" aria-hidden="true"><defs><linearGradient id="wg" x1="0" x2="1"><stop offset="0" stop-color="#7a4a12"/><stop offset=".5" stop-color="#f3cf7a"/><stop offset="1" stop-color="#fff0b8"/></linearGradient></defs><path d="M200 36C150 22 90 14 6 24c46 2 86 8 130 18-40-2-84 0-122 14 52-8 100-6 150 2-30 0-66 4-96 12 60-10 100-6 132 4z" fill="url(#wg)" opacity=".95"/></svg><div class="alogo-c"><i class="asun"></i><h1>VALKOR</h1><p>Efsane seni bekliyor</p></div><svg class="awing r" viewBox="0 0 200 70" aria-hidden="true"><path d="M200 36C150 22 90 14 6 24c46 2 86 8 130 18-40-2-84 0-122 14 52-8 100-6 150 2-30 0-66 4-96 12 60-10 100-6 132 4z" fill="url(#wg)" opacity=".95"/></svg></div><form class="acard" id="a_card" novalidate></form><div class="afoot" id="a_foot"></div></div></div>
  <div class="csel" id="c_sel"><div class="cbar top"><span class="cbrand">VALKOR</span><button class="cx" id="c_x" type="button" aria-label="Çıkış yap">✕</button></div>
    <div class="cpanel"><dl id="c_rows"></dl><div class="cnote" id="c_note"></div><div class="cbtns"><button type="button" class="cbtn" id="c_ok">Seç</button><button type="button" class="cbtn sm" id="c_del">Sil</button></div></div><div class="amsg" id="c_msg" role="alert"></div>
    <button class="carr l" id="c_l" type="button" aria-label="Önceki sınıf"><svg viewBox="0 0 64 40"><path d="M2 20 30 2l-5 18 5 18z" fill="currentColor"/><path d="M34 20 62 8v24z" fill="currentColor" opacity=".0"/></svg></button><button class="carr r" id="c_r" type="button" aria-label="Sonraki sınıf"><svg viewBox="0 0 64 40"><path d="M2 20 30 2l-5 18 5 18z" fill="currentColor"/><path d="M34 20 62 8v24z" fill="currentColor" opacity=".0"/></svg></button>
    <div class="ccls"><h3 id="c_cls"></h3><p id="c_sub"></p><div class="cdots" id="c_dots"></div></div>
    <div class="cbar bot"><span id="c_acct"></span><a href="#" id="c_pw">Şifre Değiştir</a></div>
    <div class="cmodal" id="c_modal"><div class="cm"><h4>Karakteri Sil</h4><p id="c_mt"></p><input id="c_mi" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Karakter adı"><div class="amsg" id="c_mm"></div><div class="cmb"><button type="button" class="cbtn sm" id="c_mc">Vazgeç</button><button type="button" class="cbtn sm danger" id="c_md">Sil</button></div></div></div></div>`;
  sparks(root.querySelector('.asp'), root);
  const card = root.querySelector('#a_card'), foot = root.querySelector('#a_foot');
  const $ = s => card.querySelector(s);
  const msg = (t, ok) => { const m = $('#a_msg'); if (m) { m.textContent = t || ''; m.className = 'amsg' + (ok ? ' ok' : ''); } };
  const setBusy = b => { busy = b; const g = $('#a_go'); if (g) { g.disabled = b; g.classList.toggle('busy', b); } };
  const show = v => { setSel(false); view = v; card.className = 'acard v-' + v; card.innerHTML = VIEWS[v](); wire(); const f = card.querySelector('input:not([type=checkbox]):not([type=radio])'); if (f && !matchMedia('(pointer:coarse)').matches) f.focus(); };

  function wire() {
    card.querySelectorAll('[data-v]').forEach(a => a.onclick = e => { e.preventDefault(); if (busy) return; if (a.dataset.v === 'chars') showChars(); else show(a.dataset.v); });
    card.querySelectorAll('[data-eye]').forEach(b => b.onclick = () => { const i = card.querySelector('#' + b.dataset.eye); i.type = i.type === 'password' ? 'text' : 'password'; b.classList.toggle('on', i.type === 'text'); });
    card.querySelectorAll('input').forEach(i => i.addEventListener('focus', () => setTimeout(() => i.scrollIntoView({ block: 'center', behavior: 'smooth' }), 320)));
    const pw1 = $('#a_pw'), meter = $('#a_meter');
    if (view === 'register' && pw1) pw1.addEventListener('input', () => { const v = pw1.value; let s = 0; if (v.length >= 8) s++; if (/[A-Za-z]/.test(v) && /\d/.test(v)) s++; if (v.length >= 12 && /[^A-Za-z0-9]/.test(v)) s++; meter.dataset.s = v ? s : 0; });
    card.onsubmit = async e => { e.preventDefault(); if (busy) return; msg(''); setBusy(true); try { await submit(); } catch (err) { msg(A.explain(err)); } setBusy(false); };
  }
  async function submit() {
    const v = id => ($('#' + id) || {}).value || '';
    if (view === 'login') await A.login({ id: v('a_id'), password: v('a_pw'), remember: $('#a_rem').checked });   // başarılıysa onUser tetiklenir
    else if (view === 'register') {
      registering = true;
      try { const r = await A.register({ username: v('a_user'), email: v('a_mail'), password: v('a_pw'), password2: v('a_pw2') });
        state.user = A.currentUser(); state.pending = r.username; state.notice = 'Hesabın oluşturuldu! Doğrulama e-postası gönderildi. Şimdi ilk karakterini yarat.'; }
      finally { registering = false; }
      await showChars();
    } else if (view === 'forgot') { await A.resetPassword(v('a_mail')); msg('Eğer bu e-posta kayıtlıysa sıfırlama bağlantısı gönderildi. Gelen kutunu (ve spam klasörünü) kontrol et.', true); }
    else if (view === 'pass') { await A.changePassword(v('a_old'), v('a_pw'), v('a_pw2')); msg('Şifren başarıyla değiştirildi.', true); ['a_old', 'a_pw', 'a_pw2'].forEach(i => $('#' + i).value = ''); }
    else if (view === 'create') {
      const c = await A.createCharacter(state.user.uid, { name: v('a_cn'), king: (card.querySelector('input[name=a_king]:checked') || {}).value });
      state.chars.push(c); state.notice = 'Karakter oluşturuldu. Şimdi “Seç” ile oyuna girebilirsin.'; await showChars();
    }
  }
  function enter(c) { root.classList.add('gone'); onEnter({ uid: state.user.uid, username: state.name, character: c }); }

  const sel = root.querySelector('#c_sel'), S$ = id => sel.querySelector('#' + id);
  function setSel(on) { root.classList.toggle('sel', on); if (!on) preview(false, false); }
  const chOf = cls => cls.ready ? (state.chars.find(c => (c.cls || 'warrior') === cls.id) || null) : null;
  function renderSel() {
    const cls = CLASSES[state.ci], ch = chOf(cls), inf = ch ? info(ch, state.user.uid) : null;
    preview(true, cls.ready);
    S$('c_cls').textContent = cls.name; S$('c_sub').textContent = !cls.ready ? 'Yakında' : ch ? ch.name : 'Karakter oluşturulmadı';
    S$('c_rows').innerHTML = [['İsim', ch ? esc(ch.name) : '—'], ['Seviye', inf ? inf.lvl : '—'], ['Lonca', inf ? esc(inf.guild || 'Yok') : '—'], ['Krallık', ch ? `<b class="kdot" style="background:${KINGS[ch.king | 0][1]}"></b>${KINGS[ch.king | 0][0]}` : '—'], ['Sınıf', cls.name]].map(r => `<div><dt>${r[0]}</dt><dd>${r[1]}</dd></div>`).join('');
    S$('c_note').textContent = !cls.ready ? 'Bu sınıf henüz oyuna eklenmedi.' : '';
    const ok = S$('c_ok'), del = S$('c_del'); ok.textContent = ch ? 'Seç' : 'Oluştur'; ok.disabled = !cls.ready; del.disabled = !ch;
    S$('c_dots').innerHTML = CLASSES.map((c, i) => `<i class="${i === state.ci ? 'on' : ''}${c.ready ? '' : ' lk'}"></i>`).join('');
    S$('c_acct').textContent = 'Hesap: ' + state.name; S$('c_msg').textContent = '';
    if (state.notice) { const m = S$('c_msg'); m.textContent = state.notice; m.className = 'amsg ok'; state.notice = ''; }
  }
  const cyc = d => { state.ci = (state.ci + d + CLASSES.length) % CLASSES.length; renderSel(); };
  S$('c_l').onclick = () => cyc(-1); S$('c_r').onclick = () => cyc(1);
  S$('c_ok').onclick = () => { const cls = CLASSES[state.ci]; if (!cls.ready) return; const ch = chOf(cls); if (ch) enter(ch); else { show('create'); const b = card.querySelector('#a_back'); if (b) b.innerHTML = '<a href="#" data-v="chars">← Geri</a>'; wire(); } };
  S$('c_x').onclick = () => out();
  S$('c_pw').onclick = e => { e.preventDefault(); show('pass'); };
  const modal = S$('c_modal');
  S$('c_del').onclick = () => { const ch = chOf(CLASSES[state.ci]); if (!ch) return; S$('c_mt').innerHTML = `Silmek için karakter adını yaz: <b>${esc(ch.name)}</b>. Bu işlem geri alınamaz.`; S$('c_mi').value = ''; S$('c_mm').textContent = ''; modal.classList.add('on'); };
  S$('c_mc').onclick = () => modal.classList.remove('on');
  S$('c_md').onclick = async () => { const ch = chOf(CLASSES[state.ci]); if (!ch) return; if (S$('c_mi').value.trim().toLowerCase() !== ch.name.toLowerCase()) { S$('c_mm').textContent = 'Karakter adı eşleşmiyor.'; return; } S$('c_md').disabled = true; try { await A.deleteCharacter(state.user.uid, ch); purge(ch, state.user.uid); state.chars = state.chars.filter(c => c.id !== ch.id); modal.classList.remove('on'); renderSel(); const m = S$('c_msg'); m.textContent = 'Karakter silindi.'; m.className = 'amsg ok'; } catch (err) { S$('c_mm').textContent = A.explain(err); } S$('c_md').disabled = false; };

  async function showChars() {
    setSel(false); view = 'chars'; card.className = 'acard v-chars'; card.innerHTML = '<div class="aload">Hesap yükleniyor…</div>';
    try {
      const [p, chars] = await Promise.all([A.profile(state.user.uid), A.listCharacters(state.user.uid)]);
      state.name = (p && p.username) || state.pending || state.user.email; state.chars = chars;
    } catch (err) { card.innerHTML = `<div class="abody"><div class="amsg" style="display:block">${esc(A.explain(err))}</div><button class="abtn" type="button" id="a_retry"><i>Tekrar Dene</i></button></div><div class="alinks"><a href="#" id="a_out">Çıkış Yap</a></div>`; card.querySelector('#a_retry').onclick = showChars; card.querySelector('#a_out').onclick = e => { e.preventDefault(); out(); }; return; }
    if (!state.chars.length) { show('create'); const b = card.querySelector('#a_back'); if (b) b.innerHTML = '<a href="#" id="a_out">Çıkış Yap</a>'; card.querySelector('#a_out').onclick = e => { e.preventDefault(); out(); }; if (state.notice) { msg(state.notice, true); state.notice = ''; } return; }
    state.ci = 0; setSel(true); renderSel();
  }
  async function out() { try { await A.logout(); } catch (_) {} location.reload(); }
  window.ValkorAuth = { logout: out };

  /* ---- başlangıç ---- */
  foot.textContent = '© Valkor';
  if (!A.isConfigured()) {
    card.className = 'acard v-off';
    card.innerHTML = `<h2><span>Hesap sistemi kapalı</span></h2><div class="abody"><div class="amsg" style="display:block">Firebase ayarları eksik. <b>auth/firebase-config.js</b> dosyasına proje bilgileri girilmeden giriş yapılamaz ve oyuna girilemez. Kurulum için AUTH-KURULUM.md dosyasına bak.</div></div>`;
    return;
  }
  card.innerHTML = '<div class="aload">Bağlanılıyor…</div>';
  try { await A.init(); } catch (err) { card.innerHTML = `<div class="amsg" style="display:block">${esc(A.explain(err))}</div><button class="abtn" type="button" onclick="location.reload()">Tekrar Dene</button>`; return; }
  A.onUser(async u => {
    if (registering) return;
    if (u) { if (state.user && state.user.uid === u.uid && view !== 'login' && view !== 'register') return; state.user = u; await showChars(); }
    else { state.user = null; if (!booted || view === 'chars' || view === 'create' || view === 'pass') show('login'); }
    booted = true;
  });
}
