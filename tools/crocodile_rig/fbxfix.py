import zlib, types
from io_scene_fbx import parse_fbx
_real=zlib.decompress
def safe(data, *a, **k):
    try: return _real(data,*a,**k)
    except zlib.error:
        n=k.get('bufsize',0); print('WARN corrupt array replaced by zeros', n); return bytes(n)
parse_fbx.zlib=types.SimpleNamespace(decompress=safe)
