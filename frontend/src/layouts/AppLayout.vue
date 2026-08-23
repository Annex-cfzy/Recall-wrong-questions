<template>
  <div class="app-layout">
    <TopBar />
    <main class="content-area">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import TopBar from '@/components/TopBar.vue'
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: var(--color-bg-page);
}
.content-area {
  padding: var(--space-xl);
  min-height: calc(100vh - var(--topbar-height));
}
@media (max-width: 767px) {
  .content-area {
    padding: 12px;
  }
}
</style>
