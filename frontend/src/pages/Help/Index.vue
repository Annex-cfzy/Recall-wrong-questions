<template>
  <div class="help-page">
    <header class="help-header">
      <h1 :style="{ font: 'var(--font-h1)' }">帮助中心</h1>
      <p :style="{ font: 'var(--font-body)', color: 'var(--color-text-secondary)' }">
        Recall 帮你拍照 / 文本快速录入错题，AI 自动归类并安排复习。
      </p>
    </header>

    <section class="card">
      <h2 :style="{ font: 'var(--font-h2)' }">快速入门</h2>
      <ol class="steps">
        <li><b>创建错题本</b>：在左侧点击「新建错题本」，选择学科与颜色。</li>
        <li><b>录入错题</b>：进入「录入」页，支持拍照（拖拽 / Ctrl+V 粘贴）、文本两种方式，AI 自动识别知识点与错因。</li>
        <li><b>复习</b>：进入「复习」页，选择范围后开始，系统生成变体题并批改，按 SM-2 算法安排下次复习。</li>
        <li><b>查看数据</b>：进入「看板」页，查看录入 / 复习趋势、掌握度分布与知识图谱。</li>
        <li><b>导出</b>：在错题集页点击「导出」，可导出 PDF（打印）或 Markdown（可编辑）。</li>
      </ol>
    </section>

    <section class="card">
      <h2 :style="{ font: 'var(--font-h2)' }">常见问题</h2>
      <div v-for="(item, i) in faqs" :key="i" class="faq">
        <p class="q">Q：{{ item.q }}</p>
        <p class="a">A：{{ item.a }}</p>
      </div>
    </section>

    <section class="card">
      <h2 :style="{ font: 'var(--font-h2)' }">快捷键</h2>
      <ul class="keys">
        <li><kbd>Ctrl</kbd> + <kbd>K</kbd> 全局搜索错题</li>
        <li><kbd>Ctrl</kbd> + <kbd>V</kbd> 在录入页粘贴截图触发 OCR</li>
        <li><kbd>Enter</kbd> 在搜索框提交搜索</li>
      </ul>
    </section>

    <section class="card tip">
      <h2 :style="{ font: 'var(--font-h2)' }">关于 AI 与隐私</h2>
      <p :style="{ font: 'var(--font-body)', color: 'var(--color-text-secondary)' }">
        所有数据默认存储在本地 SQLite，未联网时 AI 识别 / 归类 / 批改使用内置离线规则，
        保证功能可用；配置 DeepSeek API Key 后将自动切换为云端模型以获得更高质量。
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
const faqs = [
  { q: '拍照识别不准怎么办？', a: 'OCR 后可在预览页手动编辑题干，确认无误再导入；也可改用「文本录入」。' },
  { q: '复习计划是怎么安排的？', a: '基于 SM-2 间隔重复算法：答对则拉长间隔并提升掌握度，答错则次日重练。' },
  { q: '可以导出到哪里？', a: '支持导出 PDF（适合打印）与 Markdown（适合二次编辑 / 同步到笔记软件）。' },
  { q: '误删了错题本能恢复吗？', a: '删除前会有二次确认提示。当前版本为硬删除，请谨慎操作（后续将支持回收站）。' },
]
</script>

<style scoped>
.help-page {
  max-width: 760px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}
.help-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.steps {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font: var(--font-body);
  color: var(--color-text-primary);
}
.faq {
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-md);
}
.faq:first-of-type {
  border-top: none;
  padding-top: 0;
}
.q {
  font: var(--font-body);
  font-weight: 600;
  margin: 0 0 4px;
}
.a {
  font: var(--font-body);
  color: var(--color-text-secondary);
  margin: 0;
}
.keys {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font: var(--font-body);
}
kbd {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 2px 6px;
  font: var(--font-caption);
}
.tip {
  background: var(--color-bg-page);
}
</style>
