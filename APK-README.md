# Kızıl Vadi APK

APK'lar her derlemede **aynı kalıcı release anahtarıyla** imzalanır; telefondaki uygulamanın üzerine silmeden kurulur
(paket adı `com.kizilvadi.game` hiç değişmez, oyun kayıtları korunur).

## Bir kereye mahsus kurulum: GitHub Secrets
Depoda **Settings > Secrets and variables > Actions > New repository secret** ile şu 4 secret'ı ekle:

| Secret | Değer |
|---|---|
| `KEYSTORE_BASE64` | `kizilvadi-release.jks.base64.txt` dosyasının tüm içeriği |
| `KEYSTORE_PASSWORD` | keystore şifresi |
| `KEY_ALIAS` | `kizilvadi` |
| `KEY_PASSWORD` | anahtar şifresi (keystore şifresiyle aynı) |

Anahtarın beklenen sertifika parmak izi `signing/EXPECTED_SHA256.txt` içindedir (gizli değildir).
Derleme, APK'nın sertifikası bununla eşleşmezse **başarısız olur** (yanlış anahtar telefonda güncellemeyi bozardı).

## Derleme ve indirme
- `main`'e her push (veya Actions > "APK derle" > Run workflow) yeni APK üretir.
- APK, deponun **Releases** bölümünde `KizilVadi-1.0.N.apk` olarak yayınlanır (ayrıca Actions artifact'ı olarak da).
- `versionCode = 100 + çalışma numarası`, `versionName = 1.0.<çalışma numarası>`: her derleme otomatik artar.
- Sadece **release** derlenir; debug imzası kullanılmaz (debug APK'lar her derlemede farklı geçici anahtarla imzalanır ve güncellemeyi bozar).

## Anahtar yedeği (ÇOK ÖNEMLİ)
`kizilvadi-release.jks` dosyasını ve şifresini **depoya yükleme**; parola yöneticisi / kişisel bulut / USB gibi
iki ayrı güvenli yere kaydet. Bu anahtar kaybolursa mevcut uygulamanın üzerine güncelleme kurulamaz
(Android farklı imzayı reddeder) ve yalnızca silip yeniden kurma kalır. Anahtar depoda tutulmaz (`.gitignore` engeller).

## Deneme modu
`signing/SELFTEST` dosyası varsa derleme geçici anahtar üretir, yayınlamaz (yalnızca iş akışını sınamak içindir). Normalde dosya yok.
