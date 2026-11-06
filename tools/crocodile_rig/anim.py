# Stage 2: create idle / walk / attack actions, bake IK to FK, clean helpers, export.
# usage: python3 -I anim.py -- <in.blend> <out_dir> <basename>
import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import math, os
from mathutils import Quaternion, Vector, Matrix

IN, OUTDIR, BASE = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
sc.render.fps = 30
arm = bpy.data.objects['CrocodileRig']
mesh = bpy.data.objects['Crocodile']
P = arm.pose.bones
TAU = 2 * math.pi
D = math.radians

def B3(name): return P[name].bone.matrix_local.to_3x3()

def reset():
    for pb in P:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)

def rot(name, x=0.0, y=0.0, z=0.0):
    """rotation in armature axes (degrees): x=pitch (nose down positive for -Y facing bones), z=yaw"""
    R = (Quaternion((0, 0, 1), D(z)) @ Quaternion((0, 1, 0), D(y)) @ Quaternion((1, 0, 0), D(x))).to_matrix()
    B = B3(name)
    P[name].rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()

def move(name, d):
    P[name].location = B3(name).inverted() @ Vector(d)

def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def keys(f, kv):
    """piecewise smoothstep through (frame, value) pairs"""
    if f <= kv[0][0]: return kv[0][1]
    for (f0, v0), (f1, v1) in zip(kv, kv[1:]):
        if f <= f1: return v0 + (v1 - v0) * smooth((f - f0) / (f1 - f0))
    return kv[-1][1]

TAIL = [f'tail_{i:02d}' for i in range(1, 9)]
FEET = {'hand.L': 'IK_hand.L', 'hand.R': 'IK_hand.R', 'foot.L': 'IK_foot.L', 'foot.R': 'IK_foot.R'}
SIDE = {'hand.L': -1, 'hand.R': 1, 'foot.L': -1, 'foot.R': 1}

def key_all(f):
    for pb in P:
        pb.keyframe_insert('location', frame=f)
        pb.keyframe_insert('rotation_quaternion', frame=f)

def new_action(name):
    act = bpy.data.actions.new(name)
    arm.animation_data_create(); arm.animation_data.action = act
    return act

# ---------------- IDLE (4 s loop) ----------------
def pose_idle(f, N):
    t = f / N; s1 = math.sin(TAU * t); s2 = math.sin(2 * TAU * t)
    move('hips', (0, 0, 0.004 * (1 - math.cos(2 * TAU * t)) / 2))
    rot('spine_02', x=-0.6 * s2); rot('chest', x=-0.8 * s2)
    rot('neck', x=-1.2 * s1, z=2.0 * math.sin(TAU * t + 0.8))
    rot('head', x=1.0 * s2, z=1.5 * s1)
    rot('jaw', x=4.0 * (1 - math.cos(TAU * t)) / 2)
    for i, b in enumerate(TAIL):
        rot(b, z=(2.0 + 0.6 * i) * math.sin(TAU * (t - 0.07 * i)), x=0.3 * s2)

# ---------------- WALK (in place, 40 frames) ----------------
STRIDE, LIFT, DUTY = 0.36, 0.08, 0.62
PHASE = {'hand.L': 0.0, 'foot.R': 0.04, 'hand.R': 0.5, 'foot.L': 0.54}
def pose_walk(f, N):
    t = f / N
    move('hips', (0, 0, 0.045 + 0.008 * math.cos(2 * TAU * t)))
    # lateral S-wave travelling from chest to tail tip
    body = [('chest', 0.0, 3.0), ('spine_02', 0.12, 3.0), ('spine_01', 0.24, 2.5), ('hips', 0.36, 2.5)]
    yaw_sum = 0
    for b, ph, a in body:
        y = a * math.sin(TAU * (t - ph)); yaw_sum += y
        rot(b, z=y, x=-0.8 * math.cos(2 * TAU * t) if b == 'chest' else 0)
    for i, b in enumerate(TAIL):
        rot(b, z=(5.0 + 1.0 * i) * math.sin(TAU * (t - 0.45 - 0.09 * i)))
    rot('neck', z=-0.6 * yaw_sum, x=1.0 * math.cos(2 * TAU * t))
    rot('head', z=-0.3 * yaw_sum)
    for limb, ik in FEET.items():
        u = (t + PHASE[limb]) % 1.0
        if u < DUTY:  # stance: planted foot slides back (body moves forward = -Y)
            dy = -STRIDE / 2 + STRIDE * (u / DUTY); dz = 0; pitch = 0
        else:
            s = (u - DUTY) / (1 - DUTY); e = smooth(s)
            dy = STRIDE / 2 - STRIDE * e; dz = LIFT * math.sin(math.pi * s); pitch = 25 * math.sin(math.pi * s)
        move(ik, (SIDE[limb] * 0.02 * (dz / LIFT if dz else 0), dy, dz))
        if limb.startswith('hand'): rot(ik, x=0.6 * pitch)
        else: rot(ik, y=SIDE[limb] * 0.6 * pitch)

