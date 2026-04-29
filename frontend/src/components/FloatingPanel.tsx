import { useEffect, useRef, useState } from 'react'
import { Mic, X } from 'lucide-react'
import { voiceRespond } from '../api/client'
import { useVoice } from '../hooks/useVoice'

export function FloatingPanel() {
  const [open, setOpen] = useState(false)
  const [reply, setReply] = useState('')
  const { listening, transcript, listenOnce, speak, supported } = useVoice()
  const busy = useRef(false)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'a') {
        e.preventDefault(); setOpen((o) => !o)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const oneClick = async () => {
    if (!supported || busy.current) return
    busy.current = true
    setReply('')
    try {
      const text = await listenOnce(7000)
      if (!text) return
      const r = await voiceRespond(text)
      setReply(r.text)
      speak(r.text, r.lang)
    } finally {
      busy.current = false
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        title="Open Arajim overlay (Ctrl+Alt+A)"
        style={{
          position: 'fixed', bottom: 28, right: 28, width: 56, height: 56, borderRadius: '50%',
          border: 'none', background: 'linear-gradient(135deg,#76b900,#00e5ff,#7c5cff)',
          boxShadow: '0 12px 40px rgba(0,229,255,0.35)', color: '#06121a',
          fontWeight: 800, fontSize: 18, zIndex: 9999,
        }}>A</button>
    )
  }

  return (
    <div className="glass" style={{
      position: 'fixed', bottom: 28, right: 28, width: 360, padding: 14,
      zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <strong>Arajim · Overlay</strong>
        <button style={{ marginLeft: 'auto' }} onClick={() => setOpen(false)}><X size={14} /></button>
      </div>

      <button
        onClick={oneClick}
        className="primary"
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: 12 }}>
        <Mic size={16} /> One-Click Voice
      </button>

      {listening && <div style={{ color: 'var(--accent-2)', fontSize: 12 }}>listening… {transcript}</div>}
      {reply && (
        <div style={{ fontSize: 13, background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', borderRadius: 10, padding: 10 }}>
          {reply}
        </div>
      )}
      <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>
        Ctrl+Alt+A to toggle · Ctrl+Shift+A to start voice
      </div>
    </div>
  )
}
