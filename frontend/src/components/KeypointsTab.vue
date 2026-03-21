<template>
  <div class="keypoints-tab">
    <div class="keypoints-header">
      <h3 class="section-title">🔥 核心论点</h3>
      <div class="keypoints-stats">
        <span class="stat-badge">共 {{ keypoints.length }} 个</span>
        <span class="stat-badge">按重要性排序</span>
      </div>
    </div>
    
    <div class="keypoints-list">
      <TransitionGroup name="list">
        <div 
          v-for="(kp, index) in keypoints" 
          :key="kp.id"
          class="keypoint-card"
          :class="getCardClass(kp.importance)"
          :style="{ animationDelay: `${index * 0.08}s` }"
          @click="$emit('scroll-to', kp.id)"
        >
          <div class="card-top">
            <div class="card-rank" :class="getRankClass(index)">
              <span class="rank-number">{{ index + 1 }}</span>
              <span class="rank-label" v-if="index === 0">最重要</span>
              <span class="rank-label" v-else-if="index < 3">重要</span>
            </div>
            <div class="card-importance-badge" :style="{ backgroundColor: getImportanceColor(kp.importance) }">
              {{ kp.importance }}分
            </div>
          </div>
          
          <div class="card-content">
            <div class="card-summary">
              <span class="summary-icon">📝</span>
              <p>{{ kp.summary }}</p>
            </div>
          </div>
          
          <div class="card-footer">
            <div class="importance-bar-container">
              <div class="importance-bar-label">重要性</div>
              <div class="importance-bar">
                <div 
                  class="importance-fill" 
                  :style="{ 
                    width: `${kp.importance}%`,
                    backgroundColor: getImportanceColor(kp.importance)
                  }"
                >
                  <span class="importance-text">{{ kp.importance }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDocumentStore } from '../stores/document'

const emit = defineEmits(['scroll-to'])
const documentStore = useDocumentStore()

const keypoints = computed(() => {
  const doc = documentStore.getCurrentDocument
  if (!doc || !doc.keypoints) return []
  // 仅显示核心论点
  return doc.keypoints.filter(kp => kp.category === '核心论点')
})

const getImportanceColor = (importance) => {
  if (importance >= 80) return '#ff6b6b'
  if (importance >= 60) return '#ffa94d'
  if (importance >= 40) return '#ffd43b'
  return '#74c0fc'
}

const getCardClass = (importance) => {
  if (importance >= 90) return 'card-critical'
  if (importance >= 75) return 'card-high'
  if (importance >= 60) return 'card-medium'
  return 'card-normal'
}

const getRankClass = (index) => {
  if (index === 0) return 'rank-first'
  if (index < 3) return 'rank-top'
  return 'rank-normal'
}
</script>

<style scoped>
.keypoints-tab {
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

.keypoints-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 2px solid #e9ecef;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.keypoints-stats {
  display: flex;
  gap: 12px;
}

.stat-badge {
  padding: 6px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.keypoints-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.keypoint-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid #f1f3f5;
  animation: slideInRight 0.5s ease;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  position: relative;
  overflow: hidden;
}

.keypoint-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.keypoint-card:hover::before {
  transform: scaleY(1);
}

.card-critical {
  border-left: 4px solid #ff6b6b;
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
}

.card-high {
  border-left: 4px solid #ffa94d;
  background: linear-gradient(135deg, #fff9f0 0%, #ffffff 100%);
}

.card-medium {
  border-left: 4px solid #ffd43b;
  background: linear-gradient(135deg, #fffbf0 0%, #ffffff 100%);
}

.card-normal {
  border-left: 4px solid #74c0fc;
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.keypoint-card:hover {
  transform: translateY(-6px) scale(1.01);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
  border-color: #667eea;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-rank {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 20px;
  font-weight: 700;
}

.rank-first {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #000;
  box-shadow: 0 2px 12px rgba(255, 215, 0, 0.4);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.rank-top {
  background: linear-gradient(135deg, #ffa94d 0%, #ff8787 100%);
  color: white;
}

.rank-number {
  font-size: 18px;
  font-weight: 800;
}

.rank-label {
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  font-weight: 600;
}

.card-importance-badge {
  padding: 6px 14px;
  border-radius: 20px;
  color: white;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.card-content {
  margin-bottom: 16px;
}

.card-header {
  display: none;
}

.card-index {
  display: none;
}

.card-category {
  display: none;
}

.card-category-point {
  display: none;
}

.card-summary {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.summary-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.card-summary p {
  font-size: 15px;
  line-height: 1.7;
  color: #2c3e50;
  margin: 0;
  font-weight: 500;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.importance-bar-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.importance-bar-label {
  font-size: 12px;
  color: #7f8c8d;
  font-weight: 600;
  min-width: 50px;
}

.importance-bar {
  flex: 1;
  height: 12px;
  background: linear-gradient(90deg, #f0f0f0 0%, #e0e0e0 100%);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
}

.importance-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
}

.importance-text {
  font-size: 10px;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  letter-spacing: 0.5px;
}

.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
