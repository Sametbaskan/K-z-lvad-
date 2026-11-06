# VALKOR - Meshy'den gelen iskeletli karakter GLB'sindeki zırhı savaşçıya (models/hero.json) uyarlar.
#   python3 -I fit_meshy_armor.py -- <meshy.glb> <hero.json> <çıkış> [set_adı]
# Adımlar:
#  1) Meshy modeli bağlama (T) pozunda okunur; saç (açık renkli doku) ve baş/boyun bölgesi atılır (savaşçının kendi başı kalır).
#  2) Her köşe, Meshy kemiklerinden savaşçı kemiklerine kemik başına dönüşümle taşınır (eklem konumu + kemik yönü + boy oranı):
#     v' = Σ w_i [ h_i + R_i · S_i · (v − k_i) ]   (k: Meshy eklemi, h: savaşçı eklemi, R: yön hizalama, S: boyca ölçek)
#  3) Ağırlıklar Mixamo kemik adlarına çevrilir; yüzler baskın kemiğe göre zırh parçalarına bölünür.
#  4) Her parça ayrı GLB (doku gömülmez); ortak dokular (renk / metal-pürüzlülük / normal, 1024) ayrı dosya.
import sys, os, json, math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from PIL import Image

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, HERO, OUT = argv[0], argv[1], os.path.abspath(argv[2]); SET = argv[3] if len(argv) > 3 else 'kara_sovalye'
os.makedirs(OUT, exist_ok=True)

# ---------------- savaşçı iskeleti (three uzayı, cm)
J = json.load(open(HERO)); BN = [b['n'] for b in J['bones']]; SH = [n.replace('mixamorig', '') for n in BN]
HW = {n: np.linalg.inv(np.array(inv).reshape(4, 4).T)[:3, 3] for n, inv in zip(SH, J['inv'])}

# ---------------- Meshy modeli
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.update()
def b2t(p): return np.array([p[0], p[2], -p[1]]) * 100.0          # blender m -> three cm
KW = {b.name: b2t(arm.matrix_world @ b.head_local) for b in arm.data.bones}

dg = bpy.context.evaluated_depsgraph_get(); ev = mob.evaluated_get(dg); me = ev.to_mesh()
V = np.array([b2t(mob.matrix_world @ v.co) for v in me.vertices])
NV = len(V); gnames = [g.name for g in mob.vertex_groups]
Wk = np.zeros((NV, len(gnames)))
for v in mob.data.vertices:
    for g in v.groups: Wk[v.index, g.group] = g.weight
Wk /= np.maximum(Wk.sum(1, keepdims=True), 1e-9)
me.calc_loop_triangles()
TRI = np.array([t.vertices[:] for t in me.loop_triangles]); TLOOP = np.array([t.loops[:] for t in me.loop_triangles])
UV = np.array([d.uv[:] for d in me.uv_layers.active.data])
print('Meshy köşe', NV, 'üçgen', len(TRI))

# ---------------- dokular: renk ile saç tespiti + mobil boyuta indirme
mat = mob.data.materials[0]; nt = mat.node_tree
imgs = {}
for n in nt.nodes:
    if n.type == 'TEX_IMAGE' and n.image:
        to = [l.to_socket.name for l in n.outputs['Color'].links] + [l.to_node.type for l in n.outputs['Color'].links]
        kind = 'normal' if 'NORMAL_MAP' in to else 'base' if 'Base Color' in to else 'mr'
        imgs[kind] = n.image
def pil_of(img):
    w, h = img.size; px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px)
    a = (np.clip(px.reshape(h, w, 4)[::-1], 0, 1) * 255).astype(np.uint8)    # blender pikselleri alttan üste
    return Image.fromarray(a, 'RGBA').convert('RGB')
TEX = {}
for kind, img in imgs.items():
    im = pil_of(img)
    if kind == 'base' and img.colorspace_settings.name == 'sRGB': pass
    TEX[kind] = im.resize((1024, 1024), Image.LANCZOS)
    print('doku', kind, img.size[:], img.colorspace_settings.name)
base = np.asarray(TEX['base'], float) / 255
def sample(uv):
    x = np.clip((uv[:, 0] % 1) * 1023, 0, 1023).astype(int); y = np.clip((1 - uv[:, 1] % 1) * 1023, 0, 1023).astype(int)
    return base[y, x]
# köşe başına renk (döngü uv'lerinin ortalaması)
vcol = np.zeros((NV, 3)); cnt = np.zeros(NV)
lv = np.array([l.vertex_index for l in me.loops]); c = sample(UV)
np.add.at(vcol, lv, c); np.add.at(cnt, lv, 1); vcol /= np.maximum(cnt, 1)[:, None]
lum = vcol @ [0.3, 0.59, 0.11]

