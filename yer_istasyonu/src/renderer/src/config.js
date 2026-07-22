// YAZILIMSAL TAMAMLANDI - gercek signaling server bekleniyor.
// Henuz bir signaling sunucusu yok; asagidaki adresler sadece varsayilan/placeholder.
// Gercek sunucu hazir oldugunda .env dosyasina VITE_SIGNALING_URL=ws://...
// / VITE_SIGNALING_URL_ARKA=ws://... / VITE_SIGNALING_URL_ON=ws://...
// eklenerek degistirilebilir, kod degisikligi gerekmez.
//
// COKLU KAMERA (22 Tem): signaling_server.py tek port uzerinden path bazli
// coklu kanal destekliyor (bkz. Jetson tarafi) - ayni host:port, farkli path.
// On kamera (D435if, 22 Tem): Emin'in notu - RealSense donanimi ayni anda
// tek process'e izin veriyor, kamera_node.py'nin YOLO thread'i D435if'i
// zaten acik tutuyor; D435if icin AYRI bir process/node YOK - ayni process
// icinde appsrc uzerinden ucuncu bir WebRTC hattina besleniyor. Konsol
// tarafinda bu farkin bir onemi yok, path bazinda ayni sekilde baglaniliyor.
export const SIGNALING_SERVER_URL =
  import.meta.env.VITE_SIGNALING_URL || 'ws://localhost:8080/yer-istasyonu-video'

export const SIGNALING_SERVER_URL_ARKA =
  import.meta.env.VITE_SIGNALING_URL_ARKA || 'ws://localhost:8080/yer-istasyonu-arka-kamera'

export const SIGNALING_SERVER_URL_ON =
  import.meta.env.VITE_SIGNALING_URL_ON || 'ws://localhost:8080/yer-istasyonu-on-kamera'
