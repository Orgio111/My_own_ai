import { Mic, MicOff } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { useVoice } from '../hooks/useVoice'
import { voiceRespond } from '../api/client'

export function VoiceButton() {
  const { listening, listenOnce, stop, speak, supported } = useVoice()
  const busy = useRef(false)

  const trigger = async () => {
    if (busy.current) { stop(); return }
    busy.current = true
    try {
      const text = await listenOnce(7000)
      if (!text) return
      const r = await voiceRespond(text)
      speak(r.text, r.lang)
    } finally {
      busy.current = false
    }
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'a') {
        e.preventDefault()
        trigger()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!supported) return null

  return (
    <button
      onClick={trigger}
      title="Voice (Ctrl+Shift+A)"
      style={{
        position: 'relative',
        width: 56,
        height: 56,
        borderRadius: '50%',
        background: listening
          ? 'radial-gradient(circle, #ff5470, #7c5cff)'
          : 'linear-gradient(135deg, #76b900, #00e5ff)',
        border: 'none',
        boxShadow: listening
          ? '0 0 0 6px rgba(255,84,112,0.18), 0 8px 24px rgba(255,84,112,0.4)'
          : '0 8px 24px rgba(118,185,0,0.4)',
        color: '#06121a',
      }}
    >
      {listening ? <MicOff size={22} /> : <Mic size={22} />}
    </button>
  )
}
