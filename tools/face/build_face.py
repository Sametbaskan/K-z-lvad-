"""2. karakterin (CC/Unity) kafa + göz parçalarını klasik karakterin bind uzayına taşıyıp www/models/hero_face.json üretir.
Kullanım: python3 tools/face/build_face.py [ölçek]   (varsayılan 1.1)"""
import json,sys,numpy as np
S=float(sys.argv[1]) if len(sys.argv)>1 else 1.1
J=json.load(open('www/models/hero.json')); C=json.load(open('www/models/cc/hero_cc.json'))
hn=lambda D:{b['n'].replace('mixamorig:','').replace('mixamorig',''):i for i,b in enumerate(D['bones'])}
def rest(D,name):  # bone bind world pozisyonu = inverse(inv matrix) çevirisi
    m=np.array(D['inv'][hn(D)[name]]).reshape(4,4).T; return np.linalg.inv(m)[:3,3]
cH,kH=rest(C,'Head'),rest(J,'Head'); print('cc head',cH.round(2),'classic head',kH.round(2))
out={'scale':S,'parts':[]}
for p in C['parts']:
    if p['n'] not in ('Body/Std_Skin_Head','Eyes'): continue
    pos=np.array(p['pos']).reshape(-1,3); q=kH+S*(pos-cH)
    d={'n':p['n'],'pos':[round(float(v),3) for v in q.reshape(-1)],'nrm':[round(float(v),3) for v in p['nrm']],'uv':[round(float(v),4) for v in p['uv']],'idx':list(map(int,p['idx'])),'tex':p['tex']}
    if p['n']=='Body/Std_Skin_Head':
        idx=np.array(p['idx']).reshape(-1,3); hair=[]
        for t,(a,b,c) in enumerate(idx):
            cen=pos[[a,b,c]].mean(0); x,y,z=cen
            if (y>180.2 and z<8) or (y>170 and z<-3.5) or (y>175 and abs(x)>9.5 and z<5): hair.append(t)
        d['hair']=hair; print('hair tris',len(hair),'of',len(idx))
    out['parts'].append(d)
out['tex']={p['tex']:C['tex'][p['tex']] for p in out['parts']}
json.dump(out,open('www/models/hero_face.json','w'),separators=(',',':'))
import os; print('size',os.path.getsize('www/models/hero_face.json'))
