<template>
  <div class="sprint-page">
    <div class="dash-header">
      <h1 :style="{ font: 'var(--font-h1)' }">考前冲刺清单</h1>
      <button class="btn" @click="load">重新生成</button>
    </div>

    <div v-if="loading" class="skeleton" style="height: 320px; border-radius: 12px"></div>

    <template v-else>
      <p class="summary">{{ sprint.summary }}</p>

      <!-- 复习重点 -->
      <section class="block">
        <h2 class="block-title">🎯 复习重点（最薄弱知识点）</h2>
        <div v-if="sprint.focus_list.length === 0" class="empty-tip">
          暂无薄弱知识点，保持得很好！去录入更多错题可获得更精准的冲刺建议。
        </div>
        <div class="focus-list">
          <div v-for="(f, i) in sprint.focus_list" :key="f.knowledge_point" class="focus-card">
            <div class="fc-rank">{{ i + 1 }}</div>
            <div class="fc-body">
              <div class="fc-top">
                <span class="fc-kp">{{ f.knowledge_point }}</span>
                <span class="fc-subj">{{ f.subject }}</span>
                <span class="fc-mastery">掌握 {{ f.avg_mastery }}%</span>
              </div>
              <div class="fc-reason">{{ f.reason }}</div>
              <div class="fc-advice">💡 {{ f.advice }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 模拟组卷 -->
      <section class="block">
        <div class="paper-head">
          <h2 class="block-title">📝 模拟组卷（最易错题自测）</h2>
          <div class="paper-ctrl">
            <label>重点数
              <select v-model.number="topN" @change="load">
                <option :value="5">5</option>
                <option :value="10">10</option>
                <option :value="15">15</option>
              </select>
            </label>
            <label>题量
              <select v-model.number="paperSize" @change="load">
                <option :value="5">5</option>
                <option :value="10">10</option>
                <option :value="20">20</option>
              </select>
            </label>
          </div>
        </div>
        <div v-if="sprint.mock_paper.length === 0" class="empty-tip">暂无题目可组卷，先录入一些错题吧。</div>
        <ol class="paper-list">
          <li v-for="p in sprint.mock_paper" :key="p.index" class="paper-item">
            <div class="pi-q">
              <span class="pi-no">{{ p.index }}.</span>
              <span>{{ p.question }}</span>
            </div>
            <div class="pi-meta">
              <span v-for="kp in p.knowledge_points" :key="kp" class="kp-tag">{{ kp }}</span>
              <span class="pi-mastery">掌握 {{ p.mastery }}%</span>
            </div>
            <div class="pi-answer">
              <span class="ans-label">参考答案</span>
              <span class="ans-text">{{ p.standard_answer }}</span>
            </div>
          </li>
        </ol>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import * as upgradeApi from '@/api/upgrade'
import type { SprintData } from '@/types/upgrade'

const loading = ref(true)
const topN = ref(10)
const paperSize = ref(10)
const sprint = ref<SprintData>({
  focus_list: [],
  focus_count: 0,
  mock_paper: [],
  paper_size: 0,
  summary: '',
})

async function load() {
  loading.value = true
  try {
    sprint.value = await upgradeApi.getSprint(topN.value, paperSize.value)
  } finally {
    loading.value = false
  }
}

load()
</script>

<style scoped>
.sprint-page {
  max-width: 920px;
  margin: 0 auto;
}
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}
.btn {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  padding: 6px 14px;
  font: var(--font-body);
  background: var(--color-bg-card);
  cursor: pointer;
}
.btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.summary {
  font: var(--font-body);
  color: var(--color-text-secondary);
  background: rgba(0, 122, 255, 0.06);
  border: 1px solid rgba(0, 122, 255, 0.18);
  border-radius: 10px;
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
}
.block {
  margin-bottom: var(--space-xl);
}
.block-title {
  font: var(--font-h2);
  margin-bottom: var(--space-md);
}
.empty-tip {
  font: var(--font-body);
  color: var(--color-text-tertiary);
  padding: var(--space-md);
}
.focus-list {
  display: grid;
  gap: var(--space-sm);
}
.focus-card {
  display: flex;
  gap: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-md);
  background: var(--color-bg-card);
}
.fc-rank {
  flex: 0 0 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}
.fc-kp {
  font: var(--font-h2);
  color: var(--color-text-primary);
}
.fc-subj {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
  margin-left: var(--space-sm);
}
.fc-mastery {
  font: var(--font-caption);
  color: #ff9500;
  margin-left: auto;
}
.fc-reason {
  font: var(--font-caption);
  color: var(--color-text-secondary);
  margin-top: 4px;
}
.fc-advice {
  font: var(--font-caption);
  color: var(--color-primary);
  margin-top: 4px;
}
.paper-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-sm);
}
.paper-ctrl {
  display: flex;
  gap: var(--space-md);
  font: var(--font-caption);
  color: var(--color-text-secondary);
}
.paper-ctrl select {
  margin-left: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 3px 6px;
}
.paper-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: var(--space-sm);
}
.paper-item {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-md);
  background: var(--color-bg-card);
}
.pi-q {
  font: var(--font-body);
  color: var(--color-text-primary);
}
.pi-no {
  color: var(--color-primary);
  font-weight: 600;
  margin-right: 4px;
}
.pi-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin: 6px 0;
}
.kp-tag {
  font: var(--font-caption);
  background: rgba(0, 122, 255, 0.08);
  color: var(--color-primary);
  border-radius: 6px;
  padding: 1px 6px;
}
.pi-mastery {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
  margin-left: auto;
}
.pi-answer {
  font: var(--font-caption);
  color: var(--color-text-secondary);
}
.ans-label {
  color: var(--color-text-tertiary);
  margin-right: 6px;
}
.ans-text {
  color: #34c759;
}
@media (max-width: 767px) {
  .paper-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
