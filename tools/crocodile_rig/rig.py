# Stage 1: import, clean/decimate, cut mouth, add mouth interior + teeth, build armature, skin.
# usage: python3 -I rig.py -- <in.fbx> <out.blend> <target_tris>
import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bmesh, math
import numpy as np
from mathutils import Vector, Matrix

IN, OUT, TARGET = sys.argv[-3], sys.argv[-2], int(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN)
ob = bpy.data.objects['crocodile']
ob.name = 'Crocodile'; ob.data.name = 'CrocodileMesh'
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ---------- clean + decimate ----------
bm = bmesh.new(); bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(ob.data); bm.free()
ntri = sum(len(p.vertices) - 2 for p in ob.data.polygons)
if TARGET and ntri > TARGET:
    m = ob.modifiers.new('dec', 'DECIMATE'); m.ratio = TARGET / ntri; m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)
print('tris', ntri, '->', sum(len(p.vertices) - 2 for p in ob.data.polygons))
# drop tangent/custom normals data, flat->smooth
me = ob.data
for p in me.polygons: p.use_smooth = True

co = np.array([v.co[:] for v in me.vertices])

def slice_center(y, w=0.03, xmax=None):
    m = np.abs(co[:, 1] - y) < w
    if xmax is not None: m &= np.abs(co[:, 0]) < xmax
    c = co[m]
    return (c[:, 0].min() + c[:, 0].max()) / 2, (c[:, 2].min() + c[:, 2].max()) / 2

# ---------- mouth cut ----------
LIP_Z = 0.163
CUT_Y = -1.78          # lips split in front of this; behind it the cheek stretches
HINGE = Vector((0, -1.63, 0.205))
bm = bmesh.new(); bm.from_mesh(me)
faces = [f for f in bm.faces if max(v.co.y for v in f.verts) < CUT_Y + 0.06]
geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=(0, 0, LIP_Z), plane_no=(0, 0, 1))
cut_edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)
             and all(v.co.y < CUT_Y for v in e.verts) and all(abs(v.co.z - LIP_Z) < 1e-4 for v in e.verts)]
lip_pts = [v.co.copy() for e in cut_edges for v in e.verts]
bmesh.ops.split_edges(bm, edges=cut_edges)
bm.to_mesh(me); bm.free()
print('mouth cut edges', len(cut_edges))

# lip outline (half width per y) for interior geometry
lp = np.array([p[:] for p in lip_pts])
ys = np.linspace(lp[:, 1].min() + 0.004, -1.70, 22)
def half_w(y):
    m = np.abs(lp[:, 1] - y) < 0.015
    if m.sum() < 2:  # behind the split use head slice at lip height
        m2 = (np.abs(co[:, 1] - y) < 0.03) & (np.abs(co[:, 2] - LIP_Z) < 0.04) & (np.abs(co[:, 0]) < 0.25)
        return np.abs(co[m2, 0]).max()
    return np.abs(lp[m, 0]).max()
hw = np.array([half_w(y) for y in ys])

def mouth_plate(name, z, inset, flip, color):
    verts = []; faces = []
    for i, y in enumerate(ys):
        w = max(hw[i] - inset, 0.004)
        verts += [(-w, y, z), (w, y, z)]
    for i in range(len(ys) - 1):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2
        faces.append((a, b, c, d) if not flip else (d, c, b, a))
    m = bpy.data.meshes.new(name); m.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o)
    mat = bpy.data.materials.get(color[0]) or bpy.data.materials.new(color[0])
    mat.diffuse_color = color[1]; m.materials.append(mat)
    return o

def teeth(name, z, inset, down, n=11):
    bmt = bmesh.new()
    tys = np.linspace(ys[0] + 0.02, -1.80, n)
    for side in (-1, 1):
        for k, y in enumerate(tys):
            w = np.interp(y, ys, hw) - inset
            h = 0.016 + 0.006 * (k % 3 == 1)
            r = bmesh.ops.create_cone(bmt, cap_ends=False, segments=5, radius1=0.0045, radius2=0.0005, depth=h)
            vs = r['verts']
            off = Vector((side * w, y, z + (-h / 2 if down else h / 2)))
            M = Matrix.Translation(off) @ (Matrix.Rotation(math.pi, 4, 'X') if down else Matrix())
            bmesh.ops.transform(bmt, matrix=M, verts=vs)
    m = bpy.data.meshes.new(name); bmt.to_mesh(m); bmt.free()
    for p in m.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o)
    mat = bpy.data.materials.get('Teeth') or bpy.data.materials.new('Teeth')
    mat.diffuse_color = (0.85, 0.80, 0.66, 1); m.materials.append(mat)
    return o

