# VALKOR - 10 efsanevi tek elli kılıç: prosedürel 3D model + doku + GLB + envanter ikonu üretici.
# Blender'ın Python modülüyle çalışır (pip install bpy==5.2.*):
#   python3 -I gen_swords.py -- <çıkış_klasörü> [kılıç_id ...]
# Çıktı: <çıkış>/<id>.glb, <çıkış>/<id>_icon.webp, <çıkış>/<id>_preview.png
# Eksen sözleşmesi (oyundaki WMODELS ile aynı): kabza ortası orijinde, namlu +Y (glTF), namlu genişliği X, kalınlık Z.
# Blender içinde: namlu +Z, genişlik X, kalınlık Y (glTF dışa aktarımı Z->Y çevirir).
import sys, os, math, random
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from PIL import Image, ImageDraw, ImageFilter

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else 'out')
ONLY = set(argv[1:])
os.makedirs(OUT, exist_ok=True)
TEXDIR = os.path.join(OUT, '_tex'); os.makedirs(TEXDIR, exist_ok=True)
TAU = math.pi * 2

# ------------------------------------------------------------------ yardımcılar: sahne / malzeme
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)

def mat(name, color, metal=1.0, rough=0.3, emit=None, emit_strength=1.0, base_tex=None, emit_tex=None, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if base_tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(base_tex); t.interpolation = 'Linear'
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_strength
        if emit_tex:
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(emit_tex)
            nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    return m

def obj_from_bm(bm, name, material, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(material)
    return o

def new_uv(bm):
    return bm.loops.layers.uv.verify()

def set_face_uv(face, uvl, uvs):
    for loop, uv in zip(face.loops, uvs): loop[uvl].uv = uv

# ------------------------------------------------------------------ geometri üreticileri
def loft(name, rings, us, vs, material, smooth=False, cap0=True, cap1=True):
    """rings: [ [Vector,...] (kapalı halka, eşit nokta sayısı) ]; us: halka noktası başına u (len n+1, son = sarma); vs: halka başına v"""
    bm = bmesh.new(); uvl = new_uv(bm)
    R = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for i in range(len(R) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            a, b, c, d = R[i][j], R[i][j2], R[i + 1][j2], R[i + 1][j]
            if len({a.co.to_tuple(6), b.co.to_tuple(6), c.co.to_tuple(6), d.co.to_tuple(6)}) < 3: continue
            try:
                f = bm.faces.new((a, b, c, d))
            except ValueError:
                continue
            set_face_uv(f, uvl, [(us[j], vs[i]), (us[j + 1], vs[i]), (us[j + 1], vs[i + 1]), (us[j], vs[i + 1])])
    for cap, ring, flip in ((cap0, R[0], True), (cap1, R[-1], False)):
        if not cap: continue
        try:
            f = bm.faces.new(list(reversed(ring)) if flip else ring)
            set_face_uv(f, uvl, [(0.5, 0.5)] * len(ring))
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(bm, name, material, smooth)

def blade(name, material, L, z0, wl, wr, th, cx=lambda t: 0.0, n=56, bevel=0.45, extra_t=()):
    """namlu: t∈[0,1] boyunca kesit (8 köşeli mercek: kenar–pah–sırt). wl/wr: sol/sağ yarı genişlik, th: sırt yarı kalınlığı."""
    ts = sorted(set([i / n for i in range(n + 1)] + list(extra_t)))
    rings, vs = [], []
    for t in ts:
        x0, a, b, h = cx(t), max(wl(t), 0.0), max(wr(t), 0.0), max(th(t), 0.0004)
        e = 0.0005 if a + b > 0.002 else 0.0
        z = z0 + L * t
        ring = [Vector((x0 - a, 0, z)), Vector((x0 - a * bevel, h * 0.62, z)), Vector((x0, h, z)), Vector((x0 + b * bevel, h * 0.62, z)),
                Vector((x0 + b, 0, z)), Vector((x0 + b * bevel, -h * 0.62, z)), Vector((x0, -h, z)), Vector((x0 - a * bevel, -h * 0.62, z))]
        if a + b < 1e-5:  # uç: tek noktaya kapanır
            ring = [Vector((x0, 0, z))] * 8
        rings.append(ring); vs.append(t)
    # ön yüz 0..0.5 (kenarL=0, sırt=.25, kenarR=.5), arka yüz .5..1
    us = [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    return loft(name, rings, us, vs, material, smooth=False, cap0=True, cap1=False)

def revolve(name, material, profile, seg=12, rmod=None, smooth=True, z_off=0.0, center=(0, 0), scale_xy=(1, 1), phase=0.0):
    """profile: [(r,z)] alttan üste; rmod(theta, z, k) -> yarıçap çarpanı"""
    rings, vs = [], []
    zs = [p[1] for p in profile]; zmin, zmax = min(zs), max(zs)
    for k, (r, z) in enumerate(profile):
        ring = []
        for j in range(seg):
            th = TAU * j / seg + phase
            rr = r * (rmod(th, z, k) if rmod else 1.0)
            ring.append(Vector((center[0] + rr * math.cos(th) * scale_xy[0], center[1] + rr * math.sin(th) * scale_xy[1], z + z_off)))
        rings.append(ring); vs.append((z - zmin) / max(zmax - zmin, 1e-6))
    us = [j / seg for j in range(seg + 1)]
    return loft(name, rings, us, vs, material, smooth=smooth, cap0=profile[0][0] > 0, cap1=profile[-1][0] > 0)

def gem(name, material, center, up, down, r, sides=8, girdle=0.25, rot=None, scale_xy=(1, 1)):
    prof = [(0.0, -down), (r * 0.72, -down * girdle), (r, 0.0), (r * 0.72, up * girdle), (0.0, up)]
    o = revolve(name, material, prof, seg=sides, smooth=False, scale_xy=scale_xy, phase=math.pi / sides)
    if rot: o.rotation_euler = rot
    o.location = center
    return o

def tube(name, material, pts, radii, seg=6, smooth=True, scale_y=1.0):
    """çoklu çizgi boyunca süpürülmüş boru (boynuz, pençe, kemer). radii nokta başına."""
    pts = [Vector(p) for p in pts]
    rings, vs = [], []
    up = Vector((0, 1, 0))
    for i, p in enumerate(pts):
        tdir = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = up - tdir * up.dot(tdir)
        if nrm.length < 1e-4: nrm = Vector((1, 0, 0)) - tdir * tdir.x
        nrm.normalize(); bin_ = tdir.cross(nrm).normalized()
        ring = []
        for j in range(seg):
            a = TAU * j / seg
            ring.append(p + (nrm * math.cos(a) * scale_y + bin_ * math.sin(a)) * radii[i])
        rings.append(ring); vs.append(i / (len(pts) - 1))
    us = [j / seg for j in range(seg + 1)]
    return loft(name, rings, us, vs, material, smooth=smooth, cap0=radii[0] > 1e-5, cap1=radii[-1] > 1e-5)

def slab(name, material, outline, thick, y=0.0, bevel=0.0018, smooth=False):
    """XZ düzleminde çizilmiş 2B şekli Y yönünde kalınlaştır (muhafız, kanat, sivri uçlar)."""
    bm = bmesh.new(); uvl = new_uv(bm)
    xs = [p[0] for p in outline]; zs = [p[1] for p in outline]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    def uv(p): return ((p[0] - x0) / max(x1 - x0, 1e-6), (p[1] - z0) / max(z1 - z0, 1e-6))
    F = [bm.verts.new((p[0], y + thick / 2, p[1])) for p in outline]
    Bk = [bm.verts.new((p[0], y - thick / 2, p[1])) for p in outline]
    f = bm.faces.new(F); set_face_uv(f, uvl, [uv(p) for p in outline])
    f = bm.faces.new(list(reversed(Bk))); set_face_uv(f, uvl, [uv(p) for p in reversed(outline)])
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((F[i], Bk[i], Bk[j], F[j])); set_face_uv(f, uvl, [uv(outline[i]), uv(outline[i]), uv(outline[j]), uv(outline[j])])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(bm, name, material, smooth)
    if bevel > 0:
        m = o.modifiers.new('bv', 'BEVEL'); m.width = bevel; m.segments = 1; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(40)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.modifier_apply(modifier=m.name); o.select_set(False)
    # ngonları üçgenle (içbükey şekiller dışa aktarımda bozulmasın)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='EAR_CLIP'); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = smooth
    return o

def sphere(name, material, center, r, scale=(1, 1, 1), seg=10, rings=6, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(center)
    uvl = new_uv(bm)
    return obj_from_bm(bm, name, material, smooth)

def mirror(o, axis, name=None):
    """nesnenin dünya geometrisini X (0) ya da Y (1) eksenine göre aynala; yeni nesne döner"""
    me = o.data.copy(); me.transform(o.matrix_world)
    for v in me.vertices: v.co[axis] = -v.co[axis]
    me.flip_normals()
    c = bpy.data.objects.new(name or o.name + '_m', me); bpy.context.scene.collection.objects.link(c)
    return c
def mirror_x(o, name=None): bpy.context.view_layer.update(); return mirror(o, 0, name)
def mirror_y(o, name=None): bpy.context.view_layer.update(); return mirror(o, 1, name)

def grip(name, material, z0, z1, r0, r1, style='spiral', seg=14, rows=None, amp=0.0022):
    """kabza: deri sargı (spiral), çapraz örgü (cross), halka (rings), pul (scales) desenli yüzey"""
    nz = rows or 26
    prof = [(r0 + (r1 - r0) * (k / nz), z0 + (z1 - z0) * k / nz) for k in range(nz + 1)]
    prof = [(prof[0][0] * 0.92, z0 - 0.002)] + prof + [(prof[-1][0] * 0.92, z1 + 0.002)]
    turns = 7.0
    def rm(th, z, k):
        if k == 0 or k == len(prof) - 1: return 1.0
        u = (z - z0) / (z1 - z0)
        if style == 'spiral':
            return 1.0 + amp / r0 * (abs(math.sin(th * 0.5 + u * turns * math.pi)) ** 0.6 * 2 - 1)
        if style == 'cross':
            a = abs(math.sin(th * 1.0 + u * turns * math.pi)); b = abs(math.sin(th * 1.0 - u * turns * math.pi))
            return 1.0 + amp / r0 * (max(a, b) * 1.6 - 1)
        if style == 'rings':
            return 1.0 + amp / r0 * (abs(math.sin(u * turns * math.pi * 1.6)) ** 0.5 * 2 - 1)
        if style == 'bone':  # omur dizisi
            return 1.0 + amp / r0 * (abs(math.sin(u * 6 * math.pi)) ** 0.35 * 3 - 1.5)
        return 1.0
    return revolve(name, material, prof, seg=seg, rmod=rm, smooth=True)

def scales_grip(name, material, z0, z1, r, rows=7, per=8):
    """ejderha pulu: üst üste binen küçük piramit pullar"""
    bm = bmesh.new(); uvl = new_uv(bm)
    for i in range(rows):
        z = z0 + (z1 - z0) * (i + 0.5) / rows
        for j in range(per):
            a = TAU * (j + 0.5 * (i % 2)) / per
            c = Vector((math.cos(a), math.sin(a), 0))
            t = Vector((-math.sin(a), math.cos(a), 0))
            h = (z1 - z0) / rows * 0.95; w = TAU * r / per * 0.62
            base = c * r + Vector((0, 0, z))
            tip = c * (r + 0.0055) + Vector((0, 0, z - h * 0.55))
            v1 = bm.verts.new(base + t * w + Vector((0, 0, h * 0.45)))
            v2 = bm.verts.new(base - t * w + Vector((0, 0, h * 0.45)))
            v3 = bm.verts.new(tip)
            v4 = bm.verts.new(c * (r - 0.001) + Vector((0, 0, z - h * 0.5)))
            for f in ((v1, v2, v3), (v2, v4, v3), (v4, v1, v3)):
                ff = bm.faces.new(f); set_face_uv(ff, uvl, [(0, 0), (1, 0), (0.5, 1)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(bm, name, material, False)

def join_all(name):
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objs:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(o.data); bm.free()
    return o

# ------------------------------------------------------------------ doku üretimi (PIL)
TW, TH = 128, 512
def noise_img(w, h, sx, sy, seed, octaves=3):
    rng = np.random.default_rng(seed); out = np.zeros((h, w))
    for o in range(octaves):
        gw, gh = max(2, int(w / sx * 2 ** o)), max(2, int(h / sy * 2 ** o))
        g = rng.random((gh, gw))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, float) / 255 / 2 ** o
    out -= out.min(); out /= max(out.max(), 1e-6)
    return out

def spine_x(face): return 32 if face == 0 else 96
def vy(v): return int((1 - v) * (TH - 1))

def rune_glyph(draw, cx, cy, s, rng, color, width=2):
    """kadim rün: dikey gövde + 1-3 çapraz dal (rastgele, tohumlu)"""
    top, bot = cy - s, cy + s
    draw.line([(cx, top), (cx, bot)], fill=color, width=width)
    for _ in range(rng.integers(1, 4)):
        y0 = cy + rng.integers(-s, s // 2)
        side = rng.choice([-1, 1]); dy = rng.choice([-1, 1]) * s * 0.55
        draw.line([(cx, y0), (cx + side * s * 0.6, y0 + dy)], fill=color, width=width)
    if rng.random() < 0.4:
        draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], outline=color)

def runes_on(draw, v0, v1, step, size, color, seed, width=2, both=True):
    rng = np.random.default_rng(seed)
    v = v0
    while v < v1:
        for face in ((0, 1) if both else (0,)):
            rune_glyph(draw, spine_x(face), vy(v), size, np.random.default_rng(seed + int(v * 1000)), color, width)
        v += step

def veins_on(draw, color, seed, v0=0.02, v1=0.85, n=3, spread=11, width=2):
    rng = np.random.default_rng(seed)
    for face in (0, 1):
        for k in range(n):
            x = spine_x(face) + rng.integers(-4, 5); v = v0 + rng.random() * 0.05
            pts = [(x, vy(v))]
            while v < v1 - rng.random() * 0.25:
                v += 0.015 + rng.random() * 0.02
                x = np.clip(x + rng.integers(-3, 4), spine_x(face) - spread, spine_x(face) + spread)
                pts.append((x, vy(v)))
                if rng.random() < 0.12:  # dal
                    bx, bv = x, v; br = [(bx, vy(bv))]
                    for _ in range(rng.integers(2, 5)):
                        bv += 0.012; bx += rng.choice([-3, 3]); br.append((bx, vy(bv)))
                    draw.line(br, fill=color, width=1)
            draw.line(pts, fill=color, width=width)

def save(img, name, q=None):
    p = os.path.join(TEXDIR, name)
    if p.endswith('.jpg'): img.convert('RGB').save(p, quality=q or 88)
    else: img.save(p)
    return p

def metal_base(c_mid, c_edge, seed, brushed=True, edge_px=14, damascus=False, rust=0.0):
    n = noise_img(TW, TH, 64 if brushed else 24, 8 if brushed else 24, seed)
    n2 = noise_img(TW, TH, 16, 16, seed + 7)
    img = np.zeros((TH, TW, 3))
    x = np.arange(TW)[None, :]
    d = np.minimum(np.minimum(np.abs(x - 0), np.abs(x - 64)), np.abs(x - 127)).astype(float)
    ed = np.clip(1 - d / edge_px, 0, 1)[:, :, None] * np.ones((TH, 1, 1))
    mid = np.array(c_mid)[None, None, :]; edg = np.array(c_edge)[None, None, :]
    img = mid * (1 - ed) + edg * ed
    img *= (0.85 + 0.3 * n)[:, :, None]
    if damascus:
        yy = np.arange(TH)[:, None]
        wav = np.sin((x * 0.35 + yy * 0.09 + n2 * 9)) * 0.5 + 0.5
        img *= (0.8 + 0.35 * wav)[:, :, None] * (1 - ed) + ed
    if rust > 0:
        r = noise_img(TW, TH, 10, 10, seed + 3)
        m = np.clip((r - (1 - rust)) * 4, 0, 1)[:, :, None]
        img = img * (1 - m) + np.array([0.33, 0.17, 0.08])[None, None, :] * m * (0.7 + 0.4 * n2[:, :, None])
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

def to_lin(c): return tuple((x / 255) ** 2.2 if x > 1 else x for x in c)
def hex2(c): return ((c >> 16 & 255) / 255, (c >> 8 & 255) / 255, (c & 255) / 255)
def lin(c):   # sRGB 0..1 -> doğrusal (Blender malzeme renkleri doğrusaldır)
    return tuple(x ** 2.2 for x in c)

# ------------------------------------------------------------------ ortak malzeme kısayolları
def M_metal(name, srgb, rough=0.3, metal=1.0, emit=None):
    return mat(name, lin(srgb), metal, rough, emit=lin(emit) if emit else None)
def M_leather(name, srgb, rough=0.72):
    return mat(name, lin(srgb), 0.0, rough)
def M_crystal(name, srgb, glow):
    return mat(name, lin(srgb), 0.0, 0.08, emit=lin(glow), emit_strength=1.0)

# ================================================================== 10 KILIÇ
SPECS = {}
def sword(fn): SPECS[fn.__name__] = fn; return fn

# grip yarı boyu ve namlu başlangıcı ortak ölçüler (tek el: kabza 17–19 cm)
@sword
def kizil_hukum():
    """KIZIL HÜKÜM: siyah çelik geniş namlu, kızıl enerji damarları + rünler, ejder başlı muhafız, pençeli kabza başı"""
    base = metal_base((0.10, 0.10, 0.11), (0.42, 0.40, 0.42), 11, damascus=True)
    emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi); db = ImageDraw.Draw(base)
    veins_on(d, (255, 40, 20), 5, n=3); veins_on(db, (90, 10, 8), 5, n=3)
    runes_on(d, 0.06, 0.30, 0.075, 7, (255, 70, 40), 31); runes_on(db, 0.06, 0.30, 0.075, 7, (70, 8, 6), 31)
    emi = emi.filter(ImageFilter.GaussianBlur(0.6))
    blade_m = mat('KH_blade', (1, 1, 1), 1.0, 0.28, emit=(1, 0.2, 0.1), base_tex=save(base, 'kh_b.jpg'), emit_tex=save(emi, 'kh_e.png'))
    steel = M_metal('KH_steel', (0.12, 0.11, 0.12), 0.3); red = M_metal('KH_red', (0.55, 0.06, 0.04), 0.35)
    eye = M_crystal('KH_eye', (1, 0.15, 0.05), (1, 0.2, 0.05)); leather = M_leather('KH_grip', (0.17, 0.03, 0.025))
    G = 0.09
    L = 0.80; z0 = G + 0.05
    w = lambda t: 0.034 * (1 - 0.18 * t) * (1 - max(0, (t - 0.82) / 0.18) ** 1.4) if t < 1 else 0
    blade('blade', blade_m, L, z0, w, w, lambda t: 0.0062 * (1 - 0.6 * t))
    # ricasso kılıfı
    slab('ricasso', red, [(-0.04, z0 - 0.004), (0.04, z0 - 0.004), (0.036, z0 + 0.03), (0, z0 + 0.055), (-0.036, z0 + 0.03)], 0.016)
    # ejder kanadı muhafız: yukarı kıvrık
    wing = [(0.02, G), (0.07, G + 0.005), (0.115, G + 0.03), (0.145, G + 0.07), (0.128, G + 0.058), (0.135, G + 0.085), (0.11, G + 0.055),
            (0.105, G + 0.075), (0.085, G + 0.042), (0.05, G + 0.04), (0.02, G + 0.05)]
    o = slab('wingR', steel, wing, 0.02); mirror_x(o)
    o = slab('wingEdgeR', red, [(p[0] + 0.002, p[1] - 0.004) for p in wing[1:5]] + [(0.07, G + 0.012)], 0.012); mirror_x(o)
    # ejder başı (muhafız ortası, ön ve arka yüzde)
    for s in (1, -1):
        sphere('skull', steel, (0, s * 0.017, G + 0.03), 0.022, (0.9, 0.55, 1.15))
        sphere('snout', steel, (0, s * 0.03, G + 0.012), 0.012, (0.75, 1.0, 0.9))
        sphere('jaw', red, (0, s * 0.028, G - 0.002), 0.01, (0.8, 0.9, 0.6))
        for x in (-1, 1):
            sphere('eye', eye, (x * 0.010, s * 0.031, G + 0.035), 0.0042)
            tube('horn', steel, [(x * 0.012, s * 0.012, G + 0.045), (x * 0.025, s * 0.006, G + 0.068), (x * 0.042, 0, G + 0.08), (x * 0.06, 0, G + 0.078)], [0.0055, 0.004, 0.0025, 0.0003], seg=6)
    grip('grip', leather, -G, G, 0.0175, 0.0165, 'spiral')
    revolve('ferrule', steel, [(0.0, -G - 0.012), (0.021, -G - 0.012), (0.022, -G), (0.019, -G + 0.006), (0, -G + 0.006)], seg=12)
    # pençe kabza başı + kızıl taş
    gem('pgem', eye, (0, 0, -G - 0.035), 0.022, 0.022, 0.017, sides=8)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4; c, s_ = math.cos(a), math.sin(a)
        tube('claw', steel, [(c * 0.012, s_ * 0.012, -G - 0.006), (c * 0.024, s_ * 0.024, -G - 0.025), (c * 0.019, s_ * 0.019, -G - 0.05), (c * 0.006, s_ * 0.006, -G - 0.06)], [0.0045, 0.004, 0.0028, 0.0006], seg=6)

@sword
def geceyarigi():
    """GECEYARIĞI: ince, hafif kavisli siyah namlu, gümüş kenarlar, mor rünler, zarif tsuba muhafız"""
    base = metal_base((0.05, 0.05, 0.07), (0.86, 0.87, 0.9), 21, edge_px=15)
    emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi); db = ImageDraw.Draw(base)
    runes_on(d, 0.05, 0.62, 0.11, 5, (190, 90, 255), 41, width=1); runes_on(db, 0.05, 0.62, 0.11, 5, (60, 20, 90), 41, width=1)
    emi = emi.filter(ImageFilter.GaussianBlur(0.5))
    blade_m = mat('GY_blade', (1, 1, 1), 1.0, 0.22, emit=(0.7, 0.3, 1), base_tex=save(base, 'gy_b.jpg'), emit_tex=save(emi, 'gy_e.png'))
    silver = M_metal('GY_silver', (0.82, 0.83, 0.87), 0.22); black = M_metal('GY_black', (0.06, 0.06, 0.08), 0.35)
    wrap = M_leather('GY_wrap', (0.07, 0.05, 0.10), 0.6); amet = M_crystal('GY_gem', (0.6, 0.2, 1.0), (0.55, 0.15, 1.0))
    G = 0.10; L = 0.84; z0 = G + 0.03
    wl = lambda t: 0.0175 * (1 - 0.15 * t) if t < 0.86 else 0.0175 * 0.87 * (1 - (t - 0.86) / 0.14) ** 0.8
    wr = lambda t: 0.0155 * (1 - 0.1 * t) if t < 0.80 else 0.0155 * 0.92 * max(0, 1 - (t - 0.80) / 0.20) ** 1.6
    blade('blade', blade_m, L, z0, wl, wr, lambda t: 0.0048 * (1 - 0.5 * t), cx=lambda t: -0.055 * t * t)
    revolve('habaki', silver, [(0.0, z0 - 0.002), (0.02, z0 - 0.002), (0.019, z0 + 0.025), (0.0, z0 + 0.025)], seg=8, smooth=False, scale_xy=(1.05, 0.45))
    # tsuba: oval disk + hilal çıkıntıları
    revolve('tsuba', black, [(0.0, G), (0.042, G), (0.044, G + 0.004), (0.042, G + 0.008), (0.0, G + 0.008)], seg=20, smooth=True, scale_xy=(1.0, 0.62))
    for s in (1, -1):
        tube('crescent', silver, [(s * 0.04, 0, G + 0.004), (s * 0.058, 0, G + 0.016), (s * 0.063, 0, G + 0.036), (s * 0.056, 0, G + 0.05)], [0.004, 0.0035, 0.0025, 0.0004], seg=6)
    grip('grip', wrap, -G, G, 0.0158, 0.0152, 'cross', amp=0.0016)
    for k in range(4):  # gümüş baklava (menuki) süsleri
        z = -G + 0.035 + k * 0.045
        gem('menuki', silver, (0, 0.016 if k % 2 else -0.016, z), 0.007, 0.007, 0.005, sides=4, rot=(math.pi / 2, 0, 0))
    revolve('kashira', silver, [(0.0, -G - 0.02), (0.012, -G - 0.019), (0.017, -G - 0.008), (0.0165, -G + 0.002), (0, -G + 0.002)], seg=12)
    gem('pgem', amet, (0, 0, -G - 0.03), 0.012, 0.01, 0.008, sides=6)

@sword
def ejder_disi():
    """EJDER DİŞİ: diş biçiminde kavisli kalın namlu, testere sırtı, pul desenli kabza, bronz-koyu çelik"""
    base = metal_base((0.22, 0.21, 0.20), (0.58, 0.55, 0.50), 31, brushed=False, edge_px=12)
    emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi)
    veins_on(d, (200, 50, 20), 9, n=1, v0=0.05, v1=0.5, spread=6, width=1)
    emi = emi.filter(ImageFilter.GaussianBlur(1.0))
    blade_m = mat('ED_blade', (1, 1, 1), 0.95, 0.38, emit=(0.8, 0.2, 0.08), base_tex=save(base, 'ed_b.jpg'), emit_tex=save(emi, 'ed_e.png'))
    bronze = M_metal('ED_bronze', (0.72, 0.46, 0.22), 0.36); dsteel = M_metal('ED_dsteel', (0.20, 0.19, 0.19), 0.4)
    scale_m = M_metal('ED_scale', (0.30, 0.20, 0.13), 0.42, 0.75); ember = M_crystal('ED_ember', (1, 0.3, 0.08), (1, 0.25, 0.05))
    G = 0.09; L = 0.74; z0 = G + 0.045
    # diş: geniş taban, içbükey ön kenar, dışbükey sırt, kavisli uç
    wl = lambda t: 0.050 * (1 - t) ** 0.85 + 0.003 * (1 - t)
    wr = lambda t: 0.030 * (1 - t) ** 1.25
    cx = lambda t: -0.07 * t ** 1.8 + 0.006
    blade('blade', blade_m, L, z0, wl, wr, lambda t: 0.0095 * (1 - t) ** 0.7 + 0.0005, cx=cx)
    # testere sırtı (sol kenar alt yarı)
    for k in range(6):
        t = 0.06 + k * 0.07
        x = cx(t) - wl(t); z = z0 + L * t
        slab('tooth', dsteel, [(x + 0.004, z), (x - 0.012, z + 0.006), (x + 0.004, z + 0.018)], 0.006, bevel=0.0008)
    # bronz bilezik (namlu kökü)
    slab('collar', bronze, [(-0.058, z0 - 0.006), (0.036, z0 - 0.006), (0.034, z0 + 0.022), (-0.054, z0 + 0.026)], 0.022)
    # boynuzlu muhafız
    for s in (1, -1):
        tube('horn', bronze, [(s * 0.02, 0, G + 0.012), (s * 0.06, 0, G + 0.014), (s * 0.09, 0, G + 0.03), (s * 0.1, 0, G + 0.058), (s * 0.09, 0, G + 0.078)],
             [0.011, 0.009, 0.007, 0.004, 0.0004], seg=8, scale_y=1.2)
    revolve('guardcore', dsteel, [(0, G - 0.004), (0.026, G - 0.004), (0.03, G + 0.012), (0.026, G + 0.03), (0, G + 0.03)], seg=8, smooth=False, scale_xy=(1.1, 0.75))
    gem('ember', ember, (0, 0.022, G + 0.014), 0.009, 0.009, 0.007, sides=6, rot=(math.pi / 2, 0, 0))
    mirror_y(bpy.data.objects['ember'])
    revolve('gripcore', dsteel, [(0, -G), (0.0128, -G), (0.0128, G), (0, G)], seg=10)
    scales_grip('scales', scale_m, -G + 0.004, G - 0.004, 0.0142, rows=8, per=9)
    for z in (-G, G - 0.004):
        revolve('band', bronze, [(0.0, z - 0.004), (0.02, z - 0.004), (0.021, z + 0.004), (0.0, z + 0.004)], seg=12)
    # diş kabza başı
    tube('fang', bronze, [(0, 0, -G - 0.004), (0.004, 0, -G - 0.025), (0.012, 0, -G - 0.045), (0.024, 0, -G - 0.058)], [0.017, 0.013, 0.007, 0.0005], seg=8)

@sword
def ruhkesen():
    """RUHKESEN: gümüş namlu, kökünde iki raylı pencere ve içinde mavi kristal çekirdek, ruh tüyü kanatlı muhafız"""
    base = metal_base((0.78, 0.80, 0.84), (0.95, 0.96, 0.98), 41)
    emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi); db = ImageDraw.Draw(base)
    for face in (0, 1):
        x = spine_x(face)
        pts = [(x + 3 * math.sin(v * 40), vy(v)) for v in np.linspace(0.28, 0.9, 60)]
        d.line(pts, fill=(80, 190, 255), width=2); db.line(pts, fill=(120, 150, 190), width=2)
    emi = emi.filter(ImageFilter.GaussianBlur(0.8))
    blade_m = mat('RK_blade', (1, 1, 1), 1.0, 0.18, emit=(0.3, 0.7, 1), base_tex=save(base, 'rk_b.jpg'), emit_tex=save(emi, 'rk_e.png'))
    silver = M_metal('RK_silver', (0.84, 0.86, 0.9), 0.2); core = M_crystal('RK_core', (0.25, 0.65, 1.0), (0.2, 0.6, 1.0))
    pale = M_leather('RK_grip', (0.55, 0.62, 0.70), 0.55); dark = M_metal('RK_dark', (0.25, 0.30, 0.38), 0.3)
    G = 0.09; L = 0.82; z0 = G + 0.03
    win = 0.24
    # pencere rayları
    for s in (1, -1):
        tube('rail', silver, [(s * 0.024, 0, z0), (s * 0.03, 0, z0 + 0.06), (s * 0.03, 0, z0 + 0.16), (s * 0.016, 0, z0 + win + 0.01)], [0.0065, 0.006, 0.006, 0.006], seg=6, smooth=False, scale_y=0.6)
    gem('core', core, (0, 0, z0 + win * 0.48), 0.07, 0.07, 0.016, sides=6)
    w = lambda t: 0.0275 * (1 - 0.3 * t) * (1 - max(0, (t - 0.84) / 0.16) ** 1.3)
    zb = z0 + win
    blade('blade', blade_m, L - win, zb, w, w, lambda t: 0.0055 * (1 - 0.6 * t))
    slab('bridge', silver, [(-0.032, zb - 0.012), (0.032, zb - 0.012), (0.0275, zb + 0.008), (-0.0275, zb + 0.008)], 0.013)
    # ruh kanatları (tüy dilimleri yukarı süpürülür)
    for s in (1, -1):
        for k, (a, ln) in enumerate([(0.35, 0.10), (0.65, 0.085), (0.95, 0.065)]):
            ox, oz = s * 0.02, G + 0.012
            dx, dz = s * math.cos(a) * ln, math.sin(a) * ln
            slab('feather', silver if k != 1 else dark, [(ox, oz), (ox + dx * 0.5 + s * 0.0, oz + dz * 0.5 - 0.009), (ox + dx, oz + dz), (ox + dx * 0.45, oz + dz * 0.5 + 0.008)], 0.007, bevel=0.0009)
    revolve('guardring', silver, [(0, G - 0.004), (0.024, G - 0.004), (0.026, G + 0.006), (0.022, G + 0.016), (0, G + 0.016)], seg=10, scale_xy=(1, 0.7))
    grip('grip', pale, -G, G, 0.0158, 0.0152, 'spiral', amp=0.0014)
    revolve('cap', silver, [(0.0, -G - 0.008), (0.019, -G - 0.008), (0.02, -G + 0.004), (0.0, -G + 0.004)], seg=10)
    gem('tear', core, (0, 0, -G - 0.03), 0.014, 0.03, 0.013, sides=8)

@sword
def kara_safak():
    """KARA ŞAFAK: siyah-altın kraliyet kılıcı, altın telkari, el koruyuculu (sepet kemeri) kabza, taç kabza başı"""
    base = metal_base((0.06, 0.06, 0.06), (0.30, 0.28, 0.25), 51, damascus=False)
    db = ImageDraw.Draw(base); emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi)
    gold = (215, 170, 70)
    for face in (0, 1):  # telkari kıvrımları
        x = spine_x(face)
        for k in range(5):
            v = 0.04 + k * 0.07
            for sgn in (-1, 1):
                pts = [(x + sgn * (2 + 9 * a) * math.cos(a * 7) * 0.6, vy(v + 0.025 * a + 0.01 * math.sin(a * 7))) for a in np.linspace(0, 1, 18)]
                db.line(pts, fill=gold, width=2); d.line(pts, fill=(120, 80, 20), width=1)
        db.line([(x, vy(0.42)), (x, vy(0.86))], fill=(170, 130, 50), width=2)
    blade_m = mat('KS_blade', (1, 1, 1), 1.0, 0.3, emit=(1, 0.75, 0.3), base_tex=save(base, 'ks_b.jpg'), emit_tex=save(emi, 'ks_e.png'))
    goldm = M_metal('KS_gold', (1.0, 0.77, 0.34), 0.25); black = M_metal('KS_black', (0.07, 0.07, 0.07), 0.3)
    leather = M_leather('KS_grip', (0.08, 0.06, 0.05)); onyx = M_crystal('KS_gem', (1.0, 0.8, 0.35), (1.0, 0.7, 0.25))
    G = 0.09; L = 0.79; z0 = G + 0.035
    w = lambda t: 0.032 * (1 - 0.12 * t) * (1 - max(0, (t - 0.88) / 0.12) ** 1.2)
    blade('blade', blade_m, L, z0, w, w, lambda t: 0.0058 * (1 - 0.5 * t))
    # haç muhafız: düz kollar + taç ortası
    for s in (1, -1):
        tube('arm', black, [(0, 0, G + 0.01), (s * 0.05, 0, G + 0.01), (s * 0.085, 0, G + 0.004), (s * 0.095, 0, G - 0.006)], [0.009, 0.008, 0.007, 0.006], seg=8, scale_y=1.2)
        sphere('armend', goldm, (s * 0.097, 0, G - 0.01), 0.011, (1, 1, 1))
    slab('crown', goldm, [(-0.03, G - 0.002), (0.03, G - 0.002), (0.032, G + 0.026), (0.022, G + 0.016), (0.012, G + 0.032), (0.0, G + 0.02), (-0.012, G + 0.032), (-0.022, G + 0.016), (-0.032, G + 0.026)], 0.024)
    gem('crowngem', onyx, (0, 0.013, G + 0.012), 0.008, 0.008, 0.0075, sides=6, rot=(math.pi / 2, 0, 0)); mirror_y(bpy.data.objects['crowngem'])
    # el koruyucu kemer: muhafızın +X ucundan kabza başına (parmakların dış tarafı)
    bow = [(0.09, 0, G - 0.012), (0.075, 0, G - 0.05), (0.062, 0, G - 0.1), (0.058, 0, -G + 0.04), (0.045, 0, -G - 0.004), (0.02, 0, -G - 0.016)]
    tube('bow', goldm, bow, [0.006, 0.0055, 0.005, 0.005, 0.0055, 0.006], seg=8, scale_y=1.4)
    grip('grip', leather, -G, G, 0.0168, 0.016, 'cross', amp=0.0016)
    for z in (-G + 0.06, G - 0.06):
        revolve('ring', goldm, [(0.0, z - 0.003), (0.0185, z - 0.003), (0.019, z + 0.003), (0.0, z + 0.003)], seg=12)
    # taç kabza başı
    revolve('pommel', black, [(0.0, -G - 0.04), (0.012, -G - 0.038), (0.022, -G - 0.02), (0.02, -G - 0.004), (0, -G + 0.002)], seg=12)
    for k in range(6):
        a = TAU * k / 6
        tube('spike', goldm, [(math.cos(a) * 0.016, math.sin(a) * 0.016, -G - 0.03), (math.cos(a) * 0.02, math.sin(a) * 0.02, -G - 0.05)], [0.004, 0.0004], seg=5)
    gem('pgem', onyx, (0, 0, -G - 0.045), 0.012, 0.006, 0.0085, sides=8)

