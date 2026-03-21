<template>
  <div class="app">
    <Navbar @show-upload="showUploadModal = true" @show-history="showHistoryModal = true" />
    
    <Transition name="fade">
      <div v-if="!documentStore.hasDocument && !showHistoryModal" class="welcome-container">
        <div class="welcome-content">
          <h1 class="welcome-title">智能文章重点分析与标注</h1>
          <p class="welcome-subtitle">上传文档，智能提取关键点，一键生成分析报告</p>
          <button class="upload-btn" @click="showUploadModal = true">
            <span class="btn-icon">📄</span>
            开始分析
          </button>
        </div>
      </div>
    </Transition>

    <Transition name="slide">
      <MainContent v-if="documentStore.hasDocument" />
    </Transition>

    <UploadModal v-if="showUploadModal" @close="showUploadModal = false" />
    <HistoryModal v-if="showHistoryModal" @close="showHistoryModal = false" />
    
    <Transition name="fade">
      <LoadingOverlay v-if="documentStore.isLoading" />
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDocumentStore } from './stores/document'
import Navbar from './components/Navbar.vue'
import MainContent from './components/MainContent.vue'
import UploadModal from './components/UploadModal.vue'
import HistoryModal from './components/HistoryModal.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'

const documentStore = useDocumentStore()
const showUploadModal = ref(false)
const showHistoryModal = ref(false)
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.welcome-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.welcome-content {
  text-align: center;
  animation: fadeInUp 0.8s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome-title {
  font-size: 48px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

.welcome-subtitle {
  font-size: 20px;
  color: #7f8c8d;
  margin-bottom: 40px;
}

.upload-btn {
  padding: 16px 40px;
  font-size: 18px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.upload-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(102, 126, 234, 0.5);
}

.btn-icon {
  font-size: 24px;
}
</style>
