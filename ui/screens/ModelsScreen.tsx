import { Brain } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface ModelsScreenProps {
  data: BootstrapData | null
}

export function ModelsScreen({ data }: ModelsScreenProps) {
  const provider = data?.settings?.provider
  return (
    <ScreenShell title="Modelos" subtitle="Modelo principal e fallbacks configurados para o motor.">
      <div className="card-grid">
        <article className="data-card">
          <h3>Modelo atual</h3>
          <p>{provider?.model || 'openai/gpt-oss-120b:free'}</p>
          <small>{provider?.name || 'openrouter'}</small>
        </article>
        <article className="data-card">
          <h3>Fallback</h3>
          <p>Os fallbacks ficam no config do motor e podem ser ampliados depois.</p>
        </article>
        <div className="empty-state">
          <Brain size={20} />
          <p>Aqui entra a troca de modelos por interface.</p>
        </div>
      </div>
    </ScreenShell>
  )
}
