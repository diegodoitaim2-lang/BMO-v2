const API_BASE = import.meta.env.VITE_BMO_API_BASE || 'http://127.0.0.1:8787'

function extractMessage(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') {
    return undefined
  }

  const record = payload as Record<string, unknown>
  const message = record.message
  if (typeof message === 'string' && message.trim()) {
    return message
  }

  const detail = record.detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  return undefined
}

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text) as unknown
    } catch {
      payload = null
    }
  }
  if (!response.ok) {
    const message = extractMessage(payload) || text || `HTTP ${response.status}`
    throw new Error(message)
  }
  return payload as T
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      Accept: 'application/json',
    },
  })
  return parseResponse<T>(response)
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(body ?? {}),
  })
  return parseResponse<T>(response)
}

export { API_BASE }
