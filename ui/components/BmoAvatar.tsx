import idleFace from '../assets/faces/idle.png'
import listeningFace from '../assets/faces/listening.png'
import thinkingFace from '../assets/faces/thinking.png'
import speakingFace from '../assets/faces/speaking-01.png'
import errorFace from '../assets/faces/error.png'
import type { AvatarMood } from '../lib/types'

const FACE_BY_MOOD: Record<AvatarMood, string> = {
  idle: idleFace,
  listening: listeningFace,
  thinking: thinkingFace,
  speaking: speakingFace,
  error: errorFace,
}

interface BmoAvatarProps {
  mood: AvatarMood
  label?: string
}

export function BmoAvatar({ mood, label }: BmoAvatarProps) {
  return (
    <div className={`bmo-avatar mood-${mood}`}>
      <img src={FACE_BY_MOOD[mood]} alt={label || mood} />
      {label && <span>{label}</span>}
    </div>
  )
}
