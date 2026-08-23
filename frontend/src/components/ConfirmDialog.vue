<template>
  <transition name="fade">
    <div v-if="modelValue" class="confirm-mask" @click.self="onCancel">
      <div class="confirm-dialog" role="alertdialog" aria-live="assertive">
        <p class="confirm-title">{{ title }}</p>
        <p v-if="message" class="confirm-message">{{ message }}</p>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="onCancel">{{ cancelText }}</button>
          <button class="btn-danger" @click="onConfirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    message?: string
    confirmText?: string
    cancelText?: string
  }>(),
  { confirmText: '确认删除', cancelText: '取消' }
)
const emit = defineEmits<{ 'update:modelValue': [boolean]; confirm: []; cancel: [] }>()

function onConfirm() {
  emit('confirm')
  emit('update:modelValue', false)
}
function onCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.confirm-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.confirm-dialog {
  width: 360px;
  background: var(--color-bg-card);
  border-radius: var(--radius-card);
  padding: var(--space-xl);
  box-shadow: var(--shadow-popup);
}
.confirm-title {
  font: var(--font-h2);
  margin: 0 0 var(--space-sm);
  color: var(--color-text-primary);
}
.confirm-message {
  font: var(--font-body);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-lg);
}
.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}
.btn-cancel,
.btn-danger {
  border-radius: var(--radius-button);
  padding: 8px 16px;
  font: var(--font-body);
  cursor: pointer;
  border: 1px solid var(--color-border);
}
.btn-cancel {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}
.btn-danger {
  background: var(--color-error);
  color: #fff;
  border-color: var(--color-error);
}
.btn-danger:hover {
  opacity: 0.9;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
