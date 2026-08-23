<template>
  <div class="dashboard-page">
    <div class="dash-header">
      <h1 :style="{ font: 'var(--font-h1)' }">数据看板</h1>
      <select v-model="days" class="select" @change="load">
        <option :value="7">近 7 天</option>
        <option :value="30">近 30 天</option>
        <option :value="90">近 90 天</option>
      </select>
    </div>

    <div v-if="loading" class="dash-grid">
      <div v-for="n in 6" :key="n" class="skeleton" style="height: 180px; border-radius: 12px"></div>
    </div>

    <template v-else>
      <!-- Summary cards -->
      <div class="summary-row">
        <div class="summary-card">
          <div class="sc-label">录入数</div>
          <div class="sc-value">{{ trends.summary.total_errors }}</div>
        </div>
        <div class="summary-card">
          <div class="sc-label">复习数</div>
          <div class="sc-value">{{ trends.summary.total_reviews }}</div>
        </div>
        <div class="summary-card">
          <div class="sc-label">复习正确率</div>
          <div class="sc-value">{{ Math.round(trends.summary.review_accuracy * 100) }}%</div>
        </div>
        <div class="summary-card">
          <div class="sc-label">平均掌握度</div>
          <div class="sc-value">{{ trends.summary.avg_mastery }}%</div>
        </div>
      </div>

      <!-- Charts grid (2 columns) -->
      <div class="dash-grid">
        <div class="chart-card">
          <div class="cc-title">录入趋势</div>
          <div ref="inputChart" class="chart"></div>
        </div>
        <div class="chart-card">
          <div class="cc-title">复习趋势</div>
          <div ref="reviewChart" class="chart"></div>
        </div>
        <div class="chart-card">
          <div class="cc-title">掌握度分布</div>
          <div ref="masteryChart" class="chart"></div>
        </div>
        <div class="chart-card">
          <div class="cc-title">学科分布</div>
          <div ref="subjectChart" class="chart"></div>
        </div>
        <div class="chart-card wide">
          <div class="cc-title">知识图谱（节点大小=错题数，颜色=掌握度）</div>
          <div ref="graphChart" class="chart tall"></div>
        </div>
      </div>
    </template>

    <EmptyState
      v-if="!loading && trends.summary.total_errors === 0"
      title="还没有数据，开始录入错题后这里会显示你的学习趋势"
      subtitle="录入几道错题，或先去复习，看板会自动更新"
      primary-text="开始录入"
      @primary="goInput"
    />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import EmptyState from '@/components/EmptyState.vue'
import * as dashboardApi from '@/api/dashboard'
import type { DashboardTrends, KnowledgeGraph } from '@/types'

const router = useRouter()
const days = ref(30)
const loading = ref(true)
const trends = ref<DashboardTrends>({
  summary: { total_errors: 0, total_reviews: 0, avg_mastery: 0, review_accuracy: 0 },
  input_trend: [],
  review_trend: [],
  mastery_distribution: { mastered: 0, reviewing: 0, unstarted: 0 },
  subject_distribution: [],
  mastery_trend: [],
})

const inputChart = ref<HTMLElement | null>(null)
const reviewChart = ref<HTMLElement | null>(null)
const masteryChart = ref<HTMLElement | null>(null)
const subjectChart = ref<HTMLElement | null>(null)
const graphChart = ref<HTMLElement | null>(null)
const charts: echarts.ECharts[] = []

function goInput() {
  router.push('/input')
}

async function load() {
  loading.value = true
  try {
    trends.value = await dashboardApi.getTrends(days.value)
    const graph = await dashboardApi.getKnowledgeGraph()
    // 必须先让 loading=false、模板中的图表容器渲染出来，再初始化 ECharts，
    // 否则首屏渲染时 <template v-else> 尚未挂载，ref 为 null 导致图表实例无法创建而空白。
    loading.value = false
    await nextTick()
    renderCharts(graph)
  } finally {
    loading.value = false
  }
}

function baseGrid() {
  return { left: 40, right: 16, top: 24, bottom: 28 }
}

