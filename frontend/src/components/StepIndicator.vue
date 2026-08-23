<template>
  <div class="step-indicator">
    <div
      v-for="(step, i) in steps"
      :key="step"
      class="step"
      :class="{ active: i === current, done: i < current }"
    >
      <span class="step-dot">{{ i < current ? '✓' : i + 1 }}</span>
      <span class="step-label">{{ step }}</span>
      <span v-if="i < steps.length - 1" class="step-line"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ steps: string[]; current: number }>()
</script>

<style scoped>
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: var(--space-xl);
}
.step {
  display: flex;
  align-items: center;
  color: var(--color-text-tertiary);
}
.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font: var(--font-body);
  background: var(--color-bg-card);
}
.step-label {
  margin: 0 var(--space-sm);
  font: var(--font-body);
}
.step.active .step-dot {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.step.active .step-label {
  color: var(--color-primary);
}
.step.done .step-dot {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.step-line {
  width: 48px;
  height: 1px;
  background: var(--color-border);
  margin: 0 var(--space-sm);
}
</style>
