// YAZILIMSAL TAMAMLANDI - gercek signaling server bekleniyor.
// Henuz bir signaling sunucusu yok; asagidaki adresler sadece varsayilan/placeholder.
// Gercek sunucu hazir oldugunda .env dosyasina VITE_SIGNALING_URL=ws://...
// / VITE_SIGNALING_URL_ARKA=ws://... eklenerek degistirilebilir, kod
// degisikligi gerekmez.
//
// COKLU KAMERA (22 Tem): signaling_server.py tek port uzerinden path bazli
// coklu kanal destekliyor (bkz. Jetson tarafi) - ayni host:port, farkli path.
export const SIGNALING_SERVER_URL =
  import.meta.env.VITE_SIGNALING_URL || 'ws://localhost:8080/yer-istasyonu-video'

export const SIGNALING_SERVER_URL_ARKA =
  import.meta.env.VITE_SIGNALING_URL_ARKA || 'ws://localhost:8080/yer-istasyonu-arka-kamera'
