import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ErrorItem, ErrorListParams } from '@/types'
import * as errorsApi from '@/api/errors'

export const useErrorStore = defineStore('error', () => {
  const items = ref<ErrorItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const loading = ref(false)
  const hasMore = ref(true)
  const params = ref<ErrorListParams>({ page: 1, page_size: 20 })

  async function fetchErrors(opts: Partial<ErrorListParams> = {}, reset = false) {
    if (reset) {
      page.value = 1
      items.value = []
    }
    const merged = { ...params.value, ...opts, page: reset ? 1 : page.value }
    params.value = merged
    loading.value = true
    try {
      const res = await errorsApi.getErrorList(merged)
      if (reset) {
        items.value = res.items
      } else {
        // De-dupe by id when appending pages.
        const seen = new Set(items.value.map((i) => i.id))
        items.value.push(...res.items.filter((i) => !seen.has(i.id)))
      }
      total.value = res.total
      hasMore.value = items.value.length < res.total
      page.value += 1
    } finally {
      loading.value = false
    }
  }

  async function remove(id: number) {
    await errorsApi.deleteError(id)
    items.value = items.value.filter((i) => i.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  function masteryColor(m: number): string {
    if (m >= 80) return 'var(--color-success)'
    if (m >= 50) return 'var(--color-warning)'
    return 'var(--color-error)'
  }

  return { items, total, page, loading, hasMore, params, fetchErrors, remove, masteryColor }
})
