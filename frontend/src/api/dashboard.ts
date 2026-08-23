import http from './http'
import type { ApiResponse, DashboardTrends, KnowledgeGraph } from '@/types'

export async function getTrends(days = 30): Promise<DashboardTrends> {
  const { data } = await http.get<ApiResponse<DashboardTrends>>('/dashboard/trends', { params: { days } })
  return data.data
}

export async function getKnowledgeGraph(): Promise<KnowledgeGraph> {
  const { data } = await http.get<ApiResponse<KnowledgeGraph>>('/dashboard/knowledge-graph')
  return data.data
}
