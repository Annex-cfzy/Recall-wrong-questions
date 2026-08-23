<template>
  <el-dialog
    :model-value="modelValue"
    title="导出错题本"
    width="420px"
    @update:model-value="(v: boolean) => emit('update:modelValue', v)"
  >
    <div class="export-body">
      <div class="field">
        <span class="field-label">导出格式</span>
        <el-radio-group v-model="format">
          <el-radio value="pdf">PDF（排版打印）</el-radio>
          <el-radio value="md">Markdown（可编辑）</el-radio>
        </el-radio-group>
      </div>

      <div class="field">
        <span class="field-label">包含内容</span>
        <el-checkbox v-model="includeAnswer">包含答案与解析</el-checkbox>
      </div>

      <p class="export-hint">
        文件名格式：<code>{{ notebookName }}_{{ today }}.{{ format }}</code>
      </p>
    </div>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="onConfirm">开始导出</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { exportPdf, exportMarkdown } from '@/api/export'
import { UI_ERRORS } from '@/constants/errors'

const props = defineProps<{
  modelValue: boolean
  notebookId: number | null
  notebookName: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const format = ref<'pdf' | 'md'>('pdf')
const includeAnswer = ref(true)
const today = new Date().toISOString().slice(0, 10)

const canExport = computed(() => props.notebookId != null)

function onConfirm() {
  if (!canExport.value) {
    ElMessage.warning(UI_ERRORS.NO_NOTEBOOK_SELECTED)
    return
  }
  if (format.value === 'pdf') {
    exportPdf(props.notebookId as number, includeAnswer.value)
  } else {
    exportMarkdown(props.notebookId as number, includeAnswer.value)
  }
  ElMessage.success('已触发下载，请稍候')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.export-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.field-label {
  font: var(--font-body);
  color: var(--color-text-secondary);
}
.export-hint {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.export-hint code {
  color: var(--color-primary);
}
</style>
