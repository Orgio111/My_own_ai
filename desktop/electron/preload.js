// Preload — exposes a tightly-scoped, safe IPC bridge to the renderer.
// The renderer detects window.arajim and uses it to drive native window
// controls, fire desktop notifications, and react to global shortcuts.

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('arajim', {
  isDesktop: true,
  getState: () => ipcRenderer.invoke('arajim:get-state'),

  // window controls (used by the custom titlebar)
  minimize: () => ipcRenderer.send('arajim:window', 'minimize'),
  maximize: () => ipcRenderer.send('arajim:window', 'maximize'),
  close:    () => ipcRenderer.send('arajim:window', 'close'),

  // overlay
  toggleOverlay: () => ipcRenderer.send('arajim:overlay'),

  // notifications
  notify: (title, body) => ipcRenderer.send('arajim:notify', { title, body }),

  // events from the main process (global shortcuts, menu items)
  on: (channel, cb) => {
    const allowed = ['arajim:voice-trigger', 'arajim:new-agent']
    if (!allowed.includes(channel)) return () => {}
    const handler = (_, ...args) => cb(...args)
    ipcRenderer.on(channel, handler)
    return () => ipcRenderer.removeListener(channel, handler)
  },
})
