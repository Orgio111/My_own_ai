# Arajim — System Architecture

## 1. High-Level Topology

```
                 ┌──────────────────────────────────────────────────────┐
                 │                   USER SURFACES                      │
                 │  Web Dashboard │ Floating Overlay │ Terminal │ Voice │
                 └──────────────┬─────────────┬──────────────┬──────────┘
                                │ WebSocket   │ HTTP/REST    │ WebRTC
                 ┌──────────────▼─────────────▼──────────────▼──────────┐
                 │                  ARAJIM GATEWAY                      │
                 │           FastAPI · uvicorn · auth · CORS            │
                 └──────────────┬───────────────────────────────────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
┌───────▼────────┐    ┌─────────▼─────────┐    ┌─────────▼─────────┐
│  Orchestrator  │    │  Agent Coordinator│    │   Tool Layer      │
│  · model router│◄──►│  · planner        │◄──►│  · filesystem     │
│  · token track │    │  · executor       │    │  · shell          │
│  · rate limiter│    │  · critic         │    │  · browser        │
│  · parallel    │    │  · self-modifier  │    │  · process        │
└───────┬────────┘    └─────────┬─────────┘    └───────────────────┘
        │                       │
┌───────▼────────────────────────▼─────────────────────────────────┐
│                     NVIDIA AI API CLIENT                         │
│  meta/llama-3.1-nemotron-70b · mistralai/mixtral-8x22b           │
│  deepseek-ai/deepseek-coder · qwen/qwen2.5-72b · nvidia/nv-embed │
└──────────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│                       MEMORY  &  STATE                           │
│  Vector store (FAISS) · Episodic SQLite · Session Redis-cache    │
└──────────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│                    SUPERVISOR  (always-on)                       │
│   health-checks · auto-restart · token budgeting · telemetry     │
└──────────────────────────────────────────────────────────────────┘
```

## 2. Core Concepts

### 2.1 Always-On Supervisor
A long-lived asyncio task in `backend/app/core/supervisor.py` that:
- pings every subsystem on a 5-second heartbeat,
- inspects token budgets and re-shapes routing if a model is throttled,
- auto-restarts failed agents,
- streams `system.health` events to the dashboard.

### 2.2 Multi-Model Orchestrator
`backend/app/core/orchestrator.py` keeps a registry of models with metadata:
`{ id, role, ctx, cost, strengths, max_rpm }`. The router picks a model by:
1. **explicit user override** → use that,
2. **task class** (code, reasoning, embedding, vision, fast-chat),
3. **load balance** across healthy models,
4. **fallback chain** if rate limited.

It supports **parallel fan-out** (ask N models, vote/merge) and **sequential chaining**
(reasoner → coder → reviewer).

### 2.3 Agent Modes
`backend/app/agents/modes.py` defines three policies:

| Mode      | Risky-action gate           | Self-modify | Use case                |
|-----------|-----------------------------|-------------|-------------------------|
| `auto`    | execute immediately         | allowed     | Background workers      |
| `guided`  | ask user via WS prompt      | requires ack| Daily driver (default)  |
| `manual`  | user runs every step        | disabled    | Sensitive sessions      |

### 2.4 Plan → Execute → Critique loop
Every user goal becomes:
1. **Planner** produces JSON plan (`steps[]`).
2. **Executor** runs each step (tool call, sub-prompt, code).
3. **Critic** verifies and may re-plan.
4. **Memory** records outcome + reflection.

### 2.5 Self-Improving Code System
`backend/app/tools/self_modify.py` exposes safe primitives:
- `read_self(path)` — read repo file,
- `propose_patch(path, diff)` — write to a sandboxed branch,
- `run_tests()` — execute test suite,
- `apply_if_green()` — merge only when green AND mode allows.

### 2.6 Voice Pipeline
`backend/app/voice/pipeline.py` orchestrates:
ASR (browser `webkitSpeechRecognition` or NVIDIA Riva) →
intent → orchestrator → TTS (browser `speechSynthesis` or Riva).
A single front-end button (`VoiceButton.tsx`) starts the loop;
it auto-detects Mongolian (`mn-MN`) and English (`en-US`).

### 2.7 Memory
- **Episodic** — every turn stored in SQLite with timestamp + reflection.
- **Semantic** — vector store (FAISS) keyed by embeddings from `nvidia/nv-embedqa-e5-v5`.
- **Procedural** — recipes the agent has learned (skills folder).
- **Compression** — old transcripts summarized by a small model into "memory cards".

