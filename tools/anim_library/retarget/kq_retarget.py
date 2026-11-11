import json,sys,numpy as np
from scipy.spatial.transform import Rotation as Rot,Slerp
S=json.load(open('kq_src.json')); H=json.load(open('/home/claude/k-z-lvad-/www/models/hero.json'))
sb=S['bones']; SN={b['n']:i for i,b in enumerate(sb)}; hb=H['bones']; TN={b['n'].replace('mixamorig',''):i for i,b in enumerate(hb)}
MAP={'pelvis':'Hips','spine_01':'Spine','spine_02':'Spine1','spine_03':'Spine2','neck_01':'Neck','Head':'Head'}
for sd,td in (('l','Left'),('r','Right')):
    MAP.update({f'clavicle_{sd}':f'{td}Shoulder',f'upperarm_{sd}':f'{td}Arm',f'lowerarm_{sd}':f'{td}ForeArm',f'hand_{sd}':f'{td}Hand',f'thigh_{sd}':f'{td}UpLeg',f'calf_{sd}':f'{td}Leg',f'foot_{sd}':f'{td}Foot',f'ball_{sd}':f'{td}ToeBase'})
# bir sonraki (yön) kemik: kaynak -> hedef çocuk
KID={'pelvis':('spine_01','Spine'),'spine_01':('spine_02','Spine1'),'spine_02':('spine_03','Spine2'),'spine_03':('neck_01','Neck'),'neck_01':('Head','Head'),'Head':('head_leaf','HeadTop_End')}
for sd,td in (('l','Left'),('r','Right')):
    KID.update({f'clavicle_{sd}':(f'upperarm_{sd}',f'{td}Arm'),f'upperarm_{sd}':(f'lowerarm_{sd}',f'{td}ForeArm'),f'lowerarm_{sd}':(f'hand_{sd}',f'{td}Hand'),f'hand_{sd}':(f'middle_01_{sd}',f'{td}HandMiddle1'),
      f'thigh_{sd}':(f'calf_{sd}',f'{td}Leg'),f'calf_{sd}':(f'foot_{sd}',f'{td}Foot'),f'foot_{sd}':(f'ball_{sd}',f'{td}ToeBase'),f'ball_{sd}':(f'ball_leaf_{sd}',f'{td}Toe_End')})
def fk(par,pos,q,hp=None):
    n=len(par); W=[None]*n; P=np.zeros((n,3))
    for i in range(n):
        p=par[i]; ql=q[i]
        if p<0: W[i]=ql; P[i]=pos[i]
        else: W[i]=W[p]*ql; P[i]=P[p]+W[p].apply(pos[i])
    return W,P
spar=[b['p'] for b in sb]; spos=[np.array(b['pos']) for b in sb]; sq=[Rot.from_quat(b['q']) for b in sb]
tpar=[b['p'] for b in hb]; tpos=[np.array(b['pos']) for b in hb]; tq=[Rot.from_quat(b['q']) for b in hb]
Ws0,Ps0=fk(spar,spos,sq); Wt0,Pt0=fk(tpar,tpos,tq)
# kaynak dünya yönelimi: y yukarı mı, ileri neresi?
fwd=Ps0[SN['ball_l']]-Ps0[SN['foot_l']]; left=Ps0[SN['clavicle_l']]-Ps0[SN['clavicle_r']]
print('src ball-foot',fwd.round(3),'left',left.round(3),'pelvis',Ps0[SN['pelvis']].round(3),'head',Ps0[SN['Head']].round(3))
tl=Pt0[TN['LeftShoulder']]-Pt0[TN['RightShoulder']]; print('tgt left',tl.round(2),'hips',Pt0[TN['Hips']].round(1),'head',Pt0[TN['Head']].round(1),'foot->toe',(Pt0[TN['LeftToeBase']]-Pt0[TN['LeftFoot']]).round(2))

def rot_between(u,v):
    u=u/np.linalg.norm(u); v=v/np.linalg.norm(v); c=float(u@v)
    if c>.999999: return Rot.identity()
    if c<-.999999: ax=np.cross(u,[1,0,0]); ax/=np.linalg.norm(ax); return Rot.from_rotvec(ax*np.pi)
    ax=np.cross(u,v); s=np.linalg.norm(ax); return Rot.from_rotvec(ax/s*np.arccos(c))
