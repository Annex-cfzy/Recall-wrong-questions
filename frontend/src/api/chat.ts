import http from './http'
import type { ApiResponse, ChatMessage, ChatSession, KnowledgeGraph, DashboardTrends } from '@/types'

export async function createSession(title = '新对话'): Promise<ChatSession> {
  const { data } = await http.post<ApiResponse<ChatSession>>('/chat/sessions', { title })
  return data.data
}

export async function listSessions(): Promise<ChatSession[]> {
  const { data } = await http.get<ApiResponse<{ items: ChatSession[] }>>('/chat/sessions')
  return data.data.items
}

export async function getMessages(sessionId: number): Promise<ChatMessage[]> {
  const { data } = await http.get<ApiResponse<{ messages: ChatMessage[] }>>(
    `/chat/sessions/${sessionId}/messages`
  )
  return data.data.messages
}

export async function deleteSession(sessionId: number): Promise<{ id: number }> {
  const { data } = await http.delete<ApiResponse<{ id: number }>>(`/chat/sessions/${sessionId}`)
  return data.data
}

/**
 * Stream a chat reply via SSE (fetch + ReadableStream).
 * onChunk receives incremental text; onDone receives the full content + message_id.
 */
export async function streamChat(
  sessionId: number,
  message: string,
  handlers: { onChunk: (t: string) => void; onDone: (content: string, messageId: number) => void; onError: (msg: string) => void }
) {
  const resp = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })
  if (!resp.body) {
    handlers.onError('AI 服务暂时不可用')
    return
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let full = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      const json = line.slice(5).trim()
      try {
        const evt = JSON.parse(json)
        if (evt.type === 'chunk') {
          full += evt.content
          handlers.onChunk(evt.content)
        } else if (evt.type === 'done') {
          full = evt.content
          handlers.onDone(full, evt.message_id)
        } else if (evt.type === 'error') {
          handlers.onError(evt.message)
        }
      } catch {
        /* ignore malformed */
      }
    }
  }
}

export async function saveToErrors(payload: {
  message_id: number
  notebook_id: number
  subject: string
}): Promise<{ error_id: number }> {
  const { data } = await http.post<ApiResponse<{ error_id: number }>>('/chat/save-to-errors', payload)
  return data.data
}
