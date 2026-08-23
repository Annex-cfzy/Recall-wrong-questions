<template>
  <div class="voice-page">
    <div class="dash-header">
      <h1 :style="{ font: 'var(--font-h1)' }">语音讲解卡</h1>
      <span class="hint">碎片时间 · 听讲解复习（浏览器实时朗读，无需联网）</span>
    </div>

    <div class="voice-layout">
      <!-- 错题列表 -->
      <aside class="err-list">
        <div class="el-title">选择一道错题</div>
        <div v-if="loadingList" class="skeleton" style="height: 200px"></div>
        <div v-else-if="errors.length === 0" class="empty-tip">还没有错题，去录入几道吧。</div>
        <button
          v-for="e in errors"
          :key="e.id"
          class="err-item"
          :class="{ active: selectedId === e.id }"
          @click="selectError(e.id)"
        >
          <span class="ei-q">{{ e.question }}</span>
          <span class="ei-subj">{{ e.subject }}</span>
        </button>
      </aside>

      <!-- 讲解卡 -->
      <section class="card-area">
        <div v-if="loadingCard" class="skeleton" style="height: 320px; border-radius: 12px"></div>
        <template v-else-if="card">
          <div class="card-head">
            <h2 class="card-title">{{ card.title }}</h2>
            <div class="tts-ctrl">
              <button class="btn" :disabled="!canSpeak" @click="toggleSpeak">
                {{ speaking ? '⏸ 暂停' : '🔊 朗读' }}
              </button>
              <button class="btn ghost" :disabled="!canSpeak" @click="stopSpeak">⏹ 停止</button>
              <span v-if="!canSpeak" class="no-tts">浏览器不支持语音合成</span>
            </div>
          </div>
          <div class="sections">
            <div v-for="(s, i) in card.sections" :key="i" class="section">
              <div class="sec-type">{{ s.type }}</div>
              <div class="sec-text">{{ s.text }}</div>
            </div>
          </div>
          <div class="script-box">
            <div class="sb-title">口播稿（可整段朗读）</div>
            <p class="sb-text">{{ card.tts_script }}</p>
          </div>
        </template>
        <div v-else class="empty-tip big">从左侧选择一道错题，生成可朗读的讲解卡。</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as errorsApi from '@/api/errors'
import * as upgradeApi from '@/api/upgrade'
import type { ErrorItem } from '@/types'
import type { VoiceCard } from '@/types/upgrade'

const loadingList = ref(true)
const loadingCard = ref(false)
const errors = ref<ErrorItem[]>([])
const selectedId = ref<number | null>(null)
const card = ref<VoiceCard | null>(null)
const speaking = ref(false)
const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window

async function loadList() {
  loadingList.value = true
  try {
    const res = await errorsApi.getErrorList({ page: 1, page_size: 100 })
    errors.value = res.items
  } finally {
    loadingList.value = false
  }
}

async function selectError(id: number) {
  selectedId.value = id
  stopSpeak()
  loadingCard.value = true
  card.value = null
  try {
    card.value = await upgradeApi.getVoiceCard(id)
  } catch (e) {
    ElMessage.error('生成讲解卡失败')
  } finally {
    loadingCard.value = false
  }
}

function toggleSpeak() {
  if (!card.value) return
  if (speaking.value) {
    window.speechSynthesis.pause()
    speaking.value = false
    return
  }
  speak(card.value.tts_script)
}
function speak(text: string) {
  if (!canSpeak) return
  const synth = window.speechSynthesis
  synth.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = 'zh-CN'
  u.rate = 0.95
  u.onstart = () => (speaking.value = true)
  u.onend = () => (speaking.value = false)
  u.onerror = () => (speaking.value = false)
  synth.speak(u)
}
function stopSpeak() {
  if (canSpeak) window.speechSynthesis.cancel()
  speaking.value = false
}

onBeforeUnmount(stopSpeak)
loadList()
</script>

<style scoped>
.voice-page {
  max-width: 1100px;
  margin: 0 auto;
}
.dash-header {
  display: flex;
  align-items: baseline;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}
.hint {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.voice-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: var(--space-lg);
}
.err-list {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-md);
  background: var(--color-bg-card);
  align-self: start;
  max-height: 70vh;
  overflow: auto;
}
.el-title {
  font: var(--font-h2);
  margin-bottom: var(--space-sm);
}
.err-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 8px 10px;
  background: transparent;
  cursor: pointer;
  margin-bottom: 4px;
}
.err-item:hover {
  background: var(--color-bg-page);
}
.err-item.active {
  border-color: var(--color-primary);
  background: rgba(0, 122, 255, 0.06);
}
.ei-q {
  font: var(--font-body);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.ei-subj {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.card-area {
  min-height: 300px;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-bottom: var(--space-md);
}
.card-title {
  font: var(--font-h2);
  color: var(--color-text-primary);
}
.tts-ctrl {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.btn {
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  background: rgba(0, 122, 255, 0.06);
  border-radius: var(--radius-button);
  padding: 6px 14px;
  font: var(--font-body);
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn.ghost {
  border-color: var(--color-border);
  color: var(--color-text-secondary);
  background: transparent;
}
.no-tts {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.sections {
  display: grid;
  gap: var(--space-sm);
}
.section {
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--color-primary);
  border-radius: 10px;
  padding: var(--space-md);
  background: var(--color-bg-card);
}
.sec-type {
  font: var(--font-caption);
  color: var(--color-primary);
  margin-bottom: 4px;
}
.sec-text {
  font: var(--font-body);
  color: var(--color-text-primary);
  white-space: pre-wrap;
}
.script-box {
  margin-top: var(--space-md);
  border: 1px dashed var(--color-border);
  border-radius: 10px;
  padding: var(--space-md);
}
.sb-title {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
  margin-bottom: 4px;
}
.sb-text {
  font: var(--font-body);
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  margin: 0;
}
.empty-tip {
  font: var(--font-body);
  color: var(--color-text-tertiary);
  padding: var(--space-md);
}
.empty-tip.big {
  border: 1px dashed var(--color-border);
  border-radius: 12px;
  padding: var(--space-xl);
  text-align: center;
}
@media (max-width: 767px) {
  .voice-layout {
    grid-template-columns: 1fr;
  }
}
</style>
