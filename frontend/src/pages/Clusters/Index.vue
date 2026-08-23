<template>
  <div class="clusters-page">
    <div class="dash-header">
      <h1 :style="{ font: 'var(--font-h1)' }">相似错题 · 去重聚类</h1>
      <label class="thr">相似度阈值
        <select v-model.number="threshold" @change="load">
          <option :value="0.3">低（更聚合）</option>
          <option :value="0.5">中</option>
          <option :value="0.7">高（更精细）</option>
        </select>
      </label>
    </div>

    <div v-if="loading" class="skeleton" style="height: 300px; border-radius: 12px"></div>

    <template v-else>
      <div class="stat-row">
        <div class="stat-card">
          <div class="sc-label">错题总数</div>
          <div class="sc-value">{{ clusters.total_errors }}</div>
        </div>
        <div class="stat-card">
          <div class="sc-label">相似簇</div>
          <div class="sc-value">{{ clusters.repeated_cluster_count }}</div>
        </div>
        <div class="stat-card">
          <div class="sc-label">反复错知识点</div>
          <div class="sc-value">{{ clusters.repeated_knowledge_points.length }}</div>
        </div>
      </div>

      <!-- 反复错的知识点 -->
      <section class="block" v-if="clusters.repeated_knowledge_points.length">
        <h2 class="block-title">🔁 反复出错的知识点</h2>
        <div class="rkp-list">
          <div v-for="k in clusters.repeated_knowledge_points" :key="k.knowledge_point" class="rkp-card">
            <span class="rkp-name">{{ k.knowledge_point }}</span>
            <span class="rkp-occ">出现 {{ k.occurrences }} 次</span>
            <span class="rkp-m" :class="{ low: k.avg_mastery < 50 }">均掌握 {{ k.avg_mastery }}%</span>
          </div>
        </div>
      </section>

      <!-- 相似簇 -->
      <section class="block">
        <h2 class="block-title">📚 相似错题分组（识别重复，便于合并复习）</h2>
        <div v-if="clusters.clusters.length === 0" class="empty-tip">
          当前阈值下未发现明显相似的错题。降低阈值可更激进地聚合；或录入更多同类型题目。
        </div>
        <div class="cluster-list">
          <div v-for="c in clusters.clusters" :key="c.cluster_id" class="cluster-card">
            <div class="cc-head">
              <span class="cc-id">{{ c.cluster_id }}</span>
              <span class="cc-subj">{{ c.subject }}</span>
              <span class="cc-count">{{ c.member_ids.length }} 道</span>
            </div>
            <div class="cc-rep">代表题：{{ c.representative_question }}</div>
            <div class="cc-kps">
              <span v-for="kp in c.shared_knowledge_points" :key="kp" class="kp-tag">{{ kp }}</span>
            </div>
            <ul class="cc-members">
              <li v-for="m in c.members" :key="m.id">
                <span class="m-q">{{ m.question }}</span>
                <span class="m-m" :class="{ low: m.mastery < 50 }">掌握 {{ m.mastery }}%</span>
              </li>
            </ul>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import * as upgradeApi from '@/api/upgrade'
import type { ClustersData } from '@/types/upgrade'

const loading = ref(true)
const threshold = ref(0.5)
const clusters = ref<ClustersData>({
  threshold: 0.5,
  total_errors: 0,
  cluster_count: 0,
  repeated_cluster_count: 0,
  clusters: [],
  repeated_knowledge_points: [],
})

async function load() {
  loading.value = true
  try {
    clusters.value = await upgradeApi.getClusters(threshold.value)
  } finally {
    loading.value = false
  }
}

load()
</script>

<style scoped>
.clusters-page {
  max-width: 1000px;
  margin: 0 auto;
}
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}
.thr {
  font: var(--font-caption);
  color: var(--color-text-secondary);
}
.thr select {
  margin-left: 6px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 4px 8px;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}
.stat-card {
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
  border: 1px dashed var(--color-border);
  border-radius: 10px;
}
.rkp-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-sm);
}
.rkp-card {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  border: 1px solid var(--color-border);
  border-left: 4px solid #ff9500;
  border-radius: 10px;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-card);
}
.rkp-name {
  font: var(--font-h2);
  color: var(--color-text-primary);
}
.rkp-occ {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.rkp-m {
  font: var(--font-caption);
  color: #34c759;
  margin-left: auto;
}
.rkp-m.low {
  color: #ff3b30;
}
.cluster-list {
  display: grid;
  gap: var(--space-md);
}
.cluster-card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-md);
  background: var(--color-bg-card);
}
.cc-head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.cc-id {
  font-weight: 600;
  color: var(--color-primary);
}
.cc-subj {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.cc-count {
  font: var(--font-caption);
  color: var(--color-text-secondary);
  margin-left: auto;
}
.cc-rep {
  font: var(--font-body);
  color: var(--color-text-primary);
  margin: 6px 0;
}
.cc-kps {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.kp-tag {
  font: var(--font-caption);
  background: rgba(0, 122, 255, 0.08);
  color: var(--color-primary);
  border-radius: 6px;
  padding: 1px 6px;
}
.cc-members {
  margin: 0;
  padding-left: 18px;
  font: var(--font-caption);
  color: var(--color-text-secondary);
}
.cc-members li {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  margin: 2px 0;
}
.m-m {
  color: #34c759;
}
.m-m.low {
  color: #ff3b30;
}
@media (max-width: 767px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>