@sword
def buzul_hukmu():
    """BUZUL HÜKMÜ: buz kristali namlu (altıgen kesit, kenarlarda kristal kıymıkları), donmuş kabza, sarkıt muhafız"""
    base = Image.new('RGB', (TW, TH), (150, 205, 235)); db = ImageDraw.Draw(base)
    n = noise_img(TW, TH, 20, 30, 61)
    arr = np.asarray(base, float) * (0.8 + 0.35 * n)[:, :, None]; base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); db = ImageDraw.Draw(base)
    emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi)
    rng = np.random.default_rng(3)
    for _ in range(40):  # buz çatlakları
        x = rng.integers(0, TW); y = rng.integers(0, TH); pts = [(x, y)]
        for _ in range(4): x += rng.integers(-8, 9); y += rng.integers(-14, 15); pts.append((x, y))
        db.line(pts, fill=(235, 250, 255), width=1); d.line(pts, fill=(90, 200, 255), width=1)
    emi = emi.filter(ImageFilter.GaussianBlur(0.7))
    ice = mat('BH_ice', (1, 1, 1), 0.15, 0.06, emit=(0.4, 0.8, 1), base_tex=save(base, 'bh_b.jpg'), emit_tex=save(emi, 'bh_e.png'))
    icem = M_metal('BH_icemetal', (0.55, 0.75, 0.9), 0.22, 0.85); frost = M_crystal('BH_crystal', (0.7, 0.9, 1.0), (0.35, 0.75, 1.0))
    wrap = M_leather('BH_wrap', (0.80, 0.86, 0.92), 0.6)
    G = 0.09; L = 0.80; z0 = G + 0.035
    w = lambda t: 0.03 * (1 - 0.25 * t) * (1 - max(0, (t - 0.8) / 0.2) ** 1.0) + 0.004 * math.sin(t * 31) * (1 - t)
    blade('blade', ice, L, z0, w, w, lambda t: 0.009 * (1 - 0.65 * t), n=40)
    # kenar kristalleri
    rng = random.Random(5)
    for k, t in enumerate([0.08, 0.16, 0.27, 0.36, 0.49, 0.6, 0.71]):
        s = 1 if k % 2 == 0 else -1
        z = z0 + L * t; x = s * w(t)
        ln = 0.035 * (1 - t * 0.6)
        o = gem('shard', frost, (x + s * ln * 0.3, 0, z + ln * 0.1), ln * 0.7, ln * 0.2, 0.005, sides=4, rot=(0, -s * math.radians(55 + rng.uniform(-8, 8)), 0))
    # sarkıt muhafız (ışınsal kristaller)
    for s in (1, -1):
        for a, ln, r in [(10, 0.085, 0.009), (35, 0.06, 0.007), (-20, 0.05, 0.006), (60, 0.04, 0.005)]:
            ang = math.radians(a)
            gem('icicle', frost if a != 10 else icem, (s * 0.012, 0, G + 0.012), ln, 0.012, r, sides=5, rot=(0, -s * (math.pi / 2 - ang), 0))
    revolve('guardcore', icem, [(0, G - 0.006), (0.024, G - 0.006), (0.028, G + 0.012), (0.02, G + 0.03), (0, G + 0.034)], seg=6, smooth=False, scale_xy=(1, 0.75))
    grip('grip', wrap, -G, G, 0.0162, 0.0156, 'spiral', amp=0.0015)
    for z in (-G + 0.045, 0.0, G - 0.045):
        revolve('frostband', icem, [(0.0, z - 0.004), (0.0185, z - 0.004), (0.02, z), (0.0185, z + 0.004), (0, z + 0.004)], seg=6, smooth=False)
    gem('pommel', frost, (0, 0, -G - 0.032), 0.03, 0.03, 0.017, sides=6)

