<template>
  <div class="analysis-area">
    <div class="aa-label">解析</div>
    <div class="aa-content"><slot /></div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
/* 解析区：绿色左边框 (设计文档 §4.1) */
.analysis-area {
  border-left: 4px solid var(--color-area-analysis);
  background: rgba(16, 185, 129, 0.04);
  padding: var(--space-md) var(--space-lg);
  border-radius: 0 var(--radius-card) var(--radius-card) 0;
  margin-top: var(--space-sm);
}
.aa-label {
  font: var(--font-caption);
  color: var(--color-area-analysis);
  margin-bottom: var(--space-xs);
  font-weight: 600;
}
.aa-content {
  font: var(--font-body);
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
