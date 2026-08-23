<template>
  <el-dialog
    :model-value="modelValue"
    title="编辑错题"
    width="560px"
    @update:model-value="(v: boolean) => emit('update:modelValue', v)"
  >
    <div v-if="form" class="edit-body">
      <label class="fld">
        <span>题干 *</span>
        <el-input v-model="form.question" type="textarea" :rows="3" />
      </label>
      <label class="fld">
        <span>答案</span>
        <el-input v-model="form.answer" type="textarea" :rows="2" />
      </label>
      <label class="fld">
        <span>解析</span>
        <el-input v-model="form.analysis" type="textarea" :rows="3" />
      </label>
      <label class="fld">
        <span>错因</span>
        <el-input v-model="form.error_cause" type="textarea" :rows="2" />
      </label>
      <label class="fld">
        <span>知识点（逗号分隔）</span>
        <el-input v-model="kpText" placeholder="导数, 极值" />
      </label>
      <label class="fld">
        <span>学科</span>
        <el-input v-model="form.subject" />
      </label>
    </div>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { updateError } from '@/api/errors'
import type { ErrorItem } from '@/types'
import { UI_ERRORS } from '@/constants/errors'

const props = defineProps<{
  modelValue: boolean
  error: ErrorItem | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [id: number]
}>()

const saving = ref(false)
const form = reactive({
  question: '',
  answer: '',
  analysis: '',
  error_cause: '',
  subject: '',
})
const kpText = ref('')

watch(
  () => props.error,
  (e) => {
    if (!e) return
    form.question = e.question || ''
    form.answer = e.answer || ''
    form.analysis = e.analysis || ''
    form.error_cause = e.error_cause || ''
    form.subject = e.subject || ''
    kpText.value = (e.knowledge_points || []).join('、')
  },
  { immediate: true }
)

const knowledgePoints = computed(() =>
  kpText.value
    .split(/[，,、]/)
    .map((s) => s.trim())
    .filter(Boolean)
)

async function onSave() {
  if (!props.error) return
  if (!form.question.trim()) {
    ElMessage.warning(UI_ERRORS.EMPTY_QUESTION)
    return
  }
  saving.value = true
  try {
    await updateError(props.error.id, {
      question: form.question,
      answer: form.answer,
      analysis: form.analysis,
      error_cause: form.error_cause,
      knowledge_points: knowledgePoints.value,
      subject: form.subject,
    })
    ElMessage.success('保存成功')
    emit('saved', props.error.id)
    emit('update:modelValue', false)
  } catch {
    ElMessage.error(UI_ERRORS.SAVE_FAILED)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.edit-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.fld {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font: var(--font-body);
  color: var(--color-text-secondary);
}
</style>
