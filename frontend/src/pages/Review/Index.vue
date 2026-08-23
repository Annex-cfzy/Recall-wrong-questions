<template>
  <div class="review-page">
    <StepIndicator :steps="['选范围', '作答', '批改']" :current="stage" />

    <!-- Stage 1: choose scope -->
    <div v-if="stage === 0" class="stage-panel">
      <h2 :style="{ font: 'var(--font-h2)' }">选择复习范围</h2>
      <div class="form-row">
        <label>学科</label>
        <select v-model="subject" class="select">
          <option value="">全部学科</option>
          <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div class="form-row">
        <label>错题本</label>
        <select v-model="notebookId" class="select">
          <option :value="null">全部</option>
          <option v-for="nb in notebooks" :key="nb.id" :value="nb.id">{{ nb.name }}</option>
        </select>
      </div>
      <div class="form-row">
        <label>复习数量</label>
        <select v-model="count" class="select">
          <option :value="5">5 题</option>
          <option :value="10">10 题</option>
          <option :value="20">20 题</option>
        </select>
      </div>
      <p class="due-info">待复习题目：<strong>{{ dueCount }}</strong> 道 · 预计耗时 {{ count * 1.5 }} 分钟</p>
      <div class="panel-actions">
        <button class="btn-secondary" @click="goHome">取消</button>
        <button class="btn-primary" :disabled="starting" @click="start">
          {{ starting ? '出题中…' : '开始复习 →' }}
        </button>
      </div>
    </div>

    <!-- Stage 2: answer -->
    <div v-else-if="stage === 1" class="stage-panel">
      <div class="answer-head">
        题目 {{ currentIndex + 1 }} / {{ questions.length }}
      </div>
      <QuestionArea>
        <div style="white-space: pre-wrap">{{ currentQuestion?.variant_question }}</div>
      </QuestionArea>
      <label class="answer-label">你的答案</label>
      <textarea v-model="answers[currentIndex]" class="answer-input" rows="4"></textarea>
      <div class="panel-actions">
        <button class="btn-secondary" @click="skip">跳过</button>
        <button v-if="currentIndex < questions.length - 1" class="btn-primary" @click="next">
          下一题 →
        </button>
        <button v-else class="btn-primary" :disabled="submitting" @click="submit">
          {{ submitting ? '批改中…' : '提交批改' }}
        </button>
      </div>
      <p v-if="unansweredWarning" class="inline-warning">
        有 {{ unansweredCount }} 道题未作答，确认跳过还是返回作答？
        <button class="link-btn" @click="stage = 2">跳过未答</button>
        <button class="link-btn" @click="unansweredWarning = false">返回作答</button>
      </p>
    </div>

    <!-- Stage 3: result -->
    <div v-else class="stage-panel">
      <div class="result-summary">
        <div class="rs-score">总分 {{ result?.total_score }} / 100</div>
        <div class="rs-stats">
          答对 {{ result?.correct_count }} 题 · 答错 {{ result?.wrong_count }} 题 · 跳过
          {{ result?.skipped_count }} 题
        </div>
        <div class="rs-mastery">掌握度提升 {{ result?.mastery_delta }}</div>
      </div>

      <div
        v-for="(r, i) in result?.results"
        :key="i"
        class="result-card"
        :class="rClass(r)"
      >
        <div class="rc-head">
          <span v-if="r.is_correct" class="rc-badge ok">✅ 第 {{ i + 1 }} 题（答对）</span>
          <span v-else-if="r.sm2_updated" class="rc-badge bad">❌ 第 {{ i + 1 }} 题（答错）</span>
          <span v-else class="rc-badge skip">⏭ 第 {{ i + 1 }} 题（跳过）</span>
        </div>
        <div class="rc-field"><strong>题目：</strong>{{ questions[i]?.variant_question }}</div>
        <div class="rc-field"><strong>你的答案：</strong>{{ answers[i] || '（空）' }}</div>
        <div v-if="r.standard_answer" class="rc-field">
          <strong>标准答案：</strong>{{ r.standard_answer }}
        </div>
        <div class="rc-field"><strong>评分：</strong>{{ r.score }} / 100</div>
        <div v-if="r.ai_feedback" class="rc-field"><strong>详解：</strong>{{ r.ai_feedback }}</div>
        <div v-if="r.error_cause" class="rc-cause">错因：{{ r.error_cause }}</div>
      </div>

      <div class="panel-actions">
        <button class="btn-secondary" @click="goHome">返回错题本</button>
        <button class="btn-primary" @click="restart">继续复习 →</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import StepIndicator from '@/components/StepIndicator.vue'
import QuestionArea from '@/components/QuestionArea.vue'
import { useNotebookStore } from '@/stores/notebook'
import * as reviewApi from '@/api/review'
import { ElMessage } from 'element-plus'
import type { ReviewQuestion, ReviewSubmitResponse } from '@/types'

const router = useRouter()
const nbStore = useNotebookStore()
const { notebooks } = storeToRefs(nbStore)

