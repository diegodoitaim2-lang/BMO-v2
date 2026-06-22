type SaveFileOptions = {
  defaultPath: string
  content: string
  label: string
  extensions: string[]
  mime?: string
}

export async function saveTextFile(options: SaveFileOptions): Promise<{ ok: boolean; path?: string; error?: string }> {
  if (typeof window !== 'undefined' && window.bmoDesktop?.saveFile) {
    return window.bmoDesktop.saveFile({
      defaultPath: options.defaultPath,
      content: options.content,
      filters: [{ name: options.label, extensions: options.extensions }],
    })
  }

  const blob = new Blob([options.content], { type: options.mime || 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = options.defaultPath
  link.click()
  URL.revokeObjectURL(url)
  return { ok: true, path: options.defaultPath }
}
