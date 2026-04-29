import { useEffect, useRef, useState } from 'react'
import { WS_URL } from '../api/client'

export type WSMessage = { topic: string; [k: string]: any }

export function useWebSocket(url: string = WS_URL) {
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<WSMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const full = url.startsWith('ws') ? url : `${proto}://${location.host}${url}`
    let alive = true
    let backoff = 500

    const connect = () => {
      const ws = new WebSocket(full)
      wsRef.current = ws
      ws.onopen = () => { setConnected(true); backoff = 500 }
      ws.onclose = () => {
        setConnected(false)
        if (alive) setTimeout(connect, backoff)
        backoff = Math.min(backoff * 2, 8000)
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as WSMessage
          setMessages((m) => [...m.slice(-499), msg])
        } catch {/* ignore */}
      }
    }
    connect()
    return () => { alive = false; wsRef.current?.close() }
  }, [url])

  const send = (op: string, data: Record<string, any> = {}) => {
    wsRef.current?.send(JSON.stringify({ op, ...data }))
  }
  return { connected, messages, send }
}
