interface Window {
  bmoDesktop?: {
    saveFile: (options: {
      defaultPath: string
      content: string
      filters?: Array<{ name: string; extensions: string[] }>
    }) => Promise<{ ok: boolean; path?: string; error?: string }>
    getBmoToken: () => Promise<string>
  }
}
