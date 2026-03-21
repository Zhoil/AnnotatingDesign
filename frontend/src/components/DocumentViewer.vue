<template>
  <div class="document-viewer">
    <div class="document-header">
      <h2 class="document-title">{{ document?.title || '未命名文档' }}</h2>
      <div class="document-meta">
        <span class="meta-item">📄 {{ document?.filename }}</span>
      </div>
    </div>
    
    <div class="document-body">
      <!-- PDF 查看器 -->
      <iframe 
        v-if="document?.filename?.toLowerCase().endsWith('.pdf') && document?.annotated_url" 
        :src="`${document.annotated_url}#toolbar=1&view=FitH`" 
        class="pdf-viewer" 
        ref="pdfIframe"
      ></iframe>
      
      <!-- 网页HTML查看器 -->
      <iframe 
        v-else-if="document?.is_web && document?.annotated_url"
        :src="document.annotated_url"
        class="web-viewer"
        sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
      ></iframe>
      
      <!-- Word 文档提示与预览 -->
      <div v-else-if="document?.filename?.toLowerCase().endsWith('.docx')" class="docx-preview">
        <div class="docx-info-panel">
          <div class="docx-icon">📘</div>
          <div class="docx-text">
            <h3>已完成标注处理</h3>
            <p>Word 文档已根据 AI 分析结果进行了物理高亮标注。</p>
            <button @click="handleDownload" class="download-btn">📥 下载标注版文档</button>
          </div>
        </div>
        <div class="text-preview">
          <h4>标注内容预览：</h4>
          <div class="document-content" v-html="highlightedContent"></div>
        </div>
      </div>
      
      <!-- 其他格式预览 -->
      <div v-else class="document-content" v-html="highlightedContent"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDocumentStore } from '../stores/document'

// Store 和 Refs
const documentStore = useDocumentStore()
const pdfIframe = ref(null)
const document = computed(() => documentStore.getCurrentDocument)

// 生成高亮标注后的内容（用于文字预览）
const highlightedContent = computed(() => {
  if (!document.value || !document.value.content) {
    return `<div class="empty-state"><div class="empty-icon">📄</div><p>请上传或选择一个文档进行分析</p></div>`
  }
  
  let content = document.value.content
  const highlights = document.value.highlights || []
  
  // 按位置倒序排序，避免插入时位置偏移
  const sortedHighlights = [...highlights].sort((a, b) => b.start - a.start)
  
  // 插入高亮标记：论点(红色实线) vs 论据(蓝绿虚线)
  sortedHighlights.forEach((hl) => {
    const before = content.substring(0, hl.start)
    const text = content.substring(hl.start, hl.end)
    const after = content.substring(hl.end)
    
    const isPoint = hl.color === '#ff6b6b'
    const borderStyle = isPoint ? `3px solid ${hl.color}` : `2px dotted ${hl.color}`
    const bgOpacity = isPoint ? '55' : '33'
    
    content = before + 
      `<mark class="highlight ${isPoint ? 'highlight-point' : 'highlight-evidence'}" style="background-color: ${hl.color}${bgOpacity}; border-bottom: ${borderStyle}; font-weight: ${isPoint ? '600' : '400'}" data-id="${hl.id}">` + 
      text + 
      `</mark>` + 
      after
  })
  
  return content.split('\n').map(line => line.trim() ? `<p>${line}</p>` : '<br>').join('')
})

// 下载标注版文档（使用 Blob 解决跨域问题）
const handleDownload = async () => {
  if (!document.value?.annotated_url) return
  
  try {
    const response = await fetch(document.value.annotated_url)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = url
    link.setAttribute('download', `annotated_${document.value.filename}`)
    window.document.body.appendChild(link)
    link.click()
    window.document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
    alert('文件下载失败，请检查后端服务是否正常。')
  }
}

// PDF 跳转功能：点击关键点跳转到对应页面
const scrollToHighlight = (highlightId) => {
  const allKps = document.value?.keypoints || []
  const kp = allKps.find(k => k.id === highlightId)
  
  if (kp && kp.page) {
    // PDF: 跳转到指定页面
    console.log(`正在跳转至第 ${kp.page} 页, ID: ${highlightId}`)
    const baseUrl = document.value.annotated_url
    const jumpUrl = `${baseUrl}?t=${Date.now()}#page=${kp.page}` // 添加时间戳防止缓存
    
    if (pdfIframe.value) {
      pdfIframe.value.src = jumpUrl
    }
  } else {
    // 文字预览: 滚动 + 2秒放大高亮动画
    const element = window.document.querySelector(`[data-id="${highlightId}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      
      // 添加放大高亮动画
      setTimeout(() => {
        element.classList.add('flash-highlight')
        setTimeout(() => {
          element.classList.remove('flash-highlight')
        }, 2000)
      }, 300)
    }
  }
}

defineExpose({ scrollToHighlight })
</script>

<style scoped>
.document-viewer {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
}

.document-header {
  padding: 24px 32px;
  border-bottom: 2px solid #f0f0f0;
  background: linear-gradient(to bottom, #ffffff, #f9fafb);
}

.document-title {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 12px;
}

.document-meta {
  display: flex;
  gap: 20px;
  color: #7f8c8d;
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.document-body {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
}

.web-viewer {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.docx-preview {
  height: 100%;
  overflow-y: auto;
  padding: 32px;
  background: #f8f9fa;
}

.docx-info-panel {
  display: flex;
  align-items: center;
  gap: 24px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  margin-bottom: 24px;
}

.docx-icon {
  font-size: 48px;
}

.download-btn {
  display: inline-block;
  margin-top: 12px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);
}

.download-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(102, 126, 234, 0.3);
  opacity: 0.9;
}

.text-preview h4 {
  margin-bottom: 16px;
  color: #667eea;
}

.document-content {
  padding: 32px;
  overflow-y: auto;
  height: 100%;
  background: white;
  border-radius: 8px;
}

.document-content :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
  color: #2c3e50;
}

.document-content :deep(.highlight) {
  padding: 3px 2px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 3px;
}

/* 论点特殊样式 */
.document-content :deep(.highlight-point) {
  box-shadow: 0 2px 4px rgba(255, 107, 107, 0.15);
}

/* 论据特殊样式 */
.document-content :deep(.highlight-evidence) {
  box-shadow: 0 1px 3px rgba(81, 207, 102, 0.1);
}

.document-content :deep(.highlight:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
}

/* 点击跳转 2 秒放大高亮动画 */
.document-content :deep(.highlight.flash-highlight) {
  animation: flashHighlight 2s ease-in-out;
  transform-origin: center;
}

@keyframes flashHighlight {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 rgba(102, 126, 234, 0);
  }
  20% {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
    background-color: rgba(102, 126, 234, 0.3) !important;
  }
  50% {
    transform: scale(1.08);
    box-shadow: 0 0 30px rgba(102, 126, 234, 0.8);
    background-color: rgba(102, 126, 234, 0.4) !important;
  }
  80% {
    transform: scale(1.02);
    box-shadow: 0 0 15px rgba(102, 126, 234, 0.4);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 rgba(102, 126, 234, 0);
  }
}

.text-preview {
  margin-top: 24px;
}
</style>
