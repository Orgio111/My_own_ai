// Arajim — desktop overlay.
// Wraps the Vite dashboard in a frameless, always-on-top window
// with a global hotkey (Ctrl+Alt+A) for OS-wide voice access.

const { app, BrowserWindow, globalShortcut, Tray, Menu, nativeImage } = require('electron')
const path = require('path')

const DEV_URL = process.env.ARAJIM_URL || 'http://localhost:5173'

let win = null
let tray = null

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 600,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    alwaysOnTop: false,
    title: 'Arajim',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  win.loadURL(DEV_URL)
  win.on('closed', () => { win = null })
}

function toggleOverlay() {
  if (!win) return createWindow()
  if (win.isVisible()) {
    win.hide()
  } else {
    win.show()
    win.focus()
    win.setAlwaysOnTop(true, 'screen-saver')
  }
}

app.whenReady().then(() => {
  createWindow()

  // Global hotkey — OS-wide overlay toggle
  globalShortcut.register('CommandOrControl+Alt+A', toggleOverlay)
  // Voice hotkey is handled by the renderer too, but we also register it here
  // so it works even when the window is in the background.
  globalShortcut.register('CommandOrControl+Shift+A', () => {
    if (win) win.webContents.send('arajim:voice-trigger')
  })

  // Tray
  const icon = nativeImage.createEmpty()
  tray = new Tray(icon)
  tray.setToolTip('Arajim · Autonomous AI OS')
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Show / Hide (Ctrl+Alt+A)', click: toggleOverlay },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() },
  ]))
})

app.on('will-quit', () => globalShortcut.unregisterAll())
app.on('window-all-closed', (e) => { if (process.platform !== 'darwin') e.preventDefault() })
