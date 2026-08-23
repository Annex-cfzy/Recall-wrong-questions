// 回归测试：lucide-vue-next 图标在 Vue 3.5 + 排除预打包后能否正常挂载。
// 复现并守住曾经出现的运行时崩溃：
//   TypeError: Cannot destructure property 'slots' of 'undefined'
import { describe, it, expect } from 'vitest'
import { createApp, h } from 'vue'
import { BookOpenCheck, BarChart3, NotebookPen, Trash2, Pencil } from 'lucide-vue-next'

describe('lucide icon mounts under Vue 3.5 (slots crash regression)', () => {
  const icons: Record<string, any> = { BookOpenCheck, BarChart3, NotebookPen, Trash2, Pencil }

  for (const [name, Icon] of Object.entries(icons)) {
    it(`mounts ${name} without throwing`, () => {
      const container = document.createElement('div')
      document.body.appendChild(container)
      const app = createApp({ render: () => h(Icon) })
      expect(() => app.mount(container)).not.toThrow()
      expect(container.innerHTML).toContain('<svg')
      app.unmount()
    })
  }
})