# ---------------- kemik eşlemesi (Meshy -> Mixamo) ve kemik dönüşümleri
MAP = {'Hips': 'Hips', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head', 'head_end': 'Head', 'headfront': 'Head'}
for s in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'): MAP[s + b] = s + b
CH_K = {'Hips': 'Spine02', 'Spine02': 'Spine01', 'Spine01': 'Spine', 'Spine': 'neck', 'neck': 'Head'}
CH_H = {'Hips': 'Spine', 'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Neck', 'Neck': 'Head'}
for s in ('Left', 'Right'):
    for a, b in (('Shoulder', 'Arm'), ('Arm', 'ForeArm'), ('ForeArm', 'Hand'), ('UpLeg', 'Leg'), ('Leg', 'Foot'), ('Foot', 'ToeBase')):
        CH_K[s + a] = s + b; CH_H[s + a] = s + b
dom = np.array(gnames)[Wk.argmax(1)]
def tip(bone, axis_sign):  # el / ayak ucu: bölgedeki en uzak köşe
    m = dom == bone; p = V[m]; d = KW[bone]
    if not m.any(): return d
    if 'Hand' in bone: k = np.argmax(np.abs(p[:, 0])); return p[k]
    k = np.argmax(p[:, 2]); return np.array([p[k, 0], KW[bone][1], p[k, 2]])
KTIP = {}; HTIP = {}
for s in ('Left', 'Right'):
    KTIP[s + 'Hand'] = tip(s + 'Hand', 1); HTIP[s + 'Hand'] = HW[s + 'HandMiddle4']
    KTIP[s + 'ToeBase'] = tip(s + 'ToeBase', 1); HTIP[s + 'ToeBase'] = HW[s + 'Toe_End']
KTIP['Head'] = KW['head_end']; HTIP['Head'] = HW['HeadTop_End']
H_K = KW['head_end'][1] - min(KW['LeftToeBase'][1], 0); H_H = HW['HeadTop_End'][1]
G = 1.06   # gövde kalınlık ölçeği (savaşçı daha iri)
print('boy: Meshy', round(H_K, 1), 'cm, savaşçı', round(H_H, 1), 'cm')

def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + vx + vx @ vx / (1 + c)
XF = {}
for kb in gnames:
    hb = MAP.get(kb)
    if hb is None: continue
    k0 = KW[kb]; h0 = HW[hb]
    k1 = KW[CH_K[kb]] if kb in CH_K else KTIP.get(kb if kb in KTIP else 'Head')
    h1 = HW[CH_H[hb]] if hb in CH_H else HTIP.get(hb if hb in HTIP else 'Head')
    dk, dh = k1 - k0, h1 - h0
    s_long = np.linalg.norm(dh) / max(np.linalg.norm(dk), 1e-6)
    u = dk / np.linalg.norm(dk)
    S = G * np.eye(3) + (s_long - G) * np.outer(u, u)      # boyca s_long, enine G
    R = rot(dk, dh)
    XF[kb] = (k0, h0, R @ S)
    print(f'  {kb:>14} -> {hb:<12} boy oranı {s_long:.2f}')
# gövde zinciri (kalça..baş) tek doğrusal dönüşüm: eklem dağılımı farklı olsa da gövde bütün halinde ölçeklenir
TORSO_K = ['Hips', 'Spine02', 'Spine01', 'Spine', 'neck', 'Head', 'head_end', 'headfront']
sy = (HW['Neck'][1] - HW['Hips'][1]) / (KW['neck'][1] - KW['Hips'][1])
Mt = np.diag([G, sy, G])
for kb in TORSO_K:
    if kb in KW: XF[kb] = (KW['Hips'], HW['Hips'], Mt)
print('gövde boy oranı', round(sy, 2))
Vn = np.zeros_like(V)
for gi, kb in enumerate(gnames):
    if kb not in XF: continue
    w = Wk[:, gi]; m = w > 0
    if not m.any(): continue
    k0, h0, M = XF[kb]
    Vn[m] += w[m, None] * (h0 + (V[m] - k0) @ M.T)

# ---------------- ağırlıkları Mixamo adlarına çevir
BI = {n: i for i, n in enumerate(BN)}
Wh = np.zeros((NV, len(BN)))
for gi, kb in enumerate(gnames):
    hb = MAP.get(kb)
    if hb: Wh[:, BI['mixamorig' + hb]] += Wk[:, gi]
HDOM = np.array(SH)[Wh.argmax(1)]

# ---------------- bölütleme: saç / baş atılır, kalan yüzler parçalara
hn = Wh[:, [BI['mixamorigHead'], BI['mixamorigNeck']]].sum(1)
skin = (lum > 0.26) & (vcol[:, 0] - vcol[:, 2] > 0.06)          # çıplak deri (kızılımsı-kahve)
hair = (lum > 0.42) | skin | (hn > 0.3)                          # saç, deri, başa bağlı köşeler
FULL = os.environ.get('FULL') == '1'   # tam kostüm: hiçbir şey kesilmez, baş + saç ayrı 'bas' parçası olur
if FULL: hair[:] = False
headreg = np.isin(HDOM, ['Head', 'Neck'])
if FULL: headreg[:] = False
def piece_of(i):
    b = HDOM[i]; p = Vn[i]
    if b in ('Spine', 'Spine1', 'Spine2'): return 'gogusluk' if p[2] >= HW['Spine1'][2] else 'sirt'
    for s, t in (('Left', 'l'), ('Right', 'r')):
        if b == s + 'Shoulder': return 'omuzluk_' + t
        if b == s + 'Arm':
            fr = (abs(p[0]) - abs(HW[s + 'Arm'][0])) / (abs(HW[s + 'ForeArm'][0]) - abs(HW[s + 'Arm'][0]))
            return 'omuzluk_' + t if fr < 0.38 else 'kol_' + t
        if b == s + 'ForeArm': return 'kol_' + t
        if b == s + 'Hand': return 'eldiven'
        if b in (s + 'UpLeg', s + 'Leg'): return 'botlar' if p[1] < 22 else 'bacak_' + t
        if b in (s + 'Foot', s + 'ToeBase'): return 'botlar'
    if b == 'Hips': return 'bel'
    if FULL and b in ('Head', 'Neck'): return 'bas'
    return None
vp = np.array([piece_of(i) for i in range(NV)], dtype=object)
groups = {}
for ti, (t, l) in enumerate(zip(TRI, TLOOP)):
    if hair[t].sum() >= 2 or headreg[t].sum() >= 2: continue
    ps = [vp[i] for i in t]; p = max(set(ps), key=ps.count)
    if p is None: continue
    groups.setdefault(p, []).append(ti)
# saçtan kalan küçük kopuk adacıkları at: köşeler konuma göre birleştirilip üçgenler bileşenlere ayrılır
keep = sorted(t for g in groups.values() for t in g)
key = {}; vid = np.array([key.setdefault(tuple(np.round(V[i], 2)), len(key)) for i in range(NV)])
par = list(range(len(key)))
def fd(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for t in keep:
    a_, b_, c_ = (fd(vid[i]) for i in TRI[t]); par[b_] = a_; par[fd(c_)] = a_
lab = {t: fd(vid[TRI[t][0]]) for t in keep}
from collections import Counter
size = Counter(lab.values()); small = set() if FULL else {k for k, n in size.items() if n < 80}
for g in groups: groups[g] = [t for t in groups[g] if lab[t] not in small]
print('atılan küçük adacık', len(small), 'üçgen', sum(size[k] for k in small))
print('atılan saç köşesi', int(hair.sum()), 'baş/boyun köşesi', int(headreg.sum()))

# ---------------- dokuları yaz (parçalar arasında paylaşılır)
TEXDIR = os.path.join(OUT, 'tex'); os.makedirs(TEXDIR, exist_ok=True)
TEX['base'].save(os.path.join(TEXDIR, 'base.jpg'), quality=86)
if 'mr' in TEX: TEX['mr'].save(os.path.join(TEXDIR, 'mr.jpg'), quality=86)
if 'normal' in TEX: TEX['normal'].save(os.path.join(TEXDIR, 'normal.jpg'), quality=90)

# ---------------- Blender: Mixamo iskeleti + parça nesneleri + GLB
def b2(p): return (p[0], -p[2], p[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
ad = bpy.data.armatures.new('ValkorRig'); ao = bpy.data.objects.new('ValkorRig', ad); bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao; ao.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
for n, d in zip(BN, J['bones']):
    e = ad.edit_bones.new(n); h = Vector(b2(HW[n.replace('mixamorig', '')])); e.head = h; e.tail = h + Vector((0, 0, 3))
for n, d in zip(BN, J['bones']):
    if d['p'] >= 0: ad.edit_bones[n].parent = ad.edit_bones[BN[d['p']]]
bpy.ops.object.mode_set(mode='OBJECT')
pm = bpy.data.materials.new(SET); pm.use_nodes = True   # yalnız ad: oyun ortak dokuyu bağlar
report = []
for name, tris in sorted(groups.items()):
    tris = np.array(tris); vids = np.unique(TRI[tris]); remap = {v: i for i, v in enumerate(vids)}
    m = bpy.data.meshes.new(name); m.from_pydata([b2(Vn[v]) for v in vids], [], [tuple(remap[v] for v in TRI[t]) for t in tris])
    uvl = m.uv_layers.new(name='UVMap')
    for fi, t in enumerate(tris):
        for k, li in enumerate(m.polygons[fi].loop_indices): uvl.data[li].uv = UV[TLOOP[t][k]]
    for p in m.polygons: p.use_smooth = True
    m.materials.append(pm); m.validate(); m.update()
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o)
    for bi, bn in enumerate(BN):
        col = Wh[vids, bi]; nz = np.nonzero(col > 0.005)[0]
        if len(nz) == 0: continue
        g = o.vertex_groups.new(name=bn)
        for i in nz: g.add([int(i)], float(col[i]), 'REPLACE')
    o.parent = ao; md = o.modifiers.new('Armature', 'ARMATURE'); md.object = ao
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ntri = len(m.polygons)
    ao.select_set(True)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_skins=True, export_animations=False,
                              export_materials='EXPORT', export_image_format='NONE', export_def_bones=False, export_tangents=False)
    report.append((name, ntri, len(vids), os.path.getsize(path)))
    print('PARÇA', name, 'üçgen', ntri, 'köşe', len(vids), 'bayt', os.path.getsize(path), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, '_fit.blend'))
json.dump(report, open(os.path.join(OUT, '_report.json'), 'w'), indent=1)
