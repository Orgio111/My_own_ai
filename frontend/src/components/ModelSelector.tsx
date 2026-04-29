import { useEffect, useState } from 'react'
import { Cpu } from 'lucide-react'
import { fetchModels } from '../api/client'

export function ModelSelector({ value, onChange }: { value: string | null; onChange: (m: string | null) => void }) {
  const [models, setModels] = useState<any[]>([])
  useEffect(() => { fetchModels().then(setModels).catch(() => {}) }, [])

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <Cpu size={14} color="#76b900" />
      <select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value || null)}
      >
        <option value="">auto · best for task</option>
        {models.map((m) => (
          <option key={m.id} value={m.id}>{m.role} · {m.id}</option>
        ))}
      </select>
    </div>
  )
}
