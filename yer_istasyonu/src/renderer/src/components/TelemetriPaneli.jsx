import { useEffect, useRef, useState } from 'react'
import Gosterge from './Gosterge'

// TAM İMPLEMENTE: IPC uzerinden gelen telemetri verisini gosterir.
// Veri hic gelmediyse ya da VERI_ZAMAN_ASIMI_MS suredir gelmiyorsa
// "bağlantı bekleniyor" durumuna gecer - crash etmez, dinlemeye devam eder.
const VERI_ZAMAN_ASIMI_MS = 3000

function TelemetriPaneli() {
  const [veri, setVeri] = useState(null)
  const [bagli, setBagli] = useState(false)
  const sonAlinmaRef = useRef(0)

  useEffect(() => {
    const unsubscribe = window.api.telemetri.subscribe((gelenVeri) => {
      sonAlinmaRef.current = Date.now()
      setVeri(gelenVeri)
      setBagli(true)
    })

    const kontrolId = setInterval(() => {
      if (Date.now() - sonAlinmaRef.current > VERI_ZAMAN_ASIMI_MS) {
        setBagli(false)
      }
    }, 1000)

    return () => {
      unsubscribe()
      clearInterval(kontrolId)
    }
  }, [])

  return (
    <section className="panel">
      <h2>Telemetri</h2>
      {!bagli && (
        <p className="durum-mesaji">
          {veri ? 'Veri kesildi, bağlantı bekleniyor...' : 'Veri yok, bağlantı bekleniyor...'}
        </p>
      )}
      <div className="gosterge-izgara">
        <Gosterge baslik="Hız" deger={veri?.hiz} birim="m/s" min={0} max={2} />
        <Gosterge baslik="Batarya" deger={veri?.batarya_yuzde} birim="%" min={0} max={100} />
        <Gosterge baslik="Sıcaklık" deger={veri?.sicaklik_c} birim="°C" min={0} max={80} />
        <Gosterge baslik="Eğim" deger={veri?.egim_derece} birim="°" min={-45} max={45} />
      </div>
    </section>
  )
}

export default TelemetriPaneli
