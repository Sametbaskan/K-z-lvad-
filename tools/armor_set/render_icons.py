# Zırh ikonları: fit_meshy_armor.py çıktısındaki _fit.blend'den 112x147 şeffaf webp (kılıç ikonlarıyla aynı ölçü)
#   python3 -I render_icons.py -- <fit_klasörü> <çıkış_klasörü> <set>
import sys, os, bpy
from mathutils import Vector
from PIL import Image
D, OUT, SET = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(D, '_fit.blend'))
m = bpy.data.materials[SET]; nt = m.node_tree; b = nt.nodes['Principled BSDF']
def tex(f, inp, nc=False):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(D, 'tex', f))
    if nc: t.image.colorspace_settings.name = 'Non-Color'
    return t
nt.links.new(tex('base.jpg', '').outputs['Color'], b.inputs['Base Color'])
mr = tex('mr.jpg', '', True); sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(mr.outputs['Color'], sep.inputs[0])
nt.links.new(sep.outputs['Green'], b.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], b.inputs['Metallic'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex('normal.jpg', '', True).outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
for o in bpy.data.objects:
    if o.type == 'MESH': o.modifiers.clear()
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 1.6
for nm_, loc, en in [('key', (150, -250, 300), 9e6), ('rim', (-250, 150, 120), 6e6), ('fill', (-150, -250, 0), 3e6)]:
    L = bpy.data.lights.new(nm_, 'POINT'); L.energy = en; L.shadow_soft_size = 30; lo = bpy.data.objects.new(nm_, L); lo.location = loc; sc.collection.objects.link(lo)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 5000
def shot(names, out, view, ortho, center):
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o.name not in names
    c = Vector(center); cam.location = c + Vector(view) * 400; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = ortho
    sc.render.resolution_x, sc.render.resolution_y = 224, 294; p = os.path.join(D, out + '.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    Image.open(p).convert('RGBA').resize((112, 147), Image.LANCZOS).save(os.path.join(OUT, out + '.webp'), quality=90, method=6)
shot({'gogusluk', 'sirt', 'omuzluk_l', 'omuzluk_r', 'bel', 'bacak_l', 'bacak_r'}, SET + '_zirh', (0.35, -1, 0.1), 150, (0, 0, 115))
shot({'botlar'}, SET + '_bot', (0.35, -1, 0.45), 80, (0, 3, 14))
print('ikonlar tamam')
