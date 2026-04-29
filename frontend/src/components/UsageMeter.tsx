import { useEffect, useState } from 'react'
import { Activity, Cpu, Gauge } from 'lucide-react'
import { fetchUsage } from '../api/client'
import type { WSMessage } from '../hooks/useWebSocket'

export function UsageMeter({ messages }: { messages: WSMessage[] }) {
  const [usage, setUsage] = useState<Record<string, any>>({})
  const [health, setHealth] = useState<any>(null)

  useEffect(() => {
    fetchUsage().then(setUsage).catch(() => {})
    const id = setInterval(() => fetchUsage().then(setUsage).catch(() => {}), 4000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].topic === 'system.health') { setHealth(messages[i]); break }
    }
  }, [messages])

  return (
    <div className="glass" style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Gauge size={16} color="#00e5ff" /> <strong>System</strong>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
        <Tile icon={<Cpu size={14} />} label="CPU" value={`${health?.cpu?.toFixed?.(0) ?? '–'}%`} />
        <Tile icon={<Activity size={14} />} label="MEM" value={`${health?.mem?.toFixed?.(0) ?? '–'}%`} />
      </div>

      <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>Per-model usage</div>
      <div className="scroll" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
        {Object.entries(usage).length === 0 && <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>no calls yet</div>}
        {Object.entries(usage).map(([m, u]: any) => (
          <div key={m} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: 8, border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 12, color: 'var(--accent)' }}>{m}</div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>
              {u.total} tok · {u.requests} req · {u.tokens_per_min}/min
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Tile({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)',
      borderRadius: 12, padding: 10, display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-dim)', display: 'flex', gap: 6, alignItems: 'center' }}>
        {icon} {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 600 }}>{value}</div>
    </div>
  )
}
