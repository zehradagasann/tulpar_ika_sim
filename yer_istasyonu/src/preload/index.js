import { contextBridge, ipcRenderer } from 'electron'

// TAM İMPLEMENTE: renderer'in main process'ten telemetri verisini
// dinlemesini saglayan IPC koprusu.
contextBridge.exposeInMainWorld('api', {
  telemetri: {
    // callback: (veri) => void. Donen fonksiyon ile abonelik iptal edilir.
    subscribe(callback) {
      const listener = (_event, veri) => callback(veri)
      ipcRenderer.on('telemetri:veri', listener)
      return () => ipcRenderer.removeListener('telemetri:veri', listener)
    }
  }
})
