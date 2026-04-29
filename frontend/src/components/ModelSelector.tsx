import { useEffect, useMemo, useState } from 'react'
import { Cpu, RefreshCw, Search } from 'lucide-react'
import { AvailableModel, fetchAvailableModels } from '../api/client'

export function ModelSelector({ value, onChange }: { value: string | null; onChange: (m: string | null) => void }) {
  const [models, setModels] = useState<AvailableModel[]>([])
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(false)

  const load = async (refresh = false) => {
    setLoading(true)
    try {
      const list = await fetchAvailableModels(refresh)
      setModels(list)
    } catch {
      setModels([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(false) }, [])

  const grouped = useMemo(() => {
    const f = filter.trim().toLowerCase()
    const filtered = f ? models.filter((m) => m.id.toLowerCase().includes(f) || m.role.includes(f)) : models
    const out: Record<string, AvailableModel[]> = {}
    for (const m of filtered) {
      ;(out[m.role] ||= []).push(m)
    }
    return out
  }, [models, filter])

  const label = value ?? 'auto · best for task'

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen((o) => !o)}
        title="Choose any NVIDIA model"
        style={{ display: 'flex', alignItems: 'center', gap: 8, maxWidth: 320 }}
      >
        <Cpu size={14} color="#76b900" />
        <span style={{
          maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          fontSize: 12,
        }}>{label}</span>
      </button>

      {open && (
        <div className="glass" style={{
          position: 'absolute', right: 0, top: 'calc(100% + 8px)',
          width: 380, padding: 12, zIndex: 100, display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Search size={14} color="#8b95a8" />
            <input
              autoFocus
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Search NVIDIA models..."
              style={{ flex: 1, padding: '6px 8px', fontSize: 12 }}
            />
            <button
              onClick={() => load(true)}
              title="Refresh from NVIDIA"
              style={{ padding: 6 }}
              disabled={loading}
            >
              <RefreshCw size={12} className={loading ? 'spin' : ''} />
            </button>
          </div>

          <div className="scroll" style={{ maxHeight: 320, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <ModelRow
              label="auto · best for task"
              hint="router decides per task class"
              selected={value === null}
              onClick={() => { onChange(null); setOpen(false) }}
            />
            {Object.keys(grouped).sort().map((role) => (
              <div key={role}>
                <div style={{
                  fontSize: 10, textTransform: 'uppercase', letterSpacing: 1.5,
                  color: 'var(--text-dim)', padding: '6px 4px',
                }}>{role}</div>
                {grouped[role].map((m) => (
                  <ModelRow
                    key={m.id}
                    label={m.id}
                    hint={m.owned_by}
                    selected={value === m.id}
                    onClick={() => { onChange(m.id); setOpen(false) }}
                  />
                ))}
              </div>
            ))}
            {!loading && Object.keys(grouped).length === 0 && (
              <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 8 }}>
                No models. Set NVIDIA_API_KEY and click refresh.
              </div>
            )}
          </div>
        </div>
      )}
      <style>{`.spin { animation: spin 1s linear infinite } @keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}

function ModelRow({
  label, hint, selected, onClick,
}: { label: string; hint?: string; selected: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 2,
        padding: 8, textAlign: 'left',
        background: selected ? 'rgba(118,185,0,0.15)' : 'rgba(255,255,255,0.02)',
        border: `1px solid ${selected ? 'rgba(118,185,0,0.5)' : 'var(--border)'}`,
      }}
    >
      <span style={{ fontSize: 12, color: 'var(--text)' }}>{label}</span>
      {hint && <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>{hint}</span>}
    </button>
  )
}
