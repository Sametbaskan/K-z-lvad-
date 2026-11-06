# Kara Şövalye zırh seti (Meshy GLB → VALKOR savaşçısı)

Kaynak: kullanıcının Meshy'den indirdiği iskeletli karakter GLB'si (31 bin üçgen, 24 kemik, 2048 dokular).

1. `fit_meshy_armor.py` — zırhı ayıklar ve savaşçıya oturtur:
   - Saç (açık renk), çıplak deri ve baş/boyun bölgesi atılır; savaşçının kendi başı kalır. Küçük kopuk adacıklar temizlenir.
   - Köşeler Meshy kemiklerinden savaşçının Mixamo kemiklerine taşınır (eklem konumu + kemik yönü + boy oranı; gövde tek doğrusal dönüşüm).
   - Ağırlıklar Mixamo adlarına çevrilir, yüzler baskın kemiğe göre 11 parçaya bölünür, her parça ayrı GLB (doku gömülmez).
   - Dokular 1024'e indirilip `tex/` altına bir kez yazılır (renk, metal-pürüzlülük, normal); oyun bunları tüm parçalarda paylaşır.
2. `render_icons.py` — envanter ikonları (112x147 webp).

```
pip install bpy==5.2.* pillow numpy
python3 -I fit_meshy_armor.py -- meshy.glb ../../www/models/hero.json out kara_sovalye
for f in out/*.glb; do base64 -w0 $f > ../../www/models/armor/kara_sovalye/$(basename $f .glb).glb.b64.txt; done
cp out/tex/*.jpg ../../www/models/armor/kara_sovalye/tex/
python3 -I render_icons.py -- out ../../www/img/armor kara_sovalye
```

Oyun: `www/index.html` → `ARMOR_PIECES` (parça adı + takılıyken gizlenen gövde bölgesi), `ARMOR_SETS` (ortak dokular),
`ARMOR_ITEMS` (eşya → parçalar, savunma, fiyat), `syncArmor()` / `armorBody()`.
