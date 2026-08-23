import http from './http'
import type {
  ApiResponse,
  ErrorItem,
  ErrorListParams,
  ErrorListResponse,
} from '@/types'

export interface UploadResult {
  ocr_text: string
  questions: { index: number; question: string; selected: boolean }[]
}

export interface ImportItem {
  question: string
  answer?: string
  notebook_id: number
  subject: string
  source: string
  image_path?: string | null
}

export interface ImportResult {
  imported: {
    id: number
    question: string
    knowledge_points: string[]
    error_cause: string
    mastery: number
    next_review: string
  }[]
}

export async function uploadImage(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post<ApiResponse<UploadResult>>('/errors/upload', form)
  return data.data
}

export async function importErrors(questions: ImportItem[]): Promise<ImportResult> {
  const { data } = await http.post<ApiResponse<ImportResult>>('/errors/import', {
    questions,
  })
  return data.data
}

export async function createTextError(payload: {
  question: string
  answer: string
  notebook_id: number
  subject: string
}): Promise<{ id: number; knowledge_points: string[]; error_cause: string; mastery: number; next_review: string }> {
  const { data } = await http.post<ApiResponse<any>>('/errors/text', payload)
  return data.data
}

export async function getErrorList(params: ErrorListParams): Promise<ErrorListResponse> {
  const { data } = await http.get<ApiResponse<ErrorListResponse>>('/errors', { params })
  return data.data
}

export async function getErrorDetail(id: number): Promise<ErrorItem> {
  const { data } = await http.get<ApiResponse<ErrorItem>>(`/errors/${id}`)
  return data.data
}

export async function updateError(
  id: number,
  payload: Partial<{
    question: string
    answer: string
    analysis: string
    error_cause: string
    knowledge_points: string[]
    notebook_id: number
    subject: string
  }>
): Promise<{ id: number; vector_updated: boolean }> {
  const { data } = await http.put<ApiResponse<{ id: number; vector_updated: boolean }>>(
    `/errors/${id}`,
    payload
  )
  return data.data
}

export async function deleteError(id: number): Promise<{ id: number; vector_deleted: boolean }> {
  const { data } = await http.delete<ApiResponse<{ id: number; vector_deleted: boolean }>>(
    `/errors/${id}`
  )
  return data.data
}
