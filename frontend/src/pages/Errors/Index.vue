<template>
  <div class="errors-page">
    <NotebookList class="errors-sidebar" />

    <section class="errors-main">
      <!-- Operation bar -->
      <div class="op-bar">
        <div class="op-left">
          <button class="btn-primary" @click="goInput">
            <Plus :size="14" /> 录入
          </button>
          <button class="btn-secondary" @click="goExport">
            <Download :size="14" /> 导出
          </button>
          <button class="btn-secondary" @click="goReview">
            <Play :size="14" /> 开始复习
          </button>
        </div>
        <div class="op-right">
          <Search :size="16" class="op-search-icon" />
          <input
            v-model="searchInput"
            class="op-search"
            placeholder="搜索错题…"
            @keyup.enter="onSearch"
          />
          <button class="btn-ghost" title="筛选" @click="showFilter = !showFilter">
            <SlidersHorizontal :size="16" />
          </button>
        </div>
      </div>

      <!-- Filter row -->
      <div v-if="showFilter" class="filter-row">
        <select v-model="filterSubject" class="select" @change="applyFilter">
          <option value="">全部学科</option>
          <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="filterMastery" class="select" @change="applyFilter">
          <option value="">全部掌握度</option>
          <option value="0-50">未掌握 0–50%</option>
          <option value="50-80">复习中 50–80%</option>
          <option value="80-100">已掌握 80–100%</option>
        </select>
        <label class="due-toggle">
          <input type="checkbox" v-model="filterDue" @change="applyFilter" /> 仅看待复习
        </label>
      </div>

      <!-- Content area -->
      <div ref="scrollEl" class="errors-content" @scroll="onScroll">
        <EmptyState
          v-if="!hasNotebooks"
          title="还没有错题本，创建第一个开始记录吧"
          subtitle="Recall 帮你拍照/文本快速录入错题，AI 自动归类复习"
          primary-text="新建错题本"
          @primary="onCreateNotebook"
        />
        <template v-else>
          <EmptyState
            v-if="!store.loading && store.items.length === 0"
            title="该错题本还没有错题"
            subtitle="试试以下方式快速录入"
            :icon="NotebookPen"
          >
            <template #actions>
              <button class="btn-primary" @click="goInput">对话录入</button>
              <button class="btn-secondary" @click="goInput">识图录入</button>
              <button class="btn-secondary" @click="goInput">文本录入</button>
            </template>
          </EmptyState>

          <div v-for="err in store.items" :key="err.id">
            <ErrorCard
              :error="err"
              @edit="onEdit"
              @delete="onDelete"
            />
          </div>

          <Skeleton v-if="store.loading" v-for="n in 3" :key="'sk' + n" />

          <p v-if="!store.hasMore && store.items.length" class="load-end">— 没有更多了 —</p>
        </template>
      </div>
    </section>

    <ExportModal
      v-model="showExport"
      :notebook-id="nbStore.activeId"
      :notebook-name="activeNotebookName"
    />
    <ErrorEditModal v-model="showEdit" :error="editingError" @saved="onSaved" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Plus,
  Download,
  Play,
  Search,
  SlidersHorizontal,
  NotebookPen,
} from 'lucide-vue-next'
import NotebookList from '@/components/NotebookList.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorCard from '@/components/ErrorCard.vue'
import ExportModal from '@/components/ExportModal.vue'
import ErrorEditModal from '@/components/ErrorEditModal.vue'
import Skeleton from '@/components/Skeleton.vue'
import { useNotebookStore } from '@/stores/notebook'
import { useErrorStore } from '@/stores/error'
import { getErrorDetail } from '@/api/errors'
import { ElMessage } from 'element-plus'
import type { ErrorItem } from '@/types'

const route = useRoute()
const router = useRouter()
const nbStore = useNotebookStore()
const store = useErrorStore()

const searchInput = ref((route.query.search as string) || '')
const showFilter = ref(false)
const filterSubject = ref('')
const filterMastery = ref('')
const filterDue = ref(false)
const scrollEl = ref<HTMLElement | null>(null)

