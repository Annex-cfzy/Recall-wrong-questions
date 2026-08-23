<template>
  <div class="question-area">
    <div class="qa-label">题目</div>
    <div class="qa-content"><slot /></div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
/* 题目区：蓝色左边框 (设计文档 §4.1) */
.question-area {
  border-left: 4px solid var(--color-area-question);
  background: rgba(59, 130, 246, 0.04);
  padding: var(--space-md) var(--space-lg);
  border-radius: 0 var(--radius-card) var(--radius-card) 0;
}
.qa-label {
  font: var(--font-caption);
  color: var(--color-area-question);
  margin-bottom: var(--space-xs);
  font-weight: 600;
}
.qa-content {
  font: var(--font-body);
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
