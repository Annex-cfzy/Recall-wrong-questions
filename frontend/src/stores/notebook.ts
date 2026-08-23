import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Notebook, NotebookPayload } from '@/types'
import * as notebooksApi from '@/api/notebooks'

export const useNotebookStore = defineStore('notebook', () => {
  const notebooks = ref<Notebook[]>([])
  const activeId = ref<number | null>(null)
  const loading = ref(false)

  async function fetchNotebooks() {
    loading.value = true
    try {
      notebooks.value = await notebooksApi.getNotebooks()
      if (!activeId.value && notebooks.value.length) {
        activeId.value = notebooks.value[0].id
      }
    } finally {
      loading.value = false
    }
  }

  async function create(payload: NotebookPayload) {
    const nb = await notebooksApi.createNotebook(payload)
    notebooks.value.unshift(nb)
    return nb
  }

  async function update(id: number, payload: Partial<NotebookPayload>) {
    await notebooksApi.updateNotebook(id, payload)
    const nb = notebooks.value.find((n) => n.id === id)
    if (nb) Object.assign(nb, payload)
  }

  async function remove(id: number) {
    const res = await notebooksApi.deleteNotebook(id)
    notebooks.value = notebooks.value.filter((n) => n.id !== id)
    if (activeId.value === id) activeId.value = notebooks.value[0]?.id ?? null
    return res
  }

  function setActive(id: number) {
    activeId.value = id
  }

  return { notebooks, activeId, loading, fetchNotebooks, create, update, remove, setActive }
})
