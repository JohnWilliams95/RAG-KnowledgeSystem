import api from './client'
import type { ChatRequest, ChatResponse, ChatStreamEvent } from './types'

export function sendChat(data: ChatRequest) {
  return api.post<ChatResponse>('/api/v1/chat/', data)
}

export async function streamChat(
  data: ChatRequest,
  onChunk: (event: ChatStreamEvent) => void,
  onDone: () => void,
  onError: (error: Error) => void,
) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  try {
    const response = await fetch(`${baseURL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue
        const payload = trimmed.slice(6)
        if (payload === '[DONE]') {
          onDone()
          return
        }
        try {
          const event = JSON.parse(payload)
          onChunk(event)
        } catch {
          // skip malformed JSON
        }
      }
    }
    onDone()
  } catch (error) {
    onError(error as Error)
  }
}

export function clearHistory(conversationId: string) {
  return api.delete(`/api/v1/chat/history/${conversationId}`)
}
