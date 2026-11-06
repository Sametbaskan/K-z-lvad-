/* VALKOR — Hesap servisi (oyun motorundan bağımsız).
   Gerçek Firebase Authentication (parola sunucuda hash'lenir, istemci asla düz parola saklamaz) + Firestore.
   Dışarı: init, register, login, logout, resetPassword, changePassword, listCharacters, createCharacter, currentUser. */
import { firebaseConfig } from './firebase-config.js';
const V = '10.12.2', B = `https://www.gstatic.com/firebasejs/${V}/`;
let M = null, app, auth, db;

export const isConfigured = () => !!(firebaseConfig && firebaseConfig.apiKey && firebaseConfig.projectId && firebaseConfig.appId);
export const MAX_CHARS = 4;
export const RULES = {
  user: /^[A-Za-z0-9_]{3,16}$/, email: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/, char: /^[A-Za-zÇĞİÖŞÜçğıöşü0-9 _-]{2,14}$/
};
export function passwordProblem(p) {
  if (p.length < 8) return 'Şifre en az 8 karakter olmalı.';
  if (p.length > 64) return 'Şifre en fazla 64 karakter olabilir.';
  if (!/[A-Za-z]/.test(p) || !/\d/.test(p)) return 'Şifre en az bir harf ve bir rakam içermeli.';
  return '';
}
export class AuthError extends Error { constructor(code, msg) { super(msg); this.code = code; } }

