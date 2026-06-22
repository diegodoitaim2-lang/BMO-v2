import { FolderOpen } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface WorkspaceScreenProps {
  data: BootstrapData | null
}

export function WorkspaceScreen({ data }: WorkspaceScreenProps) {
  const items = data?.workspace.items || []
  return (
    <ScreenShell title="Workspace" subtitle="Explorador local para arquivos e resultados.">
      <div className="workspace-list">
        {items.length ? (
          items.map((item) => (
            <article key={item.path} className="workspace-item">
              <div>
                <strong>{item.name}</strong>
                <p>{item.path}</p>
              </div>
              <small>{item.is_dir ? 'pasta' : `${item.size} bytes`}</small>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <FolderOpen size={20} />
            <p>Workspace vazio por enquanto.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
