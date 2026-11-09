# VALKOR karakter seçim arka planı: gece ormanı + oymalı taş platform (Blender, Cycles)
#   python3 -I scene.py -- <çıkış.png> [genişlik yükseklik örnek]
# Kamera: (0,-CAM_D,CAM_H) -> hedef (0,0,TGT_Z), dikey görüş FOV_V. Platform üstü z=PLAT_H (karakterin ayakları).
import sys, math, random
import bpy, bmesh
from mathutils import Vector, noise

a = sys.argv[sys.argv.index('--') + 1:]
OUT = a[0]; W = int(a[1]) if len(a) > 1 else 1600; H = int(a[2]) if len(a) > 2 else 900; SMP = int(a[3]) if len(a) > 3 else 96
CAM_D, CAM_H, TGT_Z, FOV_V, PLAT_H = 7.8, 1.7, 1.3, 25.0, 0.24
rnd = random.Random(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
C = sc.collection

def mat(name, col, rough=.8, metal=0., emit=None, es=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = es
    return m

def noise_mat(name, c1, c2, scale=6., rough=.85, bump=.3, detail=8.):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (*c1, 1); ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough
    return m

def obj(name, me, m=None):
    o = bpy.data.objects.new(name, me); C.objects.link(o)
    if m: me.materials.append(m)
    return o

# ---------------- zemin: dalgalı toprak, ortadan geçen patika
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=220, y_segments=220, size=90)
for v in bm.verts:
    x, y = v.co.x, v.co.y
    h = noise.noise(Vector((x * .18, y * .18, 0))) * .35 + noise.noise(Vector((x * .9, y * .9, 3))) * .05
    h += max(0, (y - 6) * .06) + max(0, y - 32) ** 1.2 * .045 * (1 + .5 * noise.noise(Vector((x * .05, 7, 0))))   # arkada tepeler ufku kapatır
    h += .45 * max(0, abs(x) - 6) / 6 * (1 if y > -2 else .3)   # yanlar tümsek
    if math.hypot(x, y) < 3.2: h *= .2                  # platform çevresi düz
    v.co.z = h - .05
me = bpy.data.meshes.new('ground'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
gm = bpy.data.materials.new('ground'); gm.use_nodes = True; nt = gm.node_tree; b = nt.nodes['Principled BSDF']
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 10; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
mt = nt.nodes.new('ShaderNodeMath'); mt.operation = 'ABSOLUTE'; nt.links.new(sep.outputs['X'], mt.inputs[0])
wob = nt.nodes.new('ShaderNodeMath'); wob.operation = 'MULTIPLY_ADD'; wob.inputs[1].default_value = 1.4; nt.links.new(nz.outputs['Fac'], wob.inputs[0]); nt.links.new(mt.outputs[0], wob.inputs[2])
path = nt.nodes.new('ShaderNodeMapRange'); path.inputs['From Min'].default_value = 1.6; path.inputs['From Max'].default_value = 3.2; nt.links.new(wob.outputs[0], path.inputs['Value'])
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; nt.links.new(path.outputs['Result'], mix.inputs['Factor'])
r1 = nt.nodes.new('ShaderNodeValToRGB'); r1.color_ramp.elements[0].color = (.2, .08, .04, 1); r1.color_ramp.elements[1].color = (.42, .2, .1, 1); nt.links.new(nz.outputs['Fac'], r1.inputs['Fac'])
r2 = nt.nodes.new('ShaderNodeValToRGB'); r2.color_ramp.elements[0].color = (.05, .03, .025, 1); r2.color_ramp.elements[1].color = (.2, .07, .05, 1); nt.links.new(nz.outputs['Fac'], r2.inputs['Fac'])
nt.links.new(r1.outputs['Color'], mix.inputs[6]); nt.links.new(r2.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = .5; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
b.inputs['Roughness'].default_value = .95
obj('ground', me, gm)

# ---------------- platform: üç kademeli oymalı taş kaide, kenarda rün halkası
stone = noise_mat('stone', (.09, .085, .09), (.26, .24, .23), scale=9, bump=.45)
stone2 = noise_mat('stone2', (.06, .055, .06), (.17, .16, .16), scale=14, bump=.6)
gold = mat('gold', (.55, .38, .16), rough=.35, metal=1.)
rune = mat('rune', (.05, .02, .01), rough=.5, emit=(1., .35, .08), es=3.5)
def ring(r_in, r_out, z0, z1, segs, m, bevel=.02):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r_out, radius2=r_out, depth=z1 - z0)
    for v in bm.verts: v.co.z += (z0 + z1) / 2
    me = bpy.data.meshes.new('r'); bm.to_mesh(me); bm.free(); o = obj('plat', me, m)
    md = o.modifiers.new('b', 'BEVEL'); md.width = bevel; md.segments = 2
    return o
ring(0, 1.55, -.1, .06, 8, stone2, .035)                 # en alt sekizgen basamak
ring(0, 1.3, .06, .15, 8, stone, .025)                   # orta basamak
ring(0, 1.08, .15, PLAT_H, 48, stone, .015)              # üst disk
# kenar bandı (altın) + rün yazıları + iç halka oyma
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, segments=96, radius=1.86)
me = bpy.data.meshes.new('band'); bm.to_mesh(me); bm.free(); band = obj('band', me, gold)
band.location.z = PLAT_H - .035; md = band.modifiers.new('s', 'SCREW'); md.screw_offset = 0; md.angle = 0; md.steps = 1
bpy.context.view_layer.objects.active = band
for o in [band]:
    o.data = o.data  # (bant: torus ile)
bpy.data.objects.remove(band)
bpy.ops.mesh.primitive_torus_add(major_radius=1.09, minor_radius=.025, location=(0, 0, PLAT_H - .04)); bpy.context.object.data.materials.append(gold)
bpy.ops.mesh.primitive_torus_add(major_radius=.86, minor_radius=.009, location=(0, 0, PLAT_H + .001)); bpy.context.object.data.materials.append(gold)
bpy.ops.mesh.primitive_torus_add(major_radius=.62, minor_radius=.009, location=(0, 0, PLAT_H + .001)); bpy.context.object.data.materials.append(gold)
# rünler: iki halka arasında küçük ışıklı çizgi kümeleri
for i in range(36):
    ang = i / 36 * math.tau; cx, cy = math.cos(ang) * .74, math.sin(ang) * .74
    for k in range(rnd.randint(2, 3)):
        L = rnd.uniform(.04, .08); a2 = ang + rnd.choice([0, math.pi / 2, math.pi / 4, -math.pi / 4])
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx + rnd.uniform(-.03, .03), cy + rnd.uniform(-.03, .03), PLAT_H + .003))
        c = bpy.context.object; c.scale = (L, .008, .004); c.rotation_euler.z = a2; c.data.materials.append(rune)