const MSG = {
  'valkor/not-configured': 'Hesap sistemi henüz yapılandırılmamış (Firebase ayarları eksik).',
  'valkor/user-notfound': 'Bu kullanıcı adıyla kayıtlı bir hesap bulunamadı.',
  'valkor/username-taken': 'Bu kullanıcı adı zaten alınmış.',
  'valkor/charname-taken': 'Bu karakter adı zaten alınmış.',
  'valkor/char-limit': `En fazla ${MAX_CHARS} karakter oluşturabilirsin.`,
  'auth/user-not-found': 'Bu bilgilerle kayıtlı bir hesap bulunamadı.',
  'auth/wrong-password': 'Şifre hatalı.',
  'auth/invalid-credential': 'Şifre hatalı ya da bu bilgilerle hesap bulunamadı.',
  'auth/invalid-login-credentials': 'Şifre hatalı ya da bu bilgilerle hesap bulunamadı.',
  'auth/invalid-email': 'Geçerli bir e-posta adresi gir.',
  'auth/email-already-in-use': 'Bu e-posta adresiyle zaten bir hesap var.',
  'auth/weak-password': 'Şifre çok zayıf. En az 8 karakter, harf ve rakam kullan.',
  'auth/too-many-requests': 'Çok fazla deneme yapıldı. Bir süre bekleyip tekrar dene.',
  'auth/network-request-failed': 'Bağlantı hatası. İnternet bağlantını kontrol edip tekrar dene.',
  'auth/user-disabled': 'Bu hesap devre dışı bırakılmış.',
  'auth/requires-recent-login': 'Güvenlik için çıkış yapıp yeniden giriş yapman gerekiyor.',
  'auth/missing-email': 'E-posta adresini gir.',
  'permission-denied': 'Bu işlem için yetkin yok (sunucu kuralları reddetti).',
  'unavailable': 'Sunucuya ulaşılamıyor. Bağlantını kontrol et.'
};
export function explain(e) {
  const c = e && (e.code || '').replace(/^firestore\//, '');
  return MSG[c] || (e && e.message && e.code && String(e.code).startsWith('valkor/') ? e.message : 'Beklenmeyen bir hata oluştu. Tekrar dene.' + (c ? ' (' + c + ')' : ''));
}

export async function init() {
  if (M) return;
  if (!isConfigured()) throw new AuthError('valkor/not-configured', MSG['valkor/not-configured']);
  try {
    const [a, u, f] = await Promise.all([import(B + 'firebase-app.js'), import(B + 'firebase-auth.js'), import(B + 'firebase-firestore.js')]);
    M = { ...a, ...u, ...f };
    app = M.initializeApp(firebaseConfig); auth = M.getAuth(app); db = M.getFirestore(app);
    auth.languageCode = 'tr';
  } catch (e) { M = null; throw new AuthError('auth/network-request-failed', MSG['auth/network-request-failed']); }
}
/* Oturum değişimini dinle; ilk çağrıda mevcut oturum (varsa) bildirilir. */
export function onUser(cb) { return M.onAuthStateChanged(auth, u => cb(u ? { uid: u.uid, email: u.email, verified: u.emailVerified } : null)); }
export const currentUser = () => auth && auth.currentUser ? { uid: auth.currentUser.uid, email: auth.currentUser.email } : null;

const lc = s => String(s).trim().toLowerCase();
async function usernameDoc(name) { const s = await M.getDoc(M.doc(db, 'usernames', lc(name))); return s.exists() ? s.data() : null; }

export async function register({ username, email, password, password2 }) {
  username = String(username || '').trim(); email = String(email || '').trim();
  if (!RULES.user.test(username)) throw new AuthError('valkor/val', 'Kullanıcı adı 3-16 karakter olmalı; yalnızca harf, rakam ve alt çizgi içerebilir.');
  if (!RULES.email.test(email)) throw new AuthError('valkor/val', 'Geçerli bir e-posta adresi gir.');
  const pp = passwordProblem(password || ''); if (pp) throw new AuthError('valkor/val', pp);
  if (password !== password2) throw new AuthError('valkor/val', 'Şifreler birbiriyle eşleşmiyor.');
  if (await usernameDoc(username)) throw new AuthError('valkor/username-taken', MSG['valkor/username-taken']);
  await M.setPersistence(auth, M.browserLocalPersistence);
  const cred = await M.createUserWithEmailAndPassword(auth, email, password);   // e-posta tekilliği Firebase tarafından garanti edilir
  const uid = cred.user.uid;
  try {
    const b = M.writeBatch(db);
    b.set(M.doc(db, 'usernames', lc(username)), { uid, email: lc(email), username });
    b.set(M.doc(db, 'users', uid), { username, usernameLower: lc(username), createdAt: M.serverTimestamp() });
    await b.commit();
  } catch (e) {                      // kullanıcı adı yarışta alındıysa yarım kalan hesabı geri al
    try { await cred.user.delete(); } catch (_) {}
    if (e && /permission|already/i.test((e.code || '') + e.message)) throw new AuthError('valkor/username-taken', MSG['valkor/username-taken']);
    throw e;
  }
  try { await M.sendEmailVerification(cred.user); } catch (_) {}
  return { uid, username };
}

export async function login({ id, password, remember }) {
  id = String(id || '').trim();
  if (!id || !password) throw new AuthError('valkor/val', 'Kullanıcı adı/e-posta ve şifreni gir.');
  let email = id;
  if (!id.includes('@')) {
    const d = await usernameDoc(id);
    if (!d) throw new AuthError('valkor/user-notfound', MSG['valkor/user-notfound']);
    email = d.email;
  }
  await M.setPersistence(auth, remember ? M.browserLocalPersistence : M.browserSessionPersistence);
  await M.signInWithEmailAndPassword(auth, email, password);
}
export const logout = () => M.signOut(auth);
export async function resetPassword(email) {
  email = String(email || '').trim();
  if (!RULES.email.test(email)) throw new AuthError('valkor/val', 'Geçerli bir e-posta adresi gir.');
  await M.sendPasswordResetEmail(auth, email);   // hesap var/yok bilgisi sızdırılmaz
}
export async function changePassword(oldPw, newPw, newPw2) {
  const u = auth.currentUser; if (!u) throw new AuthError('auth/requires-recent-login', MSG['auth/requires-recent-login']);
  if (!oldPw) throw new AuthError('valkor/val', 'Mevcut şifreni gir.');
  const pp = passwordProblem(newPw || ''); if (pp) throw new AuthError('valkor/val', pp);
  if (newPw !== newPw2) throw new AuthError('valkor/val', 'Yeni şifreler eşleşmiyor.');
  await M.reauthenticateWithCredential(u, M.EmailAuthProvider.credential(u.email, oldPw));
  await M.updatePassword(u, newPw);
}
export async function profile(uid) { const s = await M.getDoc(M.doc(db, 'users', uid)); return s.exists() ? s.data() : null; }
export async function listCharacters(uid) {
  const s = await M.getDocs(M.collection(db, 'users', uid, 'characters'));
  return s.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => (a.createdAt?.seconds || 0) - (b.createdAt?.seconds || 0));
}
export async function deleteCharacter(uid, c) {
  const b = M.writeBatch(db);
  b.delete(M.doc(db, 'users', uid, 'characters', c.id));
  b.delete(M.doc(db, 'charnames', lc(c.name)));
  try { await b.commit(); } catch (e) { if (/permission/i.test(e.code || '')) throw new AuthError('valkor/val', 'Silme izni yok: Firestore kuralları güncel değil (firestore.rules yeniden yayınlanmalı).'); throw e; }
}
export async function createCharacter(uid, { name, king }) {
  name = String(name || '').trim().replace(/\s+/g, ' ');
  if (!RULES.char.test(name)) throw new AuthError('valkor/val', 'Karakter adı 2-14 karakter olmalı (harf, rakam, boşluk, - ve _).');
  king = +king; if (!(king >= 0 && king <= 2)) throw new AuthError('valkor/val', 'Bir krallık seç.');
  if ((await listCharacters(uid)).length >= MAX_CHARS) throw new AuthError('valkor/char-limit', MSG['valkor/char-limit']);
  const nref = M.doc(db, 'charnames', lc(name));
  if ((await M.getDoc(nref)).exists()) throw new AuthError('valkor/charname-taken', MSG['valkor/charname-taken']);
  const cref = M.doc(M.collection(db, 'users', uid, 'characters'));
  const b = M.writeBatch(db);
  b.set(nref, { uid, charId: cref.id, name });
  b.set(cref, { name, nameLower: lc(name), king, createdAt: M.serverTimestamp() });
  try { await b.commit(); } catch (e) { if (/permission/i.test(e.code || '')) throw new AuthError('valkor/charname-taken', MSG['valkor/charname-taken']); throw e; }
  return { id: cref.id, name, king };
}
