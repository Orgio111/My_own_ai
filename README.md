# Arajim — Autonomous AI Operating System

> **Arajim** (Араажим) is a continuously-running, NVIDIA-AI-powered, multi-model, multi-agent system that fuses a chat assistant, an autonomous developer, a desktop overlay, a terminal, and a live dashboard into a single AI OS.

```
                    █████╗ ██████╗  █████╗      ██╗██╗███╗   ███╗
                   ██╔══██╗██╔══██╗██╔══██╗     ██║██║████╗ ████║
                   ███████║██████╔╝███████║     ██║██║██╔████╔██║
                   ██╔══██║██╔══██╗██╔══██║██   ██║██║██║╚██╔╝██║
                   ██║  ██║██║  ██║██║  ██║╚█████╔╝██║██║ ╚═╝ ██║
                   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚════╝ ╚═╝╚═╝     ╚═╝
                              Autonomous · Always-On · NVIDIA-Powered
```

## What it is

Arajim is **not just an app** — it is a long-running AI process that:

- **Always-On Loop** — supervises itself, restarts failed tasks, watches rate limits, never stops unless terminated.
- **Multi-Model Orchestration** — routes each task to the best NVIDIA-hosted model (Llama-3.1-Nemotron, Mixtral, DeepSeek, Qwen, etc.), runs them in parallel, chains them.
- **Three Agent Modes** — `auto` (fully autonomous), `guided` (asks before risky actions), `manual` (you drive).
- **Self-Improving** — reads its own source, proposes patches, runs tests, applies them under guard.
- **Voice-First** — one-click voice button: listens → understands → executes.
- **Mongolian + English** — full bilingual UX (Монгол хэлээр ярьж, бичиж болно).
- **Full System Control** — filesystem, shell, browser automation, app launching.
- **Memory** — persistent vector + episodic store with auto-summarization.
- **Floating Overlay** — desktop panel accessible globally via hotkey.
- **Collaboration** — multiple agents share memory and delegate sub-tasks to each other.

## Quick Start

```bash
# 1. Clone and enter
git clone <repo> arajim && cd arajim

# 2. Configure
cp .env.example .env
# edit .env and set NVIDIA_API_KEY=nvapi-...

# 3. Run the whole stack
./scripts/start.sh
# or with docker:
docker compose up
```

Then open:

- **Dashboard** → http://localhost:5173
- **API docs** → http://localhost:8000/docs
- **Floating overlay** → run `cd desktop && npm install && npm start`

### Desktop App

The desktop wrapper is a full Electron app with frameless custom titlebar,
single-instance lock, persistent window-state, system tray, native menu,
global hotkeys, and OS notifications.

```bash
cd desktop
npm install

# dev — connects to the Vite dev server at :5173
npm start

# bundle the frontend, then package an installer
npm run build           # AppImage / dmg / nsis depending on platform
npm run build:dir       # unpacked app, fastest iteration
```

Global hotkeys:

- `Ctrl/Cmd + Alt + A` — show / hide the main window
- `Ctrl/Cmd + Shift + O` — toggle the floating overlay (always-on-top)
- `Ctrl/Cmd + Shift + A` — one-click voice (listens, understands, executes)

## Repository Layout

```
arajim/
├── backend/          FastAPI + WebSockets + agent orchestrator
├── frontend/         React + Vite glassmorphism dashboard
├── desktop/          Electron wrapper for OS-wide overlay
├── assets/           Logo + brand assets
├── scripts/          Start / health / deploy scripts
├── ARCHITECTURE.md   Full architecture deep-dive
└── docker-compose.yml
```

See `ARCHITECTURE.md` for the full system design.

## License

MIT © Arajim Project
