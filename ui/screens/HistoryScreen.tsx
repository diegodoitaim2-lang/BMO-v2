import { useMemo, useState } from 'react'
import { Archive, Download, RotateCcw, Search, Trash2 } from 'lucide-react'
import { apiPost } from '../lib/api'
import { saveTextFile } from '../lib/fileExport'
import type { BootstrapData, HistorySession } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface HistoryScreenProps {
  data: BootstrapData | null
  onRefresh?: () => Promise<void> | void
}

function formatDate(timestamp?: number): string {
  return timestamp ? new Date(timestamp * 1000).toLocaleString() : 'sem data'
}

function sessionText(session: HistorySession): string {
  const messages = session.messages || []
  const lines = [
    `# ${session.title || session.id}`,
    session.preview ? `Resumo: ${session.preview}` : '',
    session.createdAt ? `Criado em: ${formatDate(session.createdAt)}` : '',
    session.updatedAt ? `Atualizado em: ${formatDate(session.updatedAt)}` : '',
    '',
  ].filter(Boolean)
  for (const message of messages) {
    lines.push(`${message.role}: ${message.text}`)
  }
  return lines.join('\n').trim()
}

export function HistoryScreen({ data, onRefresh }: HistoryScreenProps) {
  const sessions = useMemo(() => data?.history.sessions || [], [data?.history.sessions])
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState('')

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase()
    const sorted = [...sessions].sort((left, right) => (right.updatedAt || right.createdAt || 0) - (left.updatedAt || left.createdAt || 0))
    if (!search) return sorted
    return sorted.filter((session) => {
      const haystack = [
        session.id,
        session.title,
        session.preview,
        session.messages?.map((item) => item.text).join(' '),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(search)
    })
  }, [query, sessions])

  async function refresh() {
    await onRefresh?.()
  }

  async function exportHistory(format: 'json' | 'txt' | 'md', sessionId?: string) {
    try {
      const response = await apiPost<{ ok: boolean; filename: string; content: string; mime: string }>('/api/history/export', {
        sessionId: sessionId || null,
        format,
      })
      if (!response.ok) {
        setMessage('Nao consegui exportar o historico.')
        return
      }
      const result = await saveTextFile({
        defaultPath: response.filename,
        content: response.content,
        label: format === 'md' ? 'Markdown' : format.toUpperCase(),
        extensions: [format],
        mime: response.mime,
      })
      setMessage(result.ok ? `Historico exportado em ${result.path || response.filename}.` : result.error || 'Exportacao cancelada.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao exportar o historico.')
    }
  }

  async function deleteSession(id: string) {
    if (!window.confirm('Excluir esta conversa do historico?')) return
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/history', {
        action: 'delete',
        id,
      })
      setMessage(response.ok ? 'Conversa excluida.' : response.message || 'Nao consegui excluir a conversa.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao excluir a conversa.')
    }
  }

  async function clearHistory() {
    if (!window.confirm('Apagar todo o historico de conversas?')) return
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/history', {
        action: 'clear',
      })
      setMessage(response.ok ? 'Historico limpo.' : response.message || 'Nao consegui limpar o historico.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao limpar o historico.')
    }
  }

  return (
    <ScreenShell
      title="Historico"
      subtitle="Busque conversas passadas, exporte em varios formatos e remova o que nao precisa mais."
      actions={<button onClick={() => void refresh()}><RotateCcw size={16} /> Atualizar</button>}
    >
      <div className="settings-form">
        <label>
          Buscar historico
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Procure por titulo, resumo ou texto..." />
        </label>
        <div className="button-row">
          <button onClick={() => void exportHistory('json')}>
            <Download size={16} /> Exportar JSON
          </button>
          <button onClick={() => void exportHistory('txt')}>
            <Archive size={16} /> Exportar TXT
          </button>
          <button onClick={() => void exportHistory('md')}>
            <Archive size={16} /> Exportar Markdown
          </button>
          <button onClick={() => void clearHistory()}>
            <Trash2 size={16} /> Limpar historico
          </button>
        </div>
        {message && <p className="result-text">{message}</p>}
      </div>

      <div className="card-grid">
        {filtered.length ? (
          filtered.map((session) => (
            <article key={session.id} className="data-card">
              <h3>{session.title}</h3>
              <p>{session.preview || 'Sem resumo'}</p>
              <small>
                {formatDate(session.updatedAt || session.createdAt)}
                {session.messages?.length ? ` - ${session.messages.length} mensagens` : ''}
              </small>
              <div className="button-row">
                <button onClick={() => void exportHistory('md', session.id)}>
                  <Download size={14} /> Exportar conversa
                </button>
                <button onClick={() => void deleteSession(session.id)}>
                  <Trash2 size={14} /> Excluir
                </button>
              </div>
              <details>
                <summary>Ver detalhes</summary>
                <pre>{sessionText(session)}</pre>
              </details>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <Search size={20} />
            <p>Nenhuma conversa encontrada com esse filtro.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
