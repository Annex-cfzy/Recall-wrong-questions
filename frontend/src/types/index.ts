// Shared TypeScript types mirroring backend API contracts.

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface Notebook {
  id: number
  name: string
  subject: string
  color: string
  error_count: number
  created_at: string | null
  updated_at: string | null
}

export interface NotebookPayload {
  name: string
  subject?: string
  color?: string
}

export interface ErrorItem {
  id: number
  notebook_id: number
  question: string
  answer: string | null
  analysis: string | null
  error_cause: string | null
  knowledge_points: string[]
  subject: string
  source: string
  image_path: string | null
  mastery: number
  repetition: number
  interval_days: number
  ease_factor: number
  next_review: string | null
  last_review: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ErrorListParams {
  page?: number
  page_size?: number
  notebook_id?: number
  subject?: string
  knowledge_points?: string
  mastery_min?: number
  mastery_max?: number
  date_from?: string
  date_to?: string
  is_due?: boolean
  search?: string
  sort?: 'created_at' | 'mastery' | 'next_review'
  order?: 'asc' | 'desc'
}

export interface ErrorListResponse {
  items: ErrorItem[]
  total: number
  page: number
  page_size: number
}

export interface ReviewQuestion {
  index: number
  error_id: number
  variant_question: string
  knowledge_points: string[]
}

export interface ReviewStartResponse {
  review_id: string
  total: number
  questions: ReviewQuestion[]
}

export interface ReviewResultItem {
  index: number
  error_id: number
  is_correct: boolean
  score: number
  quality: number
  ai_feedback: string
  standard_answer: string
  error_cause?: string
  sm2_updated: {
    repetition: number
    interval_days: number
    ease_factor: number
    mastery: number
    next_review: string
  }
}

export interface ReviewSubmitResponse {
  review_id: string
  total_score: number
  correct_count: number
  wrong_count: number
  skipped_count: number
  mastery_delta: number
  results: ReviewResultItem[]
}

export interface ChatSession {
  id: number
  title: string
  last_message_preview: string
  created_at: string | null
  updated_at: string | null
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string | null
}

export interface DashboardTrends {
  summary: {
    total_errors: number
    total_reviews: number
    avg_mastery: number
    review_accuracy: number
  }
  input_trend: { date: string; count: number }[]
  review_trend: { date: string; count: number; correct: number }[]
  mastery_distribution: { mastered: number; reviewing: number; unstarted: number }
  subject_distribution: { subject: string; count: number }[]
  mastery_trend: { date: string; avg_mastery: number }[]
}

export interface KnowledgeGraph {
  nodes: {
    id: string
    label: string
    subject: string
    error_count: number
    mastery: number
    color: string
  }[]
  edges: { source: string; target: string; relation: string }[]
}
