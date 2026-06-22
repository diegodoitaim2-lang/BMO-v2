import { useMemo, useState } from 'react'
import { SendHorizontal, Sparkles } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { AvatarMood, BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'
import { StatusPill } from '../components/StatusPill'

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
}

interface ChatScreenProps {
  data: BootstrapData | null
  setMood: (mood: AvatarMood) => void
}

export function ChatScreen({ data, setMood }: ChatScreenProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Pronto para conversar. Configure um provedor se ainda nao estiver ativo.' },
  ])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const providerName = data?.settings?.provider?.name || 'openrouter'
  const modelName = data?.settings?.provider?.model || 'openai/gpt-oss-120b:free'

  const headerActions = useMemo(
    () => (
      <>
        <StatusPill label={providerName} ok={Boolean(data?.settings?.provider?.apiKey)} />
        <StatusPill label={modelName} ok />
      </>
    ),
    [data?.settings?.provider?.apiKey, modelName, providerName],
  )

  async function send() {
    const content = text.trim()
    if (!content || busy) return
    setBusy(true)
    setMood('thinking')
    setText('')
    setMessages((current) => [...current, { role: 'user', text: content }])
    try {
      const response = await apiPost<{ reply: string }>('/api/chat', {
        message: content,
        sessionId: 'local',
        language: data?.settings?.app?.language || 'pt-BR',
      })
      setMessages((current) => [...current, { role: 'assistant', text: response.reply || 'Sem resposta.' }])
      setMood('idle')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Falha no chat.'
      setMessages((current) => [...current, { role: 'assistant', text: message }])
      setMood('error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <ScreenShell
      title="Chat"
      subtitle="Conversa principal do BMO com suporte a anexos e resposta do motor local."
      actions={headerActions}
    >
      <div className="chat-layout">
        <div className="chat-thread">
          {messages.map((message, index) => (
            <article key={`${message.role}-${index}`} className={`chat-bubble ${message.role}`}>
              <span>{message.role === 'user' ? 'Voce' : 'BMO'}</span>
              <p>{message.text}</p>
            </article>
          ))}
        </div>

        <div className="chat-composer">
          <div className="composer-hint">
            <Sparkles size={16} />
            <span>Escreva uma mensagem real para testar o motor e a chave do provedor.</span>
          </div>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Digite uma mensagem..."
            rows={4}
          />
          <div className="composer-actions">
            <button className="primary" onClick={() => void send()} disabled={busy || !text.trim()}>
              <SendHorizontal size={16} /> {busy ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </div>
      </div>
    </ScreenShell>
  )
}
