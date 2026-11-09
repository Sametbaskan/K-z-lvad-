# Karakter seçim ekranı görseli

1. `scene.py` (Blender/Cycles): ay ışıklı gece ormanı, kuru ağaçlar, toprak patika, fenerli direk, ortada rünlü taş platform.
   Kamera: (0,-7.8,1.7) → (0,0,1.3), dikey görüş 25°; platform üstü z=0.24 (karakterin ayakları).
   `python3 -I scene.py -- bg.png 1600 900 128`
2. Karakter oyunun kendi modeliyle (three.js) aynı kamerayla, şeffaf zeminde çizilir (Güneş Şövalyesi zırhı, eski bekleme duruşu).
3. `compose.py`: temas gölgesi, rün ışığı, renk düzeni, parlama + Metin2 tarzı Türkçe panel (yazı tipi: Alegreya SC, oyundaki ile aynı).
   `python3 compose.py bg.png karakter.png <alegreya-sc woff klasörü> cikis/`
