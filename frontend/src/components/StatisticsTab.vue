<template>
  <div class="statistics-tab">
    <div class="statistics-header">
      <h3 class="section-title">统计信息</h3>
    </div>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-label">总字数</div>
        <div class="stat-value">{{ statistics.word_count || 0 }}</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-label">关键点数</div>
        <div class="stat-value">{{ statistics.keypoint_count || 0 }}</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-label">平均重要性</div>
        <div class="stat-value">{{ statistics.avg_importance || 0 }}</div>
      </div>
    </div>
    
    <div class="category-distribution" v-if="categoryData.length > 0">
      <h4 class="subsection-title">类别分布</h4>
      <div class="category-list">
        <div 
          v-for="cat in categoryData" 
          :key="cat.name"
          class="category-item"
        >
          <div class="category-info">
            <span class="category-name">{{ cat.name }}</span>
            <span class="category-count">{{ cat.count }}</span>
          </div>
          <div class="category-bar">
            <div 
              class="category-bar-fill"
              :style="{ 
                width: `${(cat.count / totalKeypoints) * 100}%`,
                backgroundColor: getCategoryColor(cat.name)
              }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="keywords-section" v-if="keywords.length > 0">
      <h4 class="subsection-title">关键词云</h4>
      <div class="keywords-cloud">
        <span 
          v-for="(keyword, index) in keywords" 
          :key="keyword"
          class="keyword-tag"
          :style="{ 
            fontSize: `${16 - index * 0.8}px`,
            animationDelay: `${index * 0.1}s`
          }"
        >
          {{ keyword }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDocumentStore } from '../stores/document'

const documentStore = useDocumentStore()

const statistics = computed(() => {
  const doc = documentStore.getCurrentDocument
  return doc?.statistics || {}
})

const categoryData = computed(() => {
  const dist = statistics.value.category_distribution || {}
  return Object.entries(dist).map(([name, count]) => ({ name, count }))
})

const totalKeypoints = computed(() => {
  return categoryData.value.reduce((sum, cat) => sum + cat.count, 0)
})

const keywords = computed(() => {
  return statistics.value.top_keywords || []
})

const getCategoryColor = (category) => {
  const colors = {
    '核心观点': '#667eea',
    '关键数据': '#ff6b6b',
    '方法建议': '#ffa94d',
    '结论总结': '#51cf66',
    '重点内容': '#74c0fc'
  }
  return colors[category] || '#7f8c8d'
}
</script>

<style scoped>
.statistics-tab {
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

.statistics-header {
  margin-bottom: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
  animation: scaleIn 0.5s ease;
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.stat-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
}

.category-distribution,
.keywords-section {
  margin-bottom: 32px;
}

.subsection-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-item {
  animation: slideInLeft 0.5s ease;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.category-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.category-name {
  color: #2c3e50;
  font-weight: 500;
}

.category-count {
  color: #667eea;
  font-weight: 700;
}

.category-bar {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.category-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease;
}

.keywords-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.keyword-tag {
  display: inline-block;
  padding: 8px 16px;
  background: linear-gradient(135deg, #f9fafb 0%, #e3e8f0 100%);
  color: #2c3e50;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  animation: popIn 0.5s ease;
}

@keyframes popIn {
  0% {
    opacity: 0;
    transform: scale(0);
  }
  60% {
    transform: scale(1.1);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.keyword-tag:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
</style>
