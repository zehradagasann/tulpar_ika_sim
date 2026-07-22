import { app, BrowserWindow } from 'electron'
import { join } from 'node:path'
import rclnodejs from 'rclnodejs'

// YAZILIMSAL TAMAMLANDI - gercek telemetri yayincisi bekleniyor:
// /telemetri/veri (std_msgs/String, JSON: {hiz, batarya_yuzde, sicaklik_c,
// egim_derece}) su an hicbir node tarafindan yayinlanmiyor. Asagidaki
// subscriber mantigi calisir durumda; Teensy/Jetson koprusu bu topic'e
// yayin yapmaya basladiginda ek kod degisikligi gerekmez.
const TELEMETRI_TOPIC = '/telemetri/veri'
const TELEMETRI_SUBSCRIBE_RETRY_MS = 3000

let mainWindow
let rosNode
let telemetriSub

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 600,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js')
    }
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

async function startRosNode() {
  await rclnodejs.init()
  rosNode = new rclnodejs.Node('yer_istasyonu_node')
  rosNode.spin()
  console.log('[ROS2] yer_istasyonu_node DDS agina katildi')
}

// TAM İMPLEMENTE: gercek rclnodejs subscriber. Henuz /telemetri/veri'ye
// yayin yapan bir node yoksa mesaj hic gelmez ama abonelik hata vermez -
// ROS2 pub/sub yapisi geregi surekli beklemede kalir. Bu fonksiyon sadece
// createSubscription cagrisinin kendisi (ornegin node hazir degilse)
// patlarsa yeniden dener, uygulamayi crash ettirmez.
function startTelemetriSubscriber() {
  try {
    telemetriSub = rosNode.createSubscription(
      'std_msgs/msg/String',
      TELEMETRI_TOPIC,
      (msg) => {
        try {
          const veri = JSON.parse(msg.data)
          mainWindow?.webContents.send('telemetri:veri', {
            ...veri,
            alinmaZamani: Date.now()
          })
        } catch (err) {
          console.error('[Telemetri] Gelen mesaj JSON olarak parse edilemedi:', err.message)
        }
      }
    )
    console.log(`[ROS2] ${TELEMETRI_TOPIC} subscriber olusturuldu`)
  } catch (err) {
    console.error(
      `[Telemetri] Subscriber olusturulamadi, ${TELEMETRI_SUBSCRIBE_RETRY_MS}ms sonra tekrar denenecek:`,
      err.message
    )
    setTimeout(startTelemetriSubscriber, TELEMETRI_SUBSCRIBE_RETRY_MS)
  }
}

app.whenReady().then(async () => {
  await startRosNode()
  createWindow()
  startTelemetriSubscriber()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (rosNode) {
    rosNode.destroy()
  }
  rclnodejs.shutdown()
  if (process.platform !== 'darwin') app.quit()
})
