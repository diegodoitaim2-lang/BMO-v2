import { useRef, useState } from 'react'
import { Mic, Volume2 } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { AvatarMood, BootstrapData, SettingsState } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'
import { StatusPill } from '../components/StatusPill'

interface SpeakResponse {
  ok: boolean
  message: string
  voice?: string
  audioDataUrl?: string
  audioPath?: string
  durationMs?: number
  piperMs?: number
  spokenText?: string
}

interface WhisperTestResponse {
  ok: boolean
  message: string
  transcript?: string
  language?: string
  audioPath?: string
}

interface VoiceScreenProps {
  data: BootstrapData | null
  onRefresh?: () => Promise<void> | void
  setMood?: (mood: AvatarMood) => void
}

export function VoiceScreen({ data, onRefresh, setMood }: VoiceScreenProps) {
  const voices = data?.voices.voices || []
  const selectedVoiceFallback = data?.voices.selected || data?.settings?.app?.voice?.model || 'pt_BR-faber-medium.onnx'
  const [selectedVoice, setSelectedVoice] = useState(() => selectedVoiceFallback)
  const [selectedWhisper, setSelectedWhisper] = useState(() => data?.settings?.whisper?.model || 'base')
  const [sampleText, setSampleText] = useState('Ola, este e um teste de voz do BMO-V2. Quero ouvir a sintese completa.')
  const [saveMessage, setSaveMessage] = useState('')
  const [speakMessage, setSpeakMessage] = useState('')
  const [whisperMessage, setWhisperMessage] = useState('')
  const [transcript, setTranscript] = useState('')
  const [busy, setBusy] = useState<'speak' | 'whisper' | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

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
      setSaveMessage('Preferencias de voz salvas.')
      await onRefresh?.()
    } catch (error) {
      setSaveMessage(error instanceof Error ? error.message : 'Falha ao salvar a voz.')
    }
  }

  async function testSpeak() {
    if (!sampleText.trim()) {
      setSpeakMessage('Escreva um texto para testar a voz.')
      return
    }
    setBusy('speak')
    setMood?.('speaking')
    setSpeakMessage('Gerando audio de teste...')
    try {
      const response = await apiPost<SpeakResponse>('/api/speak', {
        text: sampleText,
        voice: selectedVoice,
      })
      if (!response.ok || !response.audioDataUrl) {
        setSpeakMessage(response.message || 'Nao foi possivel gerar a fala.')
        return
      }
      audioRef.current?.pause()
      const audio = new Audio(response.audioDataUrl)
      audioRef.current = audio
      audio.addEventListener('ended', () => {
        setMood?.('idle')
      }, { once: true })
      try {
        await audio.play()
      } catch {
        setSpeakMessage(`${response.message} O audio foi gerado, mas o navegador bloqueou a reproducao automatica.`)
        setMood?.('idle')
        return
      }
      const duration = typeof response.durationMs === 'number' && response.durationMs > 0 ? ` (${Math.round(response.durationMs / 1000)} s)` : ''
      setSpeakMessage(`${response.message}${duration} Voz ${response.voice || selectedVoice} reproduzida.`)
    } catch (error) {
      setSpeakMessage(error instanceof Error ? error.message : 'Falha ao testar a voz.')
      setMood?.('error')
    } finally {
      setBusy(null)
    }
  }

  async function testWhisper() {
    setBusy('whisper')
    setMood?.('listening')
    setWhisperMessage('Gravando microfone por alguns segundos...')
    setTranscript('')
    try {
      const response = await apiPost<WhisperTestResponse>('/api/whisper/test', {
        model: selectedWhisper,
      })
      setWhisperMessage(response.message)
      const transcriptText = response.transcript?.trim() || ''
      setTranscript(transcriptText || (response.ok ? 'Nenhuma fala reconhecida.' : ''))
    } catch (error) {
      setWhisperMessage(error instanceof Error ? error.message : 'Falha ao testar o Whisper.')
      setMood?.('error')
    } finally {
      setBusy(null)
      setMood?.('idle')
    }
  }

  return (
    <ScreenShell
      title="Voz"
      subtitle="Piper para falar e Whisper para ouvir."
      actions={<button onClick={() => void saveVoice()} disabled={busy !== null}><Mic size={16} /> Salvar voz</button>}
    >
      <div className="status-row">
        <StatusPill label="Piper pronto" ok={data?.system?.piper} />
        <StatusPill label="Whisper pronto" ok={data?.system?.whisper} />
        <StatusPill label={`Modelo: ${selectedVoice}`} ok={Boolean(selectedVoice)} />
      </div>

      {saveMessage && <p className="result-text">{saveMessage}</p>}

      <div className="card-grid">
        <article className="data-card">
          <h3>Fala</h3>
          <p>Escolha uma voz e digite um texto curto para ouvir o Piper.</p>
          <label>
            Voz Piper
            <select value={selectedVoice} onChange={(event) => setSelectedVoice(event.target.value)} disabled={busy !== null}>
              {voices.length === 0 ? (
                <option value={selectedVoice}>Nenhum modelo encontrado</option>
              ) : (
                voices.map((voice) => (
                  <option key={voice.file} value={voice.file}>
                    {voice.label} {voice.exists ? '' : '(ausente)'}
                  </option>
                ))
              )}
            </select>
          </label>
          <label>
            Texto para ler
            <textarea
              value={sampleText}
              onChange={(event) => setSampleText(event.target.value)}
              placeholder="Digite aqui o texto que o BMO deve falar..."
              disabled={busy !== null}
            />
          </label>
          <div className="button-row">
            <button className="primary" onClick={() => void testSpeak()} disabled={busy !== null}>
              <Volume2 size={16} /> Testar voz
            </button>
          </div>
          {speakMessage && <p className="result-text">{speakMessage}</p>}
        </article>

        <article className="data-card">
          <h3>Microfone</h3>
          <p>Grave alguns segundos e confira a transcricao do Whisper.</p>
          <label>
            Modelo Whisper
            <select value={selectedWhisper} onChange={(event) => setSelectedWhisper(event.target.value)} disabled={busy !== null}>
              <option value="tiny">tiny</option>
              <option value="base">base</option>
              <option value="small">small</option>
            </select>
          </label>
          <div className="button-row">
            <button onClick={() => void testWhisper()} disabled={busy !== null}>
              <Mic size={16} /> Testar microfone
            </button>
          </div>
          {whisperMessage && <p className="result-text">{whisperMessage}</p>}
          {transcript && <pre className="log-view">{transcript}</pre>}
        </article>
      </div>
    </ScreenShell>
  )
}
