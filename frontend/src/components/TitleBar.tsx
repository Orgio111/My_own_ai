import { Minus, Square, X } from 'lucide-react'
import { desktop, isDesktop } from '../desktop'
import { Logo } from './Logo'

export function TitleBar() {
  if (!isDesktop) return null
  return (
    <div
      style={{
        height: 36,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '0 12px',
        background: 'rgba(6,7,11,0.85)',
        borderBottom: '1px solid var(--border)',
        // @ts-expect-error CSS app-region is non-standard but supported by Electron/Chromium
        WebkitAppRegion: 'drag',
        userSelect: 'none',
      }}
    >
      <Logo size={20} />
      <strong style={{ fontSize: 12, color: 'var(--text-dim)', letterSpacing: 1.5 }}>ARAJIM</strong>

      <div style={{ marginLeft: 'auto', display: 'flex', gap: 4, ...({ WebkitAppRegion: 'no-drag' } as React.CSSProperties) }}>
        <TitleButton onClick={() => desktop?.minimize()} title="Minimize"><Minus size={14} /></TitleButton>
        <TitleButton onClick={() => desktop?.maximize()} title="Maximize"><Square size={12} /></TitleButton>
        <TitleButton onClick={() => desktop?.close()} title="Close" danger><X size={14} /></TitleButton>
      </div>
    </div>
  )
}

function TitleButton({
  children, onClick, title, danger,
}: { children: React.ReactNode; onClick: () => void; title: string; danger?: boolean }) {
  return (
    <button
      onClick={onClick}
      title={title}
      style={{
        width: 32, height: 24, padding: 0,
        background: 'transparent', border: 'none',
        color: 'var(--text-dim)', borderRadius: 4,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLButtonElement).style.background = danger ? 'rgba(255,84,112,0.5)' : 'rgba(255,255,255,0.08)'
        ;(e.currentTarget as HTMLButtonElement).style.color = '#fff'
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-dim)'
      }}
    >{children}</button>
  )
}
