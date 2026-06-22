import { useMemo, useState } from 'react'
import { Bot, Bell, CheckCircle2, Clock3, RotateCcw, Sparkles, Trash2 } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface ToolsScreenProps {
  data: BootstrapData | null
  onRefresh?: () => Promise<void> | void
}

function formatTime(timestamp?: number): string {
  if (!timestamp) return 'sem data'
  return new Date(timestamp * 1000).toLocaleString()
}

export function ToolsScreen({ data, onRefresh }: ToolsScreenProps) {
  const tools = data?.tools.tools || []
  const runtimeTools = data?.tools.runtimeTools || []
  const reminders = useMemo(() => [...(data?.reminders.items || [])].sort((left, right) => (left.dueAt || 0) - (right.dueAt || 0)), [data?.reminders.items])
  const subagents = useMemo(() => [...(data?.subagents.items || [])].sort((left, right) => (right.startedAt || 0) - (left.startedAt || 0)), [data?.subagents.items])
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [reminderText, setReminderText] = useState('')
  const [reminderMinutes, setReminderMinutes] = useState('30')
  const [subagentTask, setSubagentTask] = useState('')

  async function refresh() {
    await onRefresh?.()
  }

  async function createReminder() {
    const text = reminderText.trim()
    const minutes = Number(reminderMinutes || '0')
    if (!text || busy) return
    setBusy(true)
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/reminders', {
        action: 'add',
        text,
        afterMinutes: Number.isFinite(minutes) && minutes > 0 ? minutes : 30,
      })
      if (!response.ok) {
        setMessage(response.message || 'Nao consegui criar o lembrete.')
        return
      }
      setReminderText('')
      setMessage('Lembrete criado.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao criar o lembrete.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteReminder(id: string) {
    if (!window.confirm('Excluir este lembrete?')) return
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/reminders', {
        action: 'remove',
        id,
      })
      setMessage(response.ok ? 'Lembrete removido.' : response.message || 'Nao consegui remover o lembrete.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao remover o lembrete.')
    }
  }

  async function clearReminders() {
    if (!window.confirm('Remover todos os lembretes agendados?')) return
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/reminders', {
        action: 'clear',
      })
      setMessage(response.ok ? 'Lembretes limpos.' : response.message || 'Nao consegui limpar os lembretes.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao limpar os lembretes.')
    }
  }

  async function createSubagent() {
    const task = subagentTask.trim()
    if (!task || busy) return
    setBusy(true)
    try {
      const response = await apiPost<{ ok: boolean; message?: string }>('/api/subagents', {
        action: 'spawn',
        task,
      })
      if (!response.ok) {
        setMessage(response.message || 'Nao consegui criar o subagente.')
        return
      }
      setSubagentTask('')
      setMessage('Subagente iniciado.')
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao criar o subagente.')
    } finally {
      setBusy(false)
    }
  }

  const runningCount = subagents.length

  return (
    <ScreenShell
      title="Ferramentas"
      subtitle="Ferramentas herdadas do nanobot, lembretes ativos e subagentes em execucao."
      actions={<button onClick={() => void refresh()}><RotateCcw size={16} /> Atualizar</button>}
    >
      <div className="card-grid">
        <article className="data-card">
          <h3>Ferramentas reais do runtime</h3>
          <p>{runtimeTools.length} ferramentas expostas pelo motor.</p>
          <small>{runtimeTools.length ? runtimeTools.join(', ') : 'Nenhuma ferramenta runtime reportada ainda.'}</small>
        </article>
        <article className="data-card">
          <h3>Lembretes</h3>
          <p>{reminders.length} agendados agora.</p>
          <small>Crie lembretes pela tela ou pelo chat.</small>
        </article>
        <article className="data-card">
          <h3>Subagentes</h3>
          <p>{runningCount} em execucao no momento.</p>
          <small>{data?.subagents.busy ? 'O motor esta processando tarefas paralelas.' : 'Nenhum subagente rodando agora.'}</small>
        </article>
      </div>

      <div className="settings-form">
        <label>
          Novo lembrete
          <textarea
            rows={3}
            value={reminderText}
            onChange={(event) => setReminderText(event.target.value)}
            placeholder="Exemplo: lembrar de revisar o teste do Checkpoint C."
          />
        </label>
        <label>
          Agendar em minutos
          <input
            type="number"
            min="1"
            value={reminderMinutes}
            onChange={(event) => setReminderMinutes(event.target.value)}
            placeholder="30"
          />
        </label>
        <div className="button-row">
          <button className="primary" onClick={() => void createReminder()} disabled={busy || !reminderText.trim()}>
            <Bell size={16} /> {busy ? 'Salvando...' : 'Criar lembrete'}
          </button>
          <button onClick={() => void clearReminders()}>
            <Trash2 size={16} /> Limpar lembretes
          </button>
        </div>
      </div>

      <div className="settings-form">
        <label>
          Nova tarefa de subagente
          <textarea
            rows={4}
            value={subagentTask}
            onChange={(event) => setSubagentTask(event.target.value)}
            placeholder="Exemplo: revisar a tela de Configuracoes e apontar ajustes visuais."
          />
        </label>
        <div className="button-row">
          <button className="primary" onClick={() => void createSubagent()} disabled={busy || !subagentTask.trim()}>
            <Sparkles size={16} /> {busy ? 'Criando...' : 'Criar subagente'}
          </button>
        </div>
      </div>

      {message && <p className="result-text">{message}</p>}

      <div className="card-grid">
        {reminders.map((item) => (
          <article key={item.id} className="data-card">
            <h3>{item.name || item.id}</h3>
            <p>{item.text}</p>
            <small>
              {item.schedule || 'agendado'}
              {item.dueAt ? ` - ${formatTime(item.dueAt)}` : ''}
            </small>
            <div className="status-row">
              <span className="status-pill good">{item.status || 'ativo'}</span>
              {item.deliver ? <span className="status-pill good">entrega ligada</span> : <span className="status-pill bad">sem entrega</span>}
            </div>
            <div className="button-row">
              <button className="danger" onClick={() => void deleteReminder(item.id)}>
                <Trash2 size={14} /> Excluir
              </button>
            </div>
          </article>
        ))}
        {!reminders.length && (
          <div className="empty-state">
            <Clock3 size={20} />
            <p>Nenhum lembrete agendado ainda.</p>
          </div>
        )}
      </div>

      <div className="card-grid">
        {subagents.map((item) => (
          <article key={item.id} className="data-card">
            <h3>{item.title}</h3>
            <p>{item.status || 'em andamento'}</p>
            <small>
              {item.iteration ? `Iteracao ${item.iteration}` : 'Sem iteracao ainda'}
              {item.startedAt ? ` - ${formatTime(item.startedAt)}` : ''}
            </small>
            {item.error ? <p className="result-text">{item.error}</p> : null}
            {item.result ? <small>{item.result}</small> : null}
          </article>
        ))}
        {!subagents.length && (
          <div className="empty-state">
            <CheckCircle2 size={20} />
            <p>Nenhum subagente rodando no momento.</p>
          </div>
        )}
      </div>

      <div className="card-grid">
        {tools.map((tool) => (
          <article key={tool.name} className="data-card">
            <h3>{tool.name}</h3>
            <p>{tool.description}</p>
            <small>{tool.category}</small>
          </article>
        ))}
        {!tools.length && (
          <div className="empty-state">
            <Bot size={20} />
            <p>Nenhuma ferramenta catalogada ainda.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