@sword
def kanli_hilal():
    """KANLI HİLAL: hilal biçimli kavisli bordo-siyah namlu, sırtta kancalar, kemik (omur) kabza, kaburga muhafız"""
    base = metal_base((0.22, 0.03, 0.04), (0.09, 0.05, 0.05), 71, brushed=False, edge_px=10)
    emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi); db = ImageDraw.Draw(base)
    veins_on(d, (170, 10, 15), 77, n=2, spread=14); veins_on(db, (40, 0, 4), 77, n=2, spread=14)
    emi = emi.filter(ImageFilter.GaussianBlur(0.9))
    blade_m = mat('KHL_blade', (1, 1, 1), 0.9, 0.34, emit=(0.6, 0.02, 0.04), base_tex=save(base, 'khl_b.jpg'), emit_tex=save(emi, 'khl_e.png'))
    black = M_metal('KHL_black', (0.07, 0.05, 0.05), 0.35); bone = M_leather('KHL_bone', (0.64, 0.57, 0.46), 0.55)
    blood = M_crystal('KHL_gem', (0.6, 0.02, 0.05), (0.5, 0.0, 0.03))
    G = 0.09; L = 0.72; z0 = G + 0.03
    cx = lambda t: 0.13 * math.sin(math.pi * t * 0.95) * (1 - 0.25 * t) - 0.02 * t
    wl = lambda t: 0.015 + 0.036 * math.sin(math.pi * min(t, 1) ** 0.9) * (1 - t) ** 0.3   # dış (dışbükey) kenar geniş
    wr = lambda t: 0.012 * (1 - t) ** 0.8 + 0.004 * (1 - t)
    blade('blade', blade_m, L, z0, lambda t: wl(t) * (1 - t) ** 0.25, wr, lambda t: 0.0065 * (1 - 0.6 * t), cx=cx)
    # sırt kancaları (iç kenar = sağ)
    for t in (0.28, 0.5, 0.7):
        x = cx(t) + wr(t); z = z0 + L * t
        slab('hook', black, [(x - 0.004, z - 0.01), (x + 0.03, z + 0.004), (x + 0.012, z + 0.002), (x - 0.002, z + 0.012)], 0.006, bevel=0.0008)
    # kaburga muhafız
    for s in (1, -1):
        for k, (a, ln) in enumerate([(-15, 0.07), (15, 0.06), (45, 0.045)]):
            ang = math.radians(a)
            pts = [(s * 0.012, 0, G + 0.01), (s * (0.012 + math.cos(ang) * ln * 0.55), 0, G + 0.01 + math.sin(ang) * ln * 0.55 + 0.012),
                   (s * (0.012 + math.cos(ang) * ln), 0, G + 0.01 + math.sin(ang) * ln + 0.022)]
            tube('rib', bone, pts, [0.006, 0.0045, 0.0005], seg=6)
    revolve('guardcore', black, [(0, G - 0.004), (0.022, G - 0.004), (0.025, G + 0.012), (0.018, G + 0.028), (0, G + 0.03)], seg=8, smooth=False, scale_xy=(1, 0.8))
    gem('bloodgem', blood, (0, 0.016, G + 0.012), 0.008, 0.008, 0.007, sides=6, rot=(math.pi / 2, 0, 0)); mirror_y(bpy.data.objects['bloodgem'])
    grip('grip', bone, -G, G, 0.0165, 0.0165, 'bone', amp=0.0017, rows=48)
    # pençe/kemik kabza başı
    sphere('knuckle', bone, (0, 0, -G - 0.012), 0.02, (1, 0.85, 0.7))
    for s in (1, -1):
        tube('claw', bone, [(s * 0.01, 0, -G - 0.02), (s * 0.022, 0, -G - 0.04), (s * 0.016, 0, -G - 0.06)], [0.008, 0.005, 0.0005], seg=6)

