import { useEffect, useState } from 'react'
import { Brain, RotateCcw } from 'lucide-react'
import { apiGet } from '../lib/api'
import type { BootstrapData, ModelCatalogData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'
import { StatusPill } from '../components/StatusPill'

interface ModelsScreenProps {
  data: BootstrapData | null
  onRefresh?: () => Promise<void> | void
}

export function ModelsScreen({ data, onRefresh }: ModelsScreenProps) {
  const [catalog, setCatalog] = useState<ModelCatalogData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function loadModels() {
    setLoading(true)
    try {
      const response = await apiGet<ModelCatalogData>('/api/models')
      setCatalog(response)
      setError('')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Falha ao carregar os modelos.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void (async () => {
      setLoading(true)
      try {
        const response = await apiGet<ModelCatalogData>('/api/models')
        setCatalog(response)
        setError('')
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : 'Falha ao carregar os modelos.')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const current = catalog?.current || {
    provider: data?.settings?.provider?.name || 'openrouter',
    model: data?.settings?.provider?.model || 'openai/gpt-oss-120b:free',
    apiBase: data?.settings?.provider?.apiBase || 'https://openrouter.ai/api/v1',
    apiKeyConfigured: Boolean(data?.settings?.provider?.apiKey),
    runtimeModel: data?.system?.runtime?.model || '',
    runtimeReady: Boolean(data?.system?.runtime?.ready),
  }

  return (
    <ScreenShell
      title="Modelos"
      subtitle="Veja o modelo em uso e os provedores que o motor reconhece."
      actions={
        <button onClick={() => void loadModels()} disabled={loading}>
          <RotateCcw size={16} /> {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
      }
    >
      {error && <div className="banner error">{error}</div>}

      <div className="card-grid">
        <article className="data-card">
          <h3>Modelo atual</h3>
          <p>{current.model || 'nao definido'}</p>
          <small>{current.provider}</small>
          <div className="status-row">
            <StatusPill label={current.apiKeyConfigured ? 'Chave pronta' : 'Sem chave'} ok={current.apiKeyConfigured} />
            <StatusPill label={current.runtimeReady ? 'Runtime pronto' : 'Runtime offline'} ok={current.runtimeReady} />
          </div>
        </article>
        <article className="data-card">
          <h3>Endpoint atual</h3>
          <p>{current.apiBase || 'sem endpoint'}</p>
          <small>Modelo visto pelo runtime: {current.runtimeModel || 'sem resposta ainda'}</small>
        </article>
        <div className="empty-state">
          <Brain size={20} />
          <p>O catalogo abaixo vem do motor integrado e ajuda a entender o que ele ja reconhece.</p>
        </div>
      </div>

      <div className="card-grid">
        {(catalog?.providers || []).map((provider) => (
          <article key={provider.name} className="data-card">
            <h3>{provider.label}</h3>
            <p>{provider.name}</p>
            <small>{provider.defaultApiBase || 'endpoint definido pelo usuario'}</small>
            <div className="status-row">
              <StatusPill label={provider.gateway ? 'Gateway' : provider.local ? 'Local' : 'Remoto'} ok />
              <StatusPill label={provider.oauth ? 'OAuth' : 'Chave'} ok />
            </div>
          </article>
        ))}
      </div>

      {onRefresh && (
        <div className="button-row">
          <button onClick={() => void onRefresh()}>
            <RotateCcw size={16} /> Recarregar contexto geral
          </button>
        </div>
      )}
    </ScreenShell>
  )
}
