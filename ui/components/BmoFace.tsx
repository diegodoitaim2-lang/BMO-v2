import { useEffect, useMemo, useState } from 'react'
import type { AvatarMood } from '../lib/types'

import idleFace from '../assets/faces/idle.png'
import listeningFace from '../assets/faces/listening.png'
import thinkingFace from '../assets/faces/thinking.png'
import speakingFace01 from '../assets/faces/speaking-01.png'
import speakingFace02 from '../assets/faces/speaking-02.png'
import speakingFace03 from '../assets/faces/speaking-03.png'
import errorFace from '../assets/faces/error.png'

const atlasModules = import.meta.glob('../assets/bmo_faces/**/*.{png,jpg,jpeg,webp}', {
  eager: true,
  import: 'default',
}) as Record<string, string>

type FaceFrame = { file: string; src: string }

const atlasByState = Object.entries(atlasModules).reduce<Record<string, FaceFrame[]>>((acc, [path, src]) => {
  const match = path.match(/^\.\.\/assets\/bmo_faces\/([^/]+)\/(.+)$/i)
  if (!match) return acc
  const [, state, file] = match
  if (!acc[state]) {
    acc[state] = []
  }
  acc[state].push({ file, src })
  return acc
}, {})

for (const state of Object.keys(atlasByState)) {
  atlasByState[state].sort((left, right) => left.file.localeCompare(right.file, 'en', { numeric: true, sensitivity: 'base' }))
}

function resolveFrames(state: string, fallback: string[]) {
  const frames = atlasByState[state]?.map((frame) => frame.src) ?? []
  return frames.length > 0 ? frames : fallback
}

const framesByMood: Record<AvatarMood, string[]> = {
  warmup: resolveFrames('warmup', [listeningFace]),
  idle: resolveFrames('idle', [idleFace]),
  listening: resolveFrames('listening', [listeningFace]),
  thinking: resolveFrames('thinking', [thinkingFace]),
  speaking: resolveFrames('speaking', [speakingFace01, speakingFace02, speakingFace03, speakingFace02]),
  error: resolveFrames('error', [errorFace]),
}

const frameDelayByMood: Record<AvatarMood, number> = {
  warmup: 220,
  idle: 0,
  listening: 0,
  thinking: 360,
  speaking: 180,
  error: 0,
}

interface BmoFaceProps {
  mood: AvatarMood
  alt?: string
  className?: string
  animate?: boolean
}

export function BmoFace({ mood, alt = '', className, animate = true }: BmoFaceProps) {
  const frames = useMemo(() => framesByMood[mood] || framesByMood.idle, [mood])
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!animate || frames.length <= 1) return
    const delay = frameDelayByMood[mood] || 240
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % frames.length)
    }, delay)
    return () => window.clearInterval(timer)
  }, [animate, frames, mood])

  const frameIndex = frames.length > 0 ? index % frames.length : 0

  return <img className={className} src={frames[frameIndex] || frames[0]} alt={alt} />
}
