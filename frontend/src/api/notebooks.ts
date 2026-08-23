import http from './http'
import type { ApiResponse, Notebook, NotebookPayload } from '@/types'

export async function getNotebooks(): Promise<Notebook[]> {
  const { data } = await http.get<ApiResponse<{ items: Notebook[] }>>('/notebooks')
  return data.data.items
}

export async function createNotebook(payload: NotebookPayload): Promise<Notebook> {
  const { data } = await http.post<ApiResponse<Notebook>>('/notebooks', payload)
  return data.data
}

export async function updateNotebook(
  id: number,
  payload: Partial<NotebookPayload>
): Promise<{ id: number }> {
  const { data } = await http.put<ApiResponse<{ id: number }>>(`/notebooks/${id}`, payload)
  return data.data
}

export async function deleteNotebook(
  id: number
): Promise<{ id: number; deleted_errors: number }> {
  const { data } = await http.delete<ApiResponse<{ id: number; deleted_errors: number }>>(
    `/notebooks/${id}`
  )
  return data.data
}
