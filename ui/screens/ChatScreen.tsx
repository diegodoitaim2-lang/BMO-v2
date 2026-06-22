import { useState } from 'react'
import { Mic, Paperclip, SendHorizontal, Sparkles } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { AvatarMood, BootstrapData } from '../lib/types'
import { BmoFace } from '../components/BmoFace'
import bmoBody from '../assets/bmo/bmo-body-cropped.png'

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
}

interface ChatScreenProps {
  data: BootstrapData | null
  loading?: boolean
  setMood: (mood: AvatarMood) => void
}

export function ChatScreen({ data, loading = false, setMood }: ChatScreenProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Pronto para conversar. Configure um provedor se ainda nao estiver ativo.' },
  ])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [composerFocused, setComposerFocused] = useState(false)

  const sceneMood: AvatarMood = loading ? 'warmup' : busy ? 'thinking' : composerFocused ? 'listening' : 'idle'

  async function send() {
    const content = text.trim()
    if (!content || busy || loading) return

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
      setMood(composerFocused ? 'listening' : 'idle')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Falha no chat.'
      setMessages((current) => [...current, { role: 'assistant', text: message }])
      setMood('error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat-stage">
      <div className="bmo-hero">
        <div className={`bmo-character state-${sceneMood} bmo-character-center`}>
          <div className="bmo-glow" />
          <img className="bmo-body" src={bmoBody} alt="BMO" />
          <div className="bmo-screen-face">
            <BmoFace key={sceneMood} mood={sceneMood} className="bmo-face" alt="" />
          </div>
        </div>
        {busy && (
          <div className="thinking-loader chat-thinking-loader">
            <span />
            <span />
            <span />
            <span>BMO esta pensando...</span>
          </div>
        )}
        {loading && (
          <div className="thinking-loader chat-thinking-loader">
            <span />
            <span />
            <span />
            <span>Acordando o BMO...</span>
          </div>
        )}
      </div>

      <section className="chat-box">
        <div className="messages-scroll">
          <div className="messages">
            {messages.map((message, index) => (
              <div className={`message ${message.role}`} key={`${message.role}-${index}`}>
                <span>{message.role === 'user' ? 'Voce' : 'BMO'}</span>
                <p>{message.text}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="input-row">
          <div className="composer">
            <button className={busy ? 'active-tool' : ''} type="button" onClick={() => setMood('listening')} disabled={loading}>
              <Mic size={20} />
            </button>
            <button type="button" disabled={loading} aria-label="Anexar arquivo">
              <Paperclip size={20} />
            </button>
            <textarea
              value={text}
              placeholder="Digite sua mensagem para o BMO..."
              onChange={(event) => setText(event.target.value)}
              onFocus={() => {
                setComposerFocused(true)
                setMood(busy ? 'thinking' : 'listening')
              }}
              onBlur={() => {
                setComposerFocused(false)
                if (!busy && !loading) {
                  setMood('idle')
                }
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  void send()
                }
              }}
              disabled={loading}
            />
            <button type="button" className="send-button" onClick={() => void send()} disabled={busy || loading || !text.trim()}>
              <SendHorizontal size={21} />
            </button>
          </div>

          <div className="composer-hint">
            <Sparkles size={16} />
            <span>Escreva uma mensagem real para testar o motor e a chave do provedor.</span>
          </div>
        </div>
      </section>
    </div>
  )
}
