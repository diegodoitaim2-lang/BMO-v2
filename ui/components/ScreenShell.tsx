import type { ReactNode } from 'react'

interface ScreenShellProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
}

export function ScreenShell({ title, subtitle, actions, children }: ScreenShellProps) {
  return (
    <section className="screen-shell">
      <header className="screen-header">
        <div>
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {actions && <div className="screen-actions">{actions}</div>}
      </header>
      <div className="screen-body">{children}</div>
    </section>
  )
}
