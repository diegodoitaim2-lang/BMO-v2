import { Database } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface MemoryScreenProps {
  data: BootstrapData | null
}

export function MemoryScreen({ data }: MemoryScreenProps) {
  const items = data?.memory.items || []
  return (
    <ScreenShell title="Memoria" subtitle="Memorias persistentes e arquivos de referencia do assistente.">
      <div className="card-grid">
        {items.length ? (
          items.map((item) => (
            <article key={item.id} className="data-card">
              <h3>{item.id}</h3>
              <pre>{item.text}</pre>
              {item.source && <small>{item.source}</small>}
            </article>
          ))
        ) : (
          <div className="empty-state">
            <Database size={20} />
            <p>Nenhuma memoria carregada ainda.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
