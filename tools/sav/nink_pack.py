import json,base64,io,os
import numpy as np
from PIL import Image
M='/home/claude/k-z-lvad-/www/models/'; A='/mnt/user-data/attachments/3590876c-0f6c-5664-a244-97bc63ceb0c2/'
S='/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/'
raw=json.load(open(S+'savout/nink_raw.json')); meta=raw['meta']; k=meta['k']
mix=np.array(meta['mixHips']); cc=np.array(meta['ccHips']); off=cc-mix*k
def tex(f):
    im=Image.open(A+f).convert('RGBA'); b=io.BytesIO(); im.save(b,'WEBP',quality=88,method=6)
    return 'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
out={k2:raw[k2] for k2 in ('bones','inv','parts','h','lo','meta')}
out['tex']={'face':tex('cd3425cc-image.png'),'hair':tex('267da14b-image.png'),'body':tex('493a90b5-image.png')}
def conv(src):
    d=json.load(open(M+src))
    for t in d['tracks']:
        if t['name']=='mixamorigHips.position':
            v=np.array(t['values']).reshape(-1,3)*k+off; t['values']=[round(float(x),4) for x in v.ravel()]
    return d
out['clip']=conv('hero_idle2.json')
os.makedirs(M+'nink',exist_ok=True)
json.dump(out,open(M+'nink/hero_nink.json','w'),separators=(',',':'))
for nm,src in dict(run='hero_run_kq.json',combo='hero_combo.json',powerup='hero_powerup.json',heal='hero_heal.json',death='hero_death.json',cut='hero_cut_kq.json').items():
    json.dump(conv(src),open(M+'nink/%s.json'%nm,'w'),separators=(',',':'))
print({f:os.path.getsize(M+'nink/'+f)//1024 for f in os.listdir(M+'nink')})
