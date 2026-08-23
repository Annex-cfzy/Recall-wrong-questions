<template>
  <div class="chat-page">
    <!-- Left: history -->
    <aside class="chat-history">
      <div class="ch-search">
        <Search :size="16" class="ch-search-icon" />
        <input v-model="search" class="ch-search-input" placeholder="搜索对话…" />
      </div>
      <div class="ch-list">
        <div
          v-for="s in filteredSessions"
          :key="s.id"
          class="ch-item"
          :class="{ active: s.id === activeSessionId }"
          @click="selectSession(s.id)"
        >
          <MessageSquare :size="16" class="ch-item-icon" />
          <span class="ch-item-title">{{ s.title }}</span>
          <Trash2
            :size="14"
            class="ch-item-del"
            @click.stop="removeSession(s.id)"
          />
        </div>
      </div>
      <button class="ch-new" @click="newSession">
        <Plus :size="16" /> 新对话
      </button>
    </aside>

    <!-- Right: conversation -->
    <section class="chat-main">
      <div class="chat-titlebar">
        <span class="ct-title">{{ activeTitle }}</span>
        <div class="ct-actions">
          <button class="ct-btn" title="重命名" @click="renameSession">
            <Pencil :size="16" />
          </button>
          <button class="ct-btn" title="删除" @click="removeSession(activeSessionId)">
            <Trash2 :size="16" />
          </button>
        </div>
      </div>

      <div ref="msgEl" class="chat-messages">
        <EmptyState
          v-if="messages.length === 0"
          title="Hi，我是你的 AI 学习助手"
          subtitle="有什么学习问题可以问我？回答可一键加入错题本。"
          :icon="Sparkles"
        />
        <template v-for="(m, i) in messages" :key="i">
          <StreamingMessage
            :text="m.content"
            :role="m.role"
            :streaming="m.streaming"
          />
          <button
            v-if="m.role === 'assistant' && !m.streaming"
            class="add-error-btn"
            @click="openSave(m.id)"
          >
            <Plus :size="14" /> 加入错题本
          </button>
        </template>
        <div v-if="streamError" class="stream-error">{{ streamError }}</div>
      </div>

      <div class="chat-input">
        <textarea
          v-model="draft"
          class="ci-text"
          rows="2"
          placeholder="输入你的学习问题…（Shift+Enter 换行，Enter 发送）"
          @keydown.enter.exact.prevent="send"
        ></textarea>
        <div class="ci-actions">
          <button v-if="!streaming" class="btn-primary" @click="send">发送</button>
          <button v-else class="btn-secondary" @click="stop">停止生成</button>
        </div>
      </div>
    </section>

    <!-- Save to errors modal -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="showSave" class="save-mask" @click.self="showSave = false">
          <div class="save-dialog">
            <p class="save-title">加入错题本</p>
            <label class="save-field">
              <span>错题本</span>
              <select v-model="saveNotebook" class="select">
                <option v-for="nb in notebooks" :key="nb.id" :value="nb.id">{{ nb.name }}</option>
              </select>
            </label>
            <label class="save-field">
              <span>学科</span>
              <input v-model="saveSubject" class="input" placeholder="如：数学" />
            </label>
            <div class="save-actions">
              <button class="btn-cancel" @click="showSave = false">取消</button>
              <button class="btn-primary" @click="confirmSave">保存</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Search,
  Plus,
  MessageSquare,
  Trash2,
  Pencil,
  Sparkles,
} from 'lucide-vue-next'
import StreamingMessage from '@/components/StreamingMessage.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useNotebookStore } from '@/stores/notebook'
import * as chatApi from '@/api/chat'
import { ElMessage } from 'element-plus'
import type { ChatMessage, ChatSession } from '@/types'
type ChatMsg = ChatMessage & { streaming?: boolean }

const nbStore = useNotebookStore()
const { notebooks } = storeToRefs(nbStore)

const sessions = ref<ChatSession[]>([])
const activeSessionId = ref<number | null>(null)
const messages = ref<ChatMsg[]>([])
const search = ref('')
const draft = ref('')
const streaming = ref(false)
const streamError = ref('')
const abortCtrl = ref<AbortController | null>(null)
const msgEl = ref<HTMLElement | null>(null)

const showSave = ref(false)
const saveMessageId = ref<number | null>(null)
const saveNotebook = ref<number | null>(null)
const saveSubject = ref('数学')

const activeTitle = computed(
  () => sessions.value.find((s) => s.id === activeSessionId.value)?.title || 'AI 答疑'
)
const filteredSessions = computed(() =>
  sessions.value.filter((s) => s.title.includes(search.value))
)

onMounted(async () => {
  await nbStore.fetchNotebooks()
  saveNotebook.value = notebooks.value[0]?.id ?? null
  await loadSessions()
})

async function loadSessions() {
  sessions.value = await chatApi.listSessions()
  if (!activeSessionId.value && sessions.value.length) {
    await selectSession(sessions.value[0].id)
  }
}

async function selectSession(id: number) {
  activeSessionId.value = id
  messages.value = await chatApi.getMessages(id)
  scrollBottom()
}

async function newSession() {
  const s = await chatApi.createSession('新对话')
  sessions.value.unshift(s)
  activeSessionId.value = s.id
  messages.value = []
}

