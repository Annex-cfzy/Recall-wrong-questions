<template>
  <div class="skeleton-block">
    <div class="skeleton skeleton-line" style="height: 14px; width: 40%"></div>
    <div class="skeleton skeleton-line" style="height: 12px; width: 90%"></div>
    <div class="skeleton skeleton-line" style="height: 12px; width: 75%"></div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.skeleton-block {
  padding: var(--space-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}
</style>
