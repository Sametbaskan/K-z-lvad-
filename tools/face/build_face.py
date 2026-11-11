"""2. karakterin (CC/Unity) kafa + göz parçalarını klasik karakterin bind uzayına taşıyıp www/models/hero_face.json üretir.
Kullanım: python3 tools/face/build_face.py [ölçek]   [boyun kesme y] (varsayılan 1.1 157.5)"""
import json,sys,numpy as np
S=float(sys.argv[1]) if len(sys.argv)>1 else 1.1
NECK_CUT=float(sys.argv[2]) if len(sys.argv)>2 else 157.5
J=json.load(open('www/models/hero.json')); C=json.load(open('www/models/cc/hero_cc.json'))
hn=lambda D:{b['n'].replace('mixamorig:','').replace('mixamorig',''):i for i,b in enumerate(D['bones'])}
def rest(D,name):  # bone bind world pozisyonu = inverse(inv matrix) çevirisi
    m=np.array(D['inv'][hn(D)[name]]).reshape(4,4).T; return np.linalg.inv(m)[:3,3]
cH,kH=rest(C,'Head'),rest(J,'Head'); print('cc head',cH.round(2),'classic head',kH.round(2))

import math
HL=[(0,180.8),(50,179.5),(80,176.5),(105,174.5),(140,168.0),(180,163.0)]   # saç çizgisi yüksekliği (CC uzayı) - ön→arka (derece)
def hl(x,z):
    th=abs(math.degrees(math.atan2(x,z+0.5)))
    for (a,ya),(b,yb) in zip(HL,HL[1:]):
        if th<=b: return ya+(yb-ya)*(th-a)/(b-a)
    return HL[-1][1]
def make_hair(pos,nrm,idx,kH,cH,S):
    f=np.array([pos[i,1]-hl(pos[i,0],pos[i,2]) for i in range(len(pos))])
    P=[];N=[];F=[];I=[];cache={}
    def add(p,n,fv):
        P.append(p);N.append(n);F.append(fv);return len(P)-1
    def vert(i):
        if ('v',i) not in cache: cache[('v',i)]=add(pos[i],nrm[i],f[i])
        return cache[('v',i)]
    def cut(i,j):
        k=('e',min(i,j),max(i,j))
        if k not in cache:
            t=f[i]/(f[i]-f[j]); n=nrm[i]+(nrm[j]-nrm[i])*t; n=n/ (np.linalg.norm(n)+1e-9)
            cache[k]=add(pos[i]+(pos[j]-pos[i])*t,n,0.0)
        return cache[k]
    for a,b,c in idx:
        ins=[v for v in (a,b,c) if f[v]>0]
        if len(ins)==0: continue
        if len(ins)==3: I+= [vert(a),vert(b),vert(c)]; continue
        tri=[a,b,c]
        # sıralı kenarlar boyunca çokgeni kırp
        poly=[]
        for k in range(3):
            u,v=tri[k],tri[(k+1)%3]
            if f[u]>0: poly.append(vert(u))
            if (f[u]>0)!=(f[v]>0): poly.append(cut(u,v))
        for k in range(1,len(poly)-1): I+=[poly[0],poly[k],poly[k+1]]
    Pw=[kH+S*(p-cH) for p in P]
    r=lambda arr:[round(float(v),3) for v in np.array(arr).reshape(-1)]
    print('hair verts',len(P),'tris',len(I)//3)
    return {'pos':r(Pw),'nrm':r(N),'f':[round(float(v),3) for v in F],'idx':[int(v) for v in I]}
out={'scale':S,'parts':[]}
for p in C['parts']:
    if p['n'] not in ('Body/Std_Skin_Head','Eyes'): continue
    pos=np.array(p['pos']).reshape(-1,3); q=kH+S*(pos-cH)
    ii=np.array(p['idx']).reshape(-1,3)
    if p['n']=='Body/Std_Skin_Head': ii=np.array([t for t in ii if pos[t][:,1].mean()>=NECK_CUT])   # boyun tabanındaki omuza açılan yaka kesilir (klasik gövdenin boynu görünsün)
    d={'n':p['n'],'pos':[round(float(v),3) for v in q.reshape(-1)],'nrm':[round(float(v),3) for v in p['nrm']],'uv':[round(float(v),4) for v in p['uv']],'idx':[int(v) for v in ii.reshape(-1)],'tex':p['tex']}
    if p['n']=='Body/Std_Skin_Head':
        d['hair']=make_hair(pos,np.array(p['nrm']).reshape(-1,3),np.array(p['idx']).reshape(-1,3),kH,cH,S)
    out['parts'].append(d)
out['tex']={p['tex']:C['tex'][p['tex']] for p in out['parts']}
json.dump(out,open('www/models/hero_face.json','w'),separators=(',',':'))
import os; print('size',os.path.getsize('www/models/hero_face.json'))
