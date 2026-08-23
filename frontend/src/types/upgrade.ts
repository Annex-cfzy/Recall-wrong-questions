// M7 升级功能类型定义（与 backend/app/api/upgrade.py 返回结构对应）。

export interface MasteryTrendPoint {
  date: string
  avg_mastery: number | null
}
export interface MasteryTrendSeries {
  knowledge_point: string
  current_mastery: number
  points: MasteryTrendPoint[]
}
export interface MasteryTrend {
  days: number
  series: MasteryTrendSeries[]
  knowledge_point_count: number
}

export interface CauseItem {
  cause: string
  count: number
  ratio: number
}

export interface SubjectCompare {
  subject: string
  error_count: number
  avg_mastery: number
  review_count: number
  error_rate: number
  weakness: number
}

export interface WeakWarning {
  knowledge_point: string
  subject: string
  error_count: number
  avg_mastery: number
  error_rate: number
  recent_count: number
  spike: boolean
  level: 'warning' | 'danger'
  reasons: string[]
}

export interface Warnings {
  warning_count: number
  danger_count: number
  warnings: WeakWarning[]
}

export interface InsightsData {
  mastery_trend: MasteryTrend
  error_cause_distribution: CauseItem[]
  weak_subject_comparison: SubjectCompare[]
  weak_point_warnings: Warnings
}

export interface ClusterMember {
  id: number
  question: string
  subject: string
  mastery: number
}
export interface Cluster {
  cluster_id: string
  representative_id: number
  representative_question: string
  subject: string
  shared_knowledge_points: string[]
  member_ids: number[]
  members: ClusterMember[]
}
export interface RepeatedKp {
  knowledge_point: string
  occurrences: number
  avg_mastery: number
}
export interface ClustersData {
  threshold: number
  total_errors: number
  cluster_count: number
  repeated_cluster_count: number
  clusters: Cluster[]
  repeated_knowledge_points: RepeatedKp[]
}

export interface SprintFocus {
  knowledge_point: string
  subject: string
  avg_mastery: number
  error_rate: number
  reason: string
  advice: string
}
export interface SprintPaperItem {
  index: number
  error_id: number
  question: string
  standard_answer: string
  knowledge_points: string[]
  mastery: number
}
export interface SprintData {
  focus_list: SprintFocus[]
  focus_count: number
  mock_paper: SprintPaperItem[]
  paper_size: number
  summary: string
}

export interface VoiceSection {
  type: string
  text: string
}
export interface VoiceCard {
  error_id: number | null
  subject: string
  title: string
  sections: VoiceSection[]
  tts_script: string
  enriched: boolean
}
