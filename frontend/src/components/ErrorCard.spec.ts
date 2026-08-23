import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import ErrorCard from '@/components/ErrorCard.vue'
import type { ErrorItem } from '@/types'

function makeError(over: Partial<ErrorItem> = {}): ErrorItem {
  return {
    id: 1,
    notebook_id: 1,
    question: '已知函数 f(x)=x^3-3x，求极值',
    answer: '极大值2，极小值-2',
    analysis: '求导得 f"(x)=3x^2-3',
    error_cause: '概念混淆',
    knowledge_points: ['导数', '极值'],
    subject: '数学',
    source: 'text',
    image_path: null,
    mastery: 40,
    repetition: 2,
    interval_days: 6,
    ease_factor: 2.5,
    next_review: '2026-08-20',
    last_review: '2026-08-14',
    created_at: '2026-08-10T09:00:00',
    updated_at: '2026-08-14T16:00:00',
    ...over,
  }
}

describe('ErrorCard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the question text and subject tag', () => {
    const w = mount(ErrorCard, { props: { error: makeError() } })
    expect(w.text()).toContain('求极值')
    expect(w.text()).toContain('数学')
  })

  it('renders knowledge-point tags', () => {
    const w = mount(ErrorCard, { props: { error: makeError() } })
    expect(w.text()).toContain('导数')
    expect(w.text()).toContain('极值')
  })

  it('shows the mastery percentage', () => {
    const w = mount(ErrorCard, { props: { error: makeError({ mastery: 40 }) } })
    expect(w.text()).toContain('掌握 40%')
  })

  it('does not show answer until expanded', () => {
    const w = mount(ErrorCard, { props: { error: makeError(), expanded: false } })
    expect(w.text()).not.toContain('极大值2')
  })

  it('shows answer/analysis once expanded', () => {
    const w = mount(ErrorCard, { props: { error: makeError(), expanded: true } })
    expect(w.text()).toContain('极大值2')
    expect(w.text()).toContain('求导得')
  })

  it('emits edit and delete from the action row when expanded', async () => {
    const w = mount(ErrorCard, { props: { error: makeError(), expanded: true } })
    const buttons = w.findAll('.ec-btn')
    expect(buttons.length).toBe(2)
    await buttons[0].trigger('click')
    expect(w.emitted('edit')).toBeTruthy()
    await buttons[1].trigger('click')
    expect(w.emitted('delete')).toBeTruthy()
  })
})
