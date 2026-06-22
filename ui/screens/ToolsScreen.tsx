import { Bot } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface ToolsScreenProps {
  data: BootstrapData | null
}

export function ToolsScreen({ data }: ToolsScreenProps) {
  const tools = data?.tools.tools || []
  const runtimeTools = data?.tools.runtimeTools || []
  return (
    <ScreenShell title="Ferramentas" subtitle="Ferramentas herdadas do nanobot e tarefas paralelas.">
      <div className="card-grid">
        {tools.map((tool) => (
          <article key={tool.name} className="data-card">
            <h3>{tool.name}</h3>
            <p>{tool.description}</p>
            <small>{tool.category}</small>
          </article>
        ))}
        <div className="empty-state">
          <Bot size={20} />
          <p>{runtimeTools.length} ferramentas expostas pelo runtime.</p>
        </div>
      </div>
    </ScreenShell>
  )
}