MOUTH = ('MouthInside', (0.15, 0.035, 0.03, 1))
def mouth_sack(name, zt, zb, inset, wall_from_y):
    verts = []; faces = []
    for i, y in enumerate(ys):
        w = max(hw[i] - inset, 0.004); wb = max(w - 0.006, 0.004)
        verts += [(-w, y, zt), (w, y, zt), (-wb, y, zb), (wb, y, zb)]
    for i in range(len(ys) - 1):
        a = 4 * i; b = a + 4
        faces.append((b + 1, b, a, a + 1))            # palate (normal down)
        faces.append((a + 2, b + 2, b + 3, a + 3))    # tongue (normal up)
        if ys[i] >= wall_from_y:                      # cheek membranes near the hinge
            faces.append((a, b, b + 2, a + 2)); faces.append((a + 3, b + 3, b + 1, a + 1))
    n = len(ys) - 1; a = 4 * n
    faces.append((a, a + 2, a + 3, a + 1))            # throat
    m = bpy.data.meshes.new(name); m.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o)
    mat = bpy.data.materials.new(MOUTH[0]); mat.diffuse_color = MOUTH[1]; m.materials.append(mat)
    nv = len(verts)
    gh = o.vertex_groups.new(name='head'); gh.add([i for i in range(nv) if i % 4 < 2], 1.0, 'REPLACE')
    gj = o.vertex_groups.new(name='jaw'); gj.add([i for i in range(nv) if i % 4 >= 2], 1.0, 'REPLACE')
    return o
sack = mouth_sack('MouthSack', LIP_Z + 0.006, LIP_Z - 0.008, 0.010, -2.02)
uteeth = teeth('TeethUpper', LIP_Z + 0.004, 0.007, True)
lteeth = teeth('TeethLower', LIP_Z - 0.006, 0.009, False)

# ---------- armature ----------
def C(y, xmax=0.2):
    x, z = slice_center(y, xmax=xmax); return Vector((x, y, z))