# ---------------- kuru ağaçlar (dallanan, burulmuş tüpler)
bark = noise_mat('bark', (.035, .03, .03), (.12, .1, .095), scale=25, bump=.8, detail=12)
def branch(bm, p, d, L, r, depth):
    n = 6; pts = [p.copy()]; q = p.copy(); dd = d.copy()
    for i in range(n):
        dd = (dd + Vector((rnd.uniform(-.35, .35), rnd.uniform(-.35, .35), rnd.uniform(-.1, .25)))).normalized()
        q = q + dd * (L / n); pts.append(q.copy())
    rings = []
    for i, c in enumerate(pts):
        rr = r * (1 - i / (n + 1) * .7)
        t = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized(); u = t.orthogonal().normalized(); w = t.cross(u)
        rings.append([bm.verts.new(c + (u * math.cos(k / 6 * math.tau) + w * math.sin(k / 6 * math.tau)) * rr) for k in range(6)])
    for i in range(n):
        for k in range(6): bm.faces.new((rings[i][k], rings[i][(k + 1) % 6], rings[i + 1][(k + 1) % 6], rings[i + 1][k]))
    if depth > 0:
        for j in range(rnd.randint(2, 3)):
            idx = rnd.randint(2, n); nd = (dd + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-.2, .7)))).normalized()
            branch(bm, pts[idx], nd, L * rnd.uniform(.5, .72), r * .55, depth - 1)
