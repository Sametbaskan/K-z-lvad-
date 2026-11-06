# VALKOR — Hesap sistemi kurulumu

Sistem **gerçek Firebase Authentication + Firestore** kullanır. Proje bilgileri girilmeden giriş ekranı "Hesap sistemi kapalı" der ve oyuna girilemez (sahte/demo giriş yoktur).

## 1. Firebase projesi (bir kez, ücretsiz Spark planı yeter)
1. https://console.firebase.google.com → **Proje ekle**.
2. **Build → Authentication → Başla → Sign-in method → E-posta/Parola → Etkinleştir.**
3. Authentication → **Settings → User actions**: "Email enumeration protection" açık kalsın; "One account per email address" açık olmalı (varsayılan).
4. **Build → Firestore Database → Veritabanı oluştur** (production mode).
5. Firestore → **Rules** sekmesine `firestore.rules` dosyasının içeriğini yapıştırıp **Yayınla**.
6. Proje ayarları (⚙) → **Uygulamalarınız → Web (</>)** → uygulamayı kaydet → çıkan `firebaseConfig` değerlerini `www/auth/firebase-config.js` içine yaz.
7. Authentication → **Settings → Authorized domains**: Android (Capacitor) uygulaması `localhost` kullanır; varsayılan olarak ekli. Web'e koyarsan alan adını ekle.
8. İsteğe bağlı: Authentication → **Templates**: şifre sıfırlama e-postasının dilini Türkçe yap ve metni düzenle.
9. Değişikliği commit/push et → APK yeniden derlenir.

## Güvenlik notları
- Parolalar Firebase tarafında hash'lenir (scrypt); istemci hiçbir yerde düz parola saklamaz. Oturum belirteci Firebase SDK'sında tutulur; "Beni hatırla" kapalıysa yalnızca oturum süresince geçerlidir.
- Firestore kuralları: herkes yalnızca kendi profilini/karakterlerini okur; kullanıcı/karakter adı rezervasyonları bir kez oluşturulur ve değiştirilemez.
- **Bilinen ödünleşim:** "kullanıcı adı ile giriş" için `usernames/{ad}` belgesi (uid + e-posta) kimlik doğrulamasız `get` ile okunabilir; kullanıcı adını bilen biri o hesabın e-postasını öğrenebilir (listeleme kapalıdır). Bunu kapatmak için Cloud Function (Blaze planı) ile sunucu tarafı arama yapılmalıdır — MMORPG sunucusu geldiğinde yapılacak.
- Karakter ilerlemesi (seviye, envanter) şimdilik cihazda `localStorage` (hesap+karakter başına ayrı anahtar) tutulur; gerçek sunucu gelince `users/{uid}/characters/{id}` altına taşınmalıdır. Karakter oluşturma/silme sunucu tarafı doğrulama gerektirmeyen basit bir modeldir.
- Brute-force koruması Firebase tarafından uygulanır (`too-many-requests`). Ek koruma için Firebase App Check önerilir.

## Dosyalar
`www/auth/auth-service.js` (backend), `auth-ui.js` + `auth.css` (arayüz), `firebase-config.js` (ayar), `firestore.rules`.
Oyun yalnızca `enterGame({uid,username,character})` çağrısıyla başlar; hesap kodu oyun motorundan bağımsızdır.
