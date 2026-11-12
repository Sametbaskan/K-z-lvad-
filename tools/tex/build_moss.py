# mossy-forest-ground 2K (CC0, ambientCG Ground068) → orman/köy zemini detay+normal. Kullanım: python3 -I build_moss.py <color.jpg> <normalgl.jpg> <çıkış_klasörü>
import sys
from PIL import Image
import numpy as np
col,nrm,out=sys.argv[1:4]
a=np.asarray(Image.open(col).convert('RGB').resize((1024,1024),Image.LANCZOS)).astype(np.float32)/255; m=a.reshape(-1,3).mean(0)
r=a/m; lum=r.mean(2,keepdims=True)
d=1+(lum-1)*1.5+(r-lum)*.9                 # parlaklık + renk yamaları (kahverengi yaprak / yosun) korunur, tepe rengi ana tonu verir
d=np.clip(d,.35,1.7)/1.7
Image.fromarray((d*255).astype(np.uint8)).save(out+'/moss_detail.webp',quality=86)
Image.open(nrm).convert('RGB').resize((1024,1024),Image.LANCZOS).save(out+'/moss_nrm.webp',quality=88)
