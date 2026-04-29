export type Message = { role: 'user' | 'assistant' | 'system'; content: string }

// In dev / browser the Vite proxy forwards /api and /ws to the backend.
// In a packaged Electron build the renderer is served from file:// so we
// have to talk to the backend directly. Override via VITE_ARAJIM_API.
const isElectron = typeof window !== 'undefined' && !!(window as any).arajim
export const API_BASE: string =
  (import.meta as any).env?.VITE_ARAJIM_API ||
  (isElectron ? 'http://127.0.0.1:8000' : '')
export const WS_URL: string =
  (import.meta as any).env?.VITE_ARAJIM_WS ||
  (isElectron ? 'ws://127.0.0.1:8000/ws' : '/ws')

const u = (path: string) => `${API_BASE}${path}`

export async function chat(messages: Message[], opts?: { model?: string; task_class?: string; session_id?: string }) {
  const res = await fetch(u('/api/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, ...opts }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<{ model: string; content: string; usage: any }>
}

export async function listAgents() {
  return (await fetch(u('/api/agents'))).json()
}

export async function spawnAgent(name = 'agent', role = 'general', mode = 'guided') {
  const r = await fetch(u('/api/agents/spawn'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, role, mode }),
  })
  return r.json()
}

export async function runAgent(agent_id: string, goal: string) {
  const r = await fetch(u('/api/agents/run'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id, goal }),
  })
  return r.json()
}

export async function setMode(agent_id: string, mode: 'auto' | 'guided' | 'manual') {
  const r = await fetch(u('/api/agents/mode'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id, mode }),
  })
  return r.json()
}

export async function approve(step_id: string, approved: boolean) {
  const r = await fetch(u('/api/agents/approve'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step_id, approved }),
  })
  return r.json()
}

export async function fetchModels() {
  return (await fetch(u('/api/system/models'))).json()
}

export type AvailableModel = { id: string; role: string; owned_by?: string; created?: number }

export async function fetchAvailableModels(refresh = false): Promise<AvailableModel[]> {
  const r = await fetch(u(`/api/system/models/available${refresh ? '?refresh=true' : ''}`))
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function fetchUsage() {
  return (await fetch(u('/api/system/usage'))).json()
}

export async function voiceRespond(text: string) {
  const r = await fetch(u('/api/voice/respond'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json() as Promise<{ text: string; lang: string }>
}
