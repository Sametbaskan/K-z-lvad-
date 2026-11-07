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

## Saçsız (yamalı) sürüm
Meshy modelinde saç sırta/omuzlara kaynaşık olduğu için saç ve yaka bölgesi kesilir; açıkta kalan yerler
`gen_extras.py` ile üretilen ek parçalarla örtülür (Meshy zırhının dış yüzeyine göre konumlanır):
- `boyunluk` — boyundan omuz hattına açılan yaka (zırh eşyasının parçası)
- `pelerin` — sırt plakasının dışında, diz hizasına inen yırtık kızıl pelerin (zırh eşyasının parçası)
- `migfer` — taç dikenli kapalı miğfer, ayrı eşya (Kara Şövalye Miğferi, kask slotu)
```
python3 -I gen_extras.py -- ../../www/models/hero.json extras out     # out = fit_meshy_armor.py çıktısı
python3 -I render_glb_icon.py -- extras/migfer.glb ../../www/img/armor/kara_sovalye_migfer.webp
```

## Güneş Şövalyesi (Sv.75) — iskeletsiz heykel modelinden
Kaynak: "Dark Fantasy Sun Knight Warrior - With PBR Textures", FERUL (CGTrader, ücretsiz). Tek parça, iskeletsiz, ~790 bin üçgen, 2048 PBR dokular.
`fit_static_armor.py`:
- Model düz önüne baktırılır (gövde 19.7° dönük), cm'ye çevrilir; sağ eldeki kılıcın bıçağı ve muhafızı eksen boyunca kesilir (kabza yumrukta kalır).
- ~36 bin üçgene sadeleştirilir; eklemler (JOINTS) kesitlerden elle ölçüldü.
- Ağırlıklar bölgelere göre (baş, sol/sağ kol, gövde, pelerin, sol/sağ bacak); yumuşatma yalnız anatomik olarak bağlı bölgeler arasında yapılır,
  el-pelerin gibi değen yerlerde köşeler ikiye bölünür (ağırlık karışıp uzun şeritler oluşmasın). Küçük bölge adacıkları komşu bölgeye katılır.
- Savaşçı iskeleti zincir boyunca heykelin duruşuna poz verilir (burulma ebeveynden devralınır) ve her kemik için özel bağlama matrisi
  Inv_i = H_i^-1 · M_i^-1 yazılır: zırh kendi duruşunda kalır, oyunda tek karışımla bükülür (oyunda `ARMOR_SETS[set].ownBind`).
- Parçalar: govde, bacak, pelerin (zırh), bas + hale (maske; hale hafif altın nabızla parlar), botlar. GLB'ler elle yazılır (doku gömülmez).
```
python3 -I fit_static_armor.py -- SunKnightWarrior.fbx ../../www/models/hero.json PBR_Textures.jpeg out 36000
for f in out/*.glb; do base64 -w0 $f > ../../www/models/armor/gunes_sovalyesi/$(basename $f .glb).glb.b64.txt; done; cp out/tex/*.jpg ../../www/models/armor/gunes_sovalyesi/tex/
python3 -I render_statue_icons.py -- out/_cut.blend PBR_Textures.jpeg ikon/      # zırh + maske ikonları
python3 -I render_glb_icon.py -- out/botlar.glb ikon/gunes_bot.webp out/tex/base.jpg
```

### v2 (tek parça + rüzgâr)
- Zırh tek GLB (`tum.glb`): maske, hale, gövde, pelerin ve çizmeler tek eşya (Güneş Şövalyesi Zırhı, Sv.75).
- Kumaş ayrımı doku renginden (kızıl kumaş r/g > 2); çizmeler ve bacağa yapışık kayışlar renge bakılmadan bacağa, yumruktaki kabza sargısı ele bağlanır.
- Kumaş leğene katı bağlıdır; köşe özniteliği `_cloth` = [sarkma, ön/arka]. Oyunda `clothMaterial()` köşe gölgelendiricisinde rüzgâr dalgası,
  koşuda arkaya savrulma ve bacak itme (ön etek bacağın önünde, arka pelerin arkasında) uygular; `_glow` hale köşelerini parlatır.

### v3 (pelerin: yırtılma, zemin ve at)
- Kaynak: kumaş köşeleri leğene katı bağlıydı, yalnız gölgelendiricide hesaplanan itmeyle (rüzgâr, bacak itme) oynatılıyordu; komşu köşeler
  farklı miktarlarda itilince üçgenler gerilip "yırtık" gibi açılıyordu; zemin ve at hiç hesaba katılmıyordu.
- Yeni: GLB `extras.cloth` = 24x14 kumaş ızgarası (sütun = leğen çevresinde açı, satır = sarkma) + bacak zırhı yarıçapları; köşede `_cloth` = [sütun, satır, serbestlik].
  Oyunda ızgara dünya uzayında Verlet ile çözülür (yerçekimi, atalet, hafif rüzgâr, uzama sınırı, zemin, binicinin bacakları/çizmeleri,
  atın gövde dilimleri ve uzuv kapsülleri); köşeler ızgara ofsetini çift doğrusal alır (komşular hep birlikte hareket eder → kopma yok).
