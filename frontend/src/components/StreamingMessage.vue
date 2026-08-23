<template>
  <div class="streaming-message" :class="role">
    <div class="sm-bubble">
      <pre class="sm-text">{{ text }}<span v-if="streaming" class="sm-cursor"></span></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ text: string; role: 'user' | 'assistant'; streaming?: boolean }>()
</script>

<style scoped>
.streaming-message {
  display: flex;
  margin-bottom: var(--space-md);
}
.streaming-message.user {
  justify-content: flex-end;
}
.sm-bubble {
  max-width: 80%;
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-card);
  white-space: pre-wrap;
  word-break: break-word;
  font: var(--font-body);
}
.streaming-message.user .sm-bubble {
  background: var(--color-primary);
  color: #fff;
}
.streaming-message.assistant .sm-bubble {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}
.sm-text {
  margin: 0;
  font: var(--font-body);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}
.sm-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--color-primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s steps(2) infinite;
}
@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  50.01%,
  100% {
    opacity: 0;
  }
}
</style>