@sword
def firtina_muhru():
    """FIRTINA MÜHRÜ: şimşek biçiminde kırıklı gümüş namlu, elektrik mavisi kristaller, yıldırım kollu muhafız"""
    base = metal_base((0.72, 0.74, 0.79), (0.92, 0.93, 0.96), 81)
    emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi); db = ImageDraw.Draw(base)
    rng = np.random.default_rng(8)
    for face in (0, 1):
        x = spine_x(face); pts = []
        for v in np.linspace(0.02, 0.92, 26): pts.append((x + rng.integers(-4, 5), vy(v)))
        d.line(pts, fill=(80, 200, 255), width=2); db.line(pts, fill=(60, 110, 170), width=2)
    emi = emi.filter(ImageFilter.GaussianBlur(0.8))
    blade_m = mat('FM_blade', (1, 1, 1), 1.0, 0.2, emit=(0.35, 0.8, 1), base_tex=save(base, 'fm_b.jpg'), emit_tex=save(emi, 'fm_e.png'))
    silver = M_metal('FM_silver', (0.8, 0.82, 0.86), 0.22); volt = M_crystal('FM_crystal', (0.3, 0.8, 1.0), (0.25, 0.75, 1.0))
    navy = M_leather('FM_grip', (0.08, 0.12, 0.25), 0.6); dark = M_metal('FM_dark', (0.18, 0.2, 0.26), 0.35)
    G = 0.09; L = 0.80; z0 = G + 0.035
    kinks = [(0.0, 0.0), (0.3, 0.032), (0.36, -0.012), (0.64, 0.03), (0.70, -0.008), (1.0, 0.012)]
    def cx(t):
        for (t0, x0), (t1, x1) in zip(kinks, kinks[1:]):
            if t <= t1: return x0 + (x1 - x0) * (t - t0) / (t1 - t0)
        return kinks[-1][1]
    w = lambda t: 0.024 * (1 - 0.3 * t) * (1 - max(0, (t - 0.86) / 0.14) ** 1.2)
    blade('blade', blade_m, L, z0, w, w, lambda t: 0.0058 * (1 - 0.5 * t), cx=cx, extra_t=[k[0] for k in kinks])
    # yıldırım kolları (muhafız)
    for s in (1, -1):
        bolt = [(s * 0.01, G), (s * 0.055, G + 0.004), (s * 0.045, G + 0.016), (s * 0.095, G + 0.03), (s * 0.072, G + 0.032), (s * 0.11, G + 0.06),
                (s * 0.06, G + 0.036), (s * 0.072, G + 0.032), (s * 0.03, G + 0.024), (s * 0.01, G + 0.026)]
        if s < 0: bolt = list(reversed(bolt))
        slab('bolt', silver, bolt, 0.012)
    revolve('seal', dark, [(0, G - 0.006), (0.024, G - 0.006), (0.026, G + 0.016), (0.0, G + 0.03)], seg=8, smooth=False, scale_xy=(1, 0.85))
    gem('sealgem', volt, (0, 0.02, G + 0.01), 0.012, 0.012, 0.011, sides=6, rot=(math.pi / 2, 0, 0)); mirror_y(bpy.data.objects['sealgem'])
    grip('grip', navy, -G, G, 0.016, 0.0155, 'spiral', amp=0.0015)
    for z in (-G + 0.03, -0.01, G - 0.035):
        revolve('band', silver, [(0.0, z - 0.003), (0.0183, z - 0.003), (0.0186, z + 0.003), (0, z + 0.003)], seg=12)
    revolve('cap', silver, [(0.0, -G - 0.006), (0.018, -G - 0.006), (0.019, -G + 0.004), (0, -G + 0.004)], seg=10)
    gem('spike', volt, (0, 0, -G - 0.03), 0.006, 0.03, 0.011, sides=5)

