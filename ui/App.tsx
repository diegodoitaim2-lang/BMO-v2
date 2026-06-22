import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { apiGet } from './lib/api'
import type { AvatarMood, BootstrapData, PanelId } from './lib/types'
import { Sidebar } from './components/Sidebar'
import { StatusPill } from './components/StatusPill'
import { ChatScreen } from './screens/ChatScreen'
import { MemoryScreen } from './screens/MemoryScreen'
import { HistoryScreen } from './screens/HistoryScreen'
import { ModelsScreen } from './screens/ModelsScreen'
import { ProvidersScreen } from './screens/ProvidersScreen'
import { VoiceScreen } from './screens/VoiceScreen'
import { ToolsScreen } from './screens/ToolsScreen'
import { WorkspaceScreen } from './screens/WorkspaceScreen'
import { SkillsScreen } from './screens/SkillsScreen'
import { ChannelsScreen } from './screens/ChannelsScreen'
import { SystemScreen } from './screens/SystemScreen'
import { SettingsScreen } from './screens/SettingsScreen'

const NAV_ITEMS: Array<{ id: PanelId; label: string }> = [
  { id: 'Chat', label: 'Chat' },
  { id: 'Memoria', label: 'Memoria' },
  { id: 'Historico', label: 'Historico' },
  { id: 'Modelos', label: 'Modelos' },
  { id: 'Provedores', label: 'Provedores' },
  { id: 'Voz', label: 'Voz' },
  { id: 'Ferramentas', label: 'Ferramentas' },
  { id: 'Workspace', label: 'Workspace' },
  { id: 'Skills', label: 'Skills' },
  { id: 'Canais', label: 'Canais' },
  { id: 'Sistema', label: 'Sistema' },
  { id: 'Configuracoes', label: 'Configuracoes' },
]

function App() {
  const [activePanel, setActivePanel] = useState<PanelId>('Chat')
  const [bootstrap, setBootstrap] = useState<BootstrapData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mood, setMood] = useState<AvatarMood>('idle')

  async function loadBootstrap() {
    setLoading(true)
    try {
      const data = await apiGet<BootstrapData>('/api/bootstrap')
      setBootstrap(data)
      setError(null)
      setMood('idle')
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Falha ao carregar o BMO-V2.'
      setError(message)
      setMood('error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void (async () => {
      setLoading(true)
      try {
        const data = await apiGet<BootstrapData>('/api/bootstrap')
        setBootstrap(data)
        setError(null)
        setMood('idle')
      } catch (cause) {
        const message = cause instanceof Error ? cause.message : 'Falha ao carregar o BMO-V2.'
        setError(message)
        setMood('error')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const theme = bootstrap?.settings?.app?.theme || 'cartoon'
  const providerOk = Boolean(bootstrap?.settings?.provider?.apiKey)
  const providerFormKey = bootstrap
    ? [
        bootstrap.settings?.provider?.name || 'openrouter',
        bootstrap.settings?.provider?.model || 'openai/gpt-oss-120b:free',
        bootstrap.settings?.provider?.apiKey ? 'key' : 'nokey',
        bootstrap.settings?.provider?.apiBase || 'https://openrouter.ai/api/v1',
      ].join('|')
    : 'loading'
  const settingsFormKey = bootstrap
    ? [
        bootstrap.settings?.app?.language || 'pt-BR',
        bootstrap.settings?.app?.theme || 'cartoon',
        bootstrap.settings?.app?.hotkey || 'Ctrl+Alt+B',
        String(bootstrap.settings?.app?.chatFontScale || 1),
      ].join('|')
    : 'loading'
  const voiceFormKey = bootstrap
    ? [
        bootstrap.settings?.app?.voice?.model || 'pt_BR-faber-medium.onnx',
        bootstrap.settings?.whisper?.model || 'base',
      ].join('|')
    : 'loading'

  return (
    <div className={`app-shell theme-${theme}`}>
      <Sidebar navItems={NAV_ITEMS} active={activePanel} onSelect={setActivePanel} mood={mood} system={bootstrap?.system} />

      <main className="workspace">
        <header className="topbar">
          <div className="topbar-copy">
            <span className="eyebrow">BMO-V2</span>
            <h1>{activePanel}</h1>
            <p>Interface local para chat, voz, canais, ferramentas e configuracoes.</p>
          </div>
          <div className="topbar-actions">
            <StatusPill label={providerOk ? 'Provider pronto' : 'Provider pendente'} ok={providerOk} />
            <StatusPill label={bootstrap?.system?.runtime?.ready ? 'Runtime online' : 'Runtime offline'} ok={bootstrap?.system?.runtime?.ready} />
            <button onClick={() => void loadBootstrap()}>
              <RefreshCw size={16} /> Atualizar
            </button>
          </div>
        </header>

        {error && <div className="banner error">{error}</div>}
        {loading && <div className="banner">Carregando contexto local...</div>}

        <div className="panel-stage">
          {activePanel === 'Chat' && <ChatScreen data={bootstrap} setMood={setMood} />}
          {activePanel === 'Memoria' && <MemoryScreen data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Historico' && <HistoryScreen data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Modelos' && <ModelsScreen data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Provedores' && <ProvidersScreen key={providerFormKey} data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Voz' && <VoiceScreen key={voiceFormKey} data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Ferramentas' && <ToolsScreen data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Workspace' && <WorkspaceScreen data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Skills' && <SkillsScreen data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Canais' && <ChannelsScreen data={bootstrap} />}
          {activePanel === 'Sistema' && <SystemScreen data={bootstrap} onRefresh={loadBootstrap} />}
          {activePanel === 'Configuracoes' && <SettingsScreen key={settingsFormKey} data={bootstrap} onRefresh={loadBootstrap} />}
        </div>
      </main>
    </div>
  )
}

export default App