function renderCharts(graph: KnowledgeGraph) {
  disposeCharts()
  if (inputChart.value) {
    const c = echarts.init(inputChart.value)
    c.setOption({
      grid: baseGrid(),
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: trends.value.input_trend.map((d) => d.date.slice(5)), axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#EAEAEC' } } },
      series: [{ type: 'line', smooth: true, data: trends.value.input_trend.map((d) => d.count), itemStyle: { color: '#007AFF' }, areaStyle: { color: 'rgba(0,122,255,0.08)' } }],
    })
    charts.push(c)
  }
  if (reviewChart.value) {
    const c = echarts.init(reviewChart.value)
    c.setOption({
      grid: baseGrid(),
      tooltip: { trigger: 'axis' },
      legend: { data: ['复习数', '正确数'], right: 0, top: 0, textStyle: { fontSize: 10 } },
      xAxis: { type: 'category', data: trends.value.review_trend.map((d) => d.date.slice(5)), axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#EAEAEC' } } },
      series: [
        { name: '复习数', type: 'bar', data: trends.value.review_trend.map((d) => d.count), itemStyle: { color: '#007AFF' } },
        { name: '正确数', type: 'bar', data: trends.value.review_trend.map((d) => d.correct), itemStyle: { color: '#34C759' } },
      ],
    })
    charts.push(c)
  }
  if (masteryChart.value) {
    const md = trends.value.mastery_distribution
    const c = echarts.init(masteryChart.value)
    c.setOption({
      tooltip: { trigger: 'item' },
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          label: { fontSize: 10 },
          data: [
            { name: '已掌握', value: md.mastered, itemStyle: { color: '#34C759' } },
            { name: '复习中', value: md.reviewing, itemStyle: { color: '#FF9500' } },
            { name: '未掌握', value: md.unstarted, itemStyle: { color: '#FF3B30' } },
          ],
        },
      ],
    })
    charts.push(c)
  }
  if (subjectChart.value) {
    const c = echarts.init(subjectChart.value)
    c.setOption({
      tooltip: { trigger: 'item' },
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          label: { fontSize: 10 },
          data: trends.value.subject_distribution.map((s, i) => ({
            name: s.subject,
            value: s.count,
            itemStyle: { color: ['#007AFF', '#34C759', '#FF9500', '#AF52DE', '#5AC8FA', '#FF2D55'][i % 6] },
          })),
        },
      ],
    })
    charts.push(c)
  }
  if (graphChart.value) {
    const c = echarts.init(graphChart.value)
    c.setOption({
      tooltip: { trigger: 'item', formatter: (p: any) => (p.data.kp ? `${p.data.kp.label}\n错题 ${p.data.kp.error_count} · 掌握 ${p.data.kp.mastery}%` : p.data.name) },
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          label: { show: true, fontSize: 11 },
          force: { repulsion: 120, edgeLength: 80 },
          data: graph.nodes.map((n) => ({
            id: n.id,
            name: n.label,
            symbolSize: 20 + n.error_count * 3,
            itemStyle: { color: n.color },
            kp: n,
          })),
          links: graph.edges.map((e) => ({ source: e.source, target: e.target })),
        },
      ],
    })
    charts.push(c)
  }
}

function disposeCharts() {
  charts.forEach((c) => c.dispose())
  charts.length = 0
}

function onResize() {
  charts.forEach((c) => c.resize())
}

onMounted(async () => {
  await load()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeCharts()
})
</script>

<style scoped>
.dashboard-page {
  max-width: 1100px;
  margin: 0 auto;
}
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}
.select {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 6px 10px;
  font: var(--font-body);
}
.summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}
.summary-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-lg);
}
.sc-label {
  font: var(--font-caption);
  color: var(--color-text-secondary);
}
.sc-value {
  font: var(--font-h1);
  color: var(--color-text-primary);
  margin-top: var(--space-xs);
}
.dash-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}
.chart-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-md);
}
.chart-card.wide {
  grid-column: 1 / -1;
}
.cc-title {
  font: var(--font-h2);
  margin-bottom: var(--space-sm);
}
.chart {
  height: 200px;
}
.chart.tall {
  height: 320px;
}
@media (max-width: 767px) {
  .summary-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .dash-grid {
    grid-template-columns: 1fr;
  }
}
</style>
