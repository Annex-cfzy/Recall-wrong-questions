<template>
  <div class="insights-page">
    <div class="dash-header">
      <h1 :style="{ font: 'var(--font-h1)' }">智能洞察</h1>
      <select v-model="days" class="select" @change="load">
        <option :value="7">近 7 天</option>
        <option :value="30">近 30 天</option>
        <option :value="90">近 90 天</option>
      </select>
    </div>

    <div v-if="loading" class="dash-grid">
      <div v-for="n in 5" :key="n" class="skeleton" style="height: 180px; border-radius: 12px"></div>
    </div>

    <template v-else>
      <!-- 薄弱点预警 -->
      <div v-if="data.weak_point_warnings.warning_count > 0" class="warn-block">
        <div class="warn-head">
          <span class="warn-title">⚠️ 薄弱点预警</span>
          <span class="warn-count">
            {{ data.weak_point_warnings.warning_count }} 个知识点需关注
            <template v-if="data.weak_point_warnings.danger_count">
              （其中 {{ data.weak_point_warnings.danger_count }} 个高危）
            </template>
          </span>
        </div>
        <div class="warn-list">
          <div
            v-for="w in data.weak_point_warnings.warnings"
            :key="w.knowledge_point"
            class="warn-card"
            :class="w.level"
          >
            <div class="wc-top">
              <span class="wc-kp">{{ w.knowledge_point }}</span>
              <span class="wc-subj">{{ w.subject }}</span>
            </div>
            <div class="wc-meta">
              掌握度 {{ w.avg_mastery }}% · 错误率 {{ Math.round(w.error_rate * 100) }}%
              <span v-if="w.spike" class="wc-spike">近期突增</span>
            </div>
            <ul class="wc-reasons">
              <li v-for="(r, i) in w.reasons" :key="i">{{ r }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 图表网格 -->
      <div class="dash-grid">
        <div class="chart-card wide">
          <div class="cc-title">知识点掌握趋势（最薄弱的 {{ shownKpCount }} 个）</div>
          <div ref="masteryTrendChart" class="chart tall"></div>
        </div>
        <div class="chart-card">
          <div class="cc-title">错因分布</div>
          <div ref="causeChart" class="chart"></div>
        </div>
        <div class="chart-card">
          <div class="cc-title">薄弱学科对比（按薄弱度排序）</div>
          <div ref="subjectChart" class="chart"></div>
        </div>
      </div>

      <EmptyState
        v-if="data.weak_subject_comparison.length === 0"
        title="还没有足够数据生成洞察"
        subtitle="录入并复习几道错题后，这里会展示掌握趋势、错因分布与薄弱学科对比"
        primary-text="开始录入"
        @primary="goInput"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import EmptyState from '@/components/EmptyState.vue'
import * as upgradeApi from '@/api/upgrade'
import type { InsightsData } from '@/types/upgrade'

const router = useRouter()
const days = ref(30)
const loading = ref(true)
const data = ref<InsightsData>({
  mastery_trend: { days: 30, series: [], knowledge_point_count: 0 },
  error_cause_distribution: [],
  weak_subject_comparison: [],
  weak_point_warnings: { warning_count: 0, danger_count: 0, warnings: [] },
})

const masteryTrendChart = ref<HTMLElement | null>(null)
const causeChart = ref<HTMLElement | null>(null)
const subjectChart = ref<HTMLElement | null>(null)
const charts: echarts.ECharts[] = []

const shownKpCount = computed(() =>
  Math.min(6, data.value.mastery_trend.series.length)
)

function goInput() {
  router.push('/input')
}

async function load() {
  loading.value = true
  try {
    data.value = await upgradeApi.getInsights(days.value)
    loading.value = false
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

function baseGrid() {
  return { left: 44, right: 16, top: 28, bottom: 28 }
}

function renderCharts() {
  disposeCharts()
  // 知识点掌握趋势：取最薄弱的若干个知识点各画一条线
  if (masteryTrendChart.value && data.value.mastery_trend.series.length) {
    const series = data.value.mastery_trend.series.slice(0, 6)
    const dates = (series[0]?.points || []).map((p) => p.date.slice(5))
    const c = echarts.init(masteryTrendChart.value)
    c.setOption({
      grid: baseGrid(),
      tooltip: { trigger: 'axis' },
      legend: { type: 'scroll', top: 0, textStyle: { fontSize: 10 } },
      xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { color: '#EAEAEC' } } },
      series: series.map((s) => ({
        name: s.knowledge_point,
        type: 'line',
        smooth: true,
        data: s.points.map((p) => p.avg_mastery),
      })),
    })
    charts.push(c)
  }
  // 错因分布：饼图
  if (causeChart.value && data.value.error_cause_distribution.length) {
    const c = echarts.init(causeChart.value)
    c.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, textStyle: { fontSize: 10 } },
      series: [
        {
          type: 'pie',
          radius: ['40%', '68%'],
          label: { fontSize: 10 },
          data: data.value.error_cause_distribution.map((d, i) => ({
            name: d.cause,
            value: d.count,
            itemStyle: {
              color: ['#FF3B30', '#FF9500', '#007AFF', '#34C759', '#AF52DE', '#5AC8FA'][i % 6],
            },
          })),
        },
      ],
    })
    charts.push(c)
  }
  // 薄弱学科对比：横向柱（按薄弱度）
  if (subjectChart.value && data.value.weak_subject_comparison.length) {
    const cmp = [...data.value.weak_subject_comparison]
    const c = echarts.init(subjectChart.value)
    c.setOption({
      grid: { left: 56, right: 24, top: 16, bottom: 24 },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'value', splitLine: { lineStyle: { color: '#EAEAEC' } } },
      yAxis: {
        type: 'category',
        data: cmp.map((s) => s.subject),
        axisLabel: { fontSize: 10 },
      },
      series: [
        {
          type: 'bar',
          data: cmp.map((s) => ({
            value: s.weakness,
            itemStyle: { color: s.weakness >= 60 ? '#FF3B30' : s.weakness >= 35 ? '#FF9500' : '#34C759' },
          })),
          label: { show: true, position: 'right', fontSize: 10, formatter: '{c}' },
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
.insights-page {
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
  height: 300px;
}
/* 预警 */
.warn-block {
  margin-bottom: var(--space-lg);
}
.warn-head {
  display: flex;
  align-items: baseline;
  gap: var(--space-md);
  margin-bottom: var(--space-sm);
}
.warn-title {
  font: var(--font-h2);
  color: #ff9500;
}
.warn-count {
  font: var(--font-caption);
  color: var(--color-text-secondary);
}
.warn-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-sm);
}
.warn-card {
  border: 1px solid var(--color-border);
  border-left: 4px solid #ff9500;
  border-radius: 10px;
  padding: var(--space-md);
  background: var(--color-bg-card);
}
.warn-card.danger {
  border-left-color: #ff3b30;
}
.wc-top {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.wc-kp {
  font: var(--font-h2);
  color: var(--color-text-primary);
}
.wc-subj {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.wc-meta {
  font: var(--font-caption);
  color: var(--color-text-secondary);
  margin: 4px 0;
}
.wc-spike {
  margin-left: 6px;
  color: #ff3b30;
  font-weight: 600;
}
.wc-reasons {
  margin: 4px 0 0;
  padding-left: 18px;
  font: var(--font-caption);
  color: var(--color-text-secondary);
}
@media (max-width: 767px) {
  .dash-grid {
    grid-template-columns: 1fr;
  }
}
</style>
