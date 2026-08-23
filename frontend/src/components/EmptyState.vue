<template>
  <div class="empty-state">
    <div class="empty-icon">
      <slot name="icon">
        <component :is="displayIcon" :size="48" :stroke-width="1.2" />
      </slot>
    </div>
    <p class="empty-title">{{ title }}</p>
    <p v-if="subtitle" class="empty-subtitle">{{ subtitle }}</p>
    <div class="empty-actions">
      <slot name="actions">
        <button v-if="primaryText" class="btn-primary" @click="emit('primary')">
          {{ primaryText }}
        </button>
        <button v-if="secondaryText" class="btn-secondary" @click="emit('secondary')">
          {{ secondaryText }}
        </button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Inbox } from 'lucide-vue-next'
import type { Component } from 'vue'

const props = defineProps<{
  title: string
  subtitle?: string
  primaryText?: string
  secondaryText?: string
  icon?: Component
}>()
const emit = defineEmits<{ primary: []; secondary: [] }>()
const displayIcon = computed(() => props.icon ?? Inbox)
</script>

<style scoped>
.empty-state {
  height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: var(--space-sm);
}
.empty-icon {
  color: var(--color-text-tertiary);
}
.empty-title {
  font: var(--font-body);
  color: var(--color-text-primary);
  margin: 0;
}
.empty-subtitle {
  font: var(--font-caption);
  color: var(--color-text-secondary);
  margin: 0;
}
.empty-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}
.btn-primary {
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-button);
  padding: 8px 16px;
  font: var(--font-body);
  cursor: pointer;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
}
.btn-secondary {
  background: var(--color-bg-card);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-button);
  padding: 8px 16px;
  font: var(--font-body);
  cursor: pointer;
}
.btn-secondary:hover {
  background: var(--color-bg-page);
}
</style>
