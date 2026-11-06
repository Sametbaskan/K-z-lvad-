# Timsah iskeleti + animasyonları

Kaynak: `crocodile-light.fbx` (Blender 5.2 çıktısı, 377k üçgen, iskeletsiz).

Betikler Blender'ın Python modülüyle (`pip install bpy`, 5.2) çalışır:

```
python3 -I rig.py  -- crocodile-light.fbx croc_rig.blend 20000   # sadeleştirme, ağız kesimi, iskelet, ağırlıklar
python3 -I anim.py -- croc_rig.blend <çıkış_klasörü> crocodile    # idle / walk / attack + GLB/FBX dışa aktarma
```

- `fbxfix.py`: kaynak dosyadaki bozuk (kullanılmayan) Tangent dizisini sıfırla değiştirip içe aktarmayı mümkün kılar.
- İskelet: root → hips → spine_01 → spine_02 → chest → neck → head → jaw; hips → tail_01..08;
  chest → upperarm/forearm/hand (.L/.R); hips → thigh/shin/foot (.L/.R). 27 kemik, vertex başına en fazla 4 etki.
- Ağız dudak çizgisinden kesildi; içine ağız içi (damak/dil/yanak zarı) ve dişler eklendi, `jaw` kemiğiyle açılır.
- Animasyonlar 30 fps: `idle` 4.0 sn (döngü), `walk` 1.33 sn (yerinde döngü, IK ile ayak basışı fırınlandı), `attack` 1.2 sn (tek sefer).
- Model +Z'ye (three.js) bakar, ölçü metre (boy ~4.5 m).
