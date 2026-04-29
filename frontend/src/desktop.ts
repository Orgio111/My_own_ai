// Desktop bridge — typed access to the Electron preload API.
// Web builds get a no-op shim so the app keeps working in any browser.

export type ArajimDesktop = {
  isDesktop: true
  getState(): Promise<{ isDev: boolean; platform: string; version: string }>
  minimize(): void
  maximize(): void
  close(): void
  toggleOverlay(): void
  notify(title: string, body: string): void
  on(channel: 'arajim:voice-trigger' | 'arajim:new-agent', cb: () => void): () => void
}

declare global {
  interface Window {
    arajim?: ArajimDesktop
  }
}

export const desktop: ArajimDesktop | null = (typeof window !== 'undefined' && window.arajim) || null
export const isDesktop = !!desktop
