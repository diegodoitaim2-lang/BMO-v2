import type { AvatarMood } from '../lib/types'
import appIcon from '../assets/bmo/bmo-icon.png'

interface BmoAvatarProps {
  mood: AvatarMood
  label?: string
}

export function BmoAvatar({ mood, label }: BmoAvatarProps) {
  return (
    <div className={`bmo-avatar mood-${mood}`}>
      <img className="bmo-avatar-face" src={appIcon} alt={label || 'BMO'} />
      {label && <span>{label}</span>}
    </div>
  )
}
