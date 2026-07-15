// YAZILIMSAL TAMAMLANDI - gercek signaling server bekleniyor.
// Henuz bir signaling sunucusu yok; asagidaki adres sadece varsayilan/placeholder.
// Gercek sunucu hazir oldugunda .env dosyasina VITE_SIGNALING_URL=ws://... eklenerek
// degistirilebilir, kod degisikligi gerekmez.
export const SIGNALING_SERVER_URL =
  import.meta.env.VITE_SIGNALING_URL || 'ws://localhost:8080/yer-istasyonu-video'