@sword
def kral_mezari():
    """KRAL MEZARI: eskitilmiş koyu demir, çentikli kenarlar, kazınmış bronz semboller, sarkık muhafız, kafatası kabza başı"""
    base = metal_base((0.20, 0.19, 0.18), (0.38, 0.36, 0.33), 91, brushed=False, edge_px=10, rust=0.35)
    db = ImageDraw.Draw(base); emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi)
    runes_on(db, 0.05, 0.75, 0.085, 8, (120, 85, 40), 93, width=2)
    runes_on(d, 0.05, 0.75, 0.085, 8, (40, 30, 18), 93, width=1)
    blade_m = mat('KM_blade', (1, 1, 1), 0.75, 0.62, emit=(0.35, 0.3, 0.25), base_tex=save(base, 'km_b.jpg'), emit_tex=save(emi, 'km_e.png'))
    bronze = M_metal('KM_bronze', (0.55, 0.38, 0.18), 0.5); iron = M_metal('KM_iron', (0.17, 0.16, 0.15), 0.6, 0.85)
    bone = M_leather('KM_bone', (0.70, 0.64, 0.52), 0.6); leather = M_leather('KM_grip', (0.18, 0.12, 0.08), 0.85)
    void = mat('KM_void', (0.0, 0.0, 0.0), 0.0, 0.9, emit=(0.04, 0.16, 0.10), emit_strength=1.0)
    G = 0.09; L = 0.78; z0 = G + 0.04
    rng = random.Random(9)
    notch = {k: rng.uniform(0.0, 0.006) for k in range(60)}
    def wf(side):
        def f(t):
            k = int(t * 56); c = notch[(k + side * 7) % 60] if 0.1 < t < 0.85 and k % 5 == side else 0
            return 0.036 * (1 - 0.1 * t) * (1 - max(0, (t - 0.86) / 0.14) ** 1.1) - c
        return f
    blade('blade', blade_m, L, z0, wf(0), wf(2), lambda t: 0.0068 * (1 - 0.5 * t))
    for z in (z0 + 0.004, z0 + 0.03):
        slab('ring', bronze, [(-0.041, z - 0.006), (0.041, z - 0.006), (0.04, z + 0.006), (-0.04, z + 0.006)], 0.018)
    for s in (1, -1):
        tube('droop', iron, [(0, 0, G + 0.012), (s * 0.04, 0, G + 0.014), (s * 0.075, 0, G + 0.0), (s * 0.09, 0, G - 0.025)], [0.011, 0.009, 0.0075, 0.006], seg=8, scale_y=1.1)
        sphere('knot', bronze, (s * 0.091, 0, G - 0.03), 0.01, (1, 1, 1.2), seg=8, rings=5)
        sphere('stud', bronze, (s * 0.045, 0.0, G + 0.014), 0.008, (1, 1.45, 1), seg=8, rings=5)
    revolve('guardcore', bronze, [(0, G - 0.004), (0.028, G - 0.004), (0.03, G + 0.014), (0.0, G + 0.03)], seg=8, smooth=False, scale_xy=(1, 0.8))
    grip('grip', leather, -G, G, 0.0172, 0.0165, 'rings', amp=0.0017)
    # kafatası kabza başı
    zc = -G - 0.034
    sphere('cranium', bone, (0, 0, zc), 0.026, (0.85, 0.95, 1.0), seg=12, rings=8)
    sphere('jaw', bone, (0, 0.006, zc - 0.022), 0.015, (0.8, 0.9, 0.55), seg=10, rings=5)
    for s in (1, -1):
        sphere('socket', void, (s * 0.009, 0.021, zc - 0.004), 0.0062, (1, 0.6, 1), seg=8, rings=5)
    sphere('nose', void, (0, 0.024, zc - 0.014), 0.003, (1, 0.6, 1.4), seg=6, rings=4)
    for o in [o for o in bpy.data.objects if o.name.startswith(('socket', 'nose'))]: mirror_y(o)
    revolve('neck', bronze, [(0, -G - 0.01), (0.017, -G - 0.01), (0.019, -G + 0.004), (0, -G + 0.004)], seg=10)

