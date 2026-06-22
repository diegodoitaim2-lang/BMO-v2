import { useMemo, useState } from 'react'
import { Plus, RotateCcw, Search } from 'lucide-react'
import { apiPost } from '../lib/api'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface SkillsScreenProps {
  data: BootstrapData | null
  onRefresh?: () => Promise<void> | void
}

export function SkillsScreen({ data, onRefresh }: SkillsScreenProps) {
  const skills = useMemo(() => data?.skills.skills || [], [data?.skills.skills])
  const [query, setQuery] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase()
    if (!search) {
      return skills
    }
    return skills.filter((skill) => {
      const haystack = [skill.id, skill.name, skill.description, skill.path, skill.scope].filter(Boolean).join(' ').toLowerCase()
      return haystack.includes(search)
    })
  }, [query, skills])

  async function refresh() {
    await onRefresh?.()
  }

  async function createSkill() {
    const skillName = name.trim()
    if (!skillName || busy) return
    setBusy(true)
    try {
      const response = await apiPost<{ ok: boolean; message?: string; skill?: { path?: string } }>('/api/skills', {
        name: skillName,
        description: description.trim(),
      })
      if (!response.ok) {
        setMessage(response.message || 'Nao consegui criar a skill.')
        return
      }
      setName('')
      setDescription('')
      setMessage(`Skill criada em ${response.skill?.path || 'workspace/skills'}.`)
      await refresh()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Falha ao criar a skill.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <ScreenShell
      title="Skills"
      subtitle="Veja as skills internas e crie novas skills no workspace."
      actions={<button onClick={() => void refresh()}><RotateCcw size={16} /> Atualizar</button>}
    >
      <div className="settings-form">
        <label>
          Buscar skills
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Procure por nome, caminho ou descricao..." />
        </label>
        <label>
          Nome da nova skill
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Ex: resumo de emails" />
        </label>
        <label>
          Descricao
          <textarea
            rows={4}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Explique rapidamente quando o BMO deve usar esta skill."
          />
        </label>
        <div className="button-row">
          <button className="primary" onClick={() => void createSkill()} disabled={busy || !name.trim()}>
            <Plus size={16} /> {busy ? 'Criando...' : 'Criar skill'}
          </button>
        </div>
        {message && <p className="result-text">{message}</p>}
      </div>

      <div className="card-grid">
        {filtered.length ? (
          filtered.map((skill) => (
            <article key={skill.id} className="data-card">
              <h3>{skill.name}</h3>
              <p>{skill.description || 'Sem descricao'}</p>
              <small>{skill.scope || 'builtin'}</small>
              {skill.path && <p>{skill.path}</p>}
            </article>
          ))
        ) : (
          <div className="empty-state">
            <Search size={20} />
            <p>Nenhuma skill encontrada com esse filtro.</p>
          </div>
        )}
        <article className="data-card">
          <h3>Skills do workspace</h3>
          <p>As skills criadas aqui ficam no workspace e aparecem no motor automaticamente.</p>
        </article>
      </div>
    </ScreenShell>
  )
}
