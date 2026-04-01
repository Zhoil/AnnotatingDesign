<template>
  <div class="main-content">
    <div class="content-wrapper">
      <div class="left-panel">
        <DocumentViewer ref="documentViewer" />
      </div>
      
      <div class="right-panel">
        <Sidebar @scroll-to="handleScrollTo" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DocumentViewer from './DocumentViewer.vue'
import Sidebar from './Sidebar.vue'

const documentViewer = ref(null)

const handleScrollTo = (highlightId) => {
  if (documentViewer.value && documentViewer.value.scrollToHighlight) {
    documentViewer.value.scrollToHighlight(highlightId)
  }
}
</script>

<style scoped>
.main-content {
  flex: 1;
  min-height: 0;
  padding: 20px;
  overflow: hidden;
}

.content-wrapper {
  display: flex;
  gap: 20px;
  height: 100%;
  max-width: 1800px;
  margin: 0 auto;
}

.left-panel {
  flex: 3;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideInLeft 0.6s ease;
}

.right-panel {
  flex: 1;
  animation: slideInRight 0.6s ease;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@media (max-width: 1200px) {
  .content-wrapper {
    flex-direction: column;
  }
  
  .left-panel,
  .right-panel {
    flex: none;
    width: 100%;
  }
}
</style>
