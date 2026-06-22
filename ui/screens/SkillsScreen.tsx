import { Sparkles } from 'lucide-react'
import type { BootstrapData } from '../lib/types'
import { ScreenShell } from '../components/ScreenShell'

interface SkillsScreenProps {
  data: BootstrapData | null
}

export function SkillsScreen({ data }: SkillsScreenProps) {
  const skills = data?.skills.skills || []
  return (
    <ScreenShell title="Skills" subtitle="Skills internas e do workspace.">
      <div className="card-grid">
        {skills.map((skill) => (
          <article key={skill.id} className="data-card">
            <h3>{skill.name}</h3>
            <p>{skill.description || 'Sem descricao'}</p>
            <small>{skill.scope || 'builtin'}</small>
          </article>
        ))}
        {!skills.length && (
          <div className="empty-state">
            <Sparkles size={20} />
            <p>Nenhuma skill encontrada.</p>
          </div>
        )}
      </div>
    </ScreenShell>
  )
}
