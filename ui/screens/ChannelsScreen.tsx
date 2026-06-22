import { MessageSquareText } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface ChannelsScreenProps {
  data: BootstrapData | null
}

export function ChannelsScreen({ data }: ChannelsScreenProps) {
  const channels = data?.channels.channels || []
  return (
    <ScreenShell title="Canais" subtitle="Integrações disponiveis no nanobot.">
      <div className="card-grid">
        {channels.map((channel) => (
          <article key={channel.id} className="data-card">
            <h3>{channel.label}</h3>
            <p>{channel.status || 'disponivel'}</p>
            <small>{channel.configured ? 'configurado' : 'nao configurado'}</small>
          </article>
        ))}
        {!channels.length && (
          <div className="empty-state">
            <MessageSquareText size={20} />
            <p>Nenhum canal listado.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
