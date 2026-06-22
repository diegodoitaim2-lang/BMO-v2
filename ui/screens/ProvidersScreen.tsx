import { useState } from 'react'
import { CheckCircle2, SlidersHorizontal } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { BootstrapData, SettingsState } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface ProvidersScreenProps {
  data: BootstrapData | null
}

export function ProvidersScreen({ data }: ProvidersScreenProps) {
  const [name, setName] = useState(() => data?.settings?.provider?.name || 'openrouter')
  const [model, setModel] = useState(() => data?.settings?.provider?.model || 'openai/gpt-oss-120b:free')
  const [apiKey, setApiKey] = useState(() => data?.settings?.provider?.apiKey || '')
  const [apiBase, setApiBase] = useState(() => data?.settings?.provider?.apiBase || 'https://openrouter.ai/api/v1')
  const [result, setResult] = useState<string>('')
  const [testing, setTesting] = useState(false)

  async function save() {
    try {
      const payload: SettingsState = {
        provider: {
          name,
          model,
          apiKey,
          apiBase,
        },
      }
      const response = await apiPost<SettingsState>('/api/settings', payload)
      setResult(`Configuracao salva para ${response.provider?.name || name}.`)
    } catch (error) {
      setResult(error instanceof Error ? error.message : 'Falha ao salvar o provedor.')
    }
  }

  async function testConnection() {
    setTesting(true)
    try {
      const response = await apiPost<{ ok: boolean; message: string }>('/api/provider/test', {
        provider: name,
        model,
        apiKey,
      })
      setResult(response.message)
    } catch (error) {
      setResult(error instanceof Error ? error.message : 'Falha ao testar o provedor.')
    } finally {
      setTesting(false)
    }
  }

  return (
    <ScreenShell
      title="Provedores"
      subtitle="Configure a chave e o modelo usados pelo motor de conversa."
      actions={<button onClick={() => void testConnection()} disabled={testing}><CheckCircle2 size={16} /> {testing ? 'Testando...' : 'Testar conexao'}</button>}
    >
      <div className="settings-form">
        <label>
          Provedor
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <label>
          Modelo
          <input value={model} onChange={(event) => setModel(event.target.value)} />
        </label>
        <label>
          API Key
          <input type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
        </label>
        <label>
          API Base
          <input value={apiBase} onChange={(event) => setApiBase(event.target.value)} />
        </label>
        <div className="button-row">
          <button className="primary" onClick={() => void save()}>
            <SlidersHorizontal size={16} /> Salvar
          </button>
        </div>
        {result && <p className="result-text">{result}</p>}
      </div>
    </ScreenShell>
  )
}
