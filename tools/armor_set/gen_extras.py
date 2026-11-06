# VALKOR - Kara Şövalye zırhına ek parçalar: boyunluk (yaka + omuz üstü), pelerin, miğfer.
# Meshy'den uyarlanan zırhın (fit_meshy_armor.py çıktısı) dış yüzeyine göre konumlanır; savaşçı iskeletine bağlıdır.
#   python3 -I gen_extras.py -- <hero.json> <çıkış> <meshy_parça_klasörü>
# Yöntem: her plaka, gövdenin ilgili kemik ekseni etrafındaki gerçek kesit profilinden (zarf + pay) örülen kabuktur;
# ağırlıklar gövde köşelerinden (en yakın komşular) aktarılır → aynı iskeletle bükülür, gövdeye gömülmez.
# Katı süsler (omuzluk kubbesi, diken, kafatası, diz kapağı) tek bir bağlantı noktasının ağırlığıyla taşınır.
# Çıktı: parça başına GLB (iskelet adları hero.json ile aynı, birim cm, bağlama pozu = hero bağlama pozu) + önizleme.
import sys, os, json, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, kdtree
from PIL import Image, ImageDraw, ImageFilter

argv = sys.argv[sys.argv.index('--') + 1:]
HERO, OUT, KDIR = argv[0], os.path.abspath(argv[1]), argv[2]
os.makedirs(OUT, exist_ok=True); TEX = os.path.join(OUT, '_tex'); os.makedirs(TEX, exist_ok=True)
TAU = 2 * math.pi
rng = np.random.default_rng(7)

# ------------------------------------------------------------------ gövde + iskelet (three.js uzayı: Y yukarı, Z ön, cm)
J = json.load(open(HERO))
BN = [b['n'] for b in J['bones']]; SHORT = [n.replace('mixamorig', '') for n in BN]; BI = {n: i for i, n in enumerate(SHORT)}
JW = {}
for n, inv in zip(SHORT, J['inv']):
    JW[n] = np.linalg.inv(np.array(inv).reshape(4, 4).T)[:3, 3]
P_l, W_l, N_l = [], [], []
for pt in J['parts']:
    p = np.array(pt['pos']).reshape(-1, 3); si = np.array(pt['si']).reshape(-1, 4); sw = np.array(pt['sw']).reshape(-1, 4)
    w = np.zeros((len(p), len(BN)))
    for k in range(4): np.add.at(w, (np.arange(len(p)), si[:, k]), sw[:, k])
    P_l.append(p); W_l.append(w); N_l.append(np.array(pt['nrm']).reshape(-1, 3))
BP = np.concatenate(P_l); BW = np.concatenate(W_l); BNRM = np.concatenate(N_l)
DOM = np.array(SHORT)[BW.argmax(1)]
print('gövde köşe', len(BP))

def bone_set(*pref): return {n for n in SHORT if any(n == p or (p.endswith('*') and n.startswith(p[:-1])) for p in pref)}
def mask(bones): return np.isin(DOM, list(bones))

# ------------------------------------------------------------------ profil (kemik ekseni etrafında zarf)
class Axis:
    def __init__(s, A, B, up, ext=(0, 1)):
        s.A = np.array(A, float); s.B = np.array(B, float); s.L = np.linalg.norm(s.B - s.A); s.d = (s.B - s.A) / s.L
        u = np.array(up, float); u = u - s.d * u.dot(s.d); s.u = u / np.linalg.norm(u); s.v = np.cross(s.d, s.u)
    def local(s, P):
        rel = P - s.A; t = rel @ s.d / s.L; q = rel - np.outer(t * s.L, s.d)
        return t, np.hypot(q @ s.u, q @ s.v), np.arctan2(q @ s.v, q @ s.u)
    def point(s, t, th, r):
        return s.A + s.d * (t * s.L) + (s.u * math.cos(th) + s.v * math.sin(th)) * r

