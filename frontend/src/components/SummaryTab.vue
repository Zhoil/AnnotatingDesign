<template>
  <div class="summary-tab">
    <div class="summary-header">
      <h3 class="section-title">摘要报告</h3>
    </div>
    
    <div class="summary-sections">
      <div 
        v-for="section in sections" 
        :key="section.key"
        class="summary-section"
      >
        <div class="section-header">
          <span class="section-icon">{{ section.icon }}</span>
          <h4 class="section-subtitle">{{ section.title }}</h4>
        </div>
        
        <div class="section-content">
          <div 
            v-if="summary[section.key] && summary[section.key].length > 0"
            class="content-list"
          >
            <div 
              v-for="(item, index) in summary[section.key]" 
              :key="index"
              class="content-item"
            >
              <span class="item-bullet">•</span>
              <span class="item-text">{{ item }}</span>
            </div>
          </div>
          <div v-else class="empty-state">
            暂无{{ section.title }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDocumentStore } from '../stores/document'

const documentStore = useDocumentStore()

const summary = computed(() => {
  const doc = documentStore.getCurrentDocument
  return doc?.summary || {}
})

const sections = [
  { key: 'core_points', title: '核心观点', icon: '💡' },
  { key: 'key_data', title: '关键数据', icon: '📈' },
  { key: 'conclusions', title: '结论总结', icon: '✅' }
]
</script>

<style scoped>
.summary-tab {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.summary-header {
  margin-bottom: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
}

.summary-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.summary-section {
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #667eea;
  animation: slideInUp 0.5s ease;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 24px;
}

.section-subtitle {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.section-content {
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.8;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.item-bullet {
  color: #667eea;
  font-weight: 700;
  font-size: 18px;
  line-height: 1.5;
}

.item-text {
  flex: 1;
  line-height: 1.6;
}

.empty-state {
  color: #7f8c8d;
  font-style: italic;
  text-align: center;
  padding: 20px;
}
</style>
