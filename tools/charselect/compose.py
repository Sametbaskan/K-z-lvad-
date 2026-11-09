# Karakter seçim ekranı birleştirme: arka plan (Blender) + karakter (oyunun kendi modeli, şeffaf) + gölge, ışık, renk düzeni + Metin2 tarzı panel
#   python3 compose.py <bg.png> <karakter.png> <font_klasörü> <çıkış_klasörü>
# Çıktılar: karakter_secim.png (panelli), karakter_secim_temiz.png (panelsiz), karakter_secim_arkaplan.png (karaktersiz)
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont

BG, CH, FD, OUT = sys.argv[1:5]; os.makedirs(OUT, exist_ok=True)
bg = Image.open(BG).convert('RGBA'); ch = Image.open(CH).convert('RGBA'); W, H = bg.size

def grade(im):
    a = np.asarray(im.convert('RGB'), float) / 255
    a = a ** 1.08                                                     # biraz daha koyu orta tonlar
    a[..., 2] = np.clip(a[..., 2] * 1.06 + .01, 0, 1); a[..., 0] *= .97   # soğuk gece tonu
    yy, xx = np.mgrid[0:H, 0:W]; d = np.hypot((xx - W * .5) / (W * .62), (yy - H * .52) / (H * .62))
    a *= np.clip(1.12 - .42 * d ** 2.2, .35, 1)[..., None]           # vinyet
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
def bloom(im, thr=.72, k=26, s=.55):
    a = np.asarray(im, float) / 255; m = np.clip((a.max(2) - thr) / (1 - thr), 0, 1)[..., None] * a
    b = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(k)), float) / 255
    return Image.fromarray((np.clip(a + b * s, 0, 1) * 255).astype(np.uint8))

# karaktersiz arka plan
base = bloom(grade(bg)); base.save(os.path.join(OUT, 'karakter_secim_arkaplan.png'))
# temas gölgesi (ayakların altı) + rün halkasından hafif sıcak yansıma
al = np.asarray(ch)[..., 3]; ys, xs = np.nonzero(al > 20); fy = ys.max(); fx = (xs[ys > fy - 40].min() + xs[ys > fy - 40].max()) / 2
sh = Image.new('L', (W, H), 0); d = ImageDraw.Draw(sh); rw = (xs[ys > fy - 40].max() - xs[ys > fy - 40].min()) * .75 + 40
d.ellipse((fx - rw, fy - rw * .16, fx + rw, fy + rw * .16), fill=170); sh = sh.filter(ImageFilter.GaussianBlur(14))
comp = bg.copy(); dark = Image.new('RGBA', (W, H), (5, 4, 8, 255)); comp = Image.composite(dark, comp, sh)
cha = np.asarray(ch).astype(float); cha[..., :3] = np.clip(cha[..., :3] * 1.2 + 4, 0, 255); comp.alpha_composite(Image.fromarray(cha.astype(np.uint8)))
# karakterin alt kısmına rün halkasının turuncu ışığı
glow = Image.new('RGBA', (W, H), (255, 120, 40, 0)); g = np.zeros((H, W), float)
yy, xx = np.mgrid[0:H, 0:W]; g = np.clip(1 - np.hypot((xx - fx) / (rw * 1.3), (yy - fy) / (H * .2)), 0, 1) ** 2 * .35
gl = np.asarray(glow).copy(); gl[..., 3] = (g * (al > 20) * 255).astype(np.uint8); comp.alpha_composite(Image.fromarray(gl))
clean = bloom(grade(comp)); clean.save(os.path.join(OUT, 'karakter_secim_temiz.png'))

# ---------------- panel (Türkçe), oyunun yazı tipi Alegreya SC (latin + latin-ext birleşik)
F = {w: [os.path.join(FD, f'alegreya-sc-{sub}-{w}-normal.woff') for sub in ('latin', 'latin-ext')] for w in (400, 700, 800)}
CM = {p: set(TTFont(p).getBestCmap().keys()) for ws in F.values() for p in ws}
fonts = {}
def font(w, sz):
    k = (w, sz)
    if k not in fonts: fonts[k] = [(ImageFont.truetype(p, sz), CM[p]) for p in F[w]]
    return fonts[k]
def text(dr, xy, s, w, sz, fill, anchor='l', shadow=True):
    fs = font(w, sz); parts = []
    for c in s:
        f = next((f for f, cm in fs if ord(c) in cm), fs[0][0]); parts.append((c, f))
    tw = sum(f.getlength(c) for c, f in parts); x, y = xy
    if anchor == 'c': x -= tw / 2
    elif anchor == 'r': x -= tw
    for c, f in parts:
        if shadow: dr.text((x + 1.5, y + 2), c, font=f, fill=(0, 0, 0, 200))
        dr.text((x, y), c, font=f, fill=fill); x += f.getlength(c)
    return tw

ui = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ui)
GOLD = (196, 152, 82, 255); GOLD2 = (120, 86, 44, 255); DARK = (14, 11, 10, 232)
def frame(x0, y0, x1, y1, r=10, fill=DARK, w=3, inner=True):
    d.rounded_rectangle((x0, y0, x1, y1), r, fill=fill, outline=(0, 0, 0, 255), width=w + 4)
    d.rounded_rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), r, outline=GOLD, width=w)
    if inner: d.rounded_rectangle((x0 + 8, y0 + 8, x1 - 8, y1 - 8), max(2, r - 6), outline=GOLD2, width=1)