const stage = ref(0)
const subject = ref('')
const notebookId = ref<number | null>(null)
const count = ref(10)
const dueCount = ref(0)
const starting = ref(false)
const submitting = ref(false)

const reviewId = ref('')
const questions = ref<ReviewQuestion[]>([])
const currentIndex = ref(0)
const answers = ref<string[]>([])
const unansweredWarning = ref(false)

const result = ref<ReviewSubmitResponse | null>(null)

const subjectOptions = computed(() => Array.from(new Set(notebooks.value.map((n) => n.subject))))
const currentQuestion = computed(() => questions.value[currentIndex.value])
const unansweredCount = computed(() => answers.value.filter((a) => !a || !a.trim()).length)

onMounted(async () => {
  await nbStore.fetchNotebooks()
  const today = await reviewApi.getReviewToday()
  dueCount.value = today.count
})

function goHome() {
  router.push('/errors')
}
async function start() {
  starting.value = true
  try {
    const res = await reviewApi.startReview({
      subject: subject.value || null,
      notebook_id: notebookId.value,
      count: count.value,
    })
    reviewId.value = res.review_id
    questions.value = res.questions
    answers.value = res.questions.map(() => '')
    currentIndex.value = 0
    stage.value = 1
  } catch {
    /* interceptor toast — AC-4.2 / AC-4.4 */
  } finally {
    starting.value = false
  }
}
function next() {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value++
}
function skip() {
  answers.value[currentIndex.value] = ''
  next()
}
async function submit() {
  if (unansweredCount.value > 0) {
    unansweredWarning.value = true
    return
  }
  submitting.value = true
  try {
    const res = await reviewApi.submitReview({
      review_id: reviewId.value,
      answers: questions.value.map((q, i) => ({
        error_id: q.error_id,
        index: q.index,
        user_answer: answers.value[i] || '',
      })),
    })
    result.value = res
    stage.value = 2
  } catch {
    /* interceptor toast — AC-4.4 */
  } finally {
    submitting.value = false
  }
}
function rClass(r: any) {
  if (r.is_correct) return 'ok'
  if (r.sm2_updated) return 'bad'
  return 'skip'
}
function restart() {
  stage.value = 0
  result.value = null
  start()
}
</script>

<style scoped>
.review-page {
  max-width: 672px;
  margin: 0 auto;
}
.stage-panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-xl);
}
.form-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}
.form-row label {
  font: var(--font-body);
  color: var(--color-text-secondary);
  min-width: 64px;
}
.select {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 8px 12px;
  font: var(--font-body);
}
.due-info {
  font: var(--font-body);
  color: var(--color-text-secondary);
  margin: var(--space-md) 0;
}
.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}
.btn-primary,
.btn-secondary {
  border-radius: var(--radius-button);
  padding: 8px 18px;
  font: var(--font-body);
  cursor: pointer;
}
.btn-primary {
  background: var(--color-primary);
  color: #fff;
  border: 1px solid var(--color-primary);
}
.btn-primary:disabled {
  opacity: 0.6;
}
.btn-secondary {
  background: var(--color-bg-card);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}
.answer-head {
  font: var(--font-h2);
  margin-bottom: var(--space-md);
}
.answer-label {
  display: block;
  font: var(--font-body);
  color: var(--color-text-secondary);
  margin: var(--space-lg) 0 var(--space-sm);
}
.answer-input {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 10px 12px;
  font: var(--font-body);
  resize: vertical;
  outline: none;
}
.answer-input:focus {
  border-color: var(--color-primary);
}
.inline-warning {
  margin-top: var(--space-md);
  color: var(--color-warning);
  font: var(--font-caption);
}
.link-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  margin-left: var(--space-sm);
  font: var(--font-caption);
  text-decoration: underline;
}
.result-summary {
  text-align: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}
.rs-score {
  font: var(--font-h2);
}
.rs-stats,
.rs-mastery {
  font: var(--font-body);
  color: var(--color-text-secondary);
  margin-top: var(--space-xs);
}
.result-card {
  border: 1px solid var(--color-border);
  border-left-width: 4px;
  border-radius: var(--radius-card);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}
.result-card.ok {
  border-left-color: var(--color-success);
}
.result-card.bad {
  border-left-color: var(--color-error);
}
.result-card.skip {
  border-left-color: var(--color-text-tertiary);
}
.rc-badge {
  font: var(--font-body);
  font-weight: 600;
}
.rc-badge.ok {
  color: var(--color-success);
}
.rc-badge.bad {
  color: var(--color-error);
}
.rc-badge.skip {
  color: var(--color-text-tertiary);
}
.rc-field {
  font: var(--font-body);
  color: var(--color-text-primary);
  margin-top: var(--space-xs);
  word-break: break-word;
}
.rc-cause {
  font: var(--font-caption);
  color: var(--color-warning);
  margin-top: var(--space-xs);
}
</style>
