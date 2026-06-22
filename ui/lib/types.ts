export type PanelId =
  | 'Chat'
  | 'Memoria'
  | 'Historico'
  | 'Modelos'
  | 'Provedores'
  | 'Voz'
  | 'Ferramentas'
  | 'Workspace'
  | 'Skills'
  | 'Canais'
  | 'Sistema'
  | 'Configuracoes'

export type AvatarMood = 'idle' | 'listening' | 'thinking' | 'speaking' | 'error'

export interface VoiceModel {
  file: string
  label: string
  language: string
  path: string
  exists?: boolean
}

export interface ChannelItem {
  id: string
  label: string
  enabled?: boolean
  configured?: boolean
  status?: string
}

export interface SkillItem {
  id: string
  name: string
  description?: string
  path?: string
  scope?: string
}

export interface MemoryItem {
  id: string
  text: string
  source?: string
}

export interface HistorySession {
  id: string
  title: string
  preview?: string
  createdAt?: number
  updatedAt?: number
}

export interface WorkspaceItem {
  name: string
  path: string
  is_dir: boolean
  size: number
  modified: number
  category: string
}

export interface SubagentItem {
  id: string
  title: string
  status?: string
  progress?: number
  result?: string
  error?: string
  outputPath?: string
}

export interface TaskItem {
  id: string
  title: string
  status?: string
  createdAt?: number
  result?: string
}

export interface ReminderItem {
  id: string
  text: string
  dueAt?: number
  status?: string
}

export interface ToolItem {
  name: string
  category?: string
  description?: string
}

export interface SettingsState {
  app?: {
    language?: string
    theme?: string
    chatFontScale?: number
    hotkey?: string
    voice?: {
      enabled?: boolean
      model?: string
    }
  }
  provider?: {
    name?: string
    model?: string
    apiKey?: string
    apiBase?: string
  }
  whisper?: {
    gpu_enabled?: boolean
    gpu_index?: number
    model?: string
    fallback_to_cpu?: boolean
  }
}

export interface SystemState {
  backend?: boolean
  piper?: boolean
  whisper?: boolean
  wakeword?: {
    enabled?: boolean
    available?: boolean
    dependency?: boolean
    running?: boolean
    eventId?: number
    model?: string
    message?: string
    lastError?: string
  }
  runtime?: {
    ready?: boolean
    error?: string
    toolCount?: number
    provider?: string
    model?: string
  }
  provider?: { ok?: boolean; name?: string; model?: string }
  voice?: { enabled?: boolean; model?: string; models?: VoiceModel[] }
  diagnostic?: {
    provider?: { ok?: boolean; name?: string; model?: string }
    voices?: { ok?: boolean; count?: number }
    memory?: { ok?: boolean; path?: string }
    history?: { ok?: boolean; count?: number }
    skills?: { ok?: boolean; count?: number }
    channels?: { ok?: boolean; items?: ChannelItem[] }
    workspace?: { ok?: boolean; path?: string }
  }
  summary?: { memory?: number; history?: number; skills?: number; channels?: number; tools?: number }
}

export interface BootstrapData {
  settings: SettingsState
  system: SystemState
  voices: { voices: VoiceModel[]; selected?: string }
  channels: { channels: ChannelItem[] }
  skills: { skills: SkillItem[] }
  memory: { items: MemoryItem[] }
  history: { sessions: HistorySession[] }
  reminders: { items: ReminderItem[] }
  subagents: { items: SubagentItem[]; busy?: boolean }
  tasks: { items: TaskItem[] }
  tools: { tools: ToolItem[]; runtimeTools?: string[] }
  workspace: { path: string; items: WorkspaceItem[] }
  logs: { lines: string[] }
}