def stud(x, y, s=7):
    d.polygon([(x, y - s), (x + s, y), (x, y + s), (x - s, y)], fill=GOLD, outline=(40, 25, 10, 255))
    d.polygon([(x, y - s * .45), (x + s * .45, y), (x, y + s * .45), (x - s * .45, y)], fill=(255, 225, 160, 255))
def spike(x, y, dx, dy, L=46, wd=11):
    nx, ny = -dy, dx
    d.polygon([(x + nx * wd, y + ny * wd), (x + dx * L, y + dy * L), (x - nx * wd, y - ny * wd)], fill=GOLD, outline=(40, 25, 10, 255))
    d.line([(x, y), (x + dx * L * .8, y + dy * L * .8)], fill=(255, 220, 150, 255), width=2)

# ana panel
PX0, PY0, PX1, PY1 = 34, 90, 400, 826
frame(PX0, PY0, PX1, PY1, 14, (12, 9, 8, 225), 4)
for (x, y, dx, dy) in [(PX0 + 6, PY0 + 6, -.7, -.7), (PX1 - 6, PY0 + 6, .7, -.7), (PX0 + 6, PY1 - 6, -.7, .7), (PX1 - 6, PY1 - 6, .7, .7)]:
    spike(x, y, dx, dy); spike(x, y, dx * .3 + (.6 if dx > 0 else -.6) * 0, dy, 30, 8); spike(x, y, dx, 0, 30, 8)
for i in range(6):
    y = PY0 + 90 + i * (PY1 - PY0 - 180) / 5; stud(PX0 + 2, y); stud(PX1 - 2, y)
text(d, ((PX0 + PX1) / 2, PY0 + 20), 'KARAKTER SEÇİMİ', 800, 30, (238, 206, 140, 255), 'c')
d.line([(PX0 + 40, PY0 + 64), (PX1 - 40, PY0 + 64)], fill=GOLD2, width=2); stud((PX0 + PX1) / 2, PY0 + 64, 6)
CHARS = [('KrallorD', '99', '—', 'Savaşçı'), ('Yiğit', '47', 'Kızıl Kurtlar', 'Savaşçı'), ('Ayşenur', '12', '—', 'Büyücü'), None]
sy0 = PY0 + 84; SH = 124
for i, c in enumerate(CHARS):
    x0, y0, x1, y1 = PX0 + 26, sy0 + i * (SH + 10), PX1 - 26, sy0 + i * (SH + 10) + SH
    sel = i == 0
    frame(x0, y0, x1, y1, 8, (34, 22, 16, 235) if sel else (20, 15, 13, 230), 2)
    if sel:   # seçili: sıcak iç ışıma
        gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl); gd.rounded_rectangle((x0 + 3, y0 + 3, x1 - 3, y1 - 3), 8, outline=(255, 170, 70, 210), width=5)
        ui.alpha_composite(gl.filter(ImageFilter.GaussianBlur(5))); d = ImageDraw.Draw(ui)
    if c is None:
        text(d, ((x0 + x1) / 2, y0 + SH / 2 - 18), '+ Yeni Karakter', 700, 26, (170, 150, 120, 255), 'c'); continue
    lab = ('Ad:', 'Seviye:', 'Lonca:', 'Sınıf:')
    for k, (l, v) in enumerate(zip(lab, c)):
        yy = y0 + 12 + k * 26
        text(d, (x0 + 20, yy), l, 700, 21, (176, 150, 112, 255))
        text(d, (x0 + 118, yy), v, 700 if k == 0 else 400, 23 if k == 0 else 21, (255, 236, 196, 255) if k == 0 else (232, 222, 205, 255))
def button(cx, cy, label, wdt=150, hgt=46, hot=False):
    x0, y0 = cx - wdt / 2, cy - hgt / 2
    d.rounded_rectangle((x0 - 3, y0 - 3, x0 + wdt + 3, y0 + hgt + 3), 10, fill=(0, 0, 0, 255))
    for k in range(hgt):   # dikey gradyan
        t = k / hgt; col = (int(120 - 60 * t), int(40 - 20 * t), int(26 - 12 * t), 255) if hot else (int(70 - 35 * t), int(46 - 24 * t), int(34 - 18 * t), 255)
        d.line([(x0 + 4, y0 + k), (x0 + wdt - 4, y0 + k)], fill=col)
    d.rounded_rectangle((x0, y0, x0 + wdt, y0 + hgt), 9, outline=GOLD, width=2)
    for sx in (x0 - 8, x0 + wdt + 8): stud(sx, cy, 6)
    text(d, (cx, cy - 15), label, 800, 24, (255, 232, 180, 255), 'c')
button(PX0 + 105, PY1 - 46, 'SİL'); button(PX1 - 105, PY1 - 46, 'GİRİŞ', hot=True)
button(W - 130, H - 60, 'GERİ', 160)
# seçili karakterin adı (karakterin üstünde, oyundaki isim plakası gibi)
cx = fx; ty = ys.min() - 44
text(d, (cx, ty), 'Sv. 99  ·  KrallorD', 700, 26, (255, 226, 150, 255), 'c')
full = clean.convert('RGBA'); full.alpha_composite(ui); full.convert('RGB').save(os.path.join(OUT, 'karakter_secim.png'))
print('tamam', W, H, 'ayak', int(fx), int(fy))