C={}
for s,t in MAP.items():
    ks,kt=KID[s]; ds=Ps0[SN[ks]]-Ps0[SN[s]]; dt=Pt0[TN[kt]]-Pt0[TN[t]]
    C[s]=rot_between(dt,ds)
order=[s for s in MAP]  # üst kemikler önce (kaynak sırası ebeveyn öncelikli)
order.sort(key=lambda s:SN[s])
K=(hb[TN['Hips']]['pos'][1])/Ps0[SN['pelvis']][1]
def retarget(name,fps=30,strip_xz=False,t0=0,t1=None,tk=1.0):
    clip=S['clips'][name]; tr={t['name']:t for t in clip['tracks']}; dur=clip['duration']; t1=t1 or dur
    n=int(round((t1-t0)*fps))+1; times=np.linspace(t0,t1,n)
    sl={}
    for nm,t in tr.items():
        if nm.endswith('.quaternion'):
            b=nm[:-11]; ts=np.array(t['times']); q=np.array(t['values']).reshape(-1,4)
            sl[b]=(ts,Rot.from_quat(q)) 
    pp=tr.get('pelvis.position'); 
    def qat(b,tt,i):
        if b in sl:
            ts,R=sl[b]; tt=np.clip(tt,ts[0],ts[-1]); return Slerp(ts,R)(tt) if len(ts)>1 else R[0]
        return sq[i]
    outq={MAP[s]:[] for s in order}; outp=[]
    p0=None
    for tt in times:
        lq=[qat(b['n'],tt,i) for i,b in enumerate(sb)]
        if pp is not None:
            ts=np.array(pp['times']); v=np.array(pp['values']).reshape(-1,3); ps=np.array([np.interp(tt,ts,v[:,k]) for k in range(3)])
        else: ps=spos[SN['pelvis']]
        pl=[p.copy() for p in spos]; pl[SN['pelvis']]=ps
        W,P=fk(spar,pl,lq)
        Wt={}
        for s in order:
            i=SN[s]; ti=TN[MAP[s]]; D=W[i]*Ws0[i].inv()
            Wt[ti]=D*C[s]*Wt0[ti]
        for s in order:
            ti=TN[MAP[s]]; p=tpar[ti]
            loc=Wt[ti] if p not in Wt else Wt[p].inv()*Wt[ti]
            if p>=0 and p not in Wt: loc=Wt0[p].inv()*Wt[ti]
            outq[MAP[s]].append(loc.as_quat())
        hp=P[SN['pelvis']]
        if p0 is None: p0=hp.copy()
        d=(hp-p0)*K; d[0]*=tk; d[2]*=tk
        if strip_xz: d[0]=0; d[2]=0
        outp.append([hb[TN['Hips']]['pos'][0]+d[0],K*hp[1],hb[TN['Hips']]['pos'][2]+d[2]])
    tracks=[{'name':'mixamorigHips.position','type':'vector','times':[float(x-t0) for x in times],'values':[float(x) for r in outp for x in r]}]
    for td,qs in outq.items():
        q=np.array(qs); 
        for i in range(1,len(q)):
            if q[i]@q[i-1]<0: q[i]=-q[i]
        tracks.append({'name':'mixamorig'+td+'.quaternion','type':'quaternion','times':[float(x-t0) for x in times],'values':[float(x) for x in q.ravel()]})
    return {'name':name,'duration':float(t1-t0),'tracks':tracks}
if __name__=='__main__':
    import os
    M='/home/claude/k-z-lvad-/www/models/'
    for nm,out in (('Run_jog_forwards','hero_run_kq.json'),('Sword_slash','hero_cut_kq.json')):
        c=retarget(nm,tk=(0.433 if nm.startswith('Run') else 1.0)); json.dump(c,open('kq_'+out,'w'),separators=(',',':')); 
        h=c['tracks'][0]['values']; print(nm,c['duration'],len(c['tracks']),'hips z',h[2],'->',h[-1],'y',min(h[1::3]),max(h[1::3]))
