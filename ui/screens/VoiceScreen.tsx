import { useState } from 'react'
import { Mic, Volume2 } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { BootstrapData, SettingsState } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface VoiceScreenProps {
  data: BootstrapData | null
}

export function VoiceScreen({ data }: VoiceScreenProps) {
  const voices = data?.voices.voices || []
  const [selectedVoice, setSelectedVoice] = useState(() => data?.settings?.app?.voice?.model || 'pt_BR-faber-medium.onnx')
  const [selectedWhisper, setSelectedWhisper] = useState(() => data?.settings?.whisper?.model || 'base')
  const [message, setMessage] = useState('')

  async function saveVoice() {
    try {
      const payload: SettingsState = {
        app: {
          voice: { model: selectedVoice },
        },
        whisper: {
          model: selectedWhisper,
        },
      }
      await apiPost('/api/settings', payload)
      setMessage('Preferencias de voz salvas.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao salvar a voz.')
    }
  }

  async function testSpeak() {
    try {
      const response = await apiPost<{ ok: boolean; message: string }>('/api/speak', {
        text: 'Teste de voz do BMO-V2.',
        voice: selectedVoice,
      })
      setMessage(response.message)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao testar a voz.')
    }
  }

  async function testWhisper() {
    try {
      const response = await apiPost<{ ok: boolean; message: string }>('/api/whisper/test', {
        model: selectedWhisper,
      })
      setMessage(response.message)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao testar o Whisper.')
    }
  }

  return (
    <ScreenShell
      title="Voz"
      subtitle="Piper para falar e Whisper para ouvir."
      actions={<button onClick={() => void saveVoice()}><Mic size={16} /> Salvar voz</button>}
    >
      <div className="settings-form">
        <label>
          Voz Piper
          <select value={selectedVoice} onChange={(event) => setSelectedVoice(event.target.value)}>
            {voices.map((voice) => (
              <option key={voice.file} value={voice.file}>
                {voice.label} {voice.exists ? '' : '(ausente)'}
              </option>
            ))}
          </select>
        </label>
        <label>
          Modelo Whisper
          <select value={selectedWhisper} onChange={(event) => setSelectedWhisper(event.target.value)}>
            <option value="tiny">tiny</option>
            <option value="base">base</option>
            <option value="small">small</option>
          </select>
        </label>
        <div className="button-row">
          <button className="primary" onClick={() => void testSpeak()}>
            <Volume2 size={16} /> Testar voz
          </button>
          <button onClick={() => void testWhisper()}>
            <Mic size={16} /> Testar microfone
          </button>
        </div>
        {message && <p className="result-text">{message}</p>}
      </div>
    </ScreenShell>
  )
}
