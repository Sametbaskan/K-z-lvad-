# Efsanevi tek elli kılıç paketi (10 adet)

`gen_swords.py` 10 kılıcın tamamını Blender (bpy 5.2) ile **prosedürel 3D geometri** olarak üretir: namlu (8 köşeli mercek kesitli loft, pah/sırt),
muhafız, kabza (deri sargı / örgü / pul / kemik yüzey), kabza başı ve kristaller ayrı geometrilerdir. Namlu dokuları (128×512, rün/damar/telkari)
PIL ile üretilir. Çıktı GLB + 112×147 webp envanter ikonu (Cycles render, şeffaf zemin, çapraz yerleşim).

```
pip install bpy==5.2.* pillow numpy
python3 -I gen_swords.py -- out            # hepsi
python3 -I gen_swords.py -- out ruhkesen   # tek kılıç
base64 -w0 out/<id>.glb > ../../www/models/weapons/<id>.glb.b64.txt ; cp out/<id>_icon.webp ../../www/img/weapons/<id>.webp
```

Eksen sözleşmesi (oyundaki silah soketiyle aynı): kabza ortası orijinde, namlu +Y, genişlik X, kalınlık Z, birim metre.
Oyunda istatistik / fiyat / seviye / efekt ayarları `www/index.html` içindeki `LEGEND_WEAPONS` tablosundan yapılır.

| id | Ad | Üçgen | Boy (m) |
|---|---|---|---|
| kizil_hukum | Kızıl Hüküm | 3550 | 1.09 |
| geceyarigi | Geceyarığı | 2146 | 1.11 |
| ejder_disi | Ejder Dişi | 1814 | 1.02 |
| ruhkesen | Ruhkesen | 2234 | 1.09 |
| kara_safak | Kara Şafak | 2596 | 1.06 |
| buzul_hukmu | Buzul Hükmü | 2034 | 1.08 |
| kanli_hilal | Kanlı Hilal | 2926 | 0.99 |
| firtina_muhru | Fırtına Mührü | 2308 | 1.08 |
| kral_mezari | Kral Mezarı | 2814 | 1.06 |
| olumsuzun_sonu | Ölümsüzün Sonu | 3074 | 1.16 |
