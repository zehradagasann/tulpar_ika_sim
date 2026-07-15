// TAM İMPLEMENTE: tekrar kullanilabilir gosterge (gauge) bileseni.
function Gosterge({ baslik, deger, birim, min = 0, max = 100 }) {
  const gecerliDeger = typeof deger === 'number' && !Number.isNaN(deger)
  const oran = gecerliDeger ? Math.min(1, Math.max(0, (deger - min) / (max - min))) : 0

  return (
    <div className="gosterge">
      <div className="gosterge-baslik">{baslik}</div>
      <div className="gosterge-bar-arkaplan">
        <div className="gosterge-bar-dolu" style={{ width: `${oran * 100}%` }} />
      </div>
      <div className="gosterge-deger">{gecerliDeger ? `${deger} ${birim}` : '—'}</div>
    </div>
  )
}

export default Gosterge
