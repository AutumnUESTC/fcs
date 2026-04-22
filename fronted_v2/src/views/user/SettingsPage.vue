<template>
  <div class="settings-page">
    <div class="settings-content">
      <h1 class="page-title">{{ $t('settings.title') }}</h1>
      
      <div class="settings-card">
        <!-- 语言设置 -->
        <div class="setting-item">
          <div class="setting-label">
            <span class="setting-icon">🌐</span>
            <span>{{ $t('settings.language') }}</span>
          </div>
          <select v-model="settings.language" class="setting-select">
            <option value="zh-CN">简体中文</option>
            <option value="en">English</option>
            <option value="zh-TW">繁體中文</option>
          </select>
        </div>

        <!-- 字号设置 -->
        <div class="setting-item">
          <div class="setting-label">
            <span class="setting-icon">🔤</span>
            <span>{{ $t('settings.fontSize') }}</span>
          </div>
          <div class="font-size-controls">
            <button 
              class="font-btn" 
              :class="{ active: settings.fontSize === 'small' }"
              @click="settings.fontSize = 'small'"
            >
              {{ $t('settings.small') }}
            </button>
            <button 
              class="font-btn" 
              :class="{ active: settings.fontSize === 'medium' }"
              @click="settings.fontSize = 'medium'"
            >
              {{ $t('settings.medium') }}
            </button>
            <button 
              class="font-btn" 
              :class="{ active: settings.fontSize === 'large' }"
              @click="settings.fontSize = 'large'"
            >
              {{ $t('settings.large') }}
            </button>
          </div>
        </div>

        <!-- 清除历史记录 -->
        <div class="setting-item">
          <div class="setting-label">
            <span class="setting-icon">🗑️</span>
            <span>{{ $t('settings.clearHistory') }}</span>
          </div>
          <button class="btn-danger" @click="clearHistory">
            {{ $t('settings.clear') }}
          </button>
        </div>

        <div class="form-actions">
          <button class="btn-primary" @click="saveSettings">{{ $t('settings.save') }}</button>
        </div>
      </div>

      <!-- 消息提示 -->
      <div v-if="message" :class="['message', messageType]">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const message = ref('')
const messageType = ref('success')

const settings = reactive({
  language: localStorage.getItem('language') || 'zh-CN',
  fontSize: localStorage.getItem('fontSize') || 'medium'
})

const fontSizeMap = { small: '14px', medium: '16px', large: '18px' }

const showMessage = (msg, type = 'success') => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

const applyFontSize = (size) => {
  const px = fontSizeMap[size]
  document.documentElement.style.setProperty('--base-font-size', px)
  document.documentElement.style.fontSize = px
}

const saveSettings = () => {
  localStorage.setItem('language', settings.language)
  localStorage.setItem('fontSize', settings.fontSize)
  
  locale.value = settings.language
  applyFontSize(settings.fontSize)
  
  showMessage(t('settings.saveSuccess'))
}

const clearHistory = () => {
  if (confirm(t('settings.clearConfirm'))) {
    localStorage.removeItem('chatHistory')
    localStorage.removeItem('conversationHistory')
    showMessage(t('settings.clearSuccess'))
  }
}
</script>

<style scoped>
.settings-page {
  padding: 4rem 2rem;
  min-height: calc(100vh - 80px);
}

.settings-content {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #fff;
  text-align: center;
  margin-bottom: 2rem;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.settings-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 2rem;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.2rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.setting-item:last-of-type {
  border-bottom: none;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  color: #d4af37;
  font-weight: 600;
  font-size: 1rem;
}

.setting-icon {
  font-size: 1.2rem;
}

.setting-select {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 0.95rem;
  cursor: pointer;
  outline: none;
}

.setting-select:focus {
  border-color: #d4af37;
}

.setting-select option {
  background: #1a1a2e;
  color: #fff;
}

.font-size-controls {
  display: flex;
  gap: 0.5rem;
}

.font-btn {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.3s ease;
}

.font-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.font-btn.active {
  background: linear-gradient(135deg, #d4af37, #8b5a2b);
  color: #fff;
  border-color: #d4af37;
}

.btn-danger {
  padding: 0.5rem 1.2rem;
  background: rgba(255, 77, 79, 0.2);
  border: 1px solid rgba(255, 77, 79, 0.5);
  border-radius: 8px;
  color: #ff4d4f;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-danger:hover {
  background: rgba(255, 77, 79, 0.3);
  border-color: #ff4d4f;
}

.form-actions {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

.btn-primary {
  padding: 0.8rem 3rem;
  background: linear-gradient(135deg, #d4af37, #8b5a2b);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.4);
}

/* 消息提示 */
.message {
  position: fixed;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  padding: 1rem 2rem;
  border-radius: 8px;
  font-weight: 500;
  z-index: 1000;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.message.success {
  background: rgba(82, 196, 26, 0.9);
  color: #fff;
}

.message.error {
  background: rgba(255, 77, 79, 0.9);
  color: #fff;
}

@media (max-width: 768px) {
  .settings-page {
    padding: 2rem 1rem;
  }

  .page-title {
    font-size: 1.8rem;
  }

  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .setting-select,
  .font-size-controls {
    width: 100%;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-primary {
    width: 100%;
  }
}
</style>