### 2.8 Plugin System
Drop a Python file into `backend/app/plugins/contrib/` exporting:
```python
from app.plugins.base import Plugin
class MyPlugin(Plugin):
    name = "my_plugin"
    def tools(self): return [...]
```
Loader auto-discovers, validates, and exposes them as tools to agents.

## 3. Folder Structure

```
backend/
  main.py                     uvicorn entrypoint
  app/
    config.py                 settings (env-driven)
    api/
      chat.py                 /api/chat, /api/chat/stream
      agents.py               /api/agents (start, stop, list, mode)
      system.py               /api/system (health, usage, metrics)
      memory.py               /api/memory (search, upsert, forget)
      voice.py                /api/voice (transcribe, speak)
      ws.py                   /ws main websocket gateway
    core/
      orchestrator.py         multi-model orchestration
      nvidia_client.py        NVIDIA API client (chat, embed, stream)
      router.py               model selection logic
      rate_limiter.py         per-model token bucket
      token_tracker.py        usage accounting
      supervisor.py           always-on health loop
    agents/
      base.py                 Agent base class
      planner.py              breaks goals into JSON plans
      executor.py             runs plan steps via tools
      critic.py               verifies + re-plans
      coordinator.py          multi-agent orchestration
      modes.py                auto / guided / manual policy
    tools/
      filesystem.py           read/write files
      shell.py                execute commands (sandboxed)
      browser.py              Playwright automation
      process.py              launch / kill apps
      self_modify.py          self-improvement primitives
    memory/
      store.py                episodic + semantic store
      summarizer.py           compression
      embeddings.py           NVIDIA embedding wrapper
    voice/
      pipeline.py             ASR + TTS orchestration
    plugins/
      base.py                 Plugin ABC
      loader.py               auto-discovery
    utils/
      logger.py               structlog-style logger
      events.py               pub/sub event bus

frontend/
  src/
    App.tsx                   shell + routing
    components/
      Dashboard.tsx           live grid of panels
      ChatPanel.tsx           streaming chat
      Terminal.tsx            xterm.js terminal
      FloatingPanel.tsx       overlay (Electron + browser)
      VoiceButton.tsx         one-click voice
      ModelSelector.tsx       manual / auto
      AgentMonitor.tsx        live plan + step viewer
      UsageMeter.tsx          token / rate limit gauges
      Logo.tsx                Arajim logo
    hooks/
      useWebSocket.ts
      useVoice.ts
      useAgents.ts
    api/client.ts             typed REST + WS client
    styles/global.css         glassmorphism theme

desktop/
  electron/main.js            BrowserWindow + global hotkey
  package.json

assets/
  logo.svg                    Arajim wordmark
```

## 4. Execution Flow (Voice → Action)

```
[ user presses VoiceButton (Ctrl+Shift+A) ]
          │
          ▼
[ browser captures mic, streams to /ws ]
          │
          ▼
[ ASR → text (mn-MN / en-US auto-detect) ]
          │
          ▼
[ Orchestrator.route(task) → picks Nemotron-70B for reasoning ]
          │
          ▼
[ Planner builds plan: ["open browser", "search ...", "summarize"] ]
          │
          ▼
[ Executor runs each step via tool layer; emits ws events ]
          │
          ▼
[ Critic verifies; Memory stores reflection ]
          │
          ▼
[ TTS speaks summary; Dashboard shows trace ]
```

## 5. Setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export NVIDIA_API_KEY=nvapi-...
uvicorn main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev    # http://localhost:5173

# Desktop overlay (optional)
cd ../desktop
npm install && npm start
```

## 6. Security Posture

- Shell tool runs inside a configurable allow-list (`SHELL_ALLOWED_BIN`).
- Self-modify writes only inside the repo and only to a sandbox branch.
- Browser tool runs Playwright headless with disposable profiles.
- Voice + chat traffic is local; only the prompt body travels to NVIDIA.
- API keys live only in `.env` (git-ignored).

## 7. Roadmap

- ✅ MVP scaffold (this commit)
- ⏭ Riva ASR/TTS streaming
- ⏭ Skills marketplace
- ⏭ Mobile companion (PWA installed)
- ⏭ Local quantized fallback (NIM container)
