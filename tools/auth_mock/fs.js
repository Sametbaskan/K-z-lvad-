const K='__mock_fs', S=()=>JSON.parse(localStorage.getItem(K)||'{}'), W=d=>localStorage.setItem(K,JSON.stringify(d));
const uid=()=>localStorage.getItem('__mock_lid')||sessionStorage.getItem('__mock_sid');
export const getFirestore=()=>({});
export const doc=(db,...p)=>{ if(db&&db.__col){ return {path:db.path+'/'+Math.random().toString(36).slice(2,10)}; } return {path:p.join('/')}; };
export const collection=(db,...p)=>({__col:1,path:p.join('/')});
export const serverTimestamp=()=>({seconds:Math.floor(Date.now()/1000)});
const snap=(path,d)=>({exists:()=>!!d,data:()=>d,id:path.split('/').pop()});
export const getDoc=async(r)=>{ await new Promise(x=>setTimeout(x,20)); return snap(r.path,S()[r.path]); };
export const getDocs=async(c)=>({docs:Object.entries(S()).filter(([p])=>p.startsWith(c.path+'/')&&p.split('/').length===c.path.split('/').length+1).map(([p,d])=>snap(p,d))});
export const writeBatch=()=>{ const ops=[]; return { set:(r,d)=>ops.push([r.path,d]), delete:(r)=>ops.push([r.path,null]), commit:async()=>{ const s=S(); const me=uid();
  for(const [p,d] of ops){ if(d===null){ if(!me) throw Object.assign(new Error('perm'),{code:'permission-denied'}); continue; } if(!me){ throw Object.assign(new Error('perm'),{code:'permission-denied'}); }
    if((p.startsWith('usernames/')||p.startsWith('charnames/'))&&s[p]) throw Object.assign(new Error('perm'),{code:'permission-denied'});
    if((p.startsWith('usernames/')||p.startsWith('charnames/'))&&d.uid!==me) throw Object.assign(new Error('perm'),{code:'permission-denied'}); }
  for(const [p,d] of ops){ if(d===null) delete s[p]; else s[p]=d; } W(s); } }; };
