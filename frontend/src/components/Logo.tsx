export function Logo({ size = 36 }: { size?: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <img src="/logo.svg" alt="Arajim" style={{ height: size, width: 'auto' }} />
    </div>
  )
}
