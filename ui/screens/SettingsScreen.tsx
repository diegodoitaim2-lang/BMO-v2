import { useState } from 'react'
import { Save } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { BootstrapData, SettingsState } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface SettingsScreenProps {
  data: BootstrapData | null
}

const THEMES = ['cartoon', 'led', 'bmo-face', 'treehouse', 'night-forest', 'dark', 'soft'] as const

export function SettingsScreen({ data }: SettingsScreenProps) {
  const [language, setLanguage] = useState(() => data?.settings?.app?.language || 'pt-BR')
  const [theme, setTheme] = useState(() => data?.settings?.app?.theme || 'cartoon')
  const [hotkey, setHotkey] = useState(() => data?.settings?.app?.hotkey || 'Ctrl+Alt+B')
  const [chatFontScale, setChatFontScale] = useState(() => String(data?.settings?.app?.chatFontScale || 1))
  const [message, setMessage] = useState('')

  async function save() {
    try {
      const payload: SettingsState = {
        app: {
          language,
          theme,
          hotkey,
          chatFontScale: Number(chatFontScale) || 1,
        },
      }
      await apiPost('/api/settings', payload)
      setMessage('Configuracao salva.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao salvar a configuracao.')
    }
  }

  return (
    <ScreenShell
      title="Configuracoes"
      subtitle="Preferencias gerais do aplicativo."
      actions={<button className="primary" onClick={() => void save()}><Save size={16} /> Salvar</button>}
    >
      <div className="settings-form">
        <label>
          Idioma
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            <option value="pt-BR">pt-BR</option>
            <option value="en">en</option>
          </select>
        </label>
        <label>
          Tema
          <select value={theme} onChange={(event) => setTheme(event.target.value)}>
            {THEMES.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Hotkey global
          <input value={hotkey} onChange={(event) => setHotkey(event.target.value)} />
        </label>
        <label>
          Escala do chat
          <input value={chatFontScale} onChange={(event) => setChatFontScale(event.target.value)} />
        </label>
        {message && <p className="result-text">{message}</p>}
      </div>
    </ScreenShell>
  )
}
