import { useMemo, useState } from 'react'
import { FolderOpen, RotateCcw } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface WorkspaceScreenProps {
  data: BootstrapData | null
  onRefresh?: () => Promise<void> | void
}

export function WorkspaceScreen({ data, onRefresh }: WorkspaceScreenProps) {
  const items = useMemo(() => data?.workspace.items || [], [data?.workspace.items])
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase()
    if (!search) {
      return [...items].sort((left, right) => Number(right.is_dir) - Number(left.is_dir) || right.modified - left.modified)
    }
    return items
      .filter((item) => {
        const haystack = [item.name, item.path, item.category].join(' ').toLowerCase()
        return haystack.includes(search)
      })
      .sort((left, right) => Number(right.is_dir) - Number(left.is_dir) || right.modified - left.modified)
  }, [items, query])

  return (
    <ScreenShell
      title="Workspace"
      subtitle="Explorador local para arquivos, pastas e resultados gerados pelo BMO."
      actions={<button onClick={() => void onRefresh?.()}><RotateCcw size={16} /> Atualizar</button>}
    >
      <div className="settings-form">
        <label>
          Buscar arquivo
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filtre por nome, caminho ou categoria..." />
        </label>
        <p className="result-text">{data?.workspace.path || 'Workspace indisponivel no momento.'}</p>
      </div>

      <div className="workspace-list">
        {filtered.length ? (
          filtered.map((item) => (
            <article key={item.path} className="workspace-item">
              <div>
                <strong>{item.name}</strong>
                <p>{item.path}</p>
                <small>{item.category}</small>
              </div>
              <small>{item.is_dir ? 'pasta' : `${item.size} bytes`}</small>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <FolderOpen size={20} />
            <p>Nenhum arquivo encontrado com esse filtro.</p>
          </div>
        )}
      </div>
      <article className="data-card">
        <h3>Como ele cresce</h3>
        <p>O workspace vai se enchendo conforme voce cria memorias, skills e resultados de tarefa.</p>
      </article>
    </ScreenShell>
  )
}