class Profile:
    """R(t,θ): seçili gövde köşelerinin eksenden en uzak mesafesi (genişletilmiş + yumuşatılmış zarf)"""
    def __init__(s, ax, bones, t0, t1, nt=24, nth=36, dil=1, sm=2, extra=None):
        s.ax, s.t0, s.t1, s.nt, s.nth = ax, t0, t1, nt, nth
        m = mask(bones) if extra is None else (mask(bones) & extra)
        t, r, th = ax.local(BP[m])
        sel = (t >= t0 - 0.05) & (t <= t1 + 0.05)
        it = np.clip(((t[sel] - t0) / (t1 - t0) * nt).astype(int), 0, nt - 1)
        ih = ((th[sel] + math.pi) / TAU * nth).astype(int) % nth
        R = np.zeros((nt, nth)); np.maximum.at(R, (it, ih), r[sel])
        for _ in range(60):  # boşları komşulardan doldur
            z = R == 0
            if not z.any(): break
            nb = np.stack([np.roll(R, 1, 1), np.roll(R, -1, 1), np.vstack([R[:1], R[:-1]]), np.vstack([R[1:], R[-1:]])])
            cnt = (nb > 0).sum(0); avg = np.where(cnt > 0, nb.sum(0) / np.maximum(cnt, 1), 0)
            R = np.where(z, avg, R)
        for _ in range(dil):  # genişlet (kabuk çıkıntılara batmasın)
            R = np.maximum.reduce([R, np.roll(R, 1, 1), np.roll(R, -1, 1), np.vstack([R[:1], R[:-1]]), np.vstack([R[1:], R[-1:]])])
        for _ in range(sm):  # yumuşat (kas çizgileri değil plaka yüzeyi)
            R = (R * 2 + np.roll(R, 1, 1) + np.roll(R, -1, 1)) / 4
            R = (R * 2 + np.vstack([R[:1], R[:-1]]) + np.vstack([R[1:], R[-1:]])) / 4
        s.R = R
    def __call__(s, t, th):
        ft = np.clip((t - s.t0) / (s.t1 - s.t0) * s.nt - 0.5, 0, s.nt - 1.001)
        fh = ((th + math.pi) / TAU * s.nth - 0.5) % s.nth
        i0 = int(ft); a = ft - i0; j0 = int(fh) % s.nth; b = fh - int(fh); j1 = (j0 + 1) % s.nth
        R = s.R
        return (R[i0, j0] * (1 - a) * (1 - b) + R[i0 + 1, j0] * a * (1 - b) + R[i0, j1] * (1 - a) * b + R[i0 + 1, j1] * a * b)

# ------------------------------------------------------------------ mesh toplayıcı (parça başına)
def b2(p):  # three (x,y,z) -> blender (x,-z,y)
    return (p[0], -p[2], p[1])

class Piece:
    def __init__(s, name):
        s.name = name; s.V = []; s.F = []; s.UV = []; s.FM = []; s.W = []; s.mats = []
    def mat(s, m):
        if m not in s.mats: s.mats.append(m)
        return s.mats.index(m)
    def add(s, verts, faces, uvs, m, weights):
        """verts: three uzayı; uvs: yüz-köşe başına (faces ile aynı yapıda); weights: köşe başına (len BN) dizi"""
        o = len(s.V); mi = s.mat(m)
        s.V += [tuple(v) for v in verts]; s.W += list(weights)
        for f, uv in zip(faces, uvs): s.F.append(tuple(o + i for i in f)); s.UV.append(uv); s.FM.append(mi)

def kd_for(bones):
    idx = np.nonzero(mask(bones))[0]; kd = kdtree.KDTree(len(idx))
    for k, i in enumerate(idx): kd.insert(Vector(BP[i]), k)
    kd.balance(); return kd, idx

def transfer(verts, bones, k=8, sharp=2.0):
    """gövdeden ağırlık aktarımı: en yakın k köşe, ters mesafe ağırlıklı"""
    kd, idx = kd_for(bones); out = []
    for v in verts:
        res = kd.find_n(Vector(v), k); w = np.zeros(len(BN)); tot = 0
        for co, j, dist in res:
            a = 1.0 / (dist + 0.5) ** sharp; w += BW[idx[j]] * a; tot += a
        out.append(w / tot)
    return out

def anchor_w(p, bones, k=12):
    return transfer([p], bones, k=k, sharp=1.0)[0]

