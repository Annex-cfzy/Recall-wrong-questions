<template>
  <div class="error-card card-hover" :class="{ expanded }">
    <!-- 折叠态：题目区 + 元信息 -->
    <div class="ec-head" @click="toggle">
      <QuestionArea>
        <span class="ec-question">{{ truncate(error.question) }}</span>
      </QuestionArea>
      <div class="ec-meta">
        <span class="ec-tag source">{{ sourceLabel }}</span>
        <span class="ec-tag subject">{{ error.subject }}</span>
        <span v-for="kp in error.knowledge_points.slice(0, 3)" :key="kp" class="ec-tag kp">
          {{ kp }}
        </span>
        <span class="ec-mastery">
          <span
            class="ec-mastery-bar"
            :style="{ width: error.mastery + '%', background: masteryColor(error.mastery) }"
          ></span>
          <span class="ec-mastery-text">掌握 {{ error.mastery }}%</span>
        </span>
      </div>
    </div>

    <!-- 展开态：解析区 + 操作行 -->
    <div v-if="expanded" class="ec-body">
      <AnalysisArea v-if="error.analysis || error.answer">
        <div v-if="error.answer"><strong>答案：</strong>{{ error.answer }}</div>
        <div v-if="error.analysis" style="margin-top: 6px">{{ error.analysis }}</div>
      </AnalysisArea>
      <div v-if="error.error_cause" class="ec-cause">
        错因：{{ error.error_cause }}
      </div>
      <div class="ec-actions">
        <button class="ec-btn" @click.stop="emit('edit', error.id)">
          <Pencil :size="14" /> 编辑
        </button>
        <button class="ec-btn danger" @click.stop="emit('delete', error.id)">
          <Trash2 :size="14" /> 删除
        </button>
        <span class="ec-review-count">复习 {{ error.repetition }} 次</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Pencil, Trash2 } from 'lucide-vue-next'
import QuestionArea from './QuestionArea.vue'
import AnalysisArea from './AnalysisArea.vue'
import type { ErrorItem } from '@/types'
import { useErrorStore } from '@/stores/error'

const props = defineProps<{ error: ErrorItem; expanded?: boolean }>()
const emit = defineEmits<{ toggle: []; edit: [number]; delete: [number] }>()

const store = useErrorStore()
const expanded = ref(props.expanded ?? false)

function toggle() {
  expanded.value = !expanded.value
  emit('toggle')
}

function truncate(s: string) {
  return s.length > 100 ? s.slice(0, 100) + '…' : s
}

const sourceLabel: Record<string, string> = {
  photo: '识图',
  text: '文本',
  chat: '对话',
  manual: '手动',
}

function masteryColor(m: number) {
  return store.masteryColor(m)
}
</script>

<style scoped>
.error-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
  cursor: pointer;
}
.ec-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}
.ec-tag {
  font: var(--font-caption);
  padding: 2px 8px;
  border-radius: var(--radius-tag);
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
}
.ec-tag.subject {
  color: var(--color-primary);
}
.ec-tag.kp {
  color: var(--color-text-primary);
}
.ec-mastery {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}
.ec-mastery-bar {
  width: 48px;
  height: 6px;
  border-radius: 3px;
  background: var(--color-border);
  position: relative;
  overflow: hidden;
}
.ec-mastery-bar::after {
  content: '';
  position: absolute;
  inset: 0;
  width: inherit;
  background: inherit;
  border-radius: 3px;
}
.ec-mastery-text {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.ec-body {
  margin-top: var(--space-sm);
}
.ec-cause {
  font: var(--font-caption);
  color: var(--color-warning);
  margin-top: var(--space-sm);
}
.ec-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}
.ec-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  border-radius: var(--radius-button);
  padding: 5px 12px;
  font: var(--font-body);
  color: var(--color-text-secondary);
  cursor: pointer;
}
.ec-btn:hover {
  background: var(--color-bg-page);
}
.ec-btn.danger:hover {
  color: var(--color-error);
  border-color: var(--color-error);
}
.ec-review-count {
  margin-left: auto;
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
</style>