@sword
def olumsuzun_sonu():
    """ÖLÜMSÜZÜN SONU: siyah sırtlı gümüş namlu, altın rünler, kademeli kanatlı muhafız, altın merkez kristali + hale, kafesli altın kabza taşı"""
    base = metal_base((0.05, 0.05, 0.06), (0.9, 0.91, 0.94), 101, edge_px=22)
    db = ImageDraw.Draw(base); emi = Image.new('RGB', (TW, TH)); d = ImageDraw.Draw(emi)
    runes_on(d, 0.05, 0.78, 0.07, 6, (255, 200, 80), 103); runes_on(db, 0.05, 0.78, 0.07, 6, (200, 150, 60), 103)
    emi = emi.filter(ImageFilter.GaussianBlur(0.6))
    blade_m = mat('OS_blade', (1, 1, 1), 1.0, 0.2, emit=(1, 0.75, 0.3), base_tex=save(base, 'os_b.jpg'), emit_tex=save(emi, 'os_e.png'))
    silver = M_metal('OS_silver', (0.86, 0.87, 0.9), 0.18); black = M_metal('OS_black', (0.06, 0.06, 0.07), 0.28)
    goldm = M_metal('OS_gold', (1.0, 0.78, 0.36), 0.22); sun = M_crystal('OS_crystal', (1.0, 0.8, 0.3), (1.0, 0.72, 0.2))
    leather = M_leather('OS_grip', (0.06, 0.05, 0.05), 0.6)
    G = 0.095; L = 0.86; z0 = G + 0.05
    def w(t):
        lug = 0.012 if 0.06 < t < 0.1 else 0.0   # ricasso çıkıntısı
        return (0.022 if t < 0.06 else 0.033 * (1 - 0.25 * t)) * (1 - max(0, (t - 0.85) / 0.15) ** 1.15) + lug
    blade('blade', blade_m, L, z0, w, w, lambda t: 0.0062 * (1 - 0.55 * t), extra_t=[0.059, 0.061, 0.099, 0.101])
    # kademeli kanatlar: siyah alt kanat + gümüş üst kanat (yukarı) + altın uçlar (aşağı)
    for s in (1, -1):
        up = [(s * 0.02, G + 0.01), (s * 0.07, G + 0.025), (s * 0.12, G + 0.07), (s * 0.13, G + 0.11), (s * 0.1, G + 0.072), (s * 0.06, G + 0.05), (s * 0.02, G + 0.045)]
        lo = [(s * 0.02, G - 0.01), (s * 0.08, G - 0.006), (s * 0.11, G - 0.03), (s * 0.075, G - 0.018), (s * 0.02, G + 0.012)]
        if s < 0: up = list(reversed(up)); lo = list(reversed(lo))
        slab('wingU', silver, up, 0.014)
        slab('wingL', black, lo, 0.018)
        tube('tip', goldm, [(s * 0.128, 0, G + 0.1), (s * 0.135, 0, G + 0.125)], [0.0045, 0.0003], seg=6)
    revolve('heart', black, [(0, G - 0.014), (0.03, G - 0.014), (0.036, G + 0.012), (0.03, G + 0.038), (0, G + 0.044)], seg=10, smooth=False, scale_xy=(1, 0.45))
    gem('sun', sun, (0, 0.0, G + 0.014), 0.032, 0.032, 0.021, sides=8, girdle=0.12, rot=(math.pi / 2, 0, 0))
    halo = tube('halo', goldm, [(0.03 * math.cos(a), 0.0, G + 0.014 + 0.03 * math.sin(a)) for a in np.linspace(0, TAU, 25)], [0.0028] * 25, seg=6)
    o2 = tube('halo2', goldm, [(0.03 * math.cos(a), 0.0, G + 0.014 + 0.03 * math.sin(a)) for a in np.linspace(0, TAU, 25)], [0.0028] * 25, seg=6)
    halo.location.y = 0.024; o2.location.y = -0.024
    grip('grip', leather, -G, G, 0.0165, 0.016, 'cross', amp=0.0016)
    for z in (-G + 0.004, -0.004, G - 0.006):
        revolve('band', silver if z else goldm, [(0.0, z - 0.004), (0.0188, z - 0.004), (0.0192, z + 0.004), (0, z + 0.004)], seg=12)
    # kafesli kabza başı
    revolve('pbase', black, [(0, -G - 0.012), (0.02, -G - 0.012), (0.021, -G + 0.002), (0, -G + 0.002)], seg=10)
    gem('pgem', sun, (0, 0, -G - 0.036), 0.018, 0.02, 0.012, sides=8)
    for k in range(4):
        a = TAU * k / 4
        tube('cage', silver, [(math.cos(a) * 0.016, math.sin(a) * 0.016, -G - 0.012), (math.cos(a) * 0.018, math.sin(a) * 0.018, -G - 0.035), (0, 0, -G - 0.062)], [0.0028, 0.0026, 0.0008], seg=5)

