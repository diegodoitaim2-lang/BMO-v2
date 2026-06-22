interface StatusPillProps {
  label: string
  ok?: boolean
}

export function StatusPill({ label, ok }: StatusPillProps) {
  return <span className={`status-pill ${ok === false ? 'bad' : 'good'}`}>{label}</span>
}
