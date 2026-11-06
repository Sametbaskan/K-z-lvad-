# Kanlı Kral zırh seti

`gen_armor.py`, savaşçının kendi gövdesinden (`www/models/hero.json`, Mixamo iskeleti, cm, T-poz) yola çıkarak zırh parçalarını
Blender (bpy 5.2) ile **gerçek 3D geometri** olarak üretir:

- Plakalar: ilgili kemik ekseni etrafında gövde kesitinin zarfı alınır, büyütülüp yumuşatılır ve pay (2–8 cm) eklenerek kabuk örülür
  (göğüs sırtı, göğüs çıkıntıları, karın lamaları, kenar şeritleri, perçinler). Böylece zırh gövdeye gömülmez.
- Eldiven ve botlar: gövdenin el/ayak yüzeyi normal boyunca kalınlaştırılır, sonra sadeleştirilir.
- Katı süsler: omuz kubbeleri, dikenler, kafatasları, dirsek/diz kapakları tek bir bağlantı noktasının ağırlığıyla taşınır.
- Ağırlıklar: gövdenin en yakın köşelerinden aktarılır (en fazla 4 kemik) → zırh aynı iskeletle bükülür.
- Dokular PIL ile üretilir: koyu çelik (256, döşenir), kızıl damar emisyonu, kızıl kumaş, rünlü tabar.

```
pip install bpy==5.2.* pillow numpy
python3 -I gen_armor.py -- ../../www/models/hero.json out
for f in out/*.glb; do base64 -w0 $f > ../../www/models/armor/kanli_kral/$(basename $f .glb).glb.b64.txt; done
cp out/kanli_kral_*.webp ../../www/img/armor/
```

Oyun tarafı: `www/index.html` → `ARMOR_ITEMS` (eşya → parça listesi, savunma, fiyat), `syncArmor()` (yükle/bağla/çıkar).

| Parça | Dosya |
|---|---|
| Göğüslük (+ boyunluk, kafatası) | gogusluk |
| Sırt zırhı + pelerin | sirt |
| Sol / sağ omuzluk | omuzluk_l / omuzluk_r |
| Sol / sağ kol koruması (üst kol, dirsek, ön kol) | kol_l / kol_r |
| Eldivenler (+ bilek manşetleri) | eldiven |
| Bel zırhı (kemer, kalçalıklar, tabar) | bel |
| Sol / sağ bacak zırhı (uyluk, diz, baldır) | bacak_l / bacak_r |
| Botlar | botlar |