# ------------------------------------------------------------------ geometri yardımcıları
def loft_piece(pc, ax, prof, th_a, th_b, s_t0, s_t1, off, mat, ncol, nrow, bones, mod=None, urep=1.0, rim=None, rivet=None, wfn=None):
    """eksen etrafında kısmi/tam kabuk. s_t0/s_t1: θ -> t (alt/üst sınır). mod(t,θ,s) -> ek yarıçap"""
    full = abs((th_b - th_a) - TAU) < 1e-6
    cols = ncol if full else ncol + 1
    verts, grid = [], []
    for i in range(nrow + 1):
        s = i / nrow; row = []
        for j in range(cols):
            th = th_a + (th_b - th_a) * j / ncol
            t = s_t0(th) + (s_t1(th) - s_t0(th)) * s
            r = prof(t, th) + off + (mod(t, th, s) if mod else 0)
            row.append(len(verts)); verts.append(ax.point(t, th, r))
        grid.append(row)
    faces, uvs = [], []
    for i in range(nrow):
        for j in range(ncol):
            j1 = (j + 1) % cols if full else j + 1
            faces.append((grid[i][j], grid[i][j1], grid[i + 1][j1], grid[i + 1][j]))
            u0, u1 = j / ncol * urep, (j + 1) / ncol * urep
            uvs.append([(u0, i / nrow), (u1, i / nrow), (u1, (i + 1) / nrow), (u0, (i + 1) / nrow)])
    # yüz yönü: dışa baksın (eksenden uzağa)
    v = np.array(verts)
    a, b, c = v[faces[0][0]], v[faces[0][1]], v[faces[0][2]]
    n = np.cross(b - a, c - a); cen = (a + b + c) / 3
    t0 = (cen - ax.A) @ ax.d; radial = cen - (ax.A + ax.d * t0)
    if n @ radial < 0:
        faces = [tuple(reversed(f)) for f in faces]; uvs = [list(reversed(u)) for u in uvs]
    W = wfn(verts) if wfn else transfer(verts, bones)
    pc.add(verts, faces, uvs, mat, W)
    edges = {'bottom': [verts[k] for k in grid[0]], 'top': [verts[k] for k in grid[-1]]}
    if not full:
        edges['left'] = [verts[grid[i][0]] for i in range(nrow + 1)]; edges['right'] = [verts[grid[i][-1]] for i in range(nrow + 1)]
    if full:
        edges['bottom'].append(edges['bottom'][0]); edges['top'].append(edges['top'][0])
    if rim:
        for e in rim: tube_piece(pc, edges[e], 0.55, 'trim', bones, seg=5)
    if rivet:
        for e in rivet:
            pts = edges[e]
            for k in range(1, len(pts) - 1, 3): stud(pc, pts[k], ax, 0.55, 'trim', bones)
    return edges

def frames(pts):
    pts = [np.array(p, float) for p in pts]; out = []
    up = np.array([0, 1, 0.0])
    for i, p in enumerate(pts):
        t = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]; t /= (np.linalg.norm(t) or 1)
        n = up - t * up.dot(t)
        if np.linalg.norm(n) < 1e-3: n = np.array([0, 0, 1.0]) - t * t[2]
        n /= np.linalg.norm(n); out.append((p, t, n, np.cross(t, n)))
    return out

def tube_piece(pc, pts, rad, mat, bones, seg=6, radii=None, wfn=None):
    fr = frames(pts); verts = []; rings = []
    for i, (p, t, n, b) in enumerate(fr):
        r = radii[i] if radii is not None else rad; ring = []
        for k in range(seg):
            a = TAU * k / seg; ring.append(len(verts)); verts.append(p + (n * math.cos(a) + b * math.sin(a)) * r)
        rings.append(ring)
    faces, uvs = [], []
    for i in range(len(rings) - 1):
        for k in range(seg):
            k1 = (k + 1) % seg
            faces.append((rings[i][k], rings[i][k1], rings[i + 1][k1], rings[i + 1][k]))
            uvs.append([(k / seg, i / len(rings)), ((k + 1) / seg, i / len(rings)), ((k + 1) / seg, (i + 1) / len(rings)), (k / seg, (i + 1) / len(rings))])
    pc.add(verts, faces, uvs, mat, wfn(verts) if wfn else transfer(verts, bones))

