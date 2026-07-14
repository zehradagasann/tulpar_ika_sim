import { contextBridge } from 'electron'

// Bugun icin bos - renderer'a acilacak API Gun 3'te eklenecek.
contextBridge.exposeInMainWorld('api', {})
