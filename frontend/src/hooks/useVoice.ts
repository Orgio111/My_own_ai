import { useCallback, useEffect, useRef, useState } from 'react'

type SR = any
declare global { interface Window { webkitSpeechRecognition?: SR; SpeechRecognition?: SR } }

export function useVoice() {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const recRef = useRef<SR | null>(null)
  const finalRef = useRef('')                   // captures the final transcript across closures
  const onDoneRef = useRef<((text: string) => void) | null>(null)

  useEffect(() => {
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Ctor) return
    const rec = new Ctor()
    rec.continuous = false
    rec.interimResults = true
    rec.lang = navigator.language?.startsWith('mn') ? 'mn-MN' : 'en-US'
    rec.onresult = (e: any) => {
      let txt = ''
      for (let i = 0; i < e.results.length; i++) txt += e.results[i][0].transcript
      finalRef.current = txt
      setTranscript(txt)
    }
    rec.onend = () => {
      setListening(false)
      const cb = onDoneRef.current
      onDoneRef.current = null
      if (cb) cb(finalRef.current.trim())
    }
    rec.onerror = () => {
      setListening(false)
      onDoneRef.current = null
    }
    recRef.current = rec
  }, [])

  const start = useCallback(() => {
    if (!recRef.current) return
    finalRef.current = ''
    setTranscript('')
    try { recRef.current.start() } catch { /* already started */ }
    setListening(true)
  }, [])

  const stop = useCallback(() => {
    try { recRef.current?.stop() } catch { /* noop */ }
  }, [])

  /** Listen once; resolves with the final transcript when the engine ends.
   *  `maxMs` enforces a hard upper bound. */
  const listenOnce = useCallback(
    (maxMs = 8000): Promise<string> =>
      new Promise((resolve) => {
        if (!recRef.current) return resolve('')
        onDoneRef.current = (text) => resolve(text)
        finalRef.current = ''
        setTranscript('')
        try { recRef.current.start() } catch { /* noop */ }
        setListening(true)
        setTimeout(() => { try { recRef.current?.stop() } catch { /* noop */ } }, maxMs)
      }),
    [],
  )

  const speak = useCallback((text: string, lang = 'en-US') => {
    if (!('speechSynthesis' in window)) return
    const u = new SpeechSynthesisUtterance(text)
    u.lang = lang
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(u)
  }, [])

  return { listening, transcript, start, stop, listenOnce, speak, supported: !!recRef.current }
}
