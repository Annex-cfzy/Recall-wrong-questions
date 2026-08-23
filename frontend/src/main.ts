import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import './styles/global.css'

const app = createApp(App)

// 全局错误兜底：把白屏式运行时错误显示成可读文字，方便定位问题。
function showFatalError(err: unknown) {
  const msg = err instanceof Error ? `${err.message}\n\n${err.stack || ''}` : String(err)
  let box = document.getElementById('app-error')
  if (!box) {
    box = document.createElement('pre')
    box.id = 'app-error'
    box.style.cssText =
      'position:fixed;inset:0;z-index:99999;margin:0;padding:24px;background:#1e1e1e;color:#ff6b6b;font:13px/1.6 monospace;white-space:pre-wrap;overflow:auto;'
    document.body.appendChild(box)
  }
  box.textContent = 'Recall 运行时错误（请把这段发给我）：\n\n' + msg
}
app.config.errorHandler = (err) => showFatalError(err)
window.addEventListener('error', (e) => showFatalError(e.error || e.message))
window.addEventListener('unhandledrejection', (e) => showFatalError(e.reason))

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