# ------------------------------------------------------------------ dışa aktarma + ikon + önizleme
def export(name):
    o = join_all(name)
    bm = bmesh.new(); bm.from_mesh(o.data); tris = sum(len(f.verts) - 2 for f in bm.faces); bm.free()
    for m in o.data.materials:
        m.use_backface_culling = False
    xs = [v.co for v in o.data.vertices]
    bb = (min(v.z for v in xs), max(v.z for v in xs), max(abs(v.x) for v in xs))
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True, export_normals=True)
    return o, tris, bb, os.path.getsize(path)

def light_rig():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.device = 'CPU'
    try: sc.cycles.use_denoising = True
    except Exception: pass
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], ramp.inputs[0])
    ramp.color_ramp.elements[0].color = (0.05, 0.045, 0.04, 1); ramp.color_ramp.elements[1].color = (0.9, 0.85, 0.8, 1)
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.5
    for nm, loc, en, col in [('key', (1.5, -2.0, 2.5), 900, (1, 0.95, 0.88)), ('rim', (-2.0, 1.5, 1.0), 650, (0.8, 0.85, 1.0)), ('fill', (-1.5, -2.5, -0.5), 260, (1, 1, 1))]:
        L = bpy.data.lights.new(nm, 'AREA'); L.energy = en; L.size = 1.5; L.color = col
        lo = bpy.data.objects.new(nm, L); lo.location = loc; sc.collection.objects.link(lo)
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

