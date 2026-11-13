# Mixamo Great Sword Pack klipleri -> sav/kad beceri klipleri.
# 1) FBX -> AnimationClip JSON: scratchpad tools/extract_clip.py (three.js FBXLoader)  2) mixamorig1* -> mixamorig*, kalça Ch45 (98.88) -> Mixamo hero (103.27)  3) karakterin kalça ölçeği (meta.k, ccHips)
import json,os,sys,numpy as np
M='/home/claude/k-z-lvad-/www/models/'; X=sys.argv[1] if len(sys.argv)>1 else 'gsp/clips/'
SRC={'block':'great_sword_blocking','slam':'great_sword_jump_attack','gcut':'great_sword_slash_3','gspin':'great_sword_high_spin_attack'}
norm=103.2666/98.8801
for SD in ('sav','kad'):
    meta=json.load(open(M+SD+'/hero_'+SD+'.json'))['meta']; k=meta['k']; off=np.array(meta['ccHips'])-np.array(meta['mixHips'])*k
    for nm,src in SRC.items():
        d=json.load(open(X+src+'.json')); d['name']=nm
        for t in d['tracks']:
            t['name']=t['name'].replace('mixamorig1','mixamorig')
            if t['name']=='mixamorigHips.position': t['values']=[round(float(x),3) for x in (np.array(t['values']).reshape(-1,3)*norm*k+off).ravel()]
            else: t['values']=[round(float(x),5) for x in t['values']]
            t['times']=[round(float(x),4) for x in t['times']]
        json.dump(d,open(M+SD+'/'+nm+'.json','w'),separators=(',',':'))
