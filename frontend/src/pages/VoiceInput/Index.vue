<template>
  <div class="voice-input-page">
    <h1 :style="{ font: 'var(--font-h1)' }">语音录入错题</h1>
    <p class="sub">口述题目，AI 实时转成文字并自动分类入库——比拍照更快。</p>

    <div v-if="!supported" class="warn-banner">
      ⚠️ 当前浏览器不支持语音识别（建议使用 Chrome / Edge 桌面版）。你仍可手动在下方输入框填写题目。
    </div>

    <div class="form-card">
      <div class="row">
        <label>错题本
          <select v-model="notebookId" :disabled="loadingNbs">
            <option v-for="n in notebooks" :key="n.id" :value="n.id">{{ n.name }}</option>
          </select>
        </label>
        <label>学科
          <input v-model="subject" type="text" placeholder="如：数学（可留空自动识别）" />
        </label>
      </div>

      <div class="rec-box" :class="{ recording: recording }">
        <button class="rec-btn" :disabled="!supported" @click="toggleRecord">
          <span class="dot"></span>
          {{ recording ? '停止录音' : '开始口述' }}
        </button>
        <span class="rec-status">{{ recStatus }}</span>
      </div>

      <label class="ta-label">题目内容（可编辑）
        <textarea v-model="transcript" rows="6" placeholder="点击“开始口述”后对着麦克风念出题目；或在此直接输入…"></textarea>
      </label>

      <div class="actions">
        <button class="btn primary" :disabled="!canSave" @click="save">保存为错题</button>
        <button class="btn ghost" @click="clearAll">清空</button>
      </div>
      <div v-if="savedId" class="saved-tip">✅ 已保存为错题 #{{ savedId }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as notebooksApi from '@/api/notebooks'
import * as errorsApi from '@/api/errors'
import type { Notebook } from '@/types'

const supported =
  typeof window !== 'undefined' &&
  ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)

const loadingNbs = ref(true)
const notebooks = ref<Notebook[]>([])
const notebookId = ref<number | null>(null)
const subject = ref('')
const transcript = ref('')
const recording = ref(false)
const recStatus = ref('未开始')
const savedId = ref<number | null>(null)

let recognition: any = null

const canSave = computed(
  () => !!notebookId.value && transcript.value.trim().length > 0 && !saving.value
)
const saving = ref(false)

async function loadNotebooks() {
  loadingNbs.value = true
  try {
    const list = await notebooksApi.getNotebooks()
    notebooks.value = list
    if (list.length) notebookId.value = list[0].id
  } finally {
    loadingNbs.value = false
  }
}

function toggleRecord() {
  if (recording.value) {
    recognition?.stop()
    return
  }
  // @ts-ignore - webkit prefix
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SR) return
  recognition = new SR()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  recognition.onresult = (ev: any) => {
    let text = ''
    for (let i = 0; i < ev.results.length; i++) {
      text += ev.results[i][0].transcript
    }
    transcript.value = text
  }
  recognition.onstart = () => {
    recording.value = true
    recStatus.value = '正在聆听…'
  }
  recognition.onend = () => {
    recording.value = false
    recStatus.value = '已停止'
  }
  recognition.onerror = (e: any) => {
    recording.value = false
    recStatus.value = '识别出错：' + (e?.error || '未知')
  }
  recognition.start()
}

async function save() {
  if (!notebookId.value) return
  saving.value = true
  try {
    const res = await errorsApi.createTextError({
      question: transcript.value.trim(),
      answer: '',
      notebook_id: notebookId.value,
      subject: subject.value || notebooks.value.find((n) => n.id === notebookId.value)?.subject || '通用',
    })
    savedId.value = res.id
    ElMessage.success('错题已保存')
    transcript.value = ''
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function clearAll() {
  transcript.value = ''
  savedId.value = null
}

onBeforeUnmount(() => recognition?.stop())
loadNotebooks()
</script>

<style scoped>
.voice-input-page {
  max-width: 720px;
  margin: 0 auto;
}
.sub {
  font: var(--font-body);
  color: var(--color-text-secondary);
  margin: var(--space-sm) 0 var(--space-lg);
}
.warn-banner {
  background: rgba(255, 149, 0, 0.1);
  border: 1px solid rgba(255, 149, 0, 0.3);
  color: #b25e00;
  border-radius: 10px;
  padding: var(--space-md);
  font: var(--font-caption);
  margin-bottom: var(--space-md);
}
.form-card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-lg);
  background: var(--color-bg-card);
  display: grid;
  gap: var(--space-md);
}
.row {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}
.row label,
.ta-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font: var(--font-caption);
  color: var(--color-text-secondary);
  flex: 1;
}
.row select,
.row input,
textarea {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 8px 10px;
  font: var(--font-body);
  color: var(--color-text-primary);
}
textarea {
  resize: vertical;
}
.rec-box {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}
.rec-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--color-primary);
  color: #fff;
  background: var(--color-primary);
  border-radius: var(--radius-button);
  padding: 8px 18px;
  font: var(--font-body);
  cursor: pointer;
}
.rec-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
}
.rec-box.recording .dot {
  background: #ff3b30;
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
.rec-status {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.actions {
  display: flex;
  gap: var(--space-sm);
}
.btn {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  padding: 8px 18px;
  font: var(--font-body);
  cursor: pointer;
  background: var(--color-bg-card);
}
.btn.primary {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn.ghost {
  color: var(--color-text-secondary);
}
.saved-tip {
  font: var(--font-caption);
  color: #34c759;
}
</style>
