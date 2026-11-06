import numpy as np,struct,base64,json
from scipy.spatial import cKDTree
from PIL import Image
o=np.load('orig.npz'); pos,uv=o['pos'],o['uv']
b=open('out.bin','rb').read(); nv,nf=struct.unpack('ii',b[:8])
V=np.frombuffer(b[8:8+nv*24],np.float64).reshape(nv,3); F=np.frombuffer(b[8+nv*24:],np.int32).reshape(nf,3)
img=np.asarray(Image.open('raw1.jpg').convert('RGB')).astype(np.float32); H,W,_=img.shape
t=cKDTree(pos); dist,ix=t.query(V,k=24)
def samp(u,v):
    x=np.clip((u%1)*(W-1),0,W-1).astype(int); y=np.clip((1-(v%1))*(H-1),0,H-1).astype(int); return img[y,x]
col=np.zeros((nv,3),np.float32); ws=np.zeros(nv,np.float32)
for j in range(24):
    w=1.0/(dist[:,j]+2e-3)**2; col+=samp(uv[ix[:,j],0],uv[ix[:,j],1])*w[:,None]; ws+=w
col=np.clip(col/ws[:,None],0,255).astype(np.uint8)
json.dump(dict(n=nv,nf=nf,pos=base64.b64encode(V.astype(np.float32).tobytes()).decode(),col=base64.b64encode(col.tobytes()).decode(),idx=base64.b64encode(F.astype(np.uint32).tobytes()).decode()),open('dec_c.json','w'))
print(nv,nf,col.mean(0))
