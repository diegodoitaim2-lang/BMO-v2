import { Monitor } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'
import { StatusPill } from '../components/StatusPill'

interface SystemScreenProps {
  data: BootstrapData | null
}

export function SystemScreen({ data }: SystemScreenProps) {
  const system = data?.system
  const logs = data?.logs.lines || []
  return (
    <ScreenShell title="Sistema" subtitle="Status local, logs e diagnostico do BMO-V2.">
      <div className="system-grid">
        <div className="status-row">
          <StatusPill label="Backend" ok={system?.backend} />
          <StatusPill label="Piper" ok={system?.piper} />
          <StatusPill label="Whisper" ok={system?.whisper} />
          <StatusPill label={`Tools ${system?.summary?.tools ?? 0}`} ok />
        </div>
        <article className="data-card">
          <h3>Runtime</h3>
          <p>{system?.runtime?.ready ? 'Pronto' : 'Nao pronto'}</p>
          <small>{system?.runtime?.error || 'Sem erro'}</small>
        </article>
        <article className="data-card">
          <h3>Logs recentes</h3>
          <pre className="log-view">{logs.length ? logs.join('\n') : 'Sem logs ainda.'}</pre>
        </article>
        <div className="empty-state">
          <Monitor size={20} />
          <p>Os indicadores de saude aparecem aqui.</p>
        </div>
      </div>
    </ScreenShell>
  )
}
