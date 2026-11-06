/* VALKOR — Firebase yapılandırması.
   Firebase Console → Proje ayarları → "Web uygulaması ekle" → firebaseConfig değerlerini buraya yapıştır.
   (Bu değerler gizli anahtar DEĞİLDİR; güvenlik Firestore kuralları + Authentication ile sağlanır.)
   Doldurulana kadar giriş ekranı "Hesap sistemi yapılandırılmamış" uyarısı gösterir ve oyuna giriş KAPALI kalır. */
export const firebaseConfig = {
  apiKey: "",
  authDomain: "",
  projectId: "",
  storageBucket: "",
  messagingSenderId: "",
  appId: ""
};
