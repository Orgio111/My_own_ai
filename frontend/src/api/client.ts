export type Message = { role: 'user' | 'assistant' | 'system'; content: string }

const BASE = ''

export async function chat(messages: Message[], opts?: { model?: string; task_class?: string; session_id?: string }) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, ...opts }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<{ model: string; content: string; usage: any }>
}

export async function listAgents() {
  const r = await fetch('/api/agents')
  return r.json()
}

export async function spawnAgent(name = 'agent', role = 'general', mode = 'guided') {
  const r = await fetch('/api/agents/spawn', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, role, mode }),
  })
  return r.json()
}

export async function runAgent(agent_id: string, goal: string) {
  const r = await fetch('/api/agents/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id, goal }),
  })
  return r.json()
}

export async function setMode(agent_id: string, mode: 'auto' | 'guided' | 'manual') {
  const r = await fetch('/api/agents/mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id, mode }),
  })
  return r.json()
}

export async function approve(step_id: string, approved: boolean) {
  const r = await fetch('/api/agents/approve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step_id, approved }),
  })
  return r.json()
}

export async function fetchModels() {
  return (await fetch('/api/system/models')).json()
}

export type AvailableModel = { id: string; role: string; owned_by?: string; created?: number }

export async function fetchAvailableModels(refresh = false): Promise<AvailableModel[]> {
  const r = await fetch(`/api/system/models/available${refresh ? '?refresh=true' : ''}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function fetchUsage() {
  return (await fetch('/api/system/usage')).json()
}

export async function voiceRespond(text: string) {
  const r = await fetch('/api/voice/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return r.json() as Promise<{ text: string; lang: string }>
}
