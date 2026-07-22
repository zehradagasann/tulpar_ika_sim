import './App.css'
import TelemetriPaneli from './components/TelemetriPaneli'
import VideoAlici from './components/VideoAlici'
import {
  SIGNALING_SERVER_URL,
  SIGNALING_SERVER_URL_ARKA,
  SIGNALING_SERVER_URL_ON,
} from './config'

function App() {
  return (
    <>
      <h1>TULPAR İKA Yer İstasyonu</h1>
      <TelemetriPaneli />
      <div className="video-izgara">
        <VideoAlici signalingUrl={SIGNALING_SERVER_URL} baslik="Atış Kamerası" />
        <VideoAlici signalingUrl={SIGNALING_SERVER_URL_ARKA} baslik="Arka Kamera" />
        <VideoAlici signalingUrl={SIGNALING_SERVER_URL_ON} baslik="Ön Kamera (D435if)" />
      </div>
    </>
  )
}

export default App
