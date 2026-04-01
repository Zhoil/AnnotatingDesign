import { reactive } from 'vue'

// 全局单例 toast 列表（所有组件共享同一队列）
const toasts = reactive([])
let _nextId = 0

export function useToast() {
  const dismiss = (id) => {
    const idx = toasts.findIndex(t => t.id === id)
    if (idx !== -1) toasts.splice(idx, 1)
  }

  const show = (message, type = 'info', duration = 3500) => {
    const id = _nextId++
    toasts.push({ id, message, type })
    setTimeout(() => dismiss(id), duration)
    return id
  }

  return {
    toasts,
    dismiss,
    success: (msg, dur)  => show(msg, 'success', dur ?? 3500),
    error:   (msg, dur)  => show(msg, 'error',   dur ?? 5000),
    info:    (msg, dur)  => show(msg, 'info',    dur ?? 3500),
    warning: (msg, dur)  => show(msg, 'warning', dur ?? 4000),
  }
}
