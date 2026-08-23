import http from './http'
import type { ApiResponse } from '@/types'
import type {
  InsightsData,
  ClustersData,
  SprintData,
  VoiceCard,
} from '@/types/upgrade'

export async function getInsights(days = 30): Promise<InsightsData> {
  const { data } = await http.get<ApiResponse<InsightsData>>('/upgrade/insights', {
    params: { days },
  })
  return data.data
}

export async function getClusters(threshold = 0.5): Promise<ClustersData> {
  const { data } = await http.get<ApiResponse<ClustersData>>('/upgrade/clusters', {
    params: { threshold },
  })
  return data.data
}

export async function getSprint(top_n = 10, paper_size = 10): Promise<SprintData> {
  const { data } = await http.get<ApiResponse<SprintData>>('/upgrade/sprint', {
    params: { top_n, paper_size },
  })
  return data.data
}

export async function getVoiceCard(errorId: number): Promise<VoiceCard> {
  const { data } = await http.get<ApiResponse<VoiceCard>>(
    `/upgrade/voice-card/${errorId}`
  )
  return data.data
}
