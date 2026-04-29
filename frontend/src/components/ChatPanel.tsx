import { useEffect, useRef, useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { chat, Message } from '../api/client'

export function ChatPanel({ model }: { model: string | null }) {
  const [history, setHistory] = useState<Message[]>([
    { role: 'assistant', content: 'Сайн байна уу! I am Arajim. Ask me anything or give me a goal.' },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [history])

  const send = async () => {
    if (!input.trim() || busy) return
    const next: Message[] = [...history, { role: 'user', content: input }]
    setHistory(next); setInput(''); setBusy(true)
    try {
      const res = await chat(next, { model: model || undefined, session_id: 'main' })
      setHistory((h) => [...h, { role: 'assistant', content: res.content }])
    } catch (e: any) {
      setHistory((h) => [...h, { role: 'assistant', content: `error: ${e.message}` }])
    } finally { setBusy(false) }
  }

  return (
    <div className="glass" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Sparkles size={16} color="#76b900" />
        <strong>Conversation</strong>
        <span style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: 12 }}>
          {model || 'auto-route'}
        </span>
      </div>

      <div className="scroll" style={{ flex: 1, padding: '4px 4px 12px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {history.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            background: m.role === 'user'
              ? 'linear-gradient(135deg, rgba(118,185,0,0.16), rgba(0,229,255,0.12))'
              : 'rgba(255,255,255,0.04)',
            border: '1px solid var(--border)',
            borderRadius: 14, padding: '10px 14px', maxWidth: '78%',
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          }}>{m.content}</div>
        ))}
        <div ref={endRef} />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask Arajim... (Mongolian / English)"
          style={{ flex: 1 }}
          disabled={busy}
        />
        <button className="primary" onClick={send} disabled={busy}>
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