def tree(x, y, s, lean=(0, 0)):
    bm = bmesh.new(); branch(bm, Vector((x, y, -.3)), Vector((lean[0], lean[1], 1)).normalized(), 4.5 * s, .32 * s, 4)
    me = bpy.data.meshes.new('t'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    obj('tree', me, bark)
for (x, y, s, l) in [(-5.2, 2.5, 1.35, (.25, 0)), (-8, 7, 1.5, (.1, .1)), (-4, 11, 1.1, (0, 0)), (6.3, 4.5, 1.45, (-.25, .05)), (9, 9, 1.6, (-.1, 0)), (-3.2, 6, .9, (.1, 0)),
                     (4.2, 14, 1.0, (0, 0)), (-12, 14, 1.6, (.2, 0)), (12, 15, 1.5, (-.2, 0)), (-2, 20, 1.2, (0, 0)), (1.8, 24, 1.3, (0, 0)), (-15, 6, 1.5, (.3, 0)), (15, 5, 1.4, (-.3, 0))]:
    tree(x, y, s, l)
for i in range(22):   # orta mesafe: patikanın iki yanı
    sd = rnd.choice([-1, 1]); y = rnd.uniform(7, 24); x = sd * rnd.uniform(4 + .25 * y, 9 + .6 * y)
    tree(x, y, rnd.uniform(.9, 1.5), (-sd * rnd.uniform(0, .25), 0))
for i in range(16):   # arka orman: uzak, daha ince ağaçlar
    x = rnd.uniform(-34, 34); y = rnd.uniform(24, 42)
    if abs(x) < 7: continue
    tree(x, y, rnd.uniform(1.0, 1.7), (rnd.uniform(-.2, .2), 0))
# kuru çalılar: küçük diken kümeleri
shrub = noise_mat('shrub', (.05, .025, .015), (.16, .08, .04), scale=40, bump=.3)
for i in range(110):
    x = rnd.uniform(-14, 14); y = rnd.uniform(-2, 22)
    if math.hypot(x, y) < 2.2 or (abs(x) < 1.6 + .08 * y and y > 0) or (abs(x) < 2.5 and y < 0): continue
    bm = bmesh.new(); h0 = rnd.uniform(.25, .7)
    for k in range(rnd.randint(5, 9)):
        d = Vector((rnd.uniform(-.6, .6), rnd.uniform(-.6, .6), 1)).normalized()
        r = bmesh.ops.create_cone(bm, cap_ends=False, segments=3, radius1=.02, radius2=0, depth=h0 * rnd.uniform(.6, 1.1))
        rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=rot, verts=r['verts']); bmesh.ops.translate(bm, vec=d * h0 * .4, verts=r['verts'])
    me = bpy.data.meshes.new('sh'); bm.to_mesh(me); bm.free(); o = obj('shrub', me, shrub); o.location = (x, y, 0)
# kayalar
for i in range(26):
    ang = rnd.uniform(0, math.tau); rr = rnd.uniform(3.3, 13)
    x, y = math.cos(ang) * rr, abs(math.sin(ang)) * rr * rnd.choice([1, 1, -.25])
    if abs(x) < 2.5 and y < 0: continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rnd.uniform(.12, .45), location=(x, y, 0))
    o = bpy.context.object; o.scale = (1, rnd.uniform(.7, 1.2), rnd.uniform(.4, .7)); o.data.materials.append(stone2)
    for v in o.data.vertices: v.co *= 1 + rnd.uniform(-.18, .18)

# ---------------- fenerli direk (sağda)
wood = noise_mat('wood', (.07, .045, .03), (.2, .13, .08), scale=30, bump=.5)
lamp = mat('lamp', (1, .7, .35), rough=.4, emit=(1., .5, .15), es=25)
px, py = 3.6, 2.6
for (loc, sz) in [((px, py, 1.4), (.18, .18, 3.0)), ((px, py, 2.55), (1.5, .14, .14)), ((px, py, 2.2), (1.0, .1, .1))]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = sz; o.data.materials.append(wood)
for dx in (-.55, .55):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=.11, depth=.28, location=(px + dx, py, 2.15)); bpy.context.object.data.materials.append(lamp)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=.15, depth=.12, location=(px + dx, py, 2.34)); bpy.context.object.data.materials.append(wood)
    L = bpy.data.lights.new('l', 'POINT'); L.energy = 220; L.color = (1., .55, .22); L.shadow_soft_size = .15
    lo = bpy.data.objects.new('l', L); lo.location = (px + dx, py - .05, 2.1); C.objects.link(lo)

