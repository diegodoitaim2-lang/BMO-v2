import { History } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface HistoryScreenProps {
  data: BootstrapData | null
}

export function HistoryScreen({ data }: HistoryScreenProps) {
  const sessions = data?.history.sessions || []
  return (
    <ScreenShell title="Historico" subtitle="Conversas passadas e exportacao futura.">
      <div className="card-grid">
        {sessions.length ? (
          sessions.map((session) => (
            <article key={session.id} className="data-card">
              <h3>{session.title}</h3>
              <p>{session.preview || 'Sem resumo'}</p>
              <small>{session.createdAt ? new Date(session.createdAt * 1000).toLocaleString() : 'sem data'}</small>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <History size={20} />
            <p>Nenhuma conversa salva ainda.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
