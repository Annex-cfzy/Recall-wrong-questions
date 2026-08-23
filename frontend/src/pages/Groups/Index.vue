<template>
  <div class="groups-page">
    <div class="dash-header">
      <h1 :style="{ font: 'var(--font-h1)' }">学习小组</h1>
      <button class="btn" @click="createGroup">＋ 创建小组</button>
    </div>

    <div class="demo-note">
      🧪 当前为演示视图（前端 Mock 数据）。联机版需接入账号与云端同步，
      即可实现小组内错题集共享、互帮互答与组队 PK 实时排行。
    </div>

    <div class="group-grid">
      <div v-for="g in groups" :key="g.id" class="group-card">
        <div class="gc-head">
          <span class="gc-name">{{ g.name }}</span>
          <span class="gc-tag">{{ g.subject }}</span>
        </div>
        <div class="gc-members">
          <span v-for="m in g.members" :key="m.name" class="avatar" :title="m.name">
            {{ m.name.slice(0, 1) }}
          </span>
          <span class="member-count">+{{ g.members.length }} 人</span>
        </div>

        <!-- 共享错题集 -->
        <div class="gc-section">
          <div class="gc-sec-title">📚 共享错题集（{{ g.sharedCount }}）</div>
          <div class="shared-list">
            <div v-for="s in g.shared" :key="s.id" class="shared-item">
              <span class="si-kp">{{ s.kp }}</span>
              <span class="si-by">@{{ s.by }}</span>
              <span class="si-rate" :class="s.hot ? 'hot' : ''">{{ s.rate }} 人错</span>
            </div>
          </div>
        </div>

        <!-- 组队 PK 排行 -->
        <div class="gc-section">
          <div class="gc-sec-title">🏆 组队 PK（本周掌握度）</div>
          <ol class="rank-list">
            <li v-for="(r, i) in g.rank" :key="r.name" :class="{ top: i < 3 }">
              <span class="rk-no">{{ i + 1 }}</span>
              <span class="rk-name">{{ r.name }}</span>
              <span class="rk-score">{{ r.score }}%</span>
            </li>
          </ol>
        </div>

        <div class="gc-actions">
          <button class="btn small" @click="shareTo(g)">分享我的错题</button>
          <button class="btn small ghost" @click="askHelp(g)">求助互答</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

interface Member {
  name: string
}
interface Shared {
  id: number
  kp: string
  by: string
  rate: number
  hot: boolean
}
interface Rank {
  name: string
  score: number
}
interface Group {
  id: number
  name: string
  subject: string
  members: Member[]
  sharedCount: number
  shared: Shared[]
  rank: Rank[]
}

const groups = ref<Group[]>([
  {
    id: 1,
    name: '高三数学冲刺营',
    subject: '数学',
    members: [{ name: '小明' }, { name: '小红' }, { name: '阿强' }, { name: '莉莉' }],
    sharedCount: 3,
    shared: [
      { id: 11, kp: '导数', by: '小明', rate: 12, hot: true },
      { id: 12, kp: '圆锥曲线', by: '小红', rate: 8, hot: false },
      { id: 13, kp: '数列', by: '阿强', rate: 5, hot: false },
    ],
    rank: [
      { name: '莉莉', score: 92 },
      { name: '阿强', score: 85 },
      { name: '小明', score: 78 },
      { name: '小红', score: 70 },
    ],
  },
  {
    id: 2,
    name: '英语阅读互助组',
    subject: '英语',
    members: [{ name: 'Tom' }, { name: 'Lucy' }, { name: 'Kai' }],
    sharedCount: 2,
    shared: [
      { id: 21, kp: '长难句', by: 'Lucy', rate: 9, hot: true },
      { id: 22, kp: '完形填空', by: 'Tom', rate: 6, hot: false },
    ],
    rank: [
      { name: 'Kai', score: 88 },
      { name: 'Lucy', score: 81 },
      { name: 'Tom', score: 73 },
    ],
  },
])

function createGroup() {
  ElMessage.info('演示环境：创建小组需登录云端账号')
}
function shareTo(g: Group) {
  ElMessage.success(`已将你的错题本分享到「${g.name}」（演示）`)
}
function askHelp(g: Group) {
  ElMessage.info(`已在「${g.name}」发起互答求助（演示）`)
}
</script>

<style scoped>
.groups-page {
  max-width: 1000px;
  margin: 0 auto;
}
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}
.btn {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-button);
  padding: 6px 14px;
  font: var(--font-body);
  background: var(--color-bg-card);
  cursor: pointer;
}
.btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.btn.small {
  padding: 5px 12px;
  font: var(--font-caption);
}
.btn.ghost {
  color: var(--color-text-secondary);
}
.demo-note {
  background: rgba(0, 122, 255, 0.06);
  border: 1px solid rgba(0, 122, 255, 0.18);
  color: var(--color-text-secondary);
  border-radius: 10px;
  padding: var(--space-md);
  font: var(--font-caption);
  margin-bottom: var(--space-lg);
}
.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--space-md);
}
.group-card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-md);
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.gc-head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.gc-name {
  font: var(--font-h2);
  color: var(--color-text-primary);
}
.gc-tag {
  font: var(--font-caption);
  background: rgba(0, 122, 255, 0.08);
  color: var(--color-primary);
  border-radius: 6px;
  padding: 1px 6px;
}
.gc-members {
  display: flex;
  align-items: center;
  gap: 4px;
}
.avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font: var(--font-caption);
}
.member-count {
  font: var(--font-caption);
  color: var(--color-text-tertiary);
  margin-left: 4px;
}
.gc-section {
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-sm);
}
.gc-sec-title {
  font: var(--font-caption);
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}
.shared-list {
  display: grid;
  gap: 4px;
}
.shared-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font: var(--font-caption);
}
.si-kp {
  color: var(--color-text-primary);
}
.si-by {
  color: var(--color-text-tertiary);
}
.si-rate {
  margin-left: auto;
  color: var(--color-text-secondary);
}
.si-rate.hot {
  color: #ff3b30;
}
.rank-list {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 2px;
  font: var(--font-caption);
}
.rank-list li {
  display: flex;
  gap: var(--space-sm);
}
.rank-list li.top .rk-name {
  color: var(--color-primary);
  font-weight: 600;
}
.rk-score {
  margin-left: auto;
  color: #34c759;
}
.gc-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: auto;
}
@media (max-width: 767px) {
  .group-grid {
    grid-template-columns: 1fr;
  }
}
</style>
