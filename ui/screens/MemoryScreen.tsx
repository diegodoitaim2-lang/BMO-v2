import { useMemo, useState } from 'react'
import { Database, Download, Plus, RotateCcw, Trash2 } from 'lucide-react'
import { apiPost } from '../lib/api'
import { saveTextFile } from '../lib/fileExport'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface MemoryScreenProps {
  data: BootstrapData | null
  onRefresh?: () => Promise<void> | void
}

function previewText(text: string, limit = 260): string {
  const normalized = text.replace(/\s+/g, ' ').trim()
  if (normalized.length <= limit) {
    return normalized
  }
  return `${normalized.slice(0, limit).trim()}...`
}

export function MemoryScreen({ data, onRefresh }: MemoryScreenProps) {
  const items = useMemo(() => data?.memory.items || [], [data?.memory.items])
  const [query, setQuery] = useState('')
  const [draft, setDraft] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase()
    if (!search) {
      return items
    }
    return items.filter((item) => {
      const haystack = [item.id, item.source, item.text].filter(Boolean).join(' ').toLowerCase()
      return haystack.includes(search)
    })
  }, [items, query])

  async function refresh() {
    await onRefresh?.()
  }

  async function saveMemory() {
    const text = draft.trim()
    if (!text || busy) return
    setBusy(true)
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/memory', {
        action: 'add',
        text,
      })
      if (!response.ok) {
        setMessage(response.message || 'Nao consegui salvar a memoria.')
        return
      }
      setDraft('')
      setMessage('Memoria salva.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao salvar a memoria.')
    } finally {
      setBusy(false)
    }
  }

  async function exportMemory() {
    try {
      const response = await apiPost<{ ok: boolean; filename: string; content: string; mime: string }>('/api/memory', {
        action: 'export',
      })
      if (!response.ok) {
        setMessage('Nao consegui exportar a memoria.')
        return
      }
      const result = await saveTextFile({
        defaultPath: response.filename,
        content: response.content,
        label: 'JSON',
        extensions: ['json'],
        mime: response.mime,
      })
      setMessage(result.ok ? `Backup salvo em ${result.path || response.filename}.` : result.error || 'Backup nao salvo.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao exportar a memoria.')
    }
  }

  async function clearMemory() {
    if (!window.confirm('Limpar a memoria salva agora?')) return
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/memory', {
        action: 'clear',
      })
      setMessage(response.ok ? 'Memoria limpa.' : response.message || 'Nao consegui limpar a memoria.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao limpar a memoria.')
    }
  }

  async function deleteMemory(id: string) {
    if (!window.confirm('Excluir este item de memoria?')) return
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/memory', {
        action: 'delete',
        id,
      })
      setMessage(response.ok ? 'Item removido.' : response.message || 'Nao consegui remover o item.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao remover a memoria.')
    }
  }

  return (
    <ScreenShell
      title="Memoria"
      subtitle="Guarde lembrancas, revise os arquivos base e exporte um backup quando precisar."
      actions={<button onClick={() => void refresh()}><RotateCcw size={16} /> Atualizar</button>}
    >
      <div className="settings-form">
        <label>
          Buscar memoria
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Procure por texto, origem ou id..." />
        </label>
        <label>
          Nova memoria
          <textarea
            rows={4}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Escreva aqui algo importante para o BMO lembrar depois."
          />
        </label>
        <div className="button-row">
          <button className="primary" onClick={() => void saveMemory()} disabled={busy || !draft.trim()}>
            <Plus size={16} /> {busy ? 'Salvando...' : 'Salvar memoria'}
          </button>
          <button onClick={() => void exportMemory()}>
            <Download size={16} /> Exportar backup
          </button>
          <button onClick={() => void clearMemory()}>
            <Trash2 size={16} /> Limpar itens salvos
          </button>
        </div>
        {message && <p className="result-text">{message}</p>}
      </div>

      <div className="card-grid">
        {filtered.length ? (
          filtered.map((item) => (
            <article key={item.id} className="data-card">
              <h3>{item.id}</h3>
              <p>{previewText(item.text)}</p>
              <details>
                <summary>Ver texto completo</summary>
                <pre>{item.text}</pre>
              </details>
              <div className="button-row">
                <small>{item.source || 'memory.json'}</small>
                {item.editable ? (
                  <button className="danger" onClick={() => void deleteMemory(item.id)}>
                    <Trash2 size={14} /> Excluir
                  </button>
                ) : (
                  <small>Somente leitura</small>
                )}
              </div>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <Database size={20} />
            <p>Nenhuma memoria encontrada com esse filtro.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
