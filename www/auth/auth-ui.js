/* VALKOR — Giriş / kayıt / karakter seçimi arayüzü (oyun motorundan bağımsız).
   Kullanım: mountAuth({ root, onEnter({uid,username,character}) }) */
import * as A from './auth-service.js';

const KINGS = [['Kızıl', '#d33'], ['Altın', '#e3b52b'], ['Mavi', '#3a7be0']];
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const EYE = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z"/><circle cx="12" cy="12" r="3"/></svg>';

function pw(id, label, ac, ph) {
  return `<label class="af" for="${id}">${label}</label><div class="pwrap"><input id="${id}" type="password" autocomplete="${ac}" placeholder="${ph || ''}" maxlength="64" autocapitalize="off" spellcheck="false"><button type="button" class="eye" data-eye="${id}" aria-label="Şifreyi göster/gizle">${EYE}</button></div>`;
}
const VIEWS = {
  login: () => `<h2>Giriş Yap</h2>
    <label class="af" for="a_id">Kullanıcı adı veya e-posta</label><input id="a_id" type="text" autocomplete="username" autocapitalize="off" spellcheck="false" maxlength="80">
    ${pw('a_pw', 'Şifre', 'current-password')}
    <label class="rem"><input type="checkbox" id="a_rem" checked><span></span>Beni hatırla</label>
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit">Giriş Yap</button>
    <div class="alinks"><a href="#" data-v="register">Hesap Oluştur</a><a href="#" data-v="forgot">Şifremi Unuttum</a></div>`,
  register: () => `<h2>Hesap Oluştur</h2>
    <label class="af" for="a_user">Kullanıcı adı</label><input id="a_user" type="text" autocomplete="username" autocapitalize="off" spellcheck="false" maxlength="16" placeholder="3-16 karakter, harf/rakam/_">
    <label class="af" for="a_mail">E-posta</label><input id="a_mail" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" maxlength="80">
    ${pw('a_pw', 'Şifre', 'new-password', 'En az 8 karakter, harf + rakam')}
    <div class="meter" id="a_meter"><i></i></div>
    ${pw('a_pw2', 'Şifre (tekrar)', 'new-password')}
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit">Hesap Oluştur</button>
    <div class="alinks"><a href="#" data-v="login">← Girişe dön</a></div>`,
  forgot: () => `<h2>Şifremi Unuttum</h2><p class="asub">Hesabına bağlı e-posta adresini yaz; şifre sıfırlama bağlantısı gönderelim.</p>
    <label class="af" for="a_mail">E-posta</label><input id="a_mail" type="email" inputmode="email" autocomplete="email" autocapitalize="off" spellcheck="false" maxlength="80">
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit">Sıfırlama Bağlantısı Gönder</button>
    <div class="alinks"><a href="#" data-v="login">← Girişe dön</a></div>`,
  pass: () => `<h2>Şifre Değiştir</h2>
    ${pw('a_old', 'Mevcut şifre', 'current-password')}${pw('a_pw', 'Yeni şifre', 'new-password', 'En az 8 karakter, harf + rakam')}${pw('a_pw2', 'Yeni şifre (tekrar)', 'new-password')}
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit">Şifreyi Değiştir</button>
    <div class="alinks"><a href="#" data-v="chars">← Karakterlere dön</a></div>`,
  create: () => `<h2>Karakter Oluştur</h2>
    <label class="af" for="a_cn">Karakter adı</label><input id="a_cn" type="text" autocomplete="off" autocapitalize="words" spellcheck="false" maxlength="14">
    <div class="af">Krallık</div><div class="kings2">${KINGS.map((k, i) => `<label><input type="radio" name="a_king" value="${i}"${i ? '' : ' checked'}><b style="background:${k[1]}"></b>${k[0]}</label>`).join('')}</div>
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit">Karakteri Oluştur</button>
    <div class="alinks" id="a_back"><a href="#" data-v="chars">← Geri</a></div>`
};

