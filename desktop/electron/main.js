// Arajim Desktop — main process.
// A long-running, OS-integrated wrapper around the Arajim dashboard.
// In dev it loads the Vite dev server; in production it loads the bundled
// frontend that lives next to this file at ../dist/index.html.

const { app, BrowserWindow, globalShortcut, Tray, Menu, MenuItem,
        nativeImage, ipcMain, shell, Notification } = require('electron')
const path = require('path')
const fs = require('fs')

const isDev = !app.isPackaged && (process.env.NODE_ENV === 'development' || process.env.ARAJIM_URL)
const DEV_URL = process.env.ARAJIM_URL || 'http://localhost:5173'
const PROD_INDEX = path.join(__dirname, '..', 'dist', 'index.html')
const STATE_FILE = path.join(app.getPath('userData'), 'arajim-window-state.json')
const ICON_PATH  = path.join(__dirname, '..', 'icon.png')

// ───────────────────────────── single instance ─────────────────────────────
const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
  return
}

let mainWindow = null
let overlayWindow = null
let tray = null

// ───────────────────────────── window state persistence ────────────────────
function loadWindowState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'))
  } catch {
    return { width: 1280, height: 820, x: undefined, y: undefined }
  }
}

function saveWindowState(win) {
  if (!win || win.isDestroyed()) return
  const b = win.getNormalBounds()
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true })
  fs.writeFileSync(STATE_FILE, JSON.stringify(b))
}

// ───────────────────────────── window factories ────────────────────────────
function loadInto(win) {
  if (isDev) {
    win.loadURL(DEV_URL)
  } else if (fs.existsSync(PROD_INDEX)) {
    win.loadFile(PROD_INDEX)
  } else {
    // graceful fallback: still try the dev URL so the user gets something
    win.loadURL(DEV_URL)
  }
}

function createMainWindow() {
  const state = loadWindowState()
  const icon = fs.existsSync(ICON_PATH) ? nativeImage.createFromPath(ICON_PATH) : undefined

  mainWindow = new BrowserWindow({
    title: 'Arajim',
    width:  state.width || 1280,
    height: state.height || 820,
    x: state.x, y: state.y,
    minWidth: 960,
    minHeight: 600,
    frame: false,
    titleBarStyle: 'hidden',
    titleBarOverlay: { color: '#06070b', symbolColor: '#e6ebf2', height: 36 },
    backgroundColor: '#06070b',
    icon,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  loadInto(mainWindow)
  mainWindow.once('ready-to-show', () => mainWindow.show())
  mainWindow.on('close', () => saveWindowState(mainWindow))
  mainWindow.on('closed', () => { mainWindow = null })

  // open external links in the user's browser, not inside Arajim
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
}

function createOverlayWindow() {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.show(); overlayWindow.focus(); return
  }
  overlayWindow = new BrowserWindow({
    width: 380, height: 560,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  overlayWindow.setAlwaysOnTop(true, 'screen-saver')
  loadInto(overlayWindow)
  overlayWindow.once('ready-to-show', () => {
    // park it bottom-right of the primary display
    const { screen } = require('electron')
    const work = screen.getPrimaryDisplay().workArea
    overlayWindow.setPosition(work.x + work.width - 400, work.y + work.height - 580)
    overlayWindow.show()
  })
  overlayWindow.on('blur', () => {
    if (overlayWindow && !overlayWindow.isDestroyed()) overlayWindow.hide()
  })
}

function toggleMain() {
  if (!mainWindow) return createMainWindow()
  if (mainWindow.isVisible() && mainWindow.isFocused()) mainWindow.hide()
  else { mainWindow.show(); mainWindow.focus() }
}

function toggleOverlay() {
  if (!overlayWindow || overlayWindow.isDestroyed()) return createOverlayWindow()
  if (overlayWindow.isVisible()) overlayWindow.hide()
  else { overlayWindow.show(); overlayWindow.focus() }
}

// ───────────────────────────── tray + menu ─────────────────────────────────
function buildTray() {
  const icon = fs.existsSync(ICON_PATH)
    ? nativeImage.createFromPath(ICON_PATH).resize({ width: 16, height: 16 })
    : nativeImage.createEmpty()
  tray = new Tray(icon)
  tray.setToolTip('Arajim · Autonomous AI OS')
  tray.on('click', toggleMain)
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Show / Hide Arajim',     accelerator: 'CommandOrControl+Alt+A', click: toggleMain },
    { label: 'Toggle Floating Overlay',accelerator: 'CommandOrControl+Shift+O', click: toggleOverlay },
    { label: 'Trigger Voice',          accelerator: 'CommandOrControl+Shift+A', click: () => {
        const target = mainWindow?.isVisible() ? mainWindow : overlayWindow
        target?.webContents.send('arajim:voice-trigger')
    }},
    { type: 'separator' },
    { label: 'Reload',                 click: () => mainWindow?.reload() },
    { label: 'Open Dev Tools',         click: () => mainWindow?.webContents.openDevTools({ mode: 'detach' }) },
    { type: 'separator' },
    { label: 'Quit Arajim',            role: 'quit' },
  ]))
}

