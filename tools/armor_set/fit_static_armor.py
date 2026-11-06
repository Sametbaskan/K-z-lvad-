# VALKOR - iskeletsiz (heykel duruşlu) zırh modelini savaşçı iskeletine bağlar: "Güneş Şövalyesi" (SunKnightWarrior.fbx, FERUL).
#   python3 -I fit_static_armor.py -- <model.fbx> <hero.json> <doku_klasörü> <çıkış> [hedef_üçgen]
# Yöntem (tek karışımlı bağlama):
#  1) Model düz önüne baktırılır, cm'ye çevrilir; elindeki kılıç (bıçak, muhafız, kabza) eksen boyunca kesilir; mobil için sadeleştirilir.
#  2) Heykelin eklemleri (JOINTS) elle ölçüldü; köşe ağırlıkları bölgelere göre (baş, kol, bacak, gövde, pelerin) hesaplanıp kenar komşuluğunda yumuşatılır.
#  3) Her kemik için X_i (heykel kemiği -> savaşçı kemiği: eklem + yön + boy) bulunur ve özel bağlama matrisi Inv_i = H_i^-1 · X_i yazılır.
#     Köşeler heykel duruşunda kalır; oyunda  v' = Σ w_i · A_i · H_i^-1 · X_i · v  → kollar T-poza çevrilip geri bükülmez (çift karışım hatası yok).
#  4) Parçalar ayrı GLB (doku gömülmez): govde, bacak, pelerin, bas, hale, botlar. Ortak dokular 1024 (renk / metal-pürüzlülük / normal).
import sys, os, json, math, struct
import numpy as np
import bpy, bmesh
from mathutils import Matrix, Vector
from PIL import Image

a = sys.argv[sys.argv.index('--') + 1:]
SRC, HERO, TEXIN, OUT = a[0], a[1], a[2], os.path.abspath(a[3]); TARGET = int(a[4]) if len(a) > 4 else 36000
SET = 'gunes_sovalyesi'
os.makedirs(os.path.join(OUT, 'tex'), exist_ok=True)

# ---------------- heykel eklemleri (hazırlanmış uzayda: x = karakterin solu, y = arka, z = yukarı, cm)
JOINTS = {"Hips": [0, 0, 88], "Spine": [0, 0, 98], "Spine1": [0, 0, 108], "Spine2": [0, 0, 118], "Neck": [0, -2, 134], "Head": [0, -4, 141], "HeadTop_End": [0, -4, 158],
          "LeftShoulder": [6, 0, 128], "LeftArm": [20, 1, 124], "LeftForeArm": [33, 3, 98], "LeftHand": [36, -12, 72], "LeftHandTip": [38, -33, 62],
          "RightShoulder": [-6, 0, 128], "RightArm": [-20, 1, 124], "RightForeArm": [-33, 3, 98], "RightHand": [-36, -8, 68], "RightHandTip": [-36, -18, 56],
          "LeftUpLeg": [11, 0, 85], "LeftLeg": [18, -4, 53], "LeftFoot": [22, 4, 10], "LeftToeBase": [22, -12, 3], "LeftToe_End": [22, -26, 2],
          "RightUpLeg": [-11, 0, 85], "RightLeg": [-18, -4, 53], "RightFoot": [-22, 4, 10], "RightToeBase": [-22, -12, 3], "RightToe_End": [-22, -26, 2]}
JS = {k: np.array(v, float) for k, v in JOINTS.items()}

# ---------------- 1) içe aktar, hizala, kılıcı kes, sadeleştir
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
me.transform(Matrix.Rotation(-math.pi / 2, 4, 'Z')); me.transform(Matrix.Scale(240, 4))
me.transform(Matrix.Rotation(math.radians(19.7), 4, 'Z'))          # gövde 19.7° dönük duruyor
me.transform(Matrix.Translation((0.293, 1.456, 0)))                  # leğen merkezi orijine
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
# kılıç ekseni (bıçak kesitlerinden): c + s·d
C_AX = np.array([-6.44, -34.27, 26.07]); D_AX = np.array([-0.467, 0.418, 0.779])
def sword_vert(p):
    p = np.array(p); s = (p - C_AX) @ D_AX; r = np.linalg.norm(p - C_AX - s * D_AX); z = C_AX[2] + s * D_AX[2]
    if z < 47.5: return r < 5.5          # bıçak
    if z < 58.5: return r < 13.0 and p[1] < -12.5   # muhafız: yalnız uyluk zırhının önünde (uyluk delinmesin)
    if z < 71: return r < 14.0 and p[1] < -19.5 and p[0] > -29   # muhafızın yukarı uzanan dikeni (yumruğun önünde)
    return False                         # kabza yumruğun içinde kalır (parmaklar bütün; oyundaki kılıç bu ele oturur)
