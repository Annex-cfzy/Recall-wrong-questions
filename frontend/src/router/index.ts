import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', redirect: '/errors' },
        {
          path: 'errors',
          name: 'errors',
          component: () => import('@/pages/Errors/Index.vue'),
          meta: { title: '错题集' },
        },
        {
          path: 'input',
          name: 'input',
          component: () => import('@/pages/Input/Index.vue'),
          meta: { title: '录入错题' },
        },
        {
          path: 'review',
          name: 'review',
          component: () => import('@/pages/Review/Index.vue'),
          meta: { title: '一键复习' },
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('@/pages/Chat/Index.vue'),
          meta: { title: 'AI 答疑' },
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/pages/Dashboard/Index.vue'),
          meta: { title: '数据看板' },
        },
        {
          path: 'insights',
          name: 'insights',
          component: () => import('@/pages/Insights/Index.vue'),
          meta: { title: '智能洞察' },
        },
        {
          path: 'sprint',
          name: 'sprint',
          component: () => import('@/pages/Sprint/Index.vue'),
          meta: { title: '考前冲刺' },
        },
        {
          path: 'clusters',
          name: 'clusters',
          component: () => import('@/pages/Clusters/Index.vue'),
          meta: { title: '相似错题' },
        },
        {
          path: 'voice-cards',
          name: 'voice-cards',
          component: () => import('@/pages/VoiceCards/Index.vue'),
          meta: { title: '语音讲解' },
        },
        {
          path: 'voice-input',
          name: 'voice-input',
          component: () => import('@/pages/VoiceInput/Index.vue'),
          meta: { title: '语音录入' },
        },
        {
          path: 'groups',
          name: 'groups',
          component: () => import('@/pages/Groups/Index.vue'),
          meta: { title: '学习小组' },
        },
        {
          path: 'help',
          name: 'help',
          component: () => import('@/pages/Help/Index.vue'),
          meta: { title: '帮助中心' },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/errors' },
  ],
})

export default router