export async function mountAuth({ root, onEnter }) {
  let state = { user: null, name: '', chars: [] }, view = 'login', busy = false, booted = false, registering = false;
  root.innerHTML = `<div class="abg"><i class="aimg"></i><i class="avig"></i><div class="aembers">${Array.from({ length: 22 }, (_, i) => `<s style="left:${(i * 47) % 100}%;animation-delay:${-(i * 1.7) % 9}s;animation-duration:${7 + (i * 3) % 6}s;--d:${(i % 5 - 2) * 18}px"></s>`).join('')}</div></div>
  <div class="ascroll"><div class="awrap"><div class="alogo"><h1>VALKOR</h1><p>Efsane seni bekliyor</p></div><form class="acard" id="a_card" novalidate></form><div class="afoot" id="a_foot"></div></div></div>`;
  const card = root.querySelector('#a_card'), foot = root.querySelector('#a_foot');
  const $ = s => card.querySelector(s);
  const msg = (t, ok) => { const m = $('#a_msg'); if (m) { m.textContent = t || ''; m.className = 'amsg' + (ok ? ' ok' : ''); } };
  const setBusy = b => { busy = b; const g = $('#a_go'); if (g) { g.disabled = b; g.classList.toggle('busy', b); } };
  const show = v => { view = v; card.className = 'acard v-' + v; card.innerHTML = VIEWS[v](); wire(); const f = card.querySelector('input:not([type=checkbox]):not([type=radio])'); if (f && !matchMedia('(pointer:coarse)').matches) f.focus(); };

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
      state.chars.push(c); enter(c);
    }
  }
  function enter(c) { root.classList.add('gone'); onEnter({ uid: state.user.uid, username: state.name, character: c }); }

  async function showChars() {
    view = 'chars'; card.className = 'acard v-chars'; card.innerHTML = '<div class="aload">Hesap yükleniyor…</div>';
    try {
      const [p, chars] = await Promise.all([A.profile(state.user.uid), A.listCharacters(state.user.uid)]);
      state.name = (p && p.username) || state.pending || state.user.email; state.chars = chars;
    } catch (err) { card.innerHTML = `<div class="amsg" style="display:block">${esc(A.explain(err))}</div><button class="abtn" type="button" id="a_retry">Tekrar Dene</button><div class="alinks"><a href="#" id="a_out">Çıkış Yap</a></div>`; card.querySelector('#a_retry').onclick = showChars; card.querySelector('#a_out').onclick = e => { e.preventDefault(); out(); }; return; }
    if (!state.chars.length) { show('create'); const b = card.querySelector('#a_back'); if (b) b.innerHTML = '<a href="#" id="a_out">Çıkış Yap</a>'; card.querySelector('#a_out').onclick = e => { e.preventDefault(); out(); }; if (state.notice) { msg(state.notice, true); state.notice = ''; } return; }
    card.innerHTML = `<h2>Karakter Seç</h2><p class="asub">Hoş geldin, <b>${esc(state.name)}</b></p>
      <div class="clist">${state.chars.map((c, i) => `<button type="button" class="cslot" data-c="${i}"><b style="background:${KINGS[c.king | 0][1]}"></b><span>${esc(c.name)}</span><small>${KINGS[c.king | 0][0]} Krallığı</small></button>`).join('')}</div>
      ${state.chars.length < A.MAX_CHARS ? '<button class="abtn ghost" type="button" id="a_new">+ Yeni Karakter</button>' : ''}
      <div class="amsg" id="a_msg"></div>
      <div class="alinks"><a href="#" data-v="pass">Şifre Değiştir</a><a href="#" id="a_out">Çıkış Yap</a></div>`;
    card.querySelectorAll('.cslot').forEach(b => b.onclick = () => enter(state.chars[+b.dataset.c]));
    const nb = card.querySelector('#a_new'); if (nb) nb.onclick = () => { show('create'); };
    card.querySelector('#a_out').onclick = e => { e.preventDefault(); out(); };
    card.querySelector('[data-v=pass]').onclick = e => { e.preventDefault(); show('pass'); };
    card.onsubmit = e => e.preventDefault();
    if (state.notice) { msg(state.notice, true); state.notice = ''; }
  }
  async function out() { try { await A.logout(); } catch (_) {} location.reload(); }
  window.ValkorAuth = { logout: out };

  /* ---- başlangıç ---- */
  foot.textContent = '© Valkor';
  if (!A.isConfigured()) {
    card.className = 'acard v-off';
    card.innerHTML = `<h2>Hesap sistemi kapalı</h2><div class="amsg" style="display:block">Firebase ayarları eksik. <b>auth/firebase-config.js</b> dosyasına proje bilgileri girilmeden giriş yapılamaz ve oyuna girilemez. Kurulum için AUTH-KURULUM.md dosyasına bak.</div>`;
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
