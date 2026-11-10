# Animasyon kütüphanesi (oyuna otomatik girmez)

Bu klasör APK'ya dahil edilmez (`www/` dışında). İleride lazım olan klipler buradan seçilip
oyunun Mixamo iskeletine aktarılır (`tools/extract_clip.py` + kemik eşleme) ve `www/models/` altına eklenir.

## kinemiq/ — KinemIQ Free Animation Pack (CC0 1.0)
- 35 klip (FBX) + `KinemIQ_Mannequin.fbx` (iskelet + manken). 30 FPS.
- İskelet: Quaternius Universal (66 kemik, `pelvis`...). Oyundaki Mixamo iskeletinden FARKLI; kullanmadan önce kemik eşleme/yeniden hedefleme gerekir.
- Lisans: CC0 — ticari kullanım serbest, atıf gerekmez (Quaternius ve KinemIQ'e teşekkür önerilir). Ayrıntı: `kinemiq/README.txt`.
- Oyunda henüz olmayanlar: Block_with_the_sword, Dodge_roll, Hit_knockback, Hit_to_the_chest/head, Idle_* (NPC), Walk_zombie, Strike_zombie_scratch, Jump_*, Move_climb_up_1_m.
