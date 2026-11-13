# Yeni beceri simgeleri: mevcut simgelerden renk kaydırma/aynalama ile türetilir (çerçeve korunur) + eşya simgeleri (PIL ile çizim)
import io,base64,json,colorsys,math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
D='/tmp/claude-0/-home-claude/3590876c-0f6c-5664-a244-97bc63ceb0c2/scratchpad/ic/'
def hue(src,shift,sat=1.0,val=1.0,flip=False,inset=9):
    im=Image.open(D+src+'.png').convert('RGBA'); a=np.asarray(im).astype(np.float32)/255
    h,w=a.shape[:2]; rgb=a[...,:3]; mx=rgb.max(-1); mn=rgb.min(-1); df=mx-mn
    hh=np.zeros_like(mx); r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    m=df>1e-6
    hh=np.where(m&(mx==r),((g-b)/np.where(m,df,1))%6,hh); hh=np.where(m&(mx==g),(b-r)/np.where(m,df,1)+2,hh); hh=np.where(m&(mx==b),(r-g)/np.where(m,df,1)+4,hh); hh=hh/6
    s=np.where(mx>0,df/np.where(mx>0,mx,1),0); v=mx
    hh=(hh+shift)%1; s=np.clip(s*sat,0,1); v=np.clip(v*val,0,1)
    i=np.floor(hh*6).astype(int)%6; f=hh*6-np.floor(hh*6); p=v*(1-s); q=v*(1-f*s); t=v*(1-(1-f)*s)
    out=np.zeros_like(rgb)
    for k,(R,G,B) in enumerate([(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)]):
        mk=i==k; out[...,0]=np.where(mk,R,out[...,0]); out[...,1]=np.where(mk,G,out[...,1]); out[...,2]=np.where(mk,B,out[...,2])
    res=a.copy(); inner=np.zeros((h,w),bool); inner[inset:h-inset,inset:w-inset]=True
    res[...,:3]=np.where(inner[...,None],out,rgb)
    o=Image.fromarray((res*255).astype(np.uint8),'RGBA')
    if flip:
        core=o.crop((inset,inset,w-inset,h-inset)).transpose(Image.FLIP_LEFT_RIGHT); o.paste(core,(inset,inset))
    return o
def b64(im,q=86):
    b=io.BytesIO(); im.save(b,'WEBP',quality=q,method=6); return base64.b64encode(b.getvalue()).decode()
icons={
 'kukreme':        hue('buz_kalkan',0.45,1.05,1.0),           # buz mavisi -> kor/kızıl: nara atan savaşçı
 'yer_sarsintisi': hue('ofke_patlamasi',0.0,0.75,0.92,True),   # kaya patlaması: toprak tonuna çekildi
 'ruh_darbesi':    hue('guclu_vurus',0.55,0.8,1.05,True),      # kılıç: soluk mavi-beyaz ruh enerjisi
 'sihirli_kilic':  hue('guclu_vurus',0.78,1.0,1.0),            # kılıç: mor büyü
 'kalkan_alevi':   hue('demir_irade',0.93,1.15,1.0),           # kalkan: alev kızılı
 'ofke':           hue('hiz_hamlesi',0.93,1.2,1.0),            # atılan savaşçı: öfke kızılı
 'kilic_aurasi':   hue('lanet',0.83,0.7,1.1),                  # aura içinde figür: çelik mavisi
}
# eşya simgeleri (64x64)
def base(col):
    im=Image.new('RGBA',(64,64),(0,0,0,0)); return im,ImageDraw.Draw(im)
def book():
    im,d=base(0); d.rounded_rectangle((12,8,52,56),4,fill=(70,26,20,255),outline=(196,151,63,255),width=2); d.rectangle((16,8,20,56),fill=(40,14,10,255))
    d.ellipse((26,22,44,40),outline=(230,190,90,255),width=2); d.line((35,18,35,44),fill=(230,190,90,255),width=2); d.line((29,31,41,31),fill=(230,190,90,255),width=2)
    d.rectangle((22,50,50,53),fill=(222,208,170,255)); return im
def soul():
    im,d=base(0)
    g=Image.new('RGBA',(64,64),(0,0,0,0)); gd=ImageDraw.Draw(g); gd.ellipse((10,10,54,54),fill=(90,170,255,110)); g=g.filter(ImageFilter.GaussianBlur(6)); im.alpha_composite(g); d=ImageDraw.Draw(im)
    d.polygon([(32,8),(48,28),(32,56),(16,28)],fill=(60,120,210,255),outline=(200,230,255,255)); d.polygon([(32,8),(40,28),(32,56)],fill=(120,180,250,255)); d.line((16,28,48,28),fill=(200,230,255,255),width=1); return im
def seal():
    im,d=base(0); d.ellipse((8,8,56,56),fill=(120,84,20,255),outline=(240,206,110,255),width=3); d.ellipse((16,16,48,48),outline=(240,206,110,255),width=2)
    pts=[(32+math.cos(-math.pi/2+i*4*math.pi/5)*14,32+math.sin(-math.pi/2+i*4*math.pi/5)*14) for i in range(5)]; d.polygon(pts,outline=(255,236,170,255)); d.line(pts+[pts[0]],fill=(255,236,170,255),width=2); return im
def scroll():
    im,d=base(0); d.rounded_rectangle((14,12,50,52),3,fill=(214,196,150,255),outline=(120,96,60,255),width=2); d.rounded_rectangle((10,8,54,16),4,fill=(170,140,96,255),outline=(90,70,44,255)); d.rounded_rectangle((10,48,54,56),4,fill=(170,140,96,255),outline=(90,70,44,255))
    for y in (24,30,36): d.line((20,y,44,y),fill=(110,84,54,255),width=2)
    d.line((22,42,42,22),fill=(150,30,24,255),width=3); return im
items={'skbook':book(),'soulst':soul(),'pseal':seal(),'forget':scroll()}
sheet=Image.new('RGBA',(96*7+64*4,96),(30,30,30,255)); x=0
for k,im in icons.items(): sheet.alpha_composite(im,(x,0)); x+=96
for k,im in items.items(): sheet.alpha_composite(im,(x,16)); x+=64
sheet.resize((sheet.width*2,192),Image.LANCZOS).save(D+'../shots/newicons.png')
json.dump({'sk':{k:b64(v) for k,v in icons.items()},'it':{k:'data:image/webp;base64,'+b64(v,90) for k,v in items.items()}},open(D+'newicons.json','w'))
print({k:len(b64(v)) for k,v in icons.items()})
