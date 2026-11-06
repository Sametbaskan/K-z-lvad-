// TEST SAHTESİ — Firebase Auth davranışını taklit eder (yalnızca testlerde kullanılır)
const K='__mock_auth_db', S=()=>JSON.parse(localStorage.getItem(K)||'{"users":{}}'), W=d=>localStorage.setItem(K,JSON.stringify(d));
let cur=null, subs=[], persist='local';
const E=(code)=>Object.assign(new Error(code),{code});
const mk=u=>u&&{uid:u.uid,email:u.email,emailVerified:false,delete:async()=>{const d=S();delete d.users[u.uid];W(d);cur=null;fire();}};
function fire(){ subs.forEach(f=>f(cur)); }
export const getAuth=()=>{ const a={languageCode:'', get currentUser(){return cur;}};
  const sid=sessionStorage.getItem('__mock_sid'), lid=localStorage.getItem('__mock_lid'); const id=sid||lid;
  if(id){ const u=S().users[id]; if(u) cur=mk(u); } return window.__mockAuth=a; };
export const setPersistence=async(a,p)=>{persist=p;};
export const browserLocalPersistence='local', browserSessionPersistence='session';
export const onAuthStateChanged=(a,cb)=>{ subs.push(cb); setTimeout(()=>cb(cur),30); return ()=>{}; };
export const createUserWithEmailAndPassword=async(a,email,pw)=>{ await new Promise(r=>setTimeout(r,40)); const d=S();
  if(Object.values(d.users).some(u=>u.email===email.toLowerCase())) throw E('auth/email-already-in-use');
  if(pw.length<6) throw E('auth/weak-password');
  const u={uid:'u'+Math.random().toString(36).slice(2,9),email:email.toLowerCase(),pw:'H:'+btoa(pw)}; d.users[u.uid]=u; W(d); cur=mk(u); sign(u); fire(); return {user:cur}; };
function sign(u){ if(persist==='local'){localStorage.setItem('__mock_lid',u.uid);sessionStorage.removeItem('__mock_sid');} else {sessionStorage.setItem('__mock_sid',u.uid);localStorage.removeItem('__mock_lid');} }
export const signInWithEmailAndPassword=async(a,email,pw)=>{ await new Promise(r=>setTimeout(r,40)); const u=Object.values(S().users).find(x=>x.email===email.toLowerCase());
  if(!u) throw E('auth/invalid-credential'); if(u.pw!=='H:'+btoa(pw)) throw E('auth/invalid-credential'); cur=mk(u); sign(u); fire(); };
export const signOut=async()=>{ cur=null; localStorage.removeItem('__mock_lid'); sessionStorage.removeItem('__mock_sid'); fire(); };
export const sendPasswordResetEmail=async(a,e)=>{ (window.__mailLog=window.__mailLog||[]).push(['reset',e]); localStorage.setItem('__mock_mail',JSON.stringify([...(JSON.parse(localStorage.getItem('__mock_mail')||'[]')),['reset',e]])); };
export const sendEmailVerification=async()=>{};
export const EmailAuthProvider={credential:(email,pw)=>({email,pw})};
export const reauthenticateWithCredential=async(u,c)=>{ const x=S().users[u.uid]; if(x.pw!=='H:'+btoa(c.pw)) throw E('auth/invalid-credential'); };
export const updatePassword=async(u,pw)=>{ const d=S(); d.users[u.uid].pw='H:'+btoa(pw); W(d); };
