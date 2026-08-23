<template>
  <aside class="notebook-list">
    <div class="nl-header">
      <span class="nl-title">错题本列表</span>
    </div>
    <div class="nl-items">
      <div
        v-for="nb in notebooks"
        :key="nb.id"
        class="nl-item"
        :class="{ active: nb.id === activeId }"
        @click="select(nb.id)"
      >
        <span class="nl-dot" :style="{ background: nb.color }"></span>
        <span class="nl-name">{{ nb.name }}</span>
        <span class="nl-count">{{ nb.error_count }} 道</span>
        <span class="nl-actions" @click.stop>
          <button class="nl-icon-btn" title="重命名" @click="startEdit(nb)">
            <Pencil :size="14" />
          </button>
          <button class="nl-icon-btn danger" title="删除" @click="askDelete(nb)">
            <Trash2 :size="14" />
          </button>
        </span>
      </div>
    </div>
    <button class="nl-new" @click="showCreate = true">
      <Plus :size="16" /> 新建错题本
    </button>

    <!-- Create / Edit modal -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="showCreate || editing" class="nb-mask" @click.self="close">
          <div class="nb-dialog">
            <p class="nb-dialog-title">{{ editing ? '编辑错题本' : '新建错题本' }}</p>
            <label class="nb-field">
              <span>名称</span>
              <input v-model="form.name" class="nb-input" placeholder="如：考研数学错题" />
            </label>
            <label class="nb-field">
              <span>学科</span>
              <input v-model="form.subject" class="nb-input" placeholder="如：数学" />
            </label>
            <div class="nb-field">
              <span>颜色</span>
              <ColorPicker v-model="form.color" />
            </div>
            <p v-if="nameError" class="nb-error">请输入错题本名称</p>
            <div class="nb-dialog-actions">
              <button class="btn-cancel" @click="close">取消</button>
              <button class="btn-primary" :disabled="saving" @click="save">
                {{ saving ? '处理中…' : '保存' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <ConfirmDialog
      v-model="showDelete"
      title="删除错题本"
      :message="deleteMessage"
      @confirm="confirmDelete"
    />
  </aside>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { Plus, Pencil, Trash2 } from 'lucide-vue-next'
import ColorPicker from './ColorPicker.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import { useNotebookStore } from '@/stores/notebook'
import { ElMessage } from 'element-plus'
import type { Notebook } from '@/types'

const store = useNotebookStore()
const { notebooks, activeId } = storeToRefs(store)

const showCreate = ref(false)
const editing = ref<Notebook | null>(null)
const saving = ref(false)
const nameError = ref(false)
const showDelete = ref(false)
const deleteTarget = ref<Notebook | null>(null)

const form = reactive({ name: '', subject: '通用', color: '#007AFF' })

function select(id: number) {
  store.setActive(id)
}

function startEdit(nb: Notebook) {
  editing.value = nb
  form.name = nb.name
  form.subject = nb.subject
  form.color = nb.color
}

function close() {
  showCreate.value = false
  editing.value = null
  form.name = ''
  form.subject = '通用'
  form.color = '#007AFF'
  nameError.value = false
}

async function save() {
  if (!form.name.trim()) {
    nameError.value = true
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await store.update(editing.value.id, { ...form })
      ElMessage.success('已保存')
    } else {
      await store.create({ ...form })
      ElMessage.success('错题本已创建')
    }
    close()
  } catch {
    /* intercepted by http interceptor */
  } finally {
    saving.value = false
  }
}

const deleteMessage = ref('')
function askDelete(nb: Notebook) {
  deleteTarget.value = nb
  deleteMessage.value = nb.error_count
    ? `⚠️ 将同时删除本内所有 ${nb.error_count} 道错题，此操作不可撤销`
    : '确认删除该错题本？'
  showDelete.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  await store.remove(deleteTarget.value.id)
  ElMessage.success('删除成功')
  deleteTarget.value = null
}

// Allow the Errors page empty-state CTA to open this modal.
onMounted(() => {
  window.addEventListener('recall:create-notebook', () => {
    close()
    showCreate.value = true
  })
})
</script>

<style scoped>
.notebook-list {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  height: 100%;
}
.nl-header {
  margin-bottom: var(--space-md);
}
.nl-title {
  font: var(--font-h2);
  color: var(--color-text-primary);
}
.nl-items {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nl-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-button);
  cursor: pointer;
  border-left: 4px solid transparent;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.nl-item:hover {
  background: var(--color-bg-page);
}
.nl-item.active {
  background: var(--color-bg-page);
  border-left-color: var(--color-primary);
}
.nl-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.nl-name {
  flex: 1;
  font: var(--font-body);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nl-count {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
}
.nl-actions {
  display: none;
  gap: 2px;
}
.nl-item:hover .nl-actions {
  display: flex;
}
.nl-icon-btn {
  border: none;
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 2px;
}
.nl-icon-btn:hover {
  color: var(--color-text-primary);
}
.nl-icon-btn.danger:hover {
  color: var(--color-error);
}
.nl-new {
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
.nl-new:hover {
  border-color: var(--color-primary);
  background: rgba(0, 122, 255, 0.04);
}
/* modal */
.nb-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.nb-dialog {
  width: 380px;
  background: var(--color-bg-card);
  border-radius: var(--radius-card);
  padding: var(--space-xl);
  box-shadow: var(--shadow-popup);
}
.nb-dialog-title {
  font: var(--font-h2);
  margin: 0 0 var(--space-lg);
}
.nb-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
  font: var(--font-body);
  color: var(--color-text-secondary);
}
.nb-input {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
  padding: 8px 12px;
  font: var(--font-body);
  outline: none;
}
.nb-input:focus {
  border-color: var(--color-primary);
}
.nb-error {
  color: var(--color-error);
  font: var(--font-caption);
  margin: 0 0 var(--space-sm);
}
.nb-dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}
.btn-cancel,
.btn-primary {
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
.btn-primary {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  .notebook-list {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }
}
</style>
