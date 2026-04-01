<template>
  <Teleport to="body">
    <div class="toast-portal" aria-live="polite" aria-atomic="false">
      <TransitionGroup name="toast" tag="div" class="toast-list">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="`toast-${toast.type}`"
          @click="dismiss(toast.id)"
          role="alert"
        >
          <span class="toast-icon">{{ icons[toast.type] }}</span>
          <div class="toast-body">
            <span class="toast-type-label">{{ labels[toast.type] }}</span>
            <span class="toast-msg">{{ toast.message }}</span>
          </div>
          <button class="toast-close" @click.stop="dismiss(toast.id)" aria-label="关闭">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>
          <!-- progress bar -->
          <div class="toast-progress" :class="`progress-${toast.type}`"></div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '../composables/useToast.js'

const { toasts, dismiss } = useToast()

const icons = {
  success: '✓',
  error:   '✕',
  info:    'i',
  warning: '!',
}

const labels = {
  success: '成功',
  error:   '错误',
  info:    '提示',
  warning: '警告',
}
</script>

<style scoped>
.toast-portal {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  pointer-events: none;
}

.toast-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
}

/* ===== TOAST ITEM ===== */
.toast-item {
  pointer-events: all;
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 300px;
  max-width: 420px;
  padding: 14px 42px 14px 14px;
  background: white;
  border-radius: 12px;
  box-shadow:
    0 4px 6px rgba(0,0,0,0.04),
    0 10px 30px rgba(0,0,0,0.12),
    0 0 0 1px rgba(0,0,0,0.05);
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.toast-item:hover {
  transform: translateX(-4px);
  box-shadow:
    0 6px 12px rgba(0,0,0,0.06),
    0 16px 40px rgba(0,0,0,0.15),
    0 0 0 1px rgba(0,0,0,0.05);
}

/* Left accent stripe */
.toast-item::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
  border-radius: 12px 0 0 12px;
}

/* ===== TYPE COLORS ===== */
.toast-success::before { background: linear-gradient(180deg, #22c55e, #16a34a); }
.toast-error::before   { background: linear-gradient(180deg, #ef4444, #dc2626); }
.toast-info::before    { background: linear-gradient(180deg, #667eea, #764ba2); }
.toast-warning::before { background: linear-gradient(180deg, #f59e0b, #d97706); }

/* ===== ICON BADGE ===== */
.toast-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 800;
  color: white;
  line-height: 1;
  font-style: normal;
}

.toast-success .toast-icon { background: linear-gradient(135deg, #22c55e, #16a34a); }
.toast-error   .toast-icon { background: linear-gradient(135deg, #ef4444, #dc2626); }
.toast-info    .toast-icon { background: linear-gradient(135deg, #667eea, #764ba2); }
.toast-warning .toast-icon { background: linear-gradient(135deg, #f59e0b, #d97706); }

/* ===== BODY ===== */
.toast-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toast-type-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  opacity: 0.55;
  color: #374151;
}

.toast-msg {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.5;
  word-break: break-word;
}

/* ===== CLOSE BUTTON ===== */
.toast-close {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  background: transparent;
}

.toast-close:hover {
  background: #f3f4f6;
  color: #374151;
}

/* ===== PROGRESS BAR ===== */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  border-radius: 0 0 12px 12px;
  animation: toast-progress 3.5s linear forwards;
}

.progress-success { background: #22c55e; }
.progress-error   { background: #ef4444; animation-duration: 5s; }
.progress-info    { background: #667eea; }
.progress-warning { background: #f59e0b; animation-duration: 4s; }

@keyframes toast-progress {
  from { width: 100%; }
  to   { width: 0%; }
}

/* ===== TRANSITION ===== */
.toast-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.toast-leave-active {
  transition: all 0.25s ease-in;
  position: absolute;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(60px) scale(0.85);
}
.toast-move {
  transition: transform 0.3s ease;
}
</style>
