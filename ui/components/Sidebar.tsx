import { Bot, Brain, BookOpen, Database, FolderOpen, History, Monitor, Puzzle, Settings, Sparkles, SlidersHorizontal, Mic, MessageSquareText } from 'lucide-react'
import type { AvatarMood, PanelId, SystemState } from '../lib/types'
import { BmoAvatar } from './BmoAvatar'

const icons = {
  Chat: MessageSquareText,
  Memoria: Database,
  Historico: History,
  Modelos: Brain,
  Provedores: SlidersHorizontal,
  Voz: Mic,
  Ferramentas: Puzzle,
  Workspace: FolderOpen,
  Skills: Sparkles,
  Canais: BookOpen,
  Sistema: Monitor,
  Configuracoes: Settings,
}

interface NavItem {
  id: PanelId
  label: string
}

interface SidebarProps {
  navItems: NavItem[]
  active: PanelId
  onSelect: (id: PanelId) => void
  mood: AvatarMood
  system?: SystemState | null
}

export function Sidebar({ navItems, active, onSelect, mood, system }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <BmoAvatar mood={mood} label={system?.runtime?.ready ? 'BMO online' : 'BMO'} />
        <div>
          <strong>BMO-V2</strong>
          <p>{system?.runtime?.ready ? 'Motor local pronto' : 'Aguardando configuracao'}</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = icons[item.id] || Bot
          const isActive = active === item.id
          return (
            <button key={item.id} className={`nav-item ${isActive ? 'active' : ''}`} onClick={() => onSelect(item.id)}>
              <Icon size={16} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-stat">
          <span>Provider</span>
          <strong>{system?.provider?.name || 'nao definido'}</strong>
        </div>
        <div className="sidebar-stat">
          <span>Modelo</span>
          <strong>{system?.provider?.model || 'nenhum'}</strong>
        </div>
      </div>
    </aside>
  )
}
