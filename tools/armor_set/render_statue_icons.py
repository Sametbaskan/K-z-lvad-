# Güneş Şövalyesi ikonları: kesilmiş heykelin (fit_static_armor.py -> _cut.blend) dokulu render'ından bölge kırpma, 112x147 şeffaf webp
#   python3 -I render_statue_icons.py -- <_cut.blend> <doku_klasörü> <çıkış_klasörü>
import sys, os, bpy, math
from mathutils import Vector
from PIL import Image
B, TX, OUT = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=B)
o = [o for o in bpy.data.objects if o.type == 'MESH'][0]
for m in o.data.materials:
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == 'TEX_IMAGE': nt.nodes.remove(n)
    b = nt.nodes['Principled BSDF']
    def tx(k, inp, nc=False):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TX, f'SunKnightWarrior_{k}.JPEG'))
        if nc: t.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(t.outputs['Color'], b.inputs[inp])
    tx('basecolor', 'Base Color'); tx('metallic', 'Metallic', True); tx('roughness', 'Roughness', True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 2.2
for n, loc, en in [('key', (120, -200, 220), 7e6), ('rim', (-200, 150, 150), 5e6), ('fill', (-120, -220, 60), 3e6)]:
    L = bpy.data.lights.new(n, 'POINT'); L.energy = en; L.shadow_soft_size = 40; lo = bpy.data.objects.new(n, L); lo.location = loc; sc.collection.objects.link(lo)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 5000
def shot(name, c, osc, dirv=(0.35, -1, 0.12)):
    c = Vector(c); cam.location = c + Vector(dirv).normalized() * 500; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = osc
    sc.render.resolution_x, sc.render.resolution_y = 448, 588; p = os.path.join(OUT, name + '.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    im = Image.open(p).convert('RGBA'); bb = im.getbbox()
    if bb:  # içeriği ortala, kenar payı
        crop = im.crop(bb); k = min(104 / crop.width, 139 / crop.height); crop = crop.resize((max(1, int(crop.width * k)), max(1, int(crop.height * k))), Image.LANCZOS)
        out = Image.new('RGBA', (112, 147), (0, 0, 0, 0)); out.alpha_composite(crop, ((112 - crop.width) // 2, (147 - crop.height) // 2)); im = out
    im.save(os.path.join(OUT, name + '.webp'), quality=90, method=6); os.remove(p)
shot('gunes_zirh', (0, 0, 92), 175)
shot('gunes_migfer', (0, 2, 160), 62, (0.3, -1, 0.1))
import bmesh   # bot: yalnız ayak bölgesi kalsın (pelerin ve etek ikonun önünü kapatmasın)
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not (12 < abs(v.co.x) < 33 and -32 < v.co.y < 13 and v.co.z < 24)], context='VERTS'); bm.to_mesh(o.data); bm.free()
shot('gunes_bot', (0, -6, 11), 70, (0.45, -1, 0.4))
print('ikonlar tamam')