def cone_piece(pc, base, direction, length, rad, mat, w, seg=6, curve=None):
    d = np.array(direction, float); d /= np.linalg.norm(d)
    n = np.cross(d, [0, 1, 0]);  n = n if np.linalg.norm(n) > 1e-3 else np.cross(d, [1, 0, 0]); n /= np.linalg.norm(n); b = np.cross(d, n)
    base = np.array(base, float); verts = []
    for k in range(seg):
        a = TAU * k / seg; verts.append(base + (n * math.cos(a) + b * math.sin(a)) * rad)
    mid = base + d * length * 0.5 + (np.array(curve) * length * 0.15 if curve is not None else 0)
    for k in range(seg):
        a = TAU * k / seg; verts.append(mid + (n * math.cos(a) + b * math.sin(a)) * rad * 0.55)
    tip = base + d * length + (np.array(curve) * length * 0.35 if curve is not None else 0); verts.append(tip)
    faces, uvs = [], []
    for k in range(seg):
        k1 = (k + 1) % seg
        faces.append((k, k1, seg + k1, seg + k)); uvs.append([(0, 0), (1, 0), (1, .5), (0, .5)])
        faces.append((seg + k, seg + k1, 2 * seg)); uvs.append([(0, .5), (1, .5), (.5, 1)])
    pc.add(verts, faces, uvs, mat, [w] * len(verts))

def stud(pc, p, ax, r, mat, bones):
    p = np.array(p, float); t0 = (p - ax.A) @ ax.d; out = p - (ax.A + ax.d * t0); out /= (np.linalg.norm(out) or 1)
    n = np.cross(out, [0, 1, 0]); n = n if np.linalg.norm(n) > 1e-3 else np.cross(out, [1, 0, 0]); n /= np.linalg.norm(n); b = np.cross(out, n)
    verts = [p + out * r * 1.2] + [p + (n * math.cos(a) + b * math.sin(a)) * r for a in np.linspace(0, TAU, 6, endpoint=False)]
    faces = [(0, 1 + k, 1 + (k + 1) % 6) for k in range(6)]
    pc.add(verts, faces, [[(.5, .5), (0, 0), (1, 0)]] * 6, mat, transfer([p], bones, k=6) * len(verts))

def ellipsoid(center, radii, rot=None, nu=12, nv=8):
    verts = []; faces = []
    for i in range(nv + 1):
        ph = math.pi * i / nv
        for j in range(nu):
            th = TAU * j / nu
            v = np.array([math.sin(ph) * math.cos(th) * radii[0], math.cos(ph) * radii[1], math.sin(ph) * math.sin(th) * radii[2]])
            verts.append(v)
    for i in range(nv):
        for j in range(nu):
            a, b = i * nu + j, i * nu + (j + 1) % nu
            faces.append((a, b, b + nu, a + nu))
    V = np.array(verts)
    if rot is not None: V = V @ np.array(rot).T
    return V + np.array(center), faces

def add_ell(pc, center, radii, mat, w, rot=None, nu=12, nv=8, squash=None):
    V, F = ellipsoid(center, radii, rot, nu, nv)
    uvs = [[(0, 0), (1, 0), (1, 1), (0, 1)]] * len(F)
    pc.add(V, [tuple(reversed(f)) for f in F], uvs, mat, [w] * len(V))

def rotm(d_from, d_to):
    a = np.array(d_from, float); b = np.array(d_to, float); a /= np.linalg.norm(a); b /= np.linalg.norm(b)
    v = np.cross(a, b); c = a.dot(b)
    if np.linalg.norm(v) < 1e-8: return np.eye(3) if c > 0 else -np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))

def skull(pc, center, facing, size, w, up=(0, 1, 0)):
    """kafatası süsü: kafatası kubbesi, elmacık, üst çene + dişler, alt çene, kızıl parlayan göz çukurları"""
    f = np.array(facing, float); f /= np.linalg.norm(f); u = np.array(up, float); u = u - f * u.dot(f); u /= np.linalg.norm(u); rgt = np.cross(u, f)
    M = np.stack([rgt, u, f], 1)  # yerel (x sağ, y yukarı, z ön) -> dünya
    def P(x, y, z): return np.array(center) + M @ (np.array([x, y, z]) * size)
    def E(c, r, nu=8, nv=5):
        V, F = ellipsoid((0, 0, 0), r, None, nu, nv); return [P(*(np.array(c) + v)) for v in V], F
    for c, r, m in [((0, 0.25, -0.05), (0.5, 0.48, 0.55), 'bone'), ((0, -0.08, 0.18), (0.4, 0.3, 0.38), 'bone'),
                    ((-0.27, -0.12, 0.2), (0.14, 0.12, 0.16), 'bone'), ((0.27, -0.12, 0.2), (0.14, 0.12, 0.16), 'bone'),
                    ((0, -0.36, 0.22), (0.24, 0.12, 0.2), 'bone'), ((0, -0.56, 0.12), (0.26, 0.11, 0.22), 'bone'),
                    ((-0.16, 0.0, 0.42), (0.11, 0.1, 0.06), 'eye'), ((0.16, 0.0, 0.42), (0.11, 0.1, 0.06), 'eye'),
                    ((0, -0.2, 0.5), (0.05, 0.08, 0.04), 'void')]:
        V, F = E(c, r); pc.add(V, [tuple(reversed(x)) for x in F], [[(0, 0), (1, 0), (1, 1), (0, 1)]] * len(F), m, [w] * len(V))
    for k in range(-2, 3):  # dişler
        V, F = E((k * 0.07, -0.44, 0.38), (0.03, 0.05, 0.026), 4, 3)
        pc.add(V, [tuple(reversed(x)) for x in F], [[(0, 0), (1, 0), (1, 1), (0, 1)]] * len(F), 'bone', [w] * len(V))

