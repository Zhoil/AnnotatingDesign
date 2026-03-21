<template>
  <div class="sidebar">
    <div class="tab-bar">
      <div 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-item"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </div>
    </div>
    
    <div class="tab-content" :class="{ 'chat-mode': activeTab === 'chat' }">
      <Transition name="fade" mode="out-in">
        <KeypointsTab v-if="activeTab === 'keypoints'" @scroll-to="handleScrollTo" />
        <SummaryTab v-else-if="activeTab === 'summary'" />
        <StatisticsTab v-else-if="activeTab === 'statistics'" />
        <AiChatTab v-else-if="activeTab === 'chat'" />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import KeypointsTab from './KeypointsTab.vue'
import SummaryTab from './SummaryTab.vue'
import StatisticsTab from './StatisticsTab.vue'
import AiChatTab from './AiChatTab.vue'

const emit = defineEmits(['scroll-to'])
const activeTab = ref('keypoints')

const tabs = [
  { id: 'keypoints', label: '关键点', icon: '⭐' },
  { id: 'summary', label: '摘要', icon: '📝' },
  { id: 'statistics', label: '统计', icon: '📊' },
  { id: 'chat', label: 'AI 对话', icon: '🤖' }
]

const handleScrollTo = (highlightId) => {
  emit('scroll-to', highlightId)
}
</script>

<style scoped>
.sidebar {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
}

.tab-bar {
  display: flex;
  background: linear-gradient(to bottom, #ffffff, #f9fafb);
  border-bottom: 2px solid #f0f0f0;
  flex-shrink: 0;
}

.tab-item {
  flex: 1;
  padding: 12px 6px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  position: relative;
}

.tab-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.tab-item.active::after {
  transform: scaleX(1);
}

.tab-item:hover {
  background: rgba(102, 126, 234, 0.05);
}

.tab-item.active {
  color: #667eea;
  font-weight: 600;
}

/* AI 对话 tab 高亮 */
.tab-item:last-child.active {
  color: #764ba2;
}

.tab-item:last-child.active::after {
  background: linear-gradient(135deg, #764ba2 0%, #f093fb 100%);
}

.tab-icon {
  font-size: 20px;
}

.tab-label {
  font-size: 12px;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-height: 0;
}

/* 聊天模式下的 tab-content 不滚动（内部自己管理滚动） */
.tab-content.chat-mode {
  overflow: hidden;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.tab-content.chat-mode > * {
  flex: 1;
  min-height: 0;
}
</style>
