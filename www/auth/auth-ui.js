/* VALKOR — Giriş / kayıt / karakter seçimi arayüzü (oyun motorundan bağımsız).
   Kullanım: mountAuth({ root, onEnter({uid,username,character}) }) */
import * as A from './auth-service.js';

const CLASSES = [{ id: 'warrior', name: 'Savaşçı', ready: true }, { id: 'ninja', name: 'Ninja' }, { id: 'shaman', name: 'Şaman' }, { id: 'sura', name: 'Sura' }];
const HM = () => window.__heroModels || null;
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
    <div class="arow"><label class="rem"><input type="checkbox" id="a_rem" checked><span></span>Beni hatırla</label><a href="#" class="chip" data-v="forgot">Şifremi Unuttum</a></div>
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Giriş Yap</i></button>`) +
    `<div class="alinks one"><a href="#" data-v="register">Hesap Oluştur</a></div>`,
  register: () => `<h2><span>Hesap Oluştur</span></h2>` + B(`
    ${fld('a_user', 'user', 'Kullanıcı adı (3-16)', { ac: 'username', max: 16 })}
    ${fld('a_mail', 'mail', 'E-posta', { type: 'email', ac: 'email', mode: 'email' })}
    ${fld('a_pw', 'lock', 'Şifre (8+, harf+rakam)', { type: 'password', ac: 'new-password', max: 64 })}
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
    ${fld('a_pw', 'lock', 'Yeni şifre (8+, harf+rakam)', { type: 'password', ac: 'new-password', max: 64 })}
    ${fld('a_pw2', 'lock', 'Yeni şifre (tekrar)', { type: 'password', ac: 'new-password', max: 64 })}
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Şifreyi Değiştir</i></button>`) +
    `<div class="alinks"><a href="#" data-v="chars">← Karakterlere dön</a></div>`,
  create: () => `<h2><span>Karakter Oluştur</span></h2>` + B(`
    ${fld('a_cn', 'sword', 'Karakter adı', { max: 14, cap: 'words' })}
    <div class="kings2">${KINGS.map((k, i) => `<label><input type="radio" name="a_king" value="${i}"${i ? '' : ' checked'}><b style="background:${k[1]}"></b>${k[0]}</label>`).join('')}</div>
    ${HM() ? `<div class="mlab">Karakter modeli</div><div class="models">${HM().list.map(m => `<label${m[2] ? ' class="soon"' : ''}><input type="radio" name="a_model" value="${m[0]}"${m[2] ? ' disabled' : m[0] === HM().cur() ? ' checked' : ''}>${m[1]}${m[2] ? '<small>yakında</small>' : ''}</label>`).join('')}</div>` : ''}
    <div class="amsg" id="a_msg" role="alert"></div>
    <button class="abtn" id="a_go" type="submit"><i>Karakteri Oluştur</i></button>`) +
    `<div class="alinks" id="a_back"><a href="#" data-v="chars">← Geri</a></div>`
};


export async function mountAuth({ root, onEnter, preview = () => {}, info = () => ({ lvl: 1, guild: '' }), purge = () => {} }) {
  let state = { user: null, name: '', chars: [], ci: 0 }, view = 'login', busy = false, booted = false, registering = false;
  root.innerHTML = `<div class="abg"><i class="aimg"></i><i class="avig"></i></div>
  <div class="ascroll"><div class="awrap"><div class="abanner"><div class="alogo"><div class="alogo-c"><svg class="aemb" viewBox="0 0 120 64" aria-hidden="true"><defs><linearGradient id="aeg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfc9bb"/><stop offset="1" stop-color="#5f5a50"/></linearGradient></defs><path fill="url(#aeg)" d="M60 0l3.2 9v27h-6.4V9zM44 34h32l-3 5H47zM58 39h4v18l-2 6-2-6z"/><path fill="url(#aeg)" opacity=".85" d="M56 30C44 30 30 24 18 10c4 16 18 28 38 28zM64 30c12 0 26-6 38-20-4 16-18 28-38 28z"/></svg><h1>VALKOR</h1><p>Efsane seni bekliyor</p></div></div><form class="acard" id="a_card" novalidate></form><div class="afoot" id="a_foot"></div></div></div></div>
  <div class="csel" id="c_sel"><div class="cbrand">VALKOR</div>
    <div class="ccls"><h3 id="c_cls"></h3><p id="c_sub"></p></div>
    <div class="cnav"><button class="carr" id="c_l" type="button" aria-label="Önceki karakter"><svg viewBox="0 0 10 16"><path d="M9 1 2 8l7 7" /></svg></button><div class="cdots" id="c_dots"></div><button class="carr" id="c_r" type="button" aria-label="Sonraki karakter"><svg viewBox="0 0 10 16"><path d="M1 1l7 7-7 7" /></svg></button></div>
    <div class="cpanel"><div class="ckr"><div class="cflag" id="c_flag"></div><div class="cstk"><div class="cbox" id="c_king"></div><div class="cbox" id="c_guild"></div></div></div>
      <div class="crow"><label>İsim</label><div class="cbox" id="c_name"></div></div><div class="crow"><label>Seviye</label><div class="cbox" id="c_lvl"></div></div><div class="crow"><label>Oyun Süresi (dak.)</label><div class="cbox" id="c_pt"></div></div>
      <div class="cstat"><label>HP</label><div class="ctr"><i class="hp" id="c_hp_b"></i></div><div class="cbox" id="c_hp"></div></div><div class="cstat"><label>SP</label><div class="ctr"><i class="sp" id="c_sp_b"></i></div><div class="cbox" id="c_sp"></div></div><div class="cstat"><label>STR</label><div class="ctr"><i class="st" id="c_st_b"></i></div><div class="cbox" id="c_st"></div></div><div class="cstat"><label>DEX</label><div class="ctr"><i class="dx" id="c_dx_b"></i></div><div class="cbox" id="c_dx"></div></div>
      <button type="button" class="cbtn wide" id="c_ok">Başla</button><div class="cbtns2"><button type="button" class="cbtn" id="c_del">Sil</button><button type="button" class="cbtn" id="c_x">Çıkış</button></div></div>
    <div class="amsg" id="c_msg" role="alert"></div>
    <div class="cfoot"><span id="c_acct"></span><a href="#" id="c_pw">Şifre Değiştir</a></div>
    <div class="cmodal" id="c_modal"><div class="cm"><h4>Karakteri Sil</h4><p id="c_mt"></p><input id="c_mi" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Karakter adı"><div class="amsg" id="c_mm"></div><div class="cmb"><button type="button" class="cbtn" id="c_mc">Vazgeç</button><button type="button" class="cbtn danger" id="c_md">Sil</button></div></div></div></div>`;
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
      state.chars.push(c); state.keep = state.chars.length - 1; state.notice = 'Karakter oluşturuldu. “Başla” ile oyuna girebilirsin.';
      const h = HM(), pick = (card.querySelector('input[name=a_model]:checked') || {}).value;
      if (h && pick) { h.set(c.id, pick); if (pick !== h.cur()) { h.apply(pick); h.flag('keepch', c.id); location.reload(); return; } }   // model oyun açılırken yüklenir: yenile, yeni karakter seçili gelsin
      await showChars();
    }
  }
  function enter(c) { const h = HM(), m = h && h.of(c.id); if (m && m !== h.cur()) { h.apply(m); h.flag('autoch', c.id); location.reload(); return; }   // karakterin modeli farklı: modeli yükleyip otomatik gir
    root.classList.add('gone'); onEnter({ uid: state.user.uid, username: state.name, character: c }); }

  const sel = root.querySelector('#c_sel'), S$ = id => sel.querySelector('#' + id);
  function setSel(on) { root.classList.toggle('sel', on); if (!on) preview(false, false); }
  const MAX = A.MAX_CHARS || 4;
  const slots = () => state.chars.slice(0, MAX).concat(state.chars.length < MAX ? [null] : []);   // hesap başına en fazla 4 karakter + (yer varsa) “yeni karakter” yuvası
  const curCh = () => slots()[state.ci] || null;
  const FLAG = i => { const c = KINGS[i][1]; return `<svg viewBox="0 0 80 34" preserveAspectRatio="none"><rect width="80" height="34" fill="#0b1018"/><path d="M0 34 22 6l14 14 12-12 32 26z" fill="${c}" opacity=".35"/><path d="M40 5l8 8-8 16-8-16z" fill="${c}"/><path d="M40 9l4 4-4 9-4-9z" fill="#fff" opacity=".55"/></svg>`; };
  function renderSel() {
    const ch = curCh(), cls = CLASSES[0], inf = ch ? info(ch, state.user.uid) : null, K = ch ? KINGS[ch.king | 0] : null;
    preview(true, cls.ready, ch, state.user.uid);
    S$('c_cls').textContent = ch ? ch.name : 'Yeni Karakter'; S$('c_sub').textContent = ch ? (HM() ? (HM().label(HM().of(ch.id) || HM().cur()) + ' · ') : cls.name + ' · ') + (KINGS[ch.king | 0] || KINGS[0])[0] + ' Krallığı' : 'Boş yuva — yeni bir kahraman yarat';
    S$('c_flag').innerHTML = ch ? FLAG(ch.king | 0) : ''; S$('c_king').textContent = ch ? K[0] + ' Krallığı' : '—'; S$('c_guild').textContent = ch ? (inf.guild || 'Lonca yok') : '—';
    S$('c_name').textContent = ch ? ch.name : '—'; S$('c_lvl').textContent = inf ? inf.lvl : '—'; S$('c_pt').textContent = inf ? inf.min : '—';
    [['hp', 'vit'], ['sp', 'int'], ['st', 'st'], ['dx', 'dex']].forEach(([id, k]) => { const v = inf ? inf[k] : 0; S$('c_' + id).textContent = inf ? v : '—'; S$('c_' + id + '_b').style.width = inf ? Math.max(4, Math.min(100, v / inf.cap * 100)) + '%' : '0'; });
    const ok = S$('c_ok'), del = S$('c_del'); ok.textContent = ch ? 'Başla' : 'Oluştur'; ok.disabled = false; del.disabled = !ch;
    S$('c_dots').innerHTML = Array.from({ length: MAX }, (_, i) => { const c = state.chars[i], inf2 = c ? info(c, state.user.uid) : null; return `<button type="button" class="cslot${i === state.ci ? ' on' : ''}${c ? '' : (i === state.chars.length ? ' add' : ' lk')}" data-i="${i}" ${c || i === state.chars.length ? '' : 'disabled'}><b>${c ? esc(c.name) : (i === state.chars.length ? '+ Yeni' : 'Boş')}</b><u>${c ? 'Sv. ' + inf2.lvl : (i + 1)}</u></button>`; }).join('');
    S$('c_dots').querySelectorAll('.cslot').forEach(b => b.onclick = () => { if (b.disabled) return; state.ci = +b.dataset.i; renderSel(); });
    S$('c_acct').textContent = 'Hesap: ' + state.name; S$('c_msg').textContent = ''; S$('c_msg').className = 'amsg';
    if (state.notice) { const m = S$('c_msg'); m.textContent = state.notice; m.className = 'amsg ok'; state.notice = ''; }
  }
  const cyc = d => { const n = slots().length; state.ci = (state.ci + d + n) % n; renderSel(); };
  S$('c_l').onclick = () => cyc(-1); S$('c_r').onclick = () => cyc(1);
  S$('c_ok').onclick = () => { const ch = curCh(); if (ch) enter(ch); else { show('create'); const b = card.querySelector('#a_back'); if (b) b.innerHTML = '<a href="#" data-v="chars">← Geri</a>'; wire(); } };
  S$('c_x').onclick = () => out();
  S$('c_pw').onclick = e => { e.preventDefault(); show('pass'); };
  const modal = S$('c_modal');
  S$('c_del').onclick = () => { const ch = curCh(); if (!ch) return; S$('c_mt').innerHTML = `Silmek için karakter adını yaz: <b>${esc(ch.name)}</b>. Bu işlem geri alınamaz.`; S$('c_mi').value = ''; S$('c_mm').textContent = ''; modal.classList.add('on'); };
  S$('c_mc').onclick = () => modal.classList.remove('on');
  S$('c_md').onclick = async () => { const ch = curCh(); if (!ch) return; if (S$('c_mi').value.trim().toLowerCase() !== ch.name.toLowerCase()) { S$('c_mm').textContent = 'Karakter adı eşleşmiyor.'; return; } S$('c_md').disabled = true; try { await A.deleteCharacter(state.user.uid, ch); purge(ch, state.user.uid); if (HM()) HM().drop(ch.id); state.chars = state.chars.filter(c => c.id !== ch.id); modal.classList.remove('on'); state.ci = Math.min(state.ci, slots().length - 1); renderSel(); const m = S$('c_msg'); m.textContent = 'Karakter silindi.'; m.className = 'amsg ok'; } catch (err) { S$('c_mm').textContent = A.explain(err); } S$('c_md').disabled = false; };

  async function showChars() {
    setSel(false); view = 'chars'; card.className = 'acard v-chars'; card.innerHTML = '<div class="aload">Hesap yükleniyor…</div>';
    try {
      const [p, chars] = await Promise.all([A.profile(state.user.uid), A.listCharacters(state.user.uid)]);
      state.name = (p && p.username) || state.pending || state.user.email; state.chars = chars;
    } catch (err) { card.innerHTML = `<div class="abody"><div class="amsg" style="display:block">${esc(A.explain(err))}</div><button class="abtn" type="button" id="a_retry"><i>Tekrar Dene</i></button></div><div class="alinks"><a href="#" id="a_out">Çıkış Yap</a></div>`; card.querySelector('#a_retry').onclick = showChars; card.querySelector('#a_out').onclick = e => { e.preventDefault(); out(); }; return; }
    if (!state.chars.length) { show('create'); const b = card.querySelector('#a_back'); if (b) b.innerHTML = '<a href="#" id="a_out">Çıkış Yap</a>'; card.querySelector('#a_out').onclick = e => { e.preventDefault(); out(); }; if (state.notice) { msg(state.notice, true); state.notice = ''; } return; }
    { const h = HM(), kc = h && h.flag('keepch'), ac = h && h.flag('autoch'); if (kc) h.flag('keepch', null); if (ac) h.flag('autoch', null);
      const ki = kc ? state.chars.findIndex(c => c.id === kc) : -1, ai = ac ? state.chars.findIndex(c => c.id === ac) : -1;
      if (ki >= 0) { state.keep = ki; state.notice = 'Karakter oluşturuldu. “Başla” ile oyuna girebilirsin.'; }
      if (ai >= 0 && h.of(ac) === h.cur()) { enter(state.chars[ai]); return; } }
    state.ci = Math.max(0, Math.min(state.keep == null ? 0 : state.keep, slots().length - 1)); state.keep = null; setSel(true); renderSel();
  }
  async function out() { try { await A.logout(); } catch (_) {} location.reload(); }
  window.ValkorAuth = { logout: out };

  /* ---- başlangıç ---- */
  foot.innerHTML = 'Çöl binaları: ondrasaur (OndyRen)<br>CC BY 4.0 · sketchfab.com/saurondra';
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