# ---------------- gökyüzü: koyu mavi gradyan, bulut, ay; hafif hacimsel sis
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
grad = nt.nodes.new('ShaderNodeValToRGB'); grad.color_ramp.elements[0].position = .5; grad.color_ramp.elements[0].color = (.06, .14, .26, 1); grad.color_ramp.elements[1].color = (.01, .025, .07, 1)
nt.links.new(sep.outputs['Z'], grad.inputs['Fac'])
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 6; nt.links.new(tc.outputs['Generated'], nz.inputs['Vector'])
cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = .5; cr.color_ramp.elements[0].color = (0, 0, 0, 1); cr.color_ramp.elements[1].position = .72; cr.color_ramp.elements[1].color = (.12, .2, .32, 1)
nt.links.new(nz.outputs['Fac'], cr.inputs['Fac'])
add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs['Factor'].default_value = 1
nt.links.new(grad.outputs['Color'], add.inputs[6]); nt.links.new(cr.outputs['Color'], add.inputs[7]); nt.links.new(add.outputs[2], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
# ay (arkada, sol üst) + bulut kartları
moon = mat('moon', (1, 1, 1), emit=(.75, .85, 1.), es=6)
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.2, location=(-9, 80, 12.2)); bpy.context.object.data.materials.append(moon)
vol = nt.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = .005; vol.inputs['Color'].default_value = (.5, .62, .8, 1); vol.inputs['Anisotropy'].default_value = .3
fogm = bpy.data.materials.new('fog'); fogm.use_nodes = True; fn = fogm.node_tree; fn.nodes.remove(fn.nodes['Principled BSDF'])
fv = fn.nodes.new('ShaderNodeVolumePrincipled'); fv.inputs['Density'].default_value = .009; fv.inputs['Color'].default_value = (.5, .62, .8, 1); fv.inputs['Anisotropy'].default_value = .35
fn.links.new(fv.outputs[0], fn.nodes['Material Output'].inputs['Volume'])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 12, 4)); fc = bpy.context.object; fc.scale = (60, 30, 8.5); fc.data.materials.append(fogm)   # sis yalnız ön planda (gökyüzünü yutmasın)

# ay ışığı (arka-sol, soğuk) + çok hafif mavi dolgu
L = bpy.data.lights.new('moon', 'SUN'); L.energy = 1.7; L.color = (.6, .72, 1.); L.angle = .03
lo = bpy.data.objects.new('moon', L); lo.rotation_euler = (math.radians(58), 0, math.radians(200)); C.objects.link(lo)
L = bpy.data.lights.new('fill', 'AREA'); L.energy = 420; L.size = 6; L.color = (.45, .55, .85)
lo = bpy.data.objects.new('fill', L); lo.location = (0, -9, 5); lo.rotation_euler = (math.radians(60), 0, 0); C.objects.link(lo)
L = bpy.data.lights.new('plat', 'SPOT'); L.energy = 600; L.spot_size = math.radians(45); L.spot_blend = .8; L.color = (.85, .9, 1.)
lo = bpy.data.objects.new('plat', L); lo.location = (0, -1.5, 8); lo.rotation_euler = (math.radians(10), 0, 0); C.objects.link(lo)

# ---------------- kamera + render
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); C.objects.link(cam); sc.camera = cam
cam.location = (0, -CAM_D, CAM_H); cam.rotation_euler = (Vector((0, 0, TGT_Z)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(FOV_V); cam.data.clip_end = 400
sc.render.engine = 'CYCLES'; sc.cycles.samples = SMP; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.cycles.volume_step_rate = 4; sc.cycles.volume_max_steps = 64
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True); print('tamam', OUT)
