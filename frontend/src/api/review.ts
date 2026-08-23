import http from './http'
import type {
  ApiResponse,
  ReviewStartResponse,
  ReviewSubmitResponse,
} from '@/types'

export interface TodayItem {
  error_id: number
  subject: string
  knowledge_points: string[]
  mastery: number
  next_review: string
  overdue_days: number
}

export async function getReviewToday(): Promise<{
  count: number
  items: TodayItem[]
  weekly_preview: { date: string; count: number }[]
}> {
  const { data } = await http.get<ApiResponse<any>>('/review/today')
  return data.data
}

export async function startReview(payload: {
  subject?: string | null
  notebook_id?: number | null
  count: number
}): Promise<ReviewStartResponse> {
  const { data } = await http.post<ApiResponse<ReviewStartResponse>>('/review/start', payload)
  return data.data
}

export async function submitReview(payload: {
  review_id: string
  answers: { error_id: number; index: number; user_answer: string }[]
}): Promise<ReviewSubmitResponse> {
  const { data } = await http.post<ApiResponse<ReviewSubmitResponse>>('/review/submit', payload)
  return data.data
}
