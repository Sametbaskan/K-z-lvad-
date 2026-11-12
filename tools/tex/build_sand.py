# GroundSand005 (renk+normal) → oyun için küçük detay dokuları. Kullanım: python3 -I build_sand.py <GroundSand005_COL_2K.jpg> <..._NRM_2K.jpg> <çıkış_klasörü>
import sys
from PIL import Image
import numpy as np
col,nrm,out=sys.argv[1:4]
im=Image.open(col).convert('RGB').resize((1024,1024),Image.LANCZOS)
a=np.asarray(im).astype(np.float32)/255; m=a.reshape(-1,3).mean(0)
r=a/m                                   # ortalama 1 → tepe noktası rengi gelsin, doku sadece tanecik/dalga versin
lum=r.mean(2,keepdims=True)
d=1+(lum-1)*3.2+(r-lum)*2.0             # kontrast artır
d=np.clip(d,.35,1.65)/1.65              # 0..1'e sığdır (shader 1.65 ile çarpar)
Image.fromarray((d*255).astype(np.uint8)).save(out+'/sand_detail.webp',quality=86)
Image.open(nrm).convert('RGB').resize((1024,1024),Image.LANCZOS).save(out+'/sand_nrm.webp',quality=88)
