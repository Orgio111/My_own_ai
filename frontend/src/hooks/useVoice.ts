import { useCallback, useEffect, useRef, useState } from 'react'

type SR = any
declare global { interface Window { webkitSpeechRecognition?: SR; SpeechRecognition?: SR } }

export function useVoice() {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const recRef = useRef<SR | null>(null)

  useEffect(() => {
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Ctor) return
    const rec = new Ctor()
    rec.continuous = false
    rec.interimResults = true
    rec.lang = navigator.language?.startsWith('mn') ? 'mn-MN' : 'en-US'
    rec.onresult = (e: any) => {
      let txt = ''
      for (let i = e.resultIndex; i < e.results.length; i++) txt += e.results[i][0].transcript
      setTranscript(txt)
    }
    rec.onend = () => setListening(false)
    recRef.current = rec
  }, [])

  const start = useCallback(() => {
    setTranscript('')
    if (!recRef.current) return
    recRef.current.start()
    setListening(true)
  }, [])

  const stop = useCallback(() => {
    recRef.current?.stop()
    setListening(false)
  }, [])

  const speak = useCallback((text: string, lang = 'en-US') => {
    if (!('speechSynthesis' in window)) return
    const u = new SpeechSynthesisUtterance(text)
    u.lang = lang
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(u)
  }, [])

  return { listening, transcript, start, stop, speak, supported: !!recRef.current }
}
