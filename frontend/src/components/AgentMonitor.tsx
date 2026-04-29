import { useEffect, useMemo, useState } from 'react'
import { Activity, Bot, Check, Clock, Play, X } from 'lucide-react'
import { approve, runAgent, spawnAgent } from '../api/client'
import type { WSMessage } from '../hooks/useWebSocket'

type Step = { id: string; description: string; status: string; tool?: string; args?: any }
type Plan = { id: string; goal: string; summary: string; steps: Step[] }

export function AgentMonitor({ messages }: { messages: WSMessage[] }) {
  const [agentId, setAgentId] = useState<string | null>(null)
  const [goal, setGoal] = useState('')
  const [plan, setPlan] = useState<Plan | null>(null)

  const pending = useMemo(
    () => messages.filter((m) => m.topic === 'approval.request').slice(-1)[0],
    [messages],
  )

  useEffect(() => {
    for (const m of messages) {
      if (m.topic === 'plan.start' && m.plan) setPlan(m.plan)
      if (m.topic === 'plan.done' && m.plan) setPlan(m.plan)
      if (m.topic === 'step.update' && m.step && plan?.id === m.plan_id) {
        setPlan((p) => p ? { ...p, steps: p.steps.map((s) => s.id === m.step.id ? m.step : s) } : p)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages])

  const ensureAgent = async () => {
    if (agentId) return agentId
    const a = await spawnAgent('main', 'general', 'guided')
    setAgentId(a.id)
    return a.id
  }

  const launch = async () => {
    if (!goal.trim()) return
    const id = await ensureAgent()
    setPlan(null)
    runAgent(id, goal)
    setGoal('')
  }

  return (
    <div className="glass" style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Bot size={16} color="#7c5cff" />
        <strong>Autonomous Agent</strong>
        <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-dim)' }}>{agentId ?? '—'}</span>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && launch()}
          placeholder="Give the agent a goal..."
          style={{ flex: 1 }}
        />
        <button className="primary" onClick={launch}>
          <Play size={14} /> &nbsp;Run
        </button>
      </div>

      {pending && (
        <div style={{
          background: 'rgba(255,180,84,0.12)', border: '1px solid rgba(255,180,84,0.4)',
          padding: 10, borderRadius: 12, marginBottom: 12,
        }}>
          <div style={{ fontSize: 12, color: 'var(--warn)', marginBottom: 6 }}>APPROVAL REQUESTED</div>
          <div style={{ fontSize: 13, marginBottom: 8 }}>{pending.tool} — {pending.description}</div>
          <pre style={{ fontSize: 11, margin: 0, color: 'var(--text-dim)' }}>{JSON.stringify(pending.args, null, 2)}</pre>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={() => approve(pending.step_id, true)}><Check size={14} /> Approve</button>
            <button onClick={() => approve(pending.step_id, false)}><X size={14} /> Skip</button>
          </div>
        </div>
      )}

      <div className="scroll" style={{ flex: 1 }}>
        {plan && (
          <>
            <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>{plan.summary}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {plan.steps.map((s, i) => <StepRow key={s.id} index={i + 1} step={s} />)}
            </div>
          </>
        )}
        {!plan && <div style={{ color: 'var(--text-dim)' }}>No active plan. Start an agent above.</div>}
      </div>
    </div>
  )
}

function StepRow({ index, step }: { index: number; step: Step }) {
  const color = {
    pending: 'var(--text-dim)', running: 'var(--accent-2)', done: 'var(--ok)',
    failed: 'var(--danger)', skipped: 'var(--text-dim)', awaiting_approval: 'var(--warn)',
  }[step.status] || 'var(--text-dim)'
  const Icon = step.status === 'done' ? Check : step.status === 'running' ? Activity : Clock
  return (
    <div style={{
      display: 'flex', gap: 10, padding: 10,
      background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)', borderRadius: 12,
    }}>
      <div style={{ color }}><Icon size={16} /></div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13 }}>{index}. {step.description}</div>
        {step.tool && <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{step.tool}</div>}
      </div>
      <div style={{ fontSize: 11, color }}>{step.status}</div>
    </div>
  )
}
