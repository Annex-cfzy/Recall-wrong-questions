<template>
  <div
    class="drop-upload"
    :class="{ dragover }"
    @dragenter.prevent="dragover = true"
    @dragover.prevent="dragover = true"
    @dragleave.prevent="dragover = false"
    @drop.prevent="onDrop"
    @click="pickFile"
  >
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      class="hidden-input"
      @change="onFileChange"
    />
    <Camera :size="32" :stroke-width="1.3" class="du-icon" />
    <p class="du-title">拖拽图片到此 / 点击上传</p>
    <p class="du-sub">支持 JPG / PNG / WEBP，单张 ≤ 10MB；也可 Ctrl+V 粘贴截图</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Camera } from 'lucide-vue-next'

const emit = defineEmits<{ file: [File] }>()
const fileInput = ref<HTMLInputElement | null>(null)
const dragover = ref(false)

function pickFile() {
  fileInput.value?.click()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) emit('file', input.files[0])
  input.value = ''
}

function onDrop(e: DragEvent) {
  dragover.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) emit('file', f)
}

// Ctrl+V paste (design doc §5.4.3) — wired by parent via global listener.
function handlePaste(e: ClipboardEvent) {
  const item = Array.from(e.clipboardData?.items || []).find((i) => i.type.startsWith('image/'))
  if (item) {
    const f = item.getAsFile()
    if (f) emit('file', f)
  }
}

defineExpose({ handlePaste })
</script>

<style scoped>
.drop-upload {
  border: 1.5px dashed var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-2xl);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.drop-upload:hover {
  border-color: var(--color-primary);
}
.drop-upload.dragover {
  border: 2px solid var(--color-primary);
  background: var(--color-bg-page);
}
.du-icon {
  color: var(--color-text-tertiary);
}
.du-title {
  font: var(--font-body);
  color: var(--color-text-primary);
  margin: var(--space-sm) 0 4px;
}
.du-sub {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
  margin: 0;
}
.hidden-input {
  display: none;
}
</style>
