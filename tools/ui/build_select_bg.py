# VALKOR karakter seçim sahnesi: arka plan + taş zemin (özgün, kodla üretilir; harici sanat varlığı kullanılmaz).
# Kullanım: python3 -I build_select_bg.py <çıkış.webp> [yatay_ufuk=0.50]
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
out = sys.argv[1]; HZ = float(sys.argv[2]) if len(sys.argv) > 2 else 0.50
SKY = len(sys.argv) > 3 and sys.argv[3] == 'sky'   # 'sky': yalnızca gökyüzü (gerçek köy 3B sahnesi arkaya geçer)
W, H = 2520, 1080; hz = int(H * HZ)
rng = np.random.default_rng(7)

def vnoise(w, h, cell, seed):
    r = np.random.default_rng(seed); gw, gh = w // cell + 3, h // cell + 3
    g = r.random((gh, gw)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32) / 255
    return a[:h, :w]
def fbm(w, h, base, octs, seed):
    t = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for i in range(octs):
        t += amp * vnoise(w, h, max(2, base // (2 ** i)), seed + i); tot += amp; amp *= .5
    return t / tot
def lerp(a, b, t): return a + (b - a) * t
def glow(arr, x, y, r, col, k=1.0):
    ys, xs = np.ogrid[:H, :W]
    d2 = ((xs - x) ** 2 + (ys - y) ** 2) / (r * r)
    g = np.exp(-d2 * 2.2)[..., None] * np.array(col, np.float32)[None, None, :] * k
    arr += g

# ---------- gökyüzü: kor rengi ufuk, morumsu üst, bulutlar ----------
yy = np.linspace(0, 1, hz + 40, dtype=np.float32)[:, None]
top = np.array([.05, .06, .13], np.float32); mid = np.array([.34, .14, .17], np.float32); low = np.array([.98, .55, .20], np.float32)
t = np.clip(yy / (hz / (hz + 40)), 0, 1)
sky = np.where(t < .6, lerp(top, mid, (t / .6) ** .9), lerp(mid, low, ((t - .6) / .4) ** 1.6)).astype(np.float32)
sky = np.repeat(sky[:, None, :] if sky.ndim == 2 else sky, W, axis=1) if sky.ndim == 2 else sky
sky = np.broadcast_to(sky, (hz + 40, W, 3)).copy()
cl = fbm(W, hz + 40, 360, 6, 11); cl2 = fbm(W, hz + 40, 140, 5, 31)
cm = np.clip((cl - .46) * 3.2, 0, 1) * np.clip((cl2 + .15), 0, 1)
band = np.linspace(0, 1, hz + 40, dtype=np.float32)[:, None] ** .8
cloud_dark = np.array([.07, .05, .09], np.float32); cloud_lit = np.array([1.0, .62, .30], np.float32)
lit = np.clip(band * 1.4 - .15 + (fbm(W, hz + 40, 90, 4, 51) - .5) * .5, 0, 1)[..., None]
cc = lerp(cloud_dark, cloud_lit, lit)
sky = lerp(sky, cc, (cm * .85)[..., None])
S = np.zeros((H, W, 3), np.float32); S[:hz + 40] = sky
# güneş / alev halesi (sol-orta, ufka yakın)
sx, sy = int(W * .36), int(hz - 40)
glow(S, sx, sy, 460, (1.0, .50, .16), .42); glow(S, sx, sy, 130, (1.0, .85, .5), .45)

# ---------- uzak dağlar + kale silueti ----------
def ridge(base, amp, seed, col, haze):
    n = fbm(W, 8, 220, 5, seed)[0]; n2 = fbm(W, 8, 60, 3, seed + 9)[0]
    prof = base - (n * amp + n2 * amp * .25)
    ys = np.arange(H)[:, None]
    m = (ys >= prof[None, :]) & (ys < hz + 6)
    col = np.array(col, np.float32); tone = lerp(col, np.array([.55, .26, .20], np.float32), haze)
    return m, tone
for base, amp, seed, col, haze in (((hz - 60, 90, 3, (.10, .07, .12), .55),) if SKY else ((hz - 120, 210, 3, (.10, .07, .12), .45), (hz - 55, 140, 5, (.06, .04, .07), .22))):
    m, tone = ridge(base, amp, seed, col, haze); S[m] = tone
if SKY:   # yalnızca gökyüzü: ufkun altını sıcak sisle doldur, kaydet, çık
    yy2 = np.clip((np.arange(H)[:, None] - hz) / max(1, H - hz), 0, 1)[..., None]
    S[hz + 40:] = lerp(S[hz + 38:hz + 39], np.array([.30, .17, .15], np.float32), yy2[hz + 40:])
    S = 1 - np.exp(-S * 1.25); S = np.clip(S + (rng.random((H, W, 1)).astype(np.float32) - .5) * .02, 0, 1)
    Image.fromarray((S * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6)).save(out, quality=84, method=6); print('ok sky', out); sys.exit(0)
# uzak surlar (orta) — kule ve mazgal siluetleri
img = Image.fromarray((np.clip(S, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(img)
def tower(d, cx, base_y, w, h, roof, body, win, seedn):
    r = np.random.default_rng(seedn)
    d.rectangle([cx - w // 2, base_y - h, cx + w // 2, base_y], fill=body)
    for k in range(0, w, max(8, w // 6)):   # mazgal
        d.rectangle([cx - w // 2 + k, base_y - h - w // 10, cx - w // 2 + k + max(5, w // 12), base_y - h], fill=body)
    if roof:
        d.polygon([(cx - w // 2 - w // 8, base_y - h), (cx, base_y - h - int(w * 1.1)), (cx + w // 2 + w // 8, base_y - h)], fill=roof)
    for i in range(int(h // (w * .55))):
        wy = base_y - h + int(w * .4) + i * int(w * .55)
        if r.random() < .75:
            d.rectangle([cx - w // 14, wy, cx + w // 14, wy + int(w * .22)], fill=win)
far = (22, 14, 24)
for cx, wd, ht, rf in ((int(W * .43), 70, 200, True), (int(W * .48), 120, 150, False), (int(W * .53), 56, 230, True), (int(W * .60), 90, 170, True), (int(W * .31), 80, 190, True)):
    tower(d, cx, hz + 4, wd, ht, (16, 10, 18) if rf else None, far, (255, 170, 70), cx)
d.rectangle([int(W * .30), hz - 70, int(W * .66), hz + 4], fill=far)
for x in range(int(W * .30), int(W * .66), 26): d.rectangle([x, hz - 84, x + 14, hz - 70], fill=far)
S = np.asarray(img, dtype=np.float32) / 255
# ufuk sisi
hzmask = np.exp(-((np.arange(H)[:, None] - hz) / 70.0) ** 2)[..., None]
S = lerp(S, np.array([.95, .50, .22], np.float32), hzmask * .28)

# ---------- taş zemin (perspektif, Voronoi levhalar) ----------
fl = H - hz
ys = np.arange(hz, H, dtype=np.float32)[:, None] - hz + 1.0
f = 380.0
z = f * 2.2 / ys                      # derinlik
xs = (np.arange(W, dtype=np.float32)[None, :] - W / 2)
wx = xs * z / f * 1.0; wz = z
U = wx * .9; V = wz * .9
def voronoi(U, V, scale):
    u = U / scale; v = V / scale
    iu = np.floor(u); iv = np.floor(v); fu = u - iu; fv = v - iv
    d1 = np.full(u.shape, 9., np.float32); d2 = d1.copy(); cid = np.zeros(u.shape, np.float32)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx_ = iu + dx; cy_ = iv + dy
            h1 = (np.sin(cx_ * 127.1 + cy_ * 311.7) * 43758.5453) % 1
            h2 = (np.sin(cx_ * 269.5 + cy_ * 183.3) * 43758.5453) % 1
            px = dx + .15 + .7 * h1 - fu; py = dy + .15 + .7 * h2 - fv
            dd = np.sqrt(px * px + py * py * 1.0)
            nd = dd < d1
            d2 = np.where(nd, d1, np.minimum(d2, dd)); cid = np.where(nd, (h1 * 7 + h2 * 3) % 1, cid); d1 = np.minimum(d1, dd)
    return d1, d2, cid
d1, d2, cid = voronoi(U, V, .42)
edge = np.clip((d2 - d1) * 5.5, 0, 1)                     # 0 = harç çizgisi
fade = np.clip(1.0 - (ys / fl) ** .35 * 0 - 0, 0, 1)      # (yer tutucu)
near = np.clip((ys - 14) / 70.0, 0, 1)                      # uzakta detay erir (mip benzeri)
edge = lerp(.78, edge, near[:, :1] * 0 + near)
grain = fbm(W, fl, 6, 3, 77); big = fbm(W, fl, 260, 4, 91)
stone = np.array([.34, .30, .29], np.float32)
tint = (cid[..., None] - .5) * np.array([.10, .07, .05], np.float32)
col = stone[None, None, :] * (.86 + .22 * grain[..., None]) + tint*1.6
col *= (.78 + .38 * big[..., None])
col *= (.22 + .78 * edge[..., None] ** .8)                 # harç koyu
col = col * np.array([1.0, .96, .92], np.float32)
F = col.astype(np.float32)
# ıslak yansıma: ufuka yakın zeminde gökyüzü rengi
fres = np.clip(1 - (ys / fl) ** .55, 0, 1)[..., None]
refl = S[hz - 2, :, :][None].repeat(fl, 0)[:, :, :] * 0 + np.array([.9, .46, .24], np.float32)
F = lerp(F, refl * .75, fres * .55 * (.55 + .45 * grain[..., None]) )
S[hz:] = F * 1.0
# zemin ışık havuzları (meşale) + ortada sahne spotu
for gx, col_, r_, k in ((int(W * .08), (1.0, .55, .2), 520, .55), (int(W * .93), (1.0, .55, .2), 520, .55)):
    glow(S, gx, hz + 170, r_, col_, k * .30)
glow(S, int(W * .60), hz + 250, 640, (1.0, .80, .52), .12)

# ---------- ön plandaki yapılar (sol ve sağ; koyu taş + kırmızı çatı) ----------
img = Image.fromarray((np.clip(S, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(img, 'RGBA')
def hall(d, x0, x1, base_y, h, roofh, left):
    body = (24, 16, 20); wall2 = (36, 22, 26); roof = (84, 24, 26); trim = (150, 70, 40)
    d.rectangle([x0, base_y - h, x1, base_y], fill=body)
    d.rectangle([x0, base_y - h, x1, base_y - h + 18], fill=wall2)
    # çatı (iki kademe, kıvrık)
    for lv, (yo, ex) in enumerate(((0, 70), (-roofh * .75, 25))):
        top_y = base_y - h - roofh * .55 + yo - lv * 40
        d.polygon([(x0 - ex, base_y - h + 6 + yo * .25 + lv * 0), (x0 + (x1 - x0) * .08, top_y), (x1 - (x1 - x0) * .08, top_y), (x1 + ex, base_y - h + 6 + yo * .25)], fill=roof if lv == 0 else (96, 30, 30))
        d.line([(x0 - ex, base_y - h + 6 + yo * .25), (x1 + ex, base_y - h + 6 + yo * .25)], fill=trim, width=5)
    # pencereler (sıcak ışık)
    n = max(3, (x1 - x0) // 120)
    for i in range(n):
        wx_ = x0 + 30 + i * ((x1 - x0 - 60) // max(1, n - 1)) - 22
        for row in range(2):
            wy_ = base_y - h + 70 + row * 150
            d.rectangle([wx_, wy_, wx_ + 44, wy_ + 96], fill=(255, 176, 80, 235 if (i + row) % 3 else 70))
            d.line([(wx_ + 22, wy_), (wx_ + 22, wy_ + 96)], fill=(40, 20, 16, 255), width=3); d.line([(wx_, wy_ + 48), (wx_ + 44, wy_ + 48)], fill=(40, 20, 16, 255), width=3)
    # taş blok çizgileri
    for ry in range(base_y - h + 30, base_y, 44): d.line([(x0, ry), (x1, ry)], fill=(15, 9, 12, 140), width=2)
hall(d, -40, int(W * .20), hz + 130, 400, 150, True)
hall(d, int(W * .83), W + 40, hz + 130, 420, 160, False)
# sütunlar / meşale direkleri
def torch(d, x, base_y, hgt):
    d.rectangle([x - 8, base_y - hgt, x + 8, base_y], fill=(28, 18, 16)); d.rectangle([x - 20, base_y - hgt - 10, x + 20, base_y - hgt + 6], fill=(60, 30, 20))
    d.ellipse([x - 14, base_y - hgt - 44, x + 14, base_y - hgt - 6], fill=(255, 190, 80, 255)); d.ellipse([x - 7, base_y - hgt - 34, x + 7, base_y - hgt - 10], fill=(255, 240, 180, 255))
tpos = [(int(W * .215), hz + 170, 250), (int(W * .80), hz + 170, 250), (int(W * .31), hz + 70, 160), (int(W * .70), hz + 70, 160)]
for x, by, hg in tpos: torch(d, x, by, hg)
S = np.asarray(img, dtype=np.float32) / 255
for x, by, hg in tpos:
    glow(S, x, by - hg - 25, 90 + hg * .35, (1.0, .62, .22), .55)
    glow(S, x, by - hg - 25, 260 + hg, (1.0, .45, .12), .13)
    glow(S, x, by + 10, 170 + hg, (1.0, .5, .18), .12)          # zemin yansıması
# ---------- sis, kıvılcım, vinyet, tane ----------
mist = fbm(W, H, 300, 4, 123)[..., None]
S = lerp(S, np.array([.55, .32, .28], np.float32), np.clip((mist - .45) * .9, 0, 1) * .16 * np.clip(1 - np.abs(np.arange(H)[:, None] - (hz + 30)) / 380.0, 0, 1)[..., None])
for _ in range(220):    # kıvılcımlar
    px = rng.integers(0, W); py = rng.integers(int(H * .15), int(H * .8)); glow(S, px, py, rng.integers(3, 8), (1.0, .65, .25), rng.random() * .9)
vy, vx = np.ogrid[:H, :W]; vg = 1 - (((vx - W * .55) / (W * .75)) ** 2 + ((vy - H * .5) / (H * .8)) ** 2)
S *= np.clip(.35 + .85 * vg, .25, 1)[..., None]
S = 1 - np.exp(-S * 1.25)   # yumuşak ton eşleme
S += (rng.random((H, W, 1)).astype(np.float32) - .5) * .02
S = np.clip(S, 0, 1)
im = Image.fromarray((S * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))
im.save(out, quality=84, method=6)
print('ok', out, im.size)