def render_views(o, name):
    light_rig(); sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    # ikon: çapraz (uç sol-alt, kabza sağ-üst) — envanterdeki diğer ikonlarla aynı yerleşim
    piv = bpy.data.objects.new('piv', None); sc.collection.objects.link(piv)
    o.parent = piv; piv.rotation_euler = (0, math.radians(-145), 0)
    bpy.context.view_layer.update()
    ws = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = Vector((min(v.x for v in ws), 0, min(v.z for v in ws))); mx = Vector((max(v.x for v in ws), 0, max(v.z for v in ws)))
    c = (mn + mx) / 2; ext = mx - mn
    W, H = 224, 294
    cam.location = (c.x, -3, c.z); cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.ortho_scale = max(ext.x / (W / H), ext.z) * 1.06
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 100
    p = os.path.join(TEXDIR, name + '_icon.png'); sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = Image.open(p).convert('RGBA').resize((112, 147), Image.LANCZOS)
    im.save(os.path.join(OUT, name + '_icon.webp'), quality=90, method=6)
    # önizleme: dik, 3/4 açı
    piv.rotation_euler = (0, 0, math.radians(25)); bpy.context.view_layer.update()
    cam.location = (0, -3, 0.33); cam.data.ortho_scale = 1.25
    sc.render.resolution_x, sc.render.resolution_y = 360, 900
    sc.render.film_transparent = False
    sc.render.filepath = os.path.join(OUT, name + '_preview.png'); bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    report = []
    for name, fn in SPECS.items():
        if ONLY and name not in ONLY: continue
        reset_scene(); fn()
        o, tris, bb, size = export(name)
        render_views(o, name)
        report.append((name, tris, round(bb[0], 3), round(bb[1], 3), round(2 * bb[2], 3), size))
        print('SWORD', name, 'tris', tris, 'z', round(bb[0], 3), round(bb[1], 3), 'width', round(2 * bb[2], 3), 'bytes', size, flush=True)
    import json
    json.dump(report, open(os.path.join(OUT, '_report.json'), 'w'), ensure_ascii=False, indent=1)
