<template>
  <div class="input-page">
    <h1 :style="{ font: 'var(--font-h1)' }">录入错题</h1>

    <!-- Method tabs -->
    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.key"
        class="tab"
        :class="{ active: active === t.key }"
        @click="active = t.key"
      >
        <component :is="t.icon" :size="16" /> {{ t.label }}
      </button>
    </div>

    <!-- Photo / OCR -->
    <div v-if="active === 'photo'" class="panel">
      <DropUpload ref="dropRef" @file="onFile" />
      <div v-if="uploading" class="uploading">
        <span class="skeleton" style="height: 12px; width: 40%"></span>
        <p :style="{ font: 'var(--font-caption)', color: 'var(--color-text-tertiary)' }">
          识别中…（OCR < 10s）
        </p>
      </div>

      <div v-if="ocrResult" class="ocr-preview">
        <p class="op-title">识别到 {{ ocrResult.questions.length }} 道题，勾选需要导入的：</p>
        <div
          v-for="q in ocrResult.questions"
          :key="q.index"
          class="ocr-item card-hover"
        >
          <input type="checkbox" v-model="q.selected" class="ocr-check" />
          <textarea v-model="q.question" class="ocr-text" rows="2"></textarea>
        </div>

        <div class="form-row">
          <label>错题本</label>
          <select v-model="selectedNotebook" class="select">
            <option v-for="nb in notebooks" :key="nb.id" :value="nb.id">
              {{ nb.name }}
            </option>
          </select>
        </div>
        <div class="form-row">
          <label>学科</label>
          <input v-model="subject" class="input" placeholder="如：数学" />
        </div>

        <p v-if="noSelection" class="inline-error">请至少选择一道题目</p>
        <div class="panel-actions">
          <button class="btn-secondary" @click="resetPhoto">取消</button>
          <button class="btn-primary" :disabled="importing" @click="importPhoto">
            {{ importing ? '处理中…' : '导入' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Text -->
    <div v-if="active === 'text'" class="panel">
      <div class="form-row col">
        <label>题干 <span class="req">*</span></label>
        <textarea
          v-model="textQuestion"
          class="input area"
          rows="5"
          placeholder="输入或粘贴题目，支持 $LaTeX$ 公式"
        ></textarea>
      </div>
      <div class="form-row col">
        <label>你的答案（可选）</label>
        <textarea v-model="textAnswer" class="input area" rows="2"></textarea>
      </div>
      <div class="form-row">
        <label>错题本</label>
        <select v-model="selectedNotebook" class="select">
          <option v-for="nb in notebooks" :key="nb.id" :value="nb.id">{{ nb.name }}</option>
        </select>
      </div>
      <div class="form-row">
        <label>学科</label>
        <input v-model="subject" class="input" placeholder="如：数学" />
      </div>
      <p v-if="textEmpty" class="inline-error">请输入题目内容</p>
      <div class="panel-actions">
        <button class="btn-secondary" @click="resetText">取消</button>
        <button class="btn-primary" :disabled="importing" @click="submitText">
          {{ importing ? '处理中…' : '导入' }}
        </button>
      </div>
    </div>

    <!-- Chat -->
    <div v-if="active === 'chat'" class="panel chat-jump">
      <MessageSquare :size="40" :stroke-width="1.2" class="cj-icon" />
      <p :style="{ font: 'var(--font-body)' }">在 AI 答疑中提问后，可一键将问答加入错题本。</p>
      <button class="btn-primary" @click="goChat">前往 AI 答疑 →</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { Camera, Type, MessageSquare } from 'lucide-vue-next'
import DropUpload from '@/components/DropUpload.vue'
import { useNotebookStore } from '@/stores/notebook'
import * as errorsApi from '@/api/errors'
import { ElMessage } from 'element-plus'
import type { UploadResult } from '@/api/errors'

const router = useRouter()
const store = useNotebookStore()
const { notebooks } = storeToRefs(store)

const tabs = [
  { key: 'photo', label: '拍照/截图', icon: Camera },
  { key: 'text', label: '文本录入', icon: Type },
  { key: 'chat', label: 'AI 对话', icon: MessageSquare },
]
const active = ref('photo')
const dropRef = ref<InstanceType<typeof DropUpload> | null>(null)

const uploading = ref(false)
const importing = ref(false)
const ocrResult = ref<UploadResult | null>(null)
const noSelection = ref(false)

const textQuestion = ref('')
const textAnswer = ref('')
const textEmpty = ref(false)

const selectedNotebook = ref<number | null>(null)
const subject = ref('数学')

const noNotebook = computed(() => notebooks.value.length === 0)

onMounted(async () => {
  await store.fetchNotebooks()
  selectedNotebook.value = notebooks.value[0]?.id ?? null
  window.addEventListener('paste', onPaste)
})
onUnmounted(() => window.removeEventListener('paste', onPaste))

function onPaste(e: ClipboardEvent) {
  if (active.value !== 'photo') return
  dropRef.value?.handlePaste(e)
}

async function onFile(file: File) {
  uploading.value = true
  ocrResult.value = null
  noSelection.value = false
  try {
    const res = await errorsApi.uploadImage(file)
    ocrResult.value = res
  } catch {
    /* interceptor shows toast; AC-1.2/1.3/1.4 handled by backend codes */
  } finally {
    uploading.value = false
  }
}

async function importPhoto() {
  if (!ocrResult.value) return
  if (!selectedNotebook.value) {
    ElMessage.warning('请先选择错题本')
    return
  }
  const selected = ocrResult.value.questions.filter((q) => q.selected)
  if (!selected.length) {
    noSelection.value = true
    return
  }
  importing.value = true
  try {
    await errorsApi.importErrors(
      selected.map((q) => ({
        question: q.question,
        answer: '',
        notebook_id: selectedNotebook.value!,
        subject: subject.value,
        source: 'photo',
        image_path: null,
      }))
    )
    ElMessage.success('录入成功')
    router.push('/errors')
  } catch {
    /* interceptor toast */
  } finally {
    importing.value = false
  }
}

async function submitText() {
  if (!textQuestion.value.trim()) {
    textEmpty.value = true
    return
  }
  if (!selectedNotebook.value) {
    ElMessage.warning('请先选择错题本')
    return
  }
  importing.value = true
  try {
    await errorsApi.createTextError({
      question: textQuestion.value,
      answer: textAnswer.value,
      notebook_id: selectedNotebook.value,
      subject: subject.value,
    })
    ElMessage.success('录入成功')
    router.push('/errors')
  } catch {
    /* interceptor toast */
  } finally {
    importing.value = false
  }
}

function resetPhoto() {
  ocrResult.value = null
  noSelection.value = false
}
function resetText() {
  textQuestion.value = ''
  textAnswer.value = ''
  textEmpty.value = false
}
function goChat() {
  router.push('/chat')
}
</script>

<style scoped>
.input-page {
  max-width: 768px;
  margin: 0 auto;
}
.tabs {
  display: flex;
  gap: var(--space-sm);
  margin: var(--space-lg) 0;
}
.tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  border-radius: var(--radius-button);
  padding: 8px 16px;
  font: var(--font-body);
  color: var(--color-text-secondary);
  cursor: pointer;
}
.tab.active {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: rgba(0, 122, 255, 0.06);
}
.panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-xl);
}
.uploading {
  margin-top: var(--space-md);
}
.ocr-preview {
  margin-top: var(--space-lg);
}
.op-title {
  font: var(--font-body);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-md);
}
.ocr-item {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-sm);
  margin-bottom: var(--space-sm);
}
.ocr-check {
  margin-top: 6px;
}
.ocr-text {
  flex: 1;
  border: none;
  outline: none;
  resize: vertical;
  font: var(--font-body);
  color: var(--color-text-primary);
}
.form-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}
.form-row.col {
  flex-direction: column;
  align-items: stretch;
}
.form-row label {
  font: var(--font-body);
  color: var(--color-text-secondary);
  min-width: 64px;
}
.req {
  color: var(--color-error);
}
.input,
.select {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 8px 12px;
  font: var(--font-body);
  outline: none;
}
.input.area {
  resize: vertical;
}
.input:focus,
.select:focus {
  border-color: var(--color-primary);
}
.inline-error {
  color: var(--color-error);
  font: var(--font-caption);
  margin: 0 0 var(--space-sm);
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
.chat-jump {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-2xl);
}
.cj-icon {
  color: var(--color-text-tertiary);
}
</style>
