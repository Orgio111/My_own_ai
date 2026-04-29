import { useEffect, useRef } from 'react'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import type { WSMessage } from '../hooks/useWebSocket'

export function Terminal({ messages }: { messages: WSMessage[] }) {
  const ref = useRef<HTMLDivElement>(null)
  const termRef = useRef<XTerm | null>(null)
  const seenRef = useRef(0)

  useEffect(() => {
    if (!ref.current || termRef.current) return
    const term = new XTerm({
      theme: { background: '#06070b', foreground: '#cfd6e1', cursor: '#76b900' },
      fontFamily: '"JetBrains Mono", "SF Mono", monospace',
      fontSize: 12,
      convertEol: true,
    })
    const fit = new FitAddon()
    term.loadAddon(fit)
    term.open(ref.current)
    fit.fit()
    term.writeln('\x1b[38;5;148m[arajim]\x1b[0m connected — live execution log')
    termRef.current = term
    const onResize = () => fit.fit()
    window.addEventListener('resize', onResize)
    return () => { window.removeEventListener('resize', onResize); term.dispose() }
  }, [])

  useEffect(() => {
    const term = termRef.current
    if (!term) return
    for (let i = seenRef.current; i < messages.length; i++) {
      const m = messages[i]
      const ts = new Date().toLocaleTimeString()
      const color = m.topic.startsWith('step.') ? 81 : m.topic.startsWith('plan.') ? 148 : m.topic.startsWith('system.') ? 244 : 213
      term.writeln(`\x1b[38;5;${color}m${ts} ${m.topic}\x1b[0m ${truncate(JSON.stringify(m))}`)
    }
    seenRef.current = messages.length
  }, [messages])

  return <div ref={ref} style={{ height: '100%', width: '100%' }} />
}

function truncate(s: string, n = 220) { return s.length <= n ? s : s.slice(0, n) + '…' }
