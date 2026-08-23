import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
    // 保证全局只有一份 vue 实例，避免 dev/预打包出现多副本导致组件解析异常
    dedupe: ['vue'],
  },
  // lucide-vue-next 的图标是函数式组件，被 Vite 的 esbuild 预打包后会与 Vue 3.5 冲突
  // （报错：Cannot destructure property 'slots' of 'undefined'）。
  // 排除预打包、改为原始 ESM 直供，dev 行为与已通过的 rollup 构建一致即可正常工作。
  optimizeDeps: {
    exclude: ['lucide-vue-next'],
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API + SSE to the FastAPI backend during development.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