function buildAppMenu() {
  const isMac = process.platform === 'darwin'
  const template = [
    ...(isMac ? [{ label: 'Arajim', submenu: [
      { role: 'about' }, { type: 'separator' },
      { role: 'services' }, { type: 'separator' },
      { role: 'hide' }, { role: 'hideOthers' }, { role: 'unhide' }, { type: 'separator' },
      { role: 'quit' },
    ]}] : []),
    { label: 'File', submenu: [
      { label: 'New Agent', accelerator: 'CommandOrControl+N', click: () => mainWindow?.webContents.send('arajim:new-agent') },
      { type: 'separator' },
      isMac ? { role: 'close' } : { role: 'quit' },
    ]},
    { label: 'Edit', submenu: [
      { role: 'undo' }, { role: 'redo' }, { type: 'separator' },
      { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' },
    ]},
    { label: 'View', submenu: [
      { role: 'reload' }, { role: 'forceReload' }, { role: 'toggleDevTools' },
      { type: 'separator' },
      { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
      { type: 'separator' },
      { role: 'togglefullscreen' },
    ]},
    { label: 'Window', submenu: [
      { label: 'Toggle Floating Overlay', accelerator: 'CommandOrControl+Shift+O', click: toggleOverlay },
      { role: 'minimize' }, { role: 'zoom' },
      ...(isMac ? [{ type: 'separator' }, { role: 'front' }] : [{ role: 'close' }]),
    ]},
    { label: 'Help', submenu: [
      { label: 'Documentation', click: () => shell.openExternal('https://github.com/orgio111/my_own_ai') },
    ]},
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

// ───────────────────────────── ipc bridge ──────────────────────────────────
ipcMain.handle('arajim:get-state', () => ({
  isDev,
  platform: process.platform,
  version: app.getVersion(),
}))
ipcMain.on('arajim:window', (_, action) => {
  const w = BrowserWindow.getFocusedWindow()
  if (!w) return
  if (action === 'minimize')   w.minimize()
  else if (action === 'maximize') w.isMaximized() ? w.unmaximize() : w.maximize()
  else if (action === 'close') w.close()
})
ipcMain.on('arajim:notify', (_, { title, body }) => {
  if (Notification.isSupported()) new Notification({ title: title || 'Arajim', body }).show()
})
ipcMain.on('arajim:overlay', () => toggleOverlay())

// ───────────────────────────── app lifecycle ───────────────────────────────
app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.show(); mainWindow.focus()
  }
})

app.setAsDefaultProtocolClient('arajim')

app.whenReady().then(() => {
  createMainWindow()
  buildTray()
  buildAppMenu()

  globalShortcut.register('CommandOrControl+Alt+A', toggleMain)
  globalShortcut.register('CommandOrControl+Shift+O', toggleOverlay)
  globalShortcut.register('CommandOrControl+Shift+A', () => {
    const target = mainWindow?.isVisible() ? mainWindow : overlayWindow
    if (!target) createOverlayWindow()
    setImmediate(() => {
      const w = mainWindow?.isVisible() ? mainWindow : overlayWindow
      w?.webContents.send('arajim:voice-trigger')
    })
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
app.on('activate', () => { if (!mainWindow) createMainWindow() })
app.on('will-quit', () => globalShortcut.unregisterAll())