const hasNotebooks = computed(() => nbStore.notebooks.length > 0)
const subjectOptions = computed(() =>
  Array.from(new Set(nbStore.notebooks.map((n) => n.subject)))
)
const activeNotebookName = computed(
  () => nbStore.notebooks.find((n) => n.id === nbStore.activeId)?.name || '错题本'
)
const showExport = ref(false)
const showEdit = ref(false)
const editingError = ref<ErrorItem | null>(null)

onMounted(async () => {
  await nbStore.fetchNotebooks()
  await reload()
})

watch(
  () => nbStore.activeId,
  () => reload()
)

function buildParams() {
  const p: Record<string, unknown> = {}
  if (searchInput.value) p.search = searchInput.value
  if (filterSubject.value) p.subject = filterSubject.value
  if (filterDue.value) p.is_due = true
  if (filterMastery.value) {
    const [a, b] = filterMastery.value.split('-').map(Number)
    p.mastery_min = a
    p.mastery_max = b
  }
  return p
}

async function reload() {
  await store.fetchErrors({ notebook_id: nbStore.activeId ?? undefined, ...buildParams() }, true)
}

function onSearch() {
  router.replace({ path: '/errors', query: searchInput.value ? { search: searchInput.value } : {} })
  reload()
}
function applyFilter() {
  reload()
}

function onScroll() {
  const el = scrollEl.value
  if (!el || store.loading || !store.hasMore) return
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 100) {
    store.fetchErrors({ notebook_id: nbStore.activeId ?? undefined, ...buildParams() }, false)
  }
}

function goInput() {
  router.push('/input')
}
function goReview() {
  router.push('/review')
}
function goExport() {
  if (nbStore.activeId == null) {
    ElMessage.warning('请先选择一个错题本')
    return
  }
  showExport.value = true
}
function onCreateNotebook() {
  window.dispatchEvent(new CustomEvent('recall:create-notebook'))
}
async function onEdit(id: number) {
  try {
    editingError.value = await getErrorDetail(id)
    showEdit.value = true
  } catch {
    ElMessage.error('加载错题失败，请重试')
  }
}
async function onSaved() {
  await reload()
}
async function onDelete(id: number) {
  await store.remove(id)
  ElMessage.success('删除成功')
}
</script>

<style scoped>
.errors-page {
  display: flex;
  gap: 0;
  align-items: stretch;
  min-height: calc(100vh - var(--topbar-height) - 2 * var(--space-xl));
}
.errors-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-left: var(--space-xl);
}
.op-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  margin-bottom: var(--space-lg);
  gap: var(--space-md);
}
.op-left {
  display: flex;
  gap: var(--space-sm);
}
.op-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 6px 12px;
  min-width: 240px;
}
.op-search-icon {
  color: var(--color-text-tertiary);
}
.op-search {
  border: none;
  outline: none;
  background: transparent;
  font: var(--font-body);
  flex: 1;
}
.filter-row {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
  align-items: center;
  flex-wrap: wrap;
}
.select {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 6px 10px;
  font: var(--font-body);
}
.due-toggle {
  font: var(--font-caption);
  color: var(--color-text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.btn-primary,
.btn-secondary,
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: var(--radius-button);
  padding: 7px 14px;
  font: var(--font-body);
  cursor: pointer;
  border: 1px solid transparent;
}
.btn-primary {
  background: var(--color-primary);
  color: #fff;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
}
.btn-secondary {
  background: var(--color-bg-card);
  color: var(--color-primary);
  border-color: var(--color-primary);
}
.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
  padding: 6px;
}
.btn-ghost:hover {
  background: var(--color-bg-page);
}
.errors-content {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - var(--topbar-height) - 2 * var(--space-xl) - 90px);
}
.load-end {
  text-align: center;
  font: var(--font-caption);
  color: var(--color-text-tertiary);
  padding: var(--space-md);
}
@media (max-width: 767px) {
  .errors-page {
    flex-direction: column;
  }
  .errors-main {
    padding-left: 0;
  }
  .op-bar {
    flex-direction: column;
    align-items: stretch;
    height: auto;
    gap: var(--space-sm);
  }
  .op-right {
    min-width: 0;
  }
}
@media (min-width: 768px) and (max-width: 1199px) {
  .errors-sidebar {
    width: 220px;
    flex: 0 0 220px;
  }
  .errors-main {
    padding-left: var(--space-lg);
  }
}
</style>
