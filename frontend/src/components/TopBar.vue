<template>
  <header class="topbar">
    <div class="topbar-inner">
      <!-- Logo -->
      <RouterLink to="/errors" class="logo">
        <BookOpenCheck :size="22" :stroke-width="1.5" />
        <span class="logo-text">Recall</span>
      </RouterLink>

      <!-- Navigation -->
      <nav class="nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
        >
          <component :is="item.icon" :size="20" :stroke-width="1.5" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <!-- 多端云同步状态指示 -->
      <div class="sync-pill" title="数据由后端统一存储，Web / 小程序多端互通">
        <span class="sync-dot"></span> 已同步
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRoute, RouterLink } from 'vue-router'
import {
  BookOpenCheck,
  BookOpen,
  MessageCircle,
  BarChart3,
  HelpCircle,
  TrendingUp,
  Target,
  Layers,
  Volume2,
  Mic,
  Users,
} from 'lucide-vue-next'

const route = useRoute()

const navItems = [
  { to: '/errors', label: '错题集', icon: BookOpen },
  { to: '/chat', label: 'AI 答疑', icon: MessageCircle },
  { to: '/dashboard', label: '数据看板', icon: BarChart3 },
  { to: '/insights', label: '智能洞察', icon: TrendingUp },
  { to: '/sprint', label: '考前冲刺', icon: Target },
  { to: '/clusters', label: '相似错题', icon: Layers },
  { to: '/voice-cards', label: '语音讲解', icon: Volume2 },
  { to: '/voice-input', label: '语音录入', icon: Mic },
  { to: '/groups', label: '学习小组', icon: Users },
  { to: '/help', label: '帮助', icon: HelpCircle },
]

function isActive(to: string) {
  return route.path.startsWith(to)
}
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--topbar-height);
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
}
.topbar-inner {
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  padding: 0 var(--space-xl);
}
.logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 18px;
}
.logo-text {
  color: var(--color-text-primary);
}
.nav {
  display: flex;
  gap: var(--space-xs);
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-button);
  color: var(--color-text-secondary);
  text-decoration: none;
  font: var(--font-body);
  transition: background 0.15s ease, color 0.15s ease;
}
.nav-item:hover {
  background: var(--color-bg-page);
  color: var(--color-text-primary);
}
.nav-item.active {
  color: var(--color-primary);
  background: rgba(0, 122, 255, 0.08);
}
.search-box {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 260px;
  padding: 6px 12px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-input);
}
.search-icon {
  color: var(--color-text-tertiary);
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font: var(--font-body);
  color: var(--color-text-primary);
}
.search-kbd {
  font-size: 11px;
  color: var(--color-text-tertiary);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 1px 5px;
}
.sync-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  font: var(--font-caption);
  color: #34c759;
  background: rgba(52, 199, 89, 0.1);
  border: 1px solid rgba(52, 199, 89, 0.25);
  border-radius: 999px;
  padding: 3px 10px;
  white-space: nowrap;
}
.sync-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34c759;
}
@media (max-width: 767px) {
  .topbar-inner {
    gap: var(--space-sm);
    padding: 0 12px;
  }
  .nav-item span {
    display: none;
  }
  .nav {
    overflow-x: auto;
    scrollbar-width: none;
  }
  .nav::-webkit-scrollbar {
    display: none;
  }
  .sync-pill {
    display: none;
  }
}
</style>