async function removeSession(id: number | null) {
  if (id == null) return
  await chatApi.deleteSession(id)
  sessions.value = sessions.value.filter((s) => s.id !== id)
  if (activeSessionId.value === id) {
    activeSessionId.value = null
    messages.value = []
    if (sessions.value.length) await selectSession(sessions.value[0].id)
  }
}

async function renameSession() {
  const title = prompt('请输入对话标题')
  if (!title) return
  ElMessage.info('重命名功能（PUT /chat/sessions）可后续接入')
}

async function send() {
  if (!draft.value.trim() || streaming.value) return
  if (!activeSessionId.value) await newSession()
  const sid = activeSessionId.value!
  const userMsg: ChatMsg = {
    id: -Date.now(),
    session_id: sid,
    role: 'user',
    content: draft.value,
    created_at: null,
  }
  messages.value.push(userMsg)
  const assistantMsg: ChatMsg = {
    id: -Date.now() - 1,
    session_id: sid,
    role: 'assistant',
    content: '',
    created_at: null,
  }
  messages.value.push(assistantMsg)
  streaming.value = true
  streamError.value = ''
  draft.value = ''
  scrollBottom()

  const assistantIndex = messages.value.length - 1
  abortCtrl.value = new AbortController()
  try {
    await chatApi.streamChat(sid, userMsg.content, {
      onChunk: (t) => {
        messages.value[assistantIndex].content += t
        scrollBottom()
      },
      onDone: (content, messageId) => {
        messages.value[assistantIndex].content = content
        messages.value[assistantIndex].id = messageId
        messages.value[assistantIndex].streaming = false
      },
      onError: (msg) => {
        streamError.value = msg
      },
    })
  } finally {
    messages.value[assistantIndex].streaming = false
    streaming.value = false
    await loadSessions()
  }
}

function stop() {
  abortCtrl.value?.abort()
  streaming.value = false
}

function openSave(messageId: number) {
  saveMessageId.value = messageId
  showSave.value = true
}
async function confirmSave() {
  if (!saveMessageId.value || !saveNotebook.value) return
  await chatApi.saveToErrors({
    message_id: saveMessageId.value,
    notebook_id: saveNotebook.value,
    subject: saveSubject.value,
  })
  ElMessage.success('已加入错题本')
  showSave.value = false
}

function scrollBottom() {
  nextTick(() => {
    if (msgEl.value) msgEl.value.scrollTop = msgEl.value.scrollHeight
  })
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - var(--topbar-height) - 2 * var(--space-xl));
}
.chat-history {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
}
.ch-search {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 6px 10px;
  margin-bottom: var(--space-md);
}
.ch-search-icon {
  color: var(--color-text-tertiary);
}
.ch-search-input {
  border: none;
  outline: none;
  background: transparent;
  font: var(--font-body);
  flex: 1;
}
.ch-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ch-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-button);
  cursor: pointer;
  color: var(--color-text-secondary);
}
.ch-item:hover {
  background: var(--color-bg-page);
}
.ch-item.active {
  background: var(--color-bg-page);
  color: var(--color-primary);
}
.ch-item-title {
  flex: 1;
  font: var(--font-body);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ch-item-del {
  display: none;
  color: var(--color-text-tertiary);
}
.ch-item:hover .ch-item-del {
  display: inline;
}
.ch-new {
  margin-top: var(--space-md);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-button);
  padding: 10px;
  background: var(--color-bg-card);
  color: var(--color-primary);
  cursor: pointer;
  font: var(--font-body);
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-left: var(--space-xl);
}
.chat-titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  margin-bottom: var(--space-md);
}
.ct-title {
  font: var(--font-h2);
}
.ct-actions {
  display: flex;
  gap: var(--space-sm);
}
.ct-btn {
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
}
.ct-btn:hover {
  color: var(--color-text-primary);
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-right: var(--space-md);
}
.add-error-btn {
  margin: 0 0 var(--space-md) auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  border-radius: var(--radius-button);
  padding: 4px 10px;
  font: var(--font-caption);
  color: var(--color-primary);
  cursor: pointer;
}
.stream-error {
  color: var(--color-error);
  font: var(--font-caption);
  margin-top: var(--space-sm);
}
.chat-input {
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-md);
}
.ci-text {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 10px 12px;
  font: var(--font-body);
  resize: none;
  outline: none;
}
.ci-text:focus {
  border-color: var(--color-primary);
}
.ci-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-sm);
}
.btn-primary,
.btn-secondary {
  border-radius: var(--radius-button);
  padding: 8px 18px;
  font: var(--font-body);
  cursor: pointer;
}
.btn-primary {
  background: var(--color-primary);
  color: #fff;
  border: 1px solid var(--color-primary);
}
.btn-secondary {
  background: var(--color-bg-card);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}
/* modal */
.save-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.save-dialog {
  width: 360px;
  background: var(--color-bg-card);
  border-radius: var(--radius-card);
  padding: var(--space-xl);
  box-shadow: var(--shadow-popup);
}
.save-title {
  font: var(--font-h2);
  margin: 0 0 var(--space-lg);
}
.save-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
  font: var(--font-body);
  color: var(--color-text-secondary);
}
.select,
.input {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 8px 12px;
  font: var(--font-body);
  outline: none;
}
.save-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}
.btn-cancel {
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  border-radius: var(--radius-button);
  padding: 8px 16px;
  font: var(--font-body);
  cursor: pointer;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
@media (max-width: 767px) {
  .chat-history {
    width: 100%;
    border-right: none;
  }
}
</style>
