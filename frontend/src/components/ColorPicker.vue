<template>
  <div class="color-picker-wrap">
    <button class="color-trigger" @click="open = !open" type="button">
      <span class="color-dot" :style="{ background: modelValue }"></span>
      <span class="color-label">选择颜色</span>
    </button>
    <Teleport to="body">
      <transition name="pop">
        <div
          v-if="open"
          class="color-popup"
          :style="popupStyle"
          @click.stop
        >
          <button
            v-for="c in palette"
            :key="c"
            class="color-swatch"
            :class="{ selected: c === modelValue }"
            :style="{ background: c }"
            type="button"
            @click="select(c)"
          />
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()

const palette = [
  '#007AFF',
  '#34C759',
  '#FF9500',
  '#AF52DE',
  '#FF2D55',
  '#5AC8FA',
  '#FFCC00',
  '#5856D6',
]

const open = ref(false)
const popupStyle = ref({})

function select(c: string) {
  emit('update:modelValue', c)
  open.value = false
}
</script>

<style scoped>
.color-trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  padding: 6px 12px;
  background: var(--color-bg-card);
  cursor: pointer;
  font: var(--font-body);
}
.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-block;
}
.color-popup {
  position: fixed;
  z-index: 9999;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-popup);
}
.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
}
.color-swatch.selected {
  border-color: var(--color-text-primary);
}
.pop-enter-active,
.pop-leave-active {
  transition: opacity 0.15s ease;
}
.pop-enter-from,
.pop-leave-to {
  opacity: 0;
}
</style>