# ------------------------------------------------------------------ dokular (PIL, döşenebilir)
def noise(w, h, cell, seed, oct=3):
    g = np.random.default_rng(seed); out = np.zeros((h, w))
    for o in range(oct):
        n = max(2, int(w / cell * 2 ** o)); m = max(2, int(h / cell * 2 ** o))
        a = g.random((m, n)); a = np.pad(a, ((0, 1), (0, 1)), mode='wrap')
        im = Image.fromarray((a * 255).astype(np.uint8)).resize((w + w // n, h + h // m), Image.BICUBIC).crop((0, 0, w, h))
        out += np.asarray(im, float) / 255 / 2 ** o
    out -= out.min(); return out / max(out.max(), 1e-6)

def make_textures():
    T = {}
    # koyu çelik: dövme izleri + çizikler
    n = noise(512, 512, 64, 1); n2 = noise(512, 512, 16, 2)
    base = np.stack([n * 0 + 0.27, n * 0 + 0.25, n * 0 + 0.245], 2) * (0.75 + 0.4 * n[:, :, None]) * (0.9 + 0.2 * n2[:, :, None])
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    g = np.random.default_rng(3)
    for _ in range(160):
        x, y = g.integers(0, 512, 2); L = g.integers(8, 40); a = g.random() * TAU
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=(120, 116, 112), width=1)
    im.resize((256, 256), Image.LANCZOS).save(os.path.join(TEX, 'metal.jpg'), quality=86); T['metal'] = os.path.join(TEX, 'metal.jpg')
    # kızıl damar / kenar işlemesi (emisyon): kenar şeritleri + kırık rün damarları
    em = Image.new('RGB', (512, 512)); d = ImageDraw.Draw(em)
    for y in (10, 501): d.line([(0, y), (512, y)], fill=(150, 14, 8), width=2)
    g = np.random.default_rng(5)
    for k in range(5):
        x = 50 + k * 100 + g.integers(-15, 15); y = 40; pts = [(x, y)]
        while y < 470:
            y += g.integers(12, 26); x += g.integers(-10, 11); pts.append((x, y))
            if g.random() < 0.2: d.line([(x, y), (x + g.choice([-1, 1]) * g.integers(10, 26), y + g.integers(6, 16))], fill=(220, 25, 15), width=2)
        d.line(pts, fill=(200, 22, 12), width=2)
    em = em.filter(ImageFilter.GaussianBlur(1.2)).resize((256, 256), Image.LANCZOS); em.save(os.path.join(TEX, 'veins.jpg'), quality=85); T['veins'] = os.path.join(TEX, 'veins.jpg')
    # kızıl kumaş: dokuma + yıpranma
    n = noise(256, 256, 24, 9); y = np.arange(256)[:, None] / 255
    cl = np.stack([0.42 + 0 * n, 0.04 + 0 * n, 0.05 + 0 * n], 2) * (0.7 + 0.45 * n[:, :, None])
    weave = ((np.arange(256)[None, :] % 4 < 2) ^ (np.arange(256)[:, None] % 4 < 2)) * 0.06
    cl = cl * (0.94 + weave[:, :, None]) * (0.65 + 0.35 * (1 - y))[:, :, None]
    Image.fromarray((np.clip(cl, 0, 1) * 255).astype(np.uint8)).save(os.path.join(TEX, 'cloth.jpg'), quality=86); T['cloth'] = os.path.join(TEX, 'cloth.jpg')
    # tabar rünleri (emisyon, dikey sütun)
    rn = Image.new('RGB', (128, 512)); d = ImageDraw.Draw(rn); g = np.random.default_rng(11)
    for k in range(9):
        cy = 40 + k * 50; cx = 64; s = 13
        d.line([(cx, cy - s), (cx, cy + s)], fill=(255, 60, 30), width=3)
        for _ in range(g.integers(1, 4)):
            y0 = cy + g.integers(-s, s // 2); sd = g.choice([-1, 1]); d.line([(cx, y0), (cx + sd * 9, y0 + g.choice([-1, 1]) * 8)], fill=(255, 60, 30), width=3)
    rn = rn.filter(ImageFilter.GaussianBlur(1.0)); rn.save(os.path.join(TEX, 'runes.jpg'), quality=85); T['runes'] = os.path.join(TEX, 'runes.jpg')
    return T

def material(name, T):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    def tex(path, inp, cs=True):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
        if not cs: t.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(t.outputs['Color'], b.inputs[inp]); return t
    cfg = {'metal': dict(c=None, met=0.85, rough=0.42, tex='metal', em='veins'),
           'plate': dict(c=None, met=0.85, rough=0.38, tex='metal'),
           'trim': dict(c=(0.075, 0.05, 0.048), met=0.95, rough=0.3, emc=(0.05, 0.002, 0.001)),
           'cloth': dict(c=None, met=0.0, rough=0.85, tex='cloth'),
           'tabard': dict(c=None, met=0.0, rough=0.85, tex='cloth', em='runes'),
           'bone': dict(c=(0.26, 0.22, 0.16), met=0.0, rough=0.65),
           'eye': dict(c=(0.05, 0, 0), met=0.0, rough=0.5, emc=(1.0, 0.06, 0.02)),
           'void': dict(c=(0.01, 0.01, 0.01), met=0.0, rough=0.9),
           'spike': dict(c=(0.09, 0.085, 0.09), met=0.9, rough=0.3)}[name]
    if cfg.get('tex'): tex(T[cfg['tex']], 'Base Color')
    else: b.inputs['Base Color'].default_value = (*cfg['c'], 1)
    b.inputs['Metallic'].default_value = cfg['met']; b.inputs['Roughness'].default_value = cfg['rough']
    if cfg.get('em'):
        tex(T[cfg['em']], 'Emission Color'); b.inputs['Emission Strength'].default_value = 1.0
    elif cfg.get('emc'):
        b.inputs['Emission Color'].default_value = (*cfg['emc'], 1); b.inputs['Emission Strength'].default_value = 1.0
    m.use_backface_culling = False
    return m

# ================================================================== Meshy zırhının dış yüzeyi (açıklık hesabı için)
import struct
def glb_positions(path):
    d = open(path, 'rb').read(); l = struct.unpack_from('<I', d, 12)[0]; j = json.loads(d[20:20 + l]); bin_ = d[20 + l + 8:]
    out = []
    for m in j['meshes']:
        for p in m['primitives']:
            a = j['accessors'][p['attributes']['POSITION']]; bv = j['bufferViews'][a['bufferView']]
            out.append(np.frombuffer(bin_, np.float32, a['count'] * 3, bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 3))
    return np.concatenate(out)
KV = np.concatenate([glb_positions(os.path.join(KDIR, f)) for f in os.listdir(KDIR) if f.endswith('.glb')])
print('Meshy zırh köşesi', len(KV))
pieces = {}
def P(name):
    pieces[name] = Piece(name); return pieces[name]
NECK, HEAD, TOP, SP2 = JW['Neck'], JW['Head'], JW['HeadTop_End'], JW['Spine2']
TORSO = bone_set('Hips', 'Spine', 'Spine1', 'Spine2', 'LeftShoulder', 'RightShoulder')

# ---------------- BOYUNLUK: boyundan omuz üstlerine açılan yaka + apolet (pürüzlü yaka bölgesini örter)
pc = P('boyunluk')
cax = Axis((0, NECK[1] - 19, NECK[2]), (0, NECK[1] + 8, NECK[2] + 1), (0, 0, 1))
NB = bone_set('Neck', 'Spine2', 'LeftShoulder', 'RightShoulder')
nprof = Profile(cax, bone_set('Neck'), 0.5, 1.0, nt=6, nth=32, dil=1, sm=2)
def knight_r(y0, y1, th, cap):
    m = (KV[:, 1] > y0) & (KV[:, 1] < y1); q = KV[m] - np.array([0, 0, NECK[2]])
    ang = np.arctan2(q[:, 0], q[:, 2]); r = np.hypot(q[:, 0], q[:, 2])
    sel = np.abs((ang - th + math.pi) % TAU - math.pi) < 0.2
    return min(cap, r[sel].max() if sel.any() else cap)
RB = {}
def mantle_r(t, th, s):
    key = round(th, 4)
    if key not in RB: RB[key] = knight_r(NECK[1] - 22, NECK[1] - 4, th, 25.0) + 3.0
    rt = nprof(0.88, th) + 2.6
    return RB[key] + (rt - RB[key]) * s ** 1.7      # dışbükey: omuz hattında geniş kalır, boyna doğru daralır
class Zero:
    def __call__(s, t, th): return 0.0
loft_piece(pc, cax, Zero(), -math.pi, math.pi, lambda th: 0.0, lambda th: 1.0, 0.0, 'metal', 32, 8, NB, urep=3,
           mod=mantle_r, rim=['top', 'bottom'], rivet=['bottom'])
for a in (2.5, 2.9, 3.4, 3.8):
    p = cax.point(0.55, a, mantle_r(0.55, a, 0.55) + 0.5)
    cone_piece(pc, p, (math.sin(a) * 0.5, 1, -0.6), 5.5, 1.1, 'spike', anchor_w(p, NB))

# ---------------- PELERİN: omuz hattından diz hizasına, zırhın sırtının dışında, yırtık alt kenar
pc = P('pelerin')
def back_z(y, half):
    m = (np.abs(KV[:, 1] - y) < 4) & (np.abs(KV[:, 0]) < half)
    return KV[m, 2].min() if m.any() else -16
rows, cols = 16, 12; cv, cf, cuv = [], [], []
ytop = NECK[1] - 10
for i in range(rows + 1):
    s = i / rows; y = ytop - s * 92
    half = 17 + 15 * s
    zb = back_z(max(y, 60), 20) - 2.5
    for j in range(cols + 1):
        u = j / cols; x = -half + 2 * half * u
        z = zb - 7 * s ** 1.5 - 2.0 * math.sin(u * math.pi) * (1 - s) + 1.2 * math.sin(u * 9 + s * 4) * s
        cv.append((x, y + (rng.random() * 8 + 3 * (j % 2) if i == rows else 0), z))
for i in range(rows):
    for j in range(cols):
        a = i * (cols + 1) + j; cf.append((a, a + 1, a + cols + 2, a + cols + 1))
        cuv.append([(j / cols, 1 - i / rows), ((j + 1) / cols, 1 - i / rows), ((j + 1) / cols, 1 - (i + 1) / rows), (j / cols, 1 - (i + 1) / rows)])
def cape_w(verts):
    out = []
    for v in verts:
        s = (ytop - v[1]) / 92
        wb = anchor_w(np.array([0, max(v[1], 104), -12]), TORSO)
        if s > 0.5:
            k = min(1, (s - 0.5) / 0.5) * 0.45; wb = wb * (1 - k); wb[BI['LeftUpLeg']] += k * 0.5; wb[BI['RightUpLeg']] += k * 0.5
        out.append(wb / wb.sum())
    return out
pc.add(cv, [tuple(reversed(f)) for f in cf], [list(reversed(u)) for u in cuv], 'cloth', cape_w(cv))
zt = back_z(ytop, 20) - 2.5
for sx in (-1, 1):
    add_ell(pc, (sx * 15, ytop + 1, zt + 1), (2.6, 2.6, 1.4), 'trim', anchor_w(np.array([sx * 15, ytop, zt]), TORSO), nu=10, nv=6)

# ---------------- MİĞFER: kapalı başlık, göz yarığı (kızıl parlayan gözler), taç dikenleri
pc = P('migfer')
hax = Axis(NECK + np.array([0, 3, 0]), TOP, (0, 0, 1))
HB = bone_set('Head', 'HeadTop_End')
hprof = Profile(hax, HB, 0.0, 1.0, nt=14, nth=28, dil=2, sm=2)
wh = anchor_w(HEAD + np.array([0, 8, 2]), HB)
fix = lambda verts: [wh] * len(verts)
def helm_mod(t, th, s):
    dome = -(hprof(t, th) + 1.8) * max(0, (s - 0.86) / 0.14) ** 1.5             # tepe tam kapanır
    face = 1.2 * math.exp(-(th / 0.35) ** 2) * math.exp(-((s - 0.42) / 0.25) ** 2)   # ön sırt (burun çıkıntısı)
    flare = 2.2 * max(0, (0.12 - s) / 0.12)                                   # alt kenar boyun üstüne açılır
    return dome + face + flare
loft_piece(pc, hax, hprof, -math.pi, math.pi, lambda th: 0.0, lambda th: 1.0, 1.8, 'metal', 28, 14, HB, urep=2, mod=helm_mod, rim=['bottom'], wfn=fix)
# göz yarığı + gözler
ey = 0.47
slit = [hax.point(ey, a, hprof(ey, a) + 1.8 + helm_mod(ey, a, ey) + 0.2) for a in np.linspace(-0.75, 0.75, 9)]
tube_piece(pc, slit, 0.75, 'void', HB, seg=5, wfn=fix)
for a in (-0.35, 0.35):
    add_ell(pc, hax.point(ey, a, hprof(ey, a) + 1.8 + helm_mod(ey, a, ey) + 0.6), (1.1, 0.55, 0.5), 'eye', wh, nu=8, nv=5)
# taç dikenleri (tepede halka)
for k in range(9):
    a = -math.pi + TAU * (k + 0.5) / 9; tt = 0.86
    p = hax.point(tt, a, (hprof(tt, a) + 1.8 + helm_mod(tt, a, tt)) * 0.95)
    ln = 7.5 if abs(a) < 0.5 else 5.5
    cone_piece(pc, p, (math.sin(a) * 0.25, 1, math.cos(a) * 0.25), ln, 1.1, 'spike', wh)
tube_piece(pc, [hax.point(0.84, a, (hprof(0.84, a) + 1.8 + helm_mod(0.84, a, 0.84)) * 0.98) for a in np.linspace(-math.pi, math.pi, 29)], 0.7, 'trim', HB, seg=5, wfn=fix)

# ================================================================== Blender: iskelet + parça nesneleri + GLB
bpy.ops.wm.read_factory_settings(use_empty=True)
T = make_textures(); MATS = {}
def M(n):
    if n not in MATS: MATS[n] = material(n, T)
    return MATS[n]

arm_d = bpy.data.armatures.new('ValkorRig'); arm = bpy.data.objects.new('ValkorRig', arm_d); bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm; arm.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
for b, d in zip(BN, J['bones']):
    e = arm_d.edit_bones.new(b); h = Vector(b2(JW[b.replace('mixamorig', '')])); e.head = h; e.tail = h + Vector((0, 0, 3))
for b, d in zip(BN, J['bones']):
    if d['p'] >= 0: arm_d.edit_bones[b].parent = arm_d.edit_bones[BN[d['p']]]
bpy.ops.object.mode_set(mode='OBJECT')

report = []
for name, pc in pieces.items():
    me = bpy.data.meshes.new(name)
    me.from_pydata([b2(v) for v in pc.V], [], pc.F)
    uvl = me.uv_layers.new(name='UVMap')
    li = 0
    for fi, poly in enumerate(me.polygons):
        for k, l in enumerate(poly.loop_indices): uvl.data[l].uv = pc.UV[fi][k]
        poly.material_index = pc.FM[fi]; poly.use_smooth = True
    for m in pc.mats: me.materials.append(M(m))
    me.validate(); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    W = np.array(pc.W)
    for bi, bn_ in enumerate(BN):
        col = W[:, bi]; nz = np.nonzero(col > 0.01)[0]
        if len(nz) == 0: continue
        g = o.vertex_groups.new(name=bn_)
        for i in nz: g.add([int(i)], float(col[i]), 'REPLACE')
    if name in ('eldiven', 'botlar'):
        dm = o.modifiers.new('dec', 'DECIMATE'); dm.ratio = 0.42 if name == 'eldiven' else 0.55
        bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.modifier_apply(modifier=dm.name); o.select_set(False)
    o.parent = arm; md = o.modifiers.new('Armature', 'ARMATURE'); md.object = arm
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True)
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); arm.select_set(True)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_skins=True,
                              export_animations=False, export_image_format='AUTO', export_jpeg_quality=86, export_def_bones=False)
    report.append((name, tris, len(me.vertices), os.path.getsize(path)))
    print('PARÇA', name, 'üçgen', tris, 'köşe', len(me.vertices), 'bayt', os.path.getsize(path), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, '_armor.blend'))
json.dump(report, open(os.path.join(OUT, '_report.json'), 'w'), indent=1)