# ---------------- ATTACK (lunge + bite, 36 frames) ----------------
def pose_attack(f, N):
    hy = keys(f, [(0, 0), (8, 0.07), (14, -0.17), (22, -0.15), (36, 0)])
    hz = keys(f, [(0, 0), (8, 0.02), (14, 0.07), (22, 0.05), (36, 0)])
    move('hips', (0, hy, hz))
    rot('hips', x=keys(f, [(0, 0), (8, 2), (14, -3), (24, -1), (36, 0)]))
    rot('chest', x=keys(f, [(0, 0), (8, 3), (13, -6), (20, -2), (36, 0)]))
    rot('neck', x=keys(f, [(0, 0), (8, 5), (12, -14), (16, 6), (22, 2), (36, 0)]),
        z=keys(f, [(0, 0), (16, 0), (19, 9), (22, -7), (25, 5), (29, -2), (33, 0), (36, 0)]))
    rot('head', x=keys(f, [(0, 0), (8, 3), (12, -8), (16, 5), (36, 0)]),
        z=keys(f, [(0, 0), (16, 0), (19, 5), (22, -4), (25, 3), (30, 0), (36, 0)]))
    rot('jaw', x=keys(f, [(0, 0), (6, 5), (12, 40), (15, 0), (36, 0)]))
    for i, b in enumerate(TAIL):
        d = i * 0.8
        rot(b, z=keys(f, [(0, 0), (8 + d, 6 + i * 0.6), (15 + d, -8 - i), (24 + d, 3), (36, 0)]))
    # front feet step forward during the lunge, then back
    for limb in ('hand.L', 'hand.R'):
        o = 1 if limb == 'hand.R' else 0
        dy = keys(f, [(0, 0), (9 + o, 0), (14 + o, -0.15), (25 + o, -0.15), (32 + o, 0), (36, 0)])
        dz = keys(f, [(0, 0), (9 + o, 0), (11.5 + o, 0.06), (14 + o, 0), (25 + o, 0), (28.5 + o, 0.05), (32 + o, 0), (36, 0)])
        move(FEET[limb], (0, dy, dz))
    for limb in ('foot.L', 'foot.R'):
        dy = keys(f, [(0, 0), (12, 0), (16, -0.08), (26, -0.08), (33, 0), (36, 0)])
        dz = keys(f, [(0, 0), (12, 0), (14, 0.04), (16, 0), (26, 0), (29.5, 0.035), (33, 0), (36, 0)])
        move(FEET[limb], (0, dy, dz))

CLIPS = [('idle', pose_idle, 120), ('walk', pose_walk, 40), ('attack', pose_attack, 36)]
bpy.context.view_layer.objects.active = arm
for o in bpy.context.selected_objects: o.select_set(False)
arm.select_set(True)
bpy.ops.object.mode_set(mode='POSE')
baked = {}
for name, fn, N in CLIPS:
    src = new_action(name + '_src')
    for f in range(N + 1):
        reset(); fn(f, N); key_all(f)
    # bake (IK -> FK) into a fresh action
    sc.frame_start, sc.frame_end = 0, N
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(frame_start=0, frame_end=N, only_selected=False, visual_keying=True,
                     clear_constraints=False, use_current_action=False, bake_types={'POSE'})
    act = arm.animation_data.action; act.name = name; act.use_fake_user = True
    baked[name] = act
    arm.animation_data.action = None
    bpy.data.actions.remove(src)
    print('baked', name, len(act.fcurves) if hasattr(act, 'fcurves') else '')
bpy.ops.object.mode_set(mode='OBJECT')

# remove IK helpers
for pb in P:
    for c in list(pb.constraints): pb.constraints.remove(c)
bpy.ops.object.mode_set(mode='EDIT')
for b in list(arm.data.edit_bones):
    if b.name.startswith('IK_'): arm.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')
reset()

def strip_ik(act):
    try:
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in list(cb.fcurves):
                        if '"IK_' in fc.data_path or fc.data_path.endswith('.scale'): cb.fcurves.remove(fc)
    except AttributeError:
        for fc in list(act.fcurves):
            if '"IK_' in fc.data_path or fc.data_path.endswith('.scale'): act.fcurves.remove(fc)
for a in baked.values(): strip_ik(a)

# push each action to its own NLA track so every exporter sees it
ad = arm.animation_data
for name, act in baked.items():
    tr = ad.nla_tracks.new(); tr.name = name
    st = tr.strips.new(name, 0, act); st.action_frame_end = act.frame_range[1]
    tr.mute = True
ad.action = baked['idle']
sc.frame_set(0)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, BASE + '.blend'))
for o in bpy.context.selected_objects: o.select_set(False)
arm.select_set(True); mesh.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUTDIR, BASE + '.glb'), export_format='GLB', use_selection=True,
                          export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1,
                          export_image_format='JPEG', export_jpeg_quality=85, export_skins=True,
                          export_all_influences=False, export_def_bones=False, export_optimize_animation_size=True,
                          export_anim_single_armature=True, export_reset_pose_bones=True, export_apply=False,
                          export_yup=True)
ad.action = None
bpy.ops.export_scene.fbx(filepath=os.path.join(OUTDIR, BASE + '.fbx'), use_selection=True, object_types={'ARMATURE', 'MESH'},
                         add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
                         bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
                         path_mode='COPY', embed_textures=True, armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
print('exported')
