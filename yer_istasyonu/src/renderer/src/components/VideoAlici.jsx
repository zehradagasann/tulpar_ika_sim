import { useEffect, useRef, useState } from 'react'
import { SIGNALING_SERVER_URL } from '../config'

const YENIDEN_DENEME_MS = 3000

// TAM İMPLEMENTE: RTCPeerConnection kurulumu, signaling mesaj akisi
// (offer/answer/ICE aday degisimi), baglanti kopunca/kurulamayinca crash
// etmeden surekli yeniden deneme.
// YAZILIMSAL TAMAMLANDI - gercek signaling server bekleniyor (bkz. config.js).
// Varsayilan protokol (sunucu farkli calisirsa burasi guncellenmeli):
// istemci baglaninca {type:'izleyici-merhaba'} gonderir, sunucudan
// {type:'offer', sdp} bekler, cevap olarak {type:'answer', sdp} doner;
// ICE adaylari {type:'ice-candidate', candidate} ile karsilikli iletilir.
function VideoAlici() {
  const videoRef = useRef(null)
  const pcRef = useRef(null)
  const wsRef = useRef(null)
  const retryTimeoutRef = useRef(null)
  const kapandiRef = useRef(false)

  const [bagli, setBagli] = useState(false)
  const [mesaj, setMesaj] = useState('Video bağlantısı bekleniyor...')

  useEffect(() => {
    kapandiRef.current = false
    baglan()

    return () => {
      kapandiRef.current = true
      temizle()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function temizle() {
    clearTimeout(retryTimeoutRef.current)
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.onerror = null
      wsRef.current.close()
      wsRef.current = null
    }
    if (pcRef.current) {
      pcRef.current.close()
      pcRef.current = null
    }
  }

  function yenidenDene() {
    if (kapandiRef.current) return
    temizle()
    setBagli(false)
    setMesaj('Video bağlantısı bekleniyor...')
    retryTimeoutRef.current = setTimeout(baglan, YENIDEN_DENEME_MS)
  }

  function baglan() {
    if (kapandiRef.current) return

    const pc = new RTCPeerConnection()
    pcRef.current = pc

    pc.ontrack = (event) => {
      if (videoRef.current) {
        videoRef.current.srcObject = event.streams[0]
      }
      setBagli(true)
      setMesaj('Video bağlantısı kuruldu')
    }

    pc.onconnectionstatechange = () => {
      if (['disconnected', 'failed', 'closed'].includes(pc.connectionState)) {
        yenidenDene()
      }
    }

    pc.onicecandidate = (event) => {
      const ws = wsRef.current
      if (event.candidate && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ice-candidate', candidate: event.candidate }))
      }
    }

    let ws
    try {
      ws = new WebSocket(SIGNALING_SERVER_URL)
    } catch (err) {
      yenidenDene()
      return
    }
    wsRef.current = ws

    ws.onopen = () => {
      setMesaj('Sinyal sunucusuna bağlanıldı, video bekleniyor...')
      ws.send(JSON.stringify({ type: 'izleyici-merhaba' }))
    }

    ws.onmessage = async (event) => {
      try {
        const gelen = JSON.parse(event.data)
        if (gelen.type === 'offer') {
          await pc.setRemoteDescription(new RTCSessionDescription(gelen))
          const answer = await pc.createAnswer()
          await pc.setLocalDescription(answer)
          ws.send(JSON.stringify({ type: 'answer', sdp: answer.sdp }))
        } else if (gelen.type === 'ice-candidate' && gelen.candidate) {
          await pc.addIceCandidate(new RTCIceCandidate(gelen.candidate))
        }
      } catch (err) {
        console.error('[VideoAlici] Sinyal mesajı işlenemedi:', err.message)
      }
    }

    ws.onerror = () => {
      // onclose zaten tetiklenecek, yeniden deneme orada yapilir
    }

    ws.onclose = () => {
      yenidenDene()
    }
  }

  return (
    <section className="panel video-alici">
      <h2>Video</h2>
      {!bagli && <p className="durum-mesaji">{mesaj}</p>}
      <video ref={videoRef} autoPlay playsInline muted controls />
    </section>
  )
}

export default VideoAlici
