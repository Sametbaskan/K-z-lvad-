# snow-covered-grass 2K (CC0, ambientCG Snow014) → kar zemini detay+normal. Kullanım: python3 -I build_snow.py <color.jpg> <normalgl.jpg> <çıkış_klasörü>
import sys
from PIL import Image
import numpy as np
col,nrm,out=sys.argv[1:4]
a=np.asarray(Image.open(col).convert('RGB').resize((1024,1024),Image.LANCZOS)).astype(np.float32)/255; m=a.reshape(-1,3).mean(0)
r=a/m; lum=r.mean(2,keepdims=True)
d=1+(lum-1)*2.4+(r-lum)*.6                 # kontrast artır, renk sapmasını (yeşil lekeler) azalt
d=np.clip(d*1.2,.85,1.5)/1.5                   # koyu lekeler tekrar eden benek gibi durmasın diye alt sınır
Image.fromarray((d*255).astype(np.uint8)).save(out+'/snow_detail.webp',quality=86)
Image.open(nrm).convert('RGB').resize((1024,1024),Image.LANCZOS).save(out+'/snow_nrm.webp',quality=88)
