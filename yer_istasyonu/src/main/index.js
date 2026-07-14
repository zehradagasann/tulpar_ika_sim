import { app, BrowserWindow } from 'electron'
import { join } from 'node:path'
import rclnodejs from 'rclnodejs'

let mainWindow
let rosNode

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

// Placeholder: bugun sadece DDS agina katilim doğrulanıyor.
// Telemetri/heartbeat/topic aboneliği Gun 3'te eklenecek.
async function startRosNode() {
  await rclnodejs.init()
  rosNode = new rclnodejs.Node('yer_istasyonu_node')
  rosNode.spin()
  console.log('[ROS2] yer_istasyonu_node DDS agina katildi')
}

app.whenReady().then(async () => {
  await startRosNode()
  createWindow()

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