dead = [v for v in bm.verts if sword_vert(v.co)]
bmesh.ops.delete(bm, geom=dead, context='VERTS')
# kesimden kalan küçük kopuk parçalar
bm.verts.ensure_lookup_table(); seen = set(); drop = []
for v in bm.verts:
    if v.index in seen: continue
    comp = []; st = [v]; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    if len(comp) < 400: drop += comp
bmesh.ops.delete(bm, geom=drop, context='VERTS')
print('kılıç köşesi silindi', len(dead), 'kopuk', len(drop))
bm.to_mesh(me); bm.free()
ntri = sum(len(p.vertices) - 2 for p in me.polygons)
md = ob.modifiers.new('d', 'DECIMATE'); md.ratio = TARGET / ntri; bpy.ops.object.modifier_apply(modifier='d')
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
me.calc_loop_triangles() if hasattr(me, 'calc_loop_triangles') else None
print('üçgen', ntri, '->', len(me.polygons))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, '_cut.blend'))
V = np.array([v.co[:] for v in me.vertices]); NV = len(V)
TRI = np.array([p.vertices[:] for p in me.polygons])
LUV = np.array([d.uv[:] for d in me.uv_layers.active.data]); TLOOP = np.array([p.loop_indices[:] for p in me.polygons])
E = np.array([e.vertices[:] for e in me.edges])

