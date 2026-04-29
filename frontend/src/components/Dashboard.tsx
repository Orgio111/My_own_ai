import { useState } from 'react'
import { Logo } from './Logo'
import { ChatPanel } from './ChatPanel'
import { Terminal } from './Terminal'
import { AgentMonitor } from './AgentMonitor'
import { UsageMeter } from './UsageMeter'
import { ModelSelector } from './ModelSelector'
import { VoiceButton } from './VoiceButton'
import { FloatingPanel } from './FloatingPanel'
import { TitleBar } from './TitleBar'
import { useWebSocket } from '../hooks/useWebSocket'
import { isDesktop } from '../desktop'

export function Dashboard() {
  const [model, setModel] = useState<string | null>(null)
  const { connected, messages } = useWebSocket('/ws')

  return (
    <div style={{
      display: 'grid',
      gridTemplateRows: isDesktop ? '36px 64px 1fr' : '64px 1fr',
      height: '100vh',
    }}>
      <TitleBar />
      <header style={{
        display: 'flex', alignItems: 'center', gap: 16, padding: '0 20px',
        borderBottom: '1px solid var(--border)', backdropFilter: 'blur(8px)',
      }}>
        <Logo size={36} />
        <span style={{
          fontSize: 11, padding: '3px 8px', borderRadius: 999,
          background: connected ? 'rgba(90,217,127,0.15)' : 'rgba(255,84,112,0.15)',
          color: connected ? 'var(--ok)' : 'var(--danger)',
          border: `1px solid ${connected ? 'rgba(90,217,127,0.4)' : 'rgba(255,84,112,0.4)'}`,
        }}>
          {connected ? 'live' : 'reconnecting…'}
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 16, alignItems: 'center' }}>
          <ModelSelector value={model} onChange={setModel} />
          <VoiceButton />
        </div>
      </header>

      <main style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(280px,1fr) minmax(320px,1.2fr) minmax(280px,1fr)',
        gridTemplateRows: '1fr 240px',
        gap: 14, padding: 14,
        gridTemplateAreas: `
          'chat agent usage'
          'chat term  usage'
        `,
      }}>
        <div style={{ gridArea: 'chat', minHeight: 0 }}><ChatPanel model={model} /></div>
        <div style={{ gridArea: 'agent', minHeight: 0 }}><AgentMonitor messages={messages} /></div>
        <div style={{ gridArea: 'usage', minHeight: 0 }}><UsageMeter messages={messages} /></div>
        <div style={{ gridArea: 'term', minHeight: 0 }} className="glass">
          <div style={{ height: '100%', padding: 8 }}>
            <Terminal messages={messages} />
          </div>
        </div>
      </main>

      <FloatingPanel />
    </div>
  )
}