arm_data = bpy.data.armatures.new('CrocodileRig')
arm = bpy.data.objects.new('CrocodileRig', arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
for o in bpy.context.selected_objects: o.select_set(False)
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
def bone(name, h, t, parent=None, connect=False, deform=True, roll=0.0):
    b = eb.new(name); b.head = h; b.tail = t; b.roll = roll
    if parent: b.parent = eb[parent]; b.use_connect = connect
    b.use_deform = deform
    return b

bone('root', (0, 0, 0), (0, -0.4, 0), deform=False)
# spine (forward = -Y)
sp = [C(0.0), C(-0.45), C(-0.80), C(-1.05), C(-1.40), C(-1.62, 0.25)]
bone('hips', sp[0], sp[1], 'root')
bone('spine_01', sp[1], sp[2], 'hips', True)
bone('spine_02', sp[2], sp[3], 'spine_01', True)
bone('chest', sp[3], sp[4], 'spine_02', True)
bone('neck', sp[4], sp[5], 'chest', True)
head_tip = C(-2.20, 0.25); head_tip.z = sp[5].z - 0.02
bone('head', sp[5], head_tip, 'neck', True)
bone('jaw', HINGE, Vector((0, -2.22, 0.12)), 'head')
# tail
ty = [0.0, 0.30, 0.58, 0.85, 1.12, 1.38, 1.63, 1.88, 2.24]
tp = [C(y, 0.6) for y in ty[:-1]]
# true tip
m = co[:, 1] > 2.15; tip = Vector(co[m].mean(0)); tip.y = 2.25; tp.append(tip)
prev = 'hips'
for i in range(8):
    bone(f'tail_{i+1:02d}', tp[i], tp[i + 1], prev, i > 0); prev = f'tail_{i+1:02d}'
# legs  (R = +X)
LEGS = {
    'arm.R': ('chest', [(0.24, -1.15, 0.24), (0.56, -1.13, 0.17), (0.57, -1.33, 0.05), (0.62, -1.50, 0.01)]),
    'arm.L': ('chest', [(-0.25, -1.12, 0.24), (-0.57, -1.10, 0.17), (-0.52, -1.32, 0.05), (-0.53, -1.50, 0.01)]),
    'leg.R': ('hips', [(0.22, -0.15, 0.27), (0.42, -0.38, 0.21), (0.51, -0.12, 0.07), (0.73, -0.22, 0.01)]),
    'leg.L': ('hips', [(-0.23, -0.22, 0.27), (-0.45, -0.43, 0.20), (-0.58, -0.28, 0.07), (-0.74, -0.37, 0.01)]),
}
NAMES = {'arm': ('upperarm', 'forearm', 'hand'), 'leg': ('thigh', 'shin', 'foot')}
for key, (par, pts) in LEGS.items():
    kind, side = key.split('.')
    n = NAMES[kind]; pts = [Vector(p) for p in pts]
    bone(f'{n[0]}.{side}', pts[0], pts[1], par)
    bone(f'{n[1]}.{side}', pts[1], pts[2], f'{n[0]}.{side}', True)
    bone(f'{n[2]}.{side}', pts[2], pts[3], f'{n[1]}.{side}', True)
    # IK target (non-deform, child of root) with same orientation as hand/foot
    t = bone(f'IK_{n[2]}.{side}', pts[2], pts[3], 'root', deform=False)
    t.roll = eb[f'{n[2]}.{side}'].roll
# give every deform bone roll so local Z points up-ish (consistent)
bpy.ops.armature.select_all(action='SELECT')
bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
for key in LEGS:
    kind, side = key.split('.'); n = NAMES[kind]
    eb[f'IK_{n[2]}.{side}'].roll = eb[f'{n[2]}.{side}'].roll
bpy.ops.object.mode_set(mode='OBJECT')

# IK constraints
for key in LEGS:
    kind, side = key.split('.'); n = NAMES[kind]
    pb = arm.pose.bones[f'{n[1]}.{side}']
    c = pb.constraints.new('IK'); c.target = arm; c.subtarget = f'IK_{n[2]}.{side}'; c.chain_count = 2; c.use_tail = True
    # IK target positioned at the wrist/ankle: use bone head -> chain reaches target head
    c.use_stretch = False
    f = arm.pose.bones[f'{n[2]}.{side}'].constraints.new('COPY_ROTATION'); f.target = arm; f.subtarget = f'IK_{n[2]}.{side}'
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'

# ---------- skinning ----------
for o in bpy.context.selected_objects: o.select_set(False)
ob.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_NAME')
me = ob.data
V = np.array([v.co[:] for v in me.vertices])
deform = [b for b in arm.data.bones if b.use_deform]
def seg_dist(P, a, b):
    a = np.array(a); b = np.array(b); ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
def part_radius(name, b):
    if name.startswith(('upperarm', 'forearm', 'hand')): return {'upperarm': .075, 'forearm': .065, 'hand': .06}[name.split('.')[0]]
    if name.startswith(('thigh', 'shin', 'foot')): return {'thigh': .09, 'shin': .07, 'foot': .06}[name.split('.')[0]]
    if name in ('head', 'jaw'): return .12
    fixed = {'hips': .26, 'spine_01': .27, 'spine_02': .27, 'chest': .25, 'neck': .19, 'tail_01': .23}
    if name in fixed: return fixed[name]
    # tail: measure half width at segment middle
    mid = (b.head_local + b.tail_local) / 2
    m = (np.abs(V[:, 1] - mid.y) < 0.03) & (np.abs(V[:, 0] - mid.x) < 0.3) & (V[:, 2] > 0.06)
    if name.startswith(('hips', 'spine', 'chest')): m &= np.abs(V[:, 0]) < 0.30
    r = np.abs(V[m, 0] - mid.x).max() if m.sum() > 3 else 0.1
    return max(r * 0.95, 0.02)
D = np.zeros((len(V), len(deform)))
for j, b in enumerate(deform):
    r = part_radius(b.name, b)
    D[:, j] = seg_dist(V, b.head_local, b.tail_local) / r
    print('radius', b.name, round(r, 3))
W = 1.0 / np.maximum(D, 0.08) ** 6
# keep top 3
idx = np.argsort(-W, axis=1)[:, :3]
Wt = np.take_along_axis(W, idx, 1); Wt /= Wt.sum(1, keepdims=True)
# laplacian smoothing over mesh edges (keeps mouth split separated)
E = np.array([e.vertices[:] for e in me.edges])
full = np.zeros_like(W); np.put_along_axis(full, idx, Wt, 1)
for it in range(4):
    acc = np.zeros_like(full); cnt = np.zeros(len(V))
    np.add.at(acc, E[:, 0], full[E[:, 1]]); np.add.at(acc, E[:, 1], full[E[:, 0]])
    np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
    nb = acc / np.maximum(cnt, 1)[:, None]
    full = np.where(cnt[:, None] > 0, 0.5 * full + 0.5 * nb, full)
full /= full.sum(1, keepdims=True)
for j, b in enumerate(deform):
    g = ob.vertex_groups.get(b.name) or ob.vertex_groups.new(name=b.name)
    nz = np.nonzero(full[:, j] > 0.01)[0]
    for i in nz: g.add([int(i)], float(full[i, j]), 'REPLACE')
print('vgroups', len(ob.vertex_groups))

# head / jaw override with procedural weights
me = ob.data
vg = {g.name: g for g in ob.vertex_groups}
for n in ('jaw', 'head', 'neck'):
    if n not in vg: vg[n] = ob.vertex_groups.new(name=n)
def lip_line(y):  # mouth line height (rises behind the split towards the hinge)
    return float(np.interp(y, [-2.4, CUT_Y, -1.70, -1.62, -1.5], [LIP_Z, LIP_Z, 0.20, 0.215, 0.215]))
def ss(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
fz = np.zeros(len(me.vertices)); fc = np.zeros(len(me.vertices))
for p_ in me.polygons:
    cz = p_.center.z
    for vi in p_.vertices: fz[vi] += cz; fc[vi] += 1
fz /= np.maximum(fc, 1)
for v in me.vertices:
    x, y, z = v.co
    if y > -1.50: continue
    if y < CUT_Y and abs(z - LIP_Z) < 2e-4:
        below = fz[v.index] < LIP_Z  # duplicated seam vertex: side decided by its faces
    else:
        below = z < lip_line(y)
    if y < CUT_Y:
        jw = 1.0 if below else 0.0
    else:
        jw = (1 - ss(-1.74, -1.58, y)) * (1.0 if below else max(0.0, 1 - (z - lip_line(y)) / 0.015))
    hw_ = 1.0 - jw
    # in back part blend head into neck as before (keep auto weights there)
    if y > -1.62:
        fade = ss(-1.62, -1.50, y)  # 0 at -1.62 -> 1 at -1.50 (keep auto)
        if fade >= 1: continue
        auto = {g.group: g.weight for g in v.groups}
        for gi in list(auto): ob.vertex_groups[gi].remove([v.index])
        for gi, w in auto.items():
            if w * fade > 1e-4: ob.vertex_groups[gi].add([v.index], w * fade, 'REPLACE')
        s = 1 - fade
        if jw * s > 1e-4: vg['jaw'].add([v.index], jw * s, 'ADD')
        if hw_ * s > 1e-4: vg['head'].add([v.index], hw_ * s, 'ADD')
        continue
    for g in list(v.groups): ob.vertex_groups[g.group].remove([v.index])
    if jw > 1e-4: vg['jaw'].add([v.index], jw, 'REPLACE')
    if hw_ > 1e-4: vg['head'].add([v.index], hw_, 'REPLACE')

# mouth parts: rigid parenting via single vertex group
for o, b in ((uteeth, 'head'), (lteeth, 'jaw')):
    g = o.vertex_groups.new(name=b); g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
# join mouth parts into the main mesh (single skinned mesh, 3 materials)
for o in bpy.context.selected_objects: o.select_set(False)
for o in (sack, uteeth, lteeth, ob): o.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
# normalize + limit to 4 influences
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
unw = sum(1 for v in ob.data.vertices if not v.groups)
print('unweighted verts', unw)

# ---------- material (base color only, lighter for game) ----------
mat = bpy.data.materials['Material_0']; mat.name = 'CrocodileSkin'
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
for n in list(nt.nodes):
    if n.type == 'TEX_IMAGE' and n.image and n.image.name != 'Image_0': nt.nodes.remove(n)
    elif n.type == 'NORMAL_MAP': nt.nodes.remove(n)
bsdf.inputs['Roughness'].default_value = 0.72
bsdf.inputs['Metallic'].default_value = 0.0
img = bpy.data.images['Image_0']; img.name = 'crocodile_basecolor'
for nm, col in (('MouthInside', (0.15, 0.035, 0.03, 1)), ('Teeth', (0.85, 0.80, 0.66, 1))):
    m = bpy.data.materials[nm]; m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = 0.5 if nm == 'Teeth' else 0.6
for m in list(bpy.data.materials):
    if m.users == 0: bpy.data.materials.remove(m)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('saved', OUT)
