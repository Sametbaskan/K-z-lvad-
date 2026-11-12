# dark-slate-rock 2K (CC0, ambientCG Rock058) + kesme taş harç çizgileri → sur dokusu. Kullanım: python3 -I build_wall.py <color.jpg> <normalgl.jpg> <çıkış_klasörü>
import sys, random
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
col,nrm,out=sys.argv[1:4]
S=1024; rock=Image.open(col).convert('RGB').resize((S,S),Image.LANCZOS)
a=np.asarray(rock).astype(np.float32)/255
# blok düzeni: 8 sıra, 4 m döşemede 0,5 m sıra yüksekliği; sıralar kaydırmalı
rnd=random.Random(5); rows=8; rh=S//rows
shade=np.ones((S,S),np.float32); mortar=Image.new('L',(S,S),0); d=ImageDraw.Draw(mortar)
for j in range(rows):
    x=-rnd.randint(0,200); y=j*rh
    while x<S:
        w=rnd.randint(150,260); v=1+(rnd.random()-.5)*.34
        for ox in (0,-S,S):
            x0=max(0,x+ox); x1=min(S,x+ox+w)
            if x1>x0: shade[y:y+rh,x0:x1]*=v
            d.rectangle([x+ox,y,x+ox+3,y+rh],fill=255)
        d.rectangle([0,y,S,y+4],fill=255); x+=w
m=np.asarray(mortar.filter(ImageFilter.GaussianBlur(2.2))).astype(np.float32)/255
out_a=a*shade[...,None]*(1-.62*m[...,None])
# ışık: üst kenar aydınlık
Image.fromarray((np.clip(out_a,0,1)*255).astype(np.uint8)).save(out+'/wall_color.webp',quality=84)
Image.open(nrm).convert('RGB').resize((S,S),Image.LANCZOS).save(out+'/wall_nrm.webp',quality=86)
print('mean',(out_a.mean((0,1))*255).round())
