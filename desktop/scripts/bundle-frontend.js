#!/usr/bin/env node
// bundle-frontend.js — runs `vite build` in the sibling frontend/ folder
// and copies the resulting dist/ into desktop/dist/ so electron-builder
// can pack it as part of the app bundle.

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..', '..')
const FRONTEND = path.join(ROOT, 'frontend')
const SRC_DIST = path.join(FRONTEND, 'dist')
const DST_DIST = path.resolve(__dirname, '..', 'dist')

function run(cmd, cwd) {
  console.log(`\n$ ${cmd}   (in ${cwd})`)
  execSync(cmd, { cwd, stdio: 'inherit' })
}

function copyRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true })
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name)
    const d = path.join(dst, entry.name)
    if (entry.isDirectory()) copyRecursive(s, d)
    else fs.copyFileSync(s, d)
  }
}

if (!fs.existsSync(path.join(FRONTEND, 'node_modules'))) {
  run('npm install', FRONTEND)
}
run('npm run build', FRONTEND)

if (fs.existsSync(DST_DIST)) fs.rmSync(DST_DIST, { recursive: true, force: true })
copyRecursive(SRC_DIST, DST_DIST)

console.log(`\n[arajim:desktop] frontend bundled → ${DST_DIST}`)
