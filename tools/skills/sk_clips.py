# Savaşçı (sav/kad) için ek beceri klipleri: Mixamo uzayındaki klipleri karakterin kalça ölçeğine çevirir (nin_pack.py ile aynı formül)
import json,os,numpy as np
M='/home/claude/k-z-lvad-/www/models/'; K2='/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/kq2/'
SRC={'block':K2+'mx_Block_with_the_sword.json','slam':M+'hero_cut.json','land':K2+'mx_Jump_landing.json','crouch':K2+'mx_Idle_crouching.json'}
for SD in ('sav','kad'):
    meta=json.load(open(M+SD+'/hero_'+SD+'.json'))['meta']; k=meta['k']; off=np.array(meta['ccHips'])-np.array(meta['mixHips'])*k
    for nm,src in SRC.items():
        d=json.load(open(src))
        for t in d['tracks']:
            if t['name']=='mixamorigHips.position':
                v=np.array(t['values']).reshape(-1,3)*k+off; t['values']=[round(float(x),4) for x in v.ravel()]
            else: t['values']=[round(float(x),5) for x in t['values']]
            t['times']=[round(float(x),4) for x in t['times']]
        json.dump(d,open(M+SD+'/'+nm+'.json','w'),separators=(',',':'))
    print(SD,{n:os.path.getsize(M+SD+'/'+n+'.json')//1024 for n in SRC})
