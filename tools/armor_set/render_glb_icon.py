# Tek bir parça GLB'sinden 112x147 şeffaf envanter ikonu: python3 -I render_glb_icon.py -- <parça.glb> <çıkış.webp>
import sys, os, bpy
from mathutils import Vector
from PIL import Image
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
ms = [o for o in bpy.data.objects if o.type == 'MESH' and o.vertex_groups]   # içe aktarıcının kemik şekli (Icosphere) hariç
for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.vertex_groups]: bpy.data.objects.remove(o)
for o in ms: o.modifiers.clear()
for o in [o for o in bpy.data.objects if o.type == 'ARMATURE']: bpy.data.objects.remove(o)   # bağlama pozunda kalsın
for o in ms: o.parent = None; o.matrix_world = __import__('mathutils').Matrix()
bpy.context.view_layer.update()
pts = [o.matrix_world @ v.co for o in ms for v in o.data.vertices]
zs = sorted(p.z for p in pts); zlo, zhi = zs[int(len(zs) * .01)], zs[int(len(zs) * .99)]
pts = [p for p in pts if zlo - 5 <= p.z <= zhi + 5]   # uç köşeler (gltf dikiş yardımcıları) çerçeveyi bozmasın
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
c = (lo + hi) / 2; ext = max(hi.x - lo.x, hi.z - lo.z) / 2; print("ICON", lo, hi)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 1.6
for n, loc, en in [('key', (150, -250, 300), 9e6), ('rim', (-250, 150, 120), 6e6), ('fill', (-150, -250, 0), 3e6)]:
    L = bpy.data.lights.new(n, 'POINT'); L.energy = en; L.shadow_soft_size = 30; lo = bpy.data.objects.new(n, L); lo.location = c + Vector(loc); sc.collection.objects.link(lo)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = ext * 2.3; cam.data.clip_end = 5000
cam.location = c + Vector((0.4, -1, 0.15)).normalized() * 400; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y = 224, 294; p = out + '.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
Image.open(p).convert('RGBA').resize((112, 147), Image.LANCZOS).save(out, quality=90, method=6); os.remove(p)
