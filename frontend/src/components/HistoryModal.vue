<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <div class="modal-header">
        <h2 class="modal-title">📋 历史记录</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      
      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div v-else-if="history.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p>暂无历史记录</p>
        </div>
        
        <div v-else class="history-list">
          <TransitionGroup name="list">
            <div 
              v-for="record in history" 
              :key="record.id"
              class="history-item"
            >
              <div class="item-content" @click="loadRecord(record.id)">
                <div class="item-header">
                  <h4 class="item-title">{{ record.title }}</h4>
                  <span class="item-date">{{ formatDate(record.created_at) }}</span>
                </div>
                <div class="item-meta">
                  <span class="meta-tag">📄 {{ record.filename }}</span>
                  <span class="meta-tag">⭐ {{ record.keypoint_count }} 关键点</span>
                  <span class="meta-tag">📝 {{ record.word_count }} 字</span>
                </div>
              </div>
              <div class="item-actions">
                <button 
                  class="action-btn export-btn"
                  @click="handleExport(record.id)"
                  title="导出"
                >
                  💾
                </button>
                <button 
                  class="action-btn delete-btn"
                  @click="handleDelete(record.id)"
                  title="删除"
                >
                  🗑️
                </button>
              </div>
            </div>
          </TransitionGroup>
        </div>
        
        <div v-if="totalPages > 1" class="pagination">
          <button 
            class="page-btn"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            ◀ 上一页
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button 
            class="page-btn"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            下一页 ▶
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDocumentStore } from '../stores/document'
import { useToast } from '../composables/useToast.js'

const emit = defineEmits(['close'])
const documentStore = useDocumentStore()
const toast = useToast()

const loading = ref(true)
const currentPage = ref(1)
const perPage = 10

const history = computed(() => documentStore.getHistory)
const totalRecords = computed(() => documentStore.getHistoryTotal)
const totalPages = computed(() => Math.ceil(totalRecords.value / perPage))

onMounted(async () => {
  try {
    await documentStore.fetchHistory(currentPage.value, perPage)
  } catch (error) {
    console.error('加载历史记录失败:', error)
  } finally {
    loading.value = false
  }
})

const goToPage = async (page) => {
  loading.value = true
  currentPage.value = page
  try {
    await documentStore.fetchHistory(page, perPage)
  } catch (error) {
    console.error('加载历史记录失败:', error)
  } finally {
    loading.value = false
  }
}

const loadRecord = async (recordId) => {
  try {
    await documentStore.fetchHistoryDetail(recordId)
    emit('close')
  } catch (error) {
    toast.error('加载记录失败：' + error.message)
  }
}

const handleExport = async (recordId) => {
  const format = confirm('选择导出格式：\n确定 - Word文档\n取消 - PDF文档') ? 'docx' : 'pdf'
  
  try {
    await documentStore.exportDocument(recordId, format)
    toast.success('导出成功！')
  } catch (error) {
    toast.error('导出失败：' + error.message)
  }
}

const handleDelete = async (recordId) => {
  if (confirm('确定要删除这条记录吗？')) {
    try {
      await documentStore.deleteHistory(recordId)
      
      // 如果当前页没有记录了，回到上一页
      if (history.value.length === 0 && currentPage.value > 1) {
        goToPage(currentPage.value - 1)
      }
    } catch (error) {
      toast.error('删除失败：' + error.message)
    }
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(5px);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-container {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(50px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  padding: 24px 32px;
  border-bottom: 2px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-title {
  font-size: 24px;
  font-weight: 700;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.modal-body {
  padding: 32px;
  max-height: calc(90vh - 200px);
  overflow-y: auto;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f0f0f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p,
.loading-state p {
  font-size: 16px;
  color: #7f8c8d;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  display: flex;
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  padding: 20px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
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

.history-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  transform: translateY(-2px);
}

.item-content {
  flex: 1;
  cursor: pointer;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.item-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
}

.item-date {
  font-size: 13px;
  color: #7f8c8d;
  white-space: nowrap;
  margin-left: 12px;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.meta-tag {
  font-size: 13px;
  color: #7f8c8d;
  background: rgba(102, 126, 234, 0.1);
  padding: 4px 12px;
  border-radius: 12px;
}

.item-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-left: 16px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.export-btn {
  background: #4caf50;
  color: white;
}

.export-btn:hover {
  background: #45a049;
  transform: scale(1.1);
}

.delete-btn {
  background: #ff6b6b;
  color: white;
}

.delete-btn:hover {
  background: #ff5252;
  transform: scale(1.1);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 2px solid #f0f0f0;
}

.page-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.page-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.page-info {
  font-weight: 600;
  color: #2c3e50;
}

.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateY(30px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.list-leave-active {
  position: absolute;
}
</style>