# ---------------- 2) ağırlıklar
J = json.load(open(HERO)); BN = [b['n'] for b in J['bones']]; SH = [n.replace('mixamorig', '') for n in BN]; BI = {n: i for i, n in enumerate(SH)}
HINV = {n: np.array(inv).reshape(4, 4).T for n, inv in zip(SH, J['inv'])}       # satır düzeni
HW = {n: np.linalg.inv(HINV[n])[:3, 3] for n in SH}
def segd(P, A, B):
    ab = B - A; t = np.clip(((P - A) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P - (A + t[:, None] * ab), axis=1), t
def smooth01(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
W = np.zeros((NV, len(BN)))
x, y, z = V[:, 0], V[:, 1], V[:, 2]
# zincirler
def chain(segs):  # [(bone, A, B, R)] -> (en yakın uzaklık / R oranı, ters-uzaklık ağırlıkları)
    D = np.stack([segd(V, JS[A], JS[B])[0] / R for _, A, B, R in segs], 1)
    w = 1 / np.maximum(D, 0.05) ** 4; w /= w.sum(1, keepdims=True); return D.min(1), w
done = np.zeros(NV, bool)
GRP = np.full(NV, 'torso', object)   # bölge: head, armL, armR, legL, legR, torso, cloak
# baş (miğfer + hale): katı
head = z > 136.5
W[head, BI['Head']] = 1; done |= head; GRP[head] = 'head'
nb = (z > 131) & (z <= 136.5) & (np.abs(x) < 11)
k = smooth01(z[nb], 131, 136.5); W[nb, BI['Head']] = k; W[nb, BI['Neck']] = 1 - k; done |= nb; GRP[nb] = 'head'
# kollar (omuzluk dahil)
for s, sg in (('Left', 1), ('Right', -1)):
    segs = [(s + 'Arm', s + 'Arm', s + 'ForeArm', 12.0), (s + 'ForeArm', s + 'ForeArm', s + 'Hand', 9.5), (s + 'Hand', s + 'Hand', s + 'HandTip', 13.0 if s == 'Right' else 10.5)]   # sağ yumruk + kabza ucu geniş
    dmin, w = chain(segs)
    arm = (~done) & (dmin < 1.0) & (sg * x > (14 if s == 'Left' else 12)) & (z < 133)
    for j, (b, *_ ) in enumerate(segs): W[arm, BI[b]] = w[arm, j]
    done |= arm; GRP[arm] = 'arm' + s[0]
    pa = (~done) & (sg * x > 13) & (z > 104) & (z < 134)                # omuzluk kubbesi / omuz: kol + köprücük
    k = smooth01(sg * x[pa], 13, 22); W[pa, BI[s + 'Arm']] = k; W[pa, BI[s + 'Shoulder']] = (1 - k) * 0.5; W[pa, BI['Spine2']] = (1 - k) * 0.5; done |= pa; GRP[pa] = 'arm' + s[0]
# bacaklar
CLOAK = np.zeros(NV, bool)
for s, sg in (('Left', 1), ('Right', -1)):
    segs = [(s + 'UpLeg', s + 'UpLeg', s + 'Leg', 10.5), (s + 'Leg', s + 'Leg', s + 'Foot', 8.5), (s + 'Foot', s + 'Foot', s + 'ToeBase', 8.0), (s + 'ToeBase', s + 'ToeBase', s + 'Toe_End', 7.0)]
    dmin, w = chain(segs)
    leg = (~done) & (dmin < 1.0) & (z < 86)
    for j, (b, *_ ) in enumerate(segs): W[leg, BI[b]] = w[leg, j]
    done |= leg; GRP[leg] = 'leg' + s[0]
# gövde (z > 84): omurga zinciri yüksekliğe göre
TOR = [('Hips', 88), ('Spine', 98), ('Spine1', 108), ('Spine2', 118), ('Neck', 134)]
tm = (~done) & (z > 84)
zt = np.clip(z[tm], 88, 134); idx = np.searchsorted([t[1] for t in TOR], zt, side='right') - 1; idx = np.clip(idx, 0, len(TOR) - 2)
for i in range(len(TOR) - 1):
    m = idx == i; f = (zt[m] - TOR[i][1]) / (TOR[i + 1][1] - TOR[i][1]); rows = np.nonzero(tm)[0][m]
    W[rows, BI[TOR[i][0]]] += 1 - f; W[rows, BI[TOR[i + 1][0]]] += f
done |= tm
# pelerin / etek (kalan, z <= 84): leğen + aynı taraftaki uyluk (aşağı indikçe artar)
cm = ~done; CLOAK[cm] = True; GRP[cm] = 'cloak'
kk = 0.6 * smooth01(84 - z[cm], 0, 70); left = smooth01(x[cm], -10, 10)
W[cm, BI['Hips']] = 1 - kk; W[cm, BI['LeftUpLeg']] = kk * left; W[cm, BI['RightUpLeg']] = kk * (1 - left)
# küçük bölge adacıkları (ör. yumruğa yapışık ama pelerin sayılmış parçalar): komşu bölgeye katılır, ağırlığı komşudan alınır
from collections import Counter
nbr = [[] for _ in range(NV)]
for i, j in E: nbr[i].append(j); nbr[j].append(i)
for pas in range(3):
    lab = -np.ones(NV, int); comps = []
    for v0 in range(NV):
        if lab[v0] >= 0: continue
        st = [v0]; lab[v0] = len(comps); cc = []
        while st:
            u = st.pop(); cc.append(u)
            for w_ in nbr[u]:
                if lab[w_] < 0 and GRP[w_] == GRP[v0]: lab[w_] = len(comps); st.append(w_)
        comps.append(cc)
    moved = 0
    for cc in comps:
        if len(cc) >= 150: continue
        g0 = GRP[cc[0]]; ext = Counter(); src = {}
        for u in cc:
            for w_ in nbr[u]:
                if GRP[w_] != g0: ext[GRP[w_]] += 1; src.setdefault(GRP[w_], []).append(w_)
        if not ext or (g0 == 'head'): continue
        g1 = ext.most_common(1)[0][0]; wn = W[src[g1]].mean(0)
        for u in cc: GRP[u] = g1; W[u] = wn
        CLOAK[cc] = (g1 == 'cloak'); moved += len(cc)
    print('adacık birleştirme', pas, moved)
# kenar komşuluğunda yumuşatma — yalnız anatomik olarak bağlı bölgeler arasında (el pelerine değse de ağırlık karışmaz)
def allowed(g1, g2, z1, z2):
    if g1 == g2: return True
    pr = {g1, g2}
    if pr <= {'torso', 'cloak', 'legL', 'legR'} and not pr == {'legL', 'legR'}: return True
    if pr == {'head', 'torso'}: return True
    if len(pr & {'armL', 'armR'}) == 1 and (pr - {'armL', 'armR'}) == {'torso'}: return min(z1, z2) > 104   # yalnız omuz hattında
    return False
AL = np.array([allowed(GRP[i], GRP[j], z[i], z[j]) for i, j in E]); EA = E[AL]
print('kesilen kenar (bölgeler arası)', int((~AL).sum()))
W0 = W.copy()
for it in range(4):
    acc = np.zeros_like(W); cnt = np.zeros(NV)
    np.add.at(acc, EA[:, 0], W[EA[:, 1]]); np.add.at(acc, EA[:, 1], W[EA[:, 0]]); np.add.at(cnt, EA[:, 0], 1); np.add.at(cnt, EA[:, 1], 1)
    nbw = acc / np.maximum(cnt, 1)[:, None]; W = np.where((head[:, None]) | (cnt[:, None] == 0), W, 0.5 * W + 0.5 * nbw)
# en fazla 4 etki
Wt_full = W / W.sum(1, keepdims=True)
order = np.argsort(-W, 1)[:, :4]; Wt = np.take_along_axis(W, order, 1); Wt /= Wt.sum(1, keepdims=True)
print('ağırlık: baş', head.sum(), 'pelerin', CLOAK.sum())

# ---------------- 3) savaşçı iskeletini heykelin duruşuna poz ver (zincir boyunca tutarlı burulma) -> özel bağlama matrisleri
#   M_i: savaşçı dinlenme uzayı -> heykel uzayı (kemik i için),  M_i(x) = JP_i + D_i · Sc_i · (x - HW_i)
#   D_i = salınım(ebeveynden devralınan yön -> heykel kemik yönü) · D_ebeveyn  (burulma ebeveynden gelir: el ve ön kol uyumlu)
#   Inv_i = H_i^-1 · M_i^-1  →  oyunda v' = Σ w · A_i · Inv_i · v
def T3(p): p = np.asarray(p, float); return np.array([p[0], p[2], -p[1]])
G = 1.18                                                              # heykel -> savaşçı boyu
KS = {k: T3(v) for k, v in JS.items()}
JP = {k: HW['Hips'] + G * (v - KS['Hips']) for k, v in KS.items()}  # ölçekli heykel eklemleri (savaşçı uzayında)
def swing(a_, b_):
    a_ = a_ / np.linalg.norm(a_); b_ = b_ / np.linalg.norm(b_); v = np.cross(a_, b_); c = a_ @ b_
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + vx + vx @ vx / (1 + c)
CHILD = {'Hips': ('Spine', 'Spine'), 'Spine': ('Spine1', 'Spine1'), 'Spine1': ('Spine2', 'Spine2'), 'Spine2': ('Neck', 'Neck'), 'Neck': ('Head', 'Head'), 'Head': ('HeadTop_End', 'HeadTop_End')}
for s_ in ('Left', 'Right'):
    for a_, b_ in (('Shoulder', 'Arm'), ('Arm', 'ForeArm'), ('ForeArm', 'Hand'), ('UpLeg', 'Leg'), ('Leg', 'Foot'), ('Foot', 'ToeBase'), ('ToeBase', 'Toe_End')):
        CHILD[s_ + a_] = (s_ + b_, s_ + b_)
    CHILD[s_ + 'Hand'] = (s_ + 'HandTip', s_ + 'HandMiddle4')
PAR = {SH[i]: (SH[b['p']] if b['p'] >= 0 else None) for i, b in enumerate(J['bones'])}
D, M = {}, {}
def aff(lin, src, dst):  # x -> dst + lin (x - src)
    A_ = np.eye(4); A_[:3, :3] = lin; A_[:3, 3] = dst - lin @ src; return A_
for n in SH:                                                          # hero.json: ebeveyn her zaman önce gelir
    p_ = PAR[n]; Dp = D[p_] if p_ else np.eye(3)
    if n in CHILD and n in JP:
        kc, hc = CHILD[n]; hv = HW[hc] - HW[n]; sv = JP[kc] - JP[n]
        D[n] = swing(Dp @ hv, sv) @ Dp
        u = hv / np.linalg.norm(hv); f = (np.linalg.norm(sv) / np.linalg.norm(hv)) ** 0.5   # boy farkının yarısı ölçekle, yarısı eklemde
        M[n] = aff(D[n] @ (np.eye(3) + (f - 1) * np.outer(u, u)), HW[n], JP[n])
        print(f'  {n:>14} boy oranı {np.linalg.norm(sv) / np.linalg.norm(hv):.2f}')
    else:                                                             # parmaklar, uçlar: ebeveyne katı bağlı
        D[n] = Dp; M[n] = M[p_] if p_ else np.eye(4)
INV = np.stack([HINV[n] @ np.linalg.inv(M[n]) for n in SH])

# ---------------- 4) parçalar
P3 = HW['Hips'] + G * (np.stack([x, z, -y], 1) - KS['Hips'])        # ölçekli heykel köşeleri (savaşçı uzayında)
dom = np.array(SH)[W.argmax(1)]
halo = head & (y > 4.0)
part = np.empty(NV, object)
for i in range(NV):
    b = dom[i]
    if halo[i]: part[i] = 'hale'
    elif b in ('Head', 'Neck', 'HeadTop_End') or head[i]: part[i] = 'bas'
    elif CLOAK[i]: part[i] = 'pelerin'
    elif 'Foot' in b or 'Toe' in b or (('Leg' in b and 'Up' not in b) and z[i] < 18): part[i] = 'botlar'
    elif 'UpLeg' in b or ('Leg' in b) or b == 'Hips' and z[i] < 90: part[i] = 'bacak'
    else: part[i] = 'govde'
groups = {}
for t, tri in enumerate(TRI):
    ps = [part[v] for v in tri]; p = max(set(ps), key=ps.count); groups.setdefault(p, []).append(t)

# üçgen bölgesi (çoğunluk); izinsiz sınırdaki köşeler o üçgende bölgenin ağırlığıyla kopyalanır
TG = np.empty(len(TRI), object); SEAM = {}
for t, tri in enumerate(TRI):
    gs = [GRP[v] for v in tri]; TG[t] = max(set(gs), key=gs.count)
    for v in tri:
        if GRP[v] != TG[t] and not allowed(GRP[v], TG[t], z[v], z[v]):
            own = [u for u in tri if GRP[u] == TG[t]]
            ww = np.mean([Wt_full[u] for u in own], 0); SEAM[(v, TG[t])] = ww
print('dikiş kopyası', len(SEAM))
# normaller (heykel uzayında, three eksenlerine)
me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
VN = np.array([v.normal[:] for v in me.vertices]); N3 = np.stack([VN[:, 0], VN[:, 2], -VN[:, 1]], 1)

def write_glb(path, name, mat, vids, tris):
    remap = np.full(NV, -1); remap[vids] = np.arange(len(vids))
    # köşe başına uv: döngü uv'lerinden (dikişte köşe kopyalanır)
    keys = {}; pos, nrm, uv, jj, ww, idx = [], [], [], [], [], []
    for t in tris:
        for k_, li in zip(TRI[t], TLOOP[t]):
            u_, v_ = LUV[li]; sk = (k_, TG[t]) if (k_, TG[t]) in SEAM else None; key = (k_, round(u_, 5), round(v_, 5), sk)
            if key not in keys:
                keys[key] = len(pos); pos.append(P3[k_]); nrm.append(N3[k_]); uv.append((u_, 1 - v_))
                if sk: wf = SEAM[sk]; oo = np.argsort(-wf)[:4]; wv = wf[oo] / wf[oo].sum(); jj.append(oo); ww.append(wv)
                else: jj.append(order[k_]); ww.append(Wt[k_])
            idx.append(keys[key])
    pos = np.array(pos, np.float32); nrm = np.array(nrm, np.float32); uv = np.array(uv, np.float32)
    jj = np.array(jj, np.uint16); ww = np.array(ww, np.float32); idx = np.array(idx, np.uint32)
    ib = INV.transpose(0, 2, 1).reshape(-1).astype(np.float32)          # sütun düzeni
    blobs = [pos, nrm, uv, jj, ww, idx, ib]; views = []; bin_ = b''
    for bl in blobs:
        while len(bin_) % 4: bin_ += b'\0'
        views.append({'buffer': 0, 'byteOffset': len(bin_), 'byteLength': bl.nbytes}); bin_ += bl.tobytes()
    while len(bin_) % 4: bin_ += b'\0'
    acc = [{'bufferView': 0, 'componentType': 5126, 'count': len(pos), 'type': 'VEC3', 'min': pos.min(0).tolist(), 'max': pos.max(0).tolist()},
           {'bufferView': 1, 'componentType': 5126, 'count': len(pos), 'type': 'VEC3'},
           {'bufferView': 2, 'componentType': 5126, 'count': len(pos), 'type': 'VEC2'},
           {'bufferView': 3, 'componentType': 5123, 'count': len(pos), 'type': 'VEC4'},
           {'bufferView': 4, 'componentType': 5126, 'count': len(pos), 'type': 'VEC4'},
           {'bufferView': 5, 'componentType': 5125, 'count': len(idx), 'type': 'SCALAR'},
           {'bufferView': 6, 'componentType': 5126, 'count': len(BN), 'type': 'MAT4'}]
    nodes = [{'name': name, 'mesh': 0, 'skin': 0}] + [{'name': n} for n in BN]
    gl = {'asset': {'version': '2.0', 'generator': 'VALKOR fit_static_armor'}, 'scene': 0, 'scenes': [{'nodes': list(range(len(nodes)))}], 'nodes': nodes,
          'meshes': [{'name': name, 'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2, 'JOINTS_0': 3, 'WEIGHTS_0': 4}, 'indices': 5, 'material': 0}]}],
          'materials': [{'name': mat, 'pbrMetallicRoughness': {'metallicFactor': 1, 'roughnessFactor': 1}}],
          'skins': [{'joints': list(range(1, len(nodes))), 'inverseBindMatrices': 6}],
          'accessors': acc, 'bufferViews': views, 'buffers': [{'byteLength': len(bin_)}]}
    js = json.dumps(gl, separators=(',', ':')).encode()
    while len(js) % 4: js += b' '
    out = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(bin_)) + b'BIN\0' + bin_
    open(path, 'wb').write(out); return len(idx) // 3, len(pos), len(out)

np.savez(os.path.join(OUT, '_dbg.npz'), P3=P3, order=order, Wt=Wt, INV=INV, M=np.stack([M[n] for n in SH]), HINV=np.stack([HINV[n] for n in SH]), E=E, V=V, part=np.array([str(q) for q in part]), grp=np.array([str(q) for q in GRP]))
report = []
for name, tris in sorted(groups.items()):
    tris = np.array(tris); vids = np.unique(TRI[tris])
    nt, nv, sz = write_glb(os.path.join(OUT, name + '.glb'), name, SET + ('_hale' if name == 'hale' else ''), vids, tris)
    report.append((name, nt, nv, sz)); print('PARÇA', name, 'üçgen', nt, 'köşe', nv, 'bayt', sz, flush=True)
json.dump(report, open(os.path.join(OUT, '_report.json'), 'w'), indent=1)

# ---------------- dokular (1024): renk, metal-pürüzlülük (G = pürüzlülük, B = metal), normal
def ld(n): return Image.open(os.path.join(TEXIN, f'SunKnightWarrior_{n}.JPEG')).convert('RGB').resize((1024, 1024), Image.LANCZOS)
ld('basecolor').save(os.path.join(OUT, 'tex', 'base.jpg'), quality=88)
r_ = np.asarray(ld('roughness'))[:, :, 0]; m_ = np.asarray(ld('metallic'))[:, :, 0]
Image.fromarray(np.stack([np.zeros_like(r_), r_, m_], 2)).save(os.path.join(OUT, 'tex', 'mr.jpg'), quality=90)
ld('normal').save(os.path.join(OUT, 'tex', 'normal.jpg'), quality=90)
print('dokular tamam')
