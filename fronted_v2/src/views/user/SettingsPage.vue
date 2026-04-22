<template>
  <div class="settings-page">
    <div class="settings-content">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="title-icon-wrap">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        </div>
        <h1 class="page-title">系统设置</h1>
        <p class="page-subtitle">自定义您的使用体验</p>
      </div>

      <!-- ===== 分组1: 账户 ===== -->
      <div class="section-group">
        <div class="section-label">账户</div>
        <div class="settings-card">

          <!-- 账户信息入口 -->
          <router-link to="/chat/user-center" class="setting-item clickable">
            <div class="setting-left">
              <div class="icon-box account-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              </div>
              <div class="setting-info">
                <span class="setting-name">账户信息</span>
                <span class="setting-desc">管理用户名、邮箱、密码等基本信息</span>
              </div>
            </div>
            <div class="item-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>
          </router-link>

          <!-- 当前用户信息展示 -->
          <div class="setting-item user-summary">
            <div class="setting-left">
              <div class="icon-box current-user-icon">
                {{ userInitial }}
              </div>
              <div class="setting-info">
                <span class="setting-name">{{ displayName }}</span>
                <span class="setting-desc">当前登录账户 · 免费版</span>
              </div>
            </div>
            <span class="badge-online">在线</span>
          </div>

          <div class="item-divider"></div>

          <!-- 修改密码快捷入口 -->
          <div class="setting-item clickable" @click="$router.push('/chat/user-center')">
            <div class="setting-left">
              <div class="icon-box security-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              </div>
              <div class="setting-info">
                <span class="setting-name">安全设置</span>
                <span class="setting-desc">修改密码、查看登录记录</span>
              </div>
            </div>
            <div class="item-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 分组2: 外观设置 ===== -->
      <div class="section-group">
        <div class="section-label">外观</div>
        <div class="settings-card">

          <!-- 语言 -->
          <div class="setting-item">
            <div class="setting-left">
              <div class="icon-box lang-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
              </div>
              <div class="setting-info">
                <span class="setting-name">界面语言</span>
                <span class="setting-desc">切换显示语言</span>
              </div>
            </div>
            <select v-model="settings.language" class="setting-select">
              <option value="zh-CN">简体中文</option>
              <option value="en">English</option>
              <option value="zh-TW">繁體中文</option>
            </select>
          </div>

          <div class="item-divider"></div>

          <!-- 字号 -->
          <div class="setting-item">
            <div class="setting-left">
              <div class="icon-box font-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>
              </div>
              <div class="setting-info">
                <span class="setting-name">字体大小</span>
                <span class="setting-desc">调整文字显示大小</span>
              </div>
            </div>
            <div class="font-size-controls">
              <button :class="['size-btn', { active: settings.fontSize === 'small' }]" @click="settings.fontSize = 'small'">小</button>
              <button :class="['size-btn', { active: settings.fontSize === 'medium' }]" @click="settings.fontSize = 'medium'">中</button>
              <button :class="['size-btn', { active: settings.fontSize === 'large' }]" @click="settings.fontSize = 'large'">大</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 分组3: 数据管理 ===== -->
      <div class="section-group">
        <div class="section-label">数据管理</div>
        <div class="settings-card">

          <!-- 清除历史 -->
          <div class="setting-item">
            <div class="setting-left">
              <div class="icon-box data-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </div>
              <div class="setting-info">
                <span class="setting-name">清除历史记录</span>
                <span class="setting-desc">删除所有本地缓存的聊天记录</span>
              </div>
            </div>
            <button class="btn-outline-danger" @click="clearHistory">清除</button>
          </div>
        </div>
      </div>

      <!-- ===== 分组4: 帮助与支持 ===== -->
      <div class="section-group">
        <div class="section-label">帮助与支持</div>
        <div class="settings-card">

          <!-- 使用帮助 -->
          <div class="setting-item clickable" @click="openHelp">
            <div class="setting-left">
              <div class="icon-box help-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              </div>
              <div class="setting-info">
                <span class="setting-name">使用帮助</span>
                <span class="setting-desc">查看功能指南和常见问题</span>
              </div>
            </div>
            <div class="item-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>
          </div>

          <div class="item-divider"></div>

          <!-- 意见反馈 -->
          <div class="setting-item clickable" @click="openFeedback">
            <div class="setting-left">
              <div class="icon-box feedback-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
              </div>
              <div class="setting-info">
                <span class="setting-name">意见反馈</span>
                <span class="setting-desc">提交建议或报告问题</span>
              </div>
            </div>
            <div class="item-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 分组5: 关于 ===== -->
      <div class="section-group about-section">
        <div class="about-card">
          <div class="about-logo">
            <span>⚖️</span>
            <span class="about-name">法脉智联</span>
          </div>
          <div class="about-version">
            <span class="version-text">版本 2.0.0 (Build 20260422)</span>
            <span class="version-divider">·</span>
            <span class="version-tech">Powered by 混元 AI + 小理法律引擎</span>
          </div>
        </div>
      </div>

      <!-- ===== 分组6: 危险区（退出登录） ===== -->
      <div class="section-group danger-zone-group">
        <div class="settings-card danger-card">
          <div class="danger-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <span>退出登录后需要重新登录才能使用全部功能</span>
          </div>
          <button class="btn-logout" @click="handleLogout">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            退出登录
          </button>
        </div>
      </div>

      <!-- Toast 消息 -->
      <transition name="toast">
        <div v-if="message" :class="['toast', messageType]">
          <svg v-if="messageType === 'success'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          {{ message }}
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { clearUserInfo } from '@/api/chat'

const router = useRouter()
const { t, locale } = useI18n()

// 用户信息
const storedUsername = ref(localStorage.getItem('fcs_username') || '')
const displayName = computed(() => storedUsername.value || '未登录用户')
const userInitial = computed(() => {
  const name = storedUsername.value || 'U'
  return name.charAt(0).toUpperCase()
})

// 设置
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
  setTimeout(() => { message.value = '' }, 3000)
}

const applyFontSize = (size) => {
  const px = fontSizeMap[size]
  document.documentElement.style.setProperty('--base-font-size', px)
  document.documentElement.style.fontSize = px
}

// 自动保存语言和字号变更
const saveSetting = () => {
  localStorage.setItem('language', settings.language)
  localStorage.setItem('fontSize', settings.fontSize)
  locale.value = settings.language
  applyFontSize(settings.fontSize)
}

// 监听变化自动保存
import { watch } from 'vue'
watch(() => settings.language, saveSetting)
watch(() => settings.fontSize, saveSetting)

// 清除历史
const clearHistory = () => {
  if (!confirm('确定要清除所有本地历史记录吗？\n\n此操作不可恢复，将删除所有聊天缓存。')) return
  localStorage.removeItem('chatHistory')
  localStorage.removeItem('conversationHistory')
  showMessage('历史记录已清除')
}

// 帮助
const openHelp = () => {
  window.open('#', '_blank') // TODO: 接入帮助页面或文档
}

// 反馈
const openFeedback = () => {
  showMessage('感谢您的反馈！我们已收到。')
}

// 登出
const handleLogout = () => {
  if (!confirm('确定要退出登录吗？')) return
  clearUserInfo()
  showMessage('已退出登录')
  setTimeout(() => router.push('/login'), 800)
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.settings-page {
  padding: 1.75rem;
  min-height: calc(100vh - 80px);
  background: linear-gradient(135deg, #f5f7fa 0%, #eef0f4 50%, #f0f4f8 100%);
}

.settings-content {
  max-width: 660px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ========== 页面标题 ========== */
.page-header {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding-bottom: 0.25rem;
}

.title-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.08));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  flex-shrink: 0;
}

.page-title {
  font-size: 1.55rem;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.02em;
  line-height: 1.2;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 0.8rem;
  color: #94a3b8;
  margin-top: 1px;
}

/* ========== 分组 ========== */
.section-group {
  display: flex;
  flex-direction: column;
}

.section-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 0.45rem;
  padding-left: 0.15rem;
}

/* ========== 卡片 ========== */
.settings-card {
  background: white;
  border-radius: 18px;
  overflow: hidden;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.04),
    0 10px 30px -5px rgba(102, 126, 234, 0.07);
  border: 1px solid rgba(99, 102, 241, 0.05);
}

/* ========== 设置项 ========== */
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.2rem;
  transition: background 0.2s ease;
}

.setting-item.clickable {
  cursor: pointer;
}

.setting-item.clickable:hover {
  background: #fafbff;
}

.setting-item.user-summary {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03), rgba(118, 75, 162, 0.02));
}

.setting-left {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-width: 0;
}

/* 图标盒子 */
.icon-box {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.account-icon { background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.08)); color: #667eea; }
.security-icon { background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.07)); color: #10b981; }
.lang-icon { background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.07)); color: #3b82f6; }
.font-icon { background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(168, 85, 247, 0.07)); color: #8b5cf6; }
.data-icon { background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.07)); color: #f59e0b; }
.help-icon { background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(8, 145, 178, 0.07)); color: #06b6d4; }
.feedback-icon { background: linear-gradient(135deg, rgba(236, 72, 153, 0.1), rgba(219, 39, 119, 0.07)); color: #ec4899; }

.current-user-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white !important;
  font-weight: 700;
  font-size: 1.05rem;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: #1e293b;
}

.setting-desc {
  font-size: 0.77rem;
  color: #94a3b8;
}

.item-arrow {
  flex-shrink: 0;
  color: #cbd5e1;
  transition: all 0.2s;
}

.setting-item.clickable:hover .item-arrow {
  color: #667eea;
  transform: translateX(2px);
}

.badge-online {
  flex-shrink: 0;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.08));
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

/* 下拉选择框 */
.setting-select {
  padding: 0.45rem 2rem 0.45rem 0.85rem;
  padding-right: 2rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  background: white;
  color: #374151;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  transition: all 0.25s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.6rem center;
  flex-shrink: 0;
}

.setting-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 字号控制 */
.font-size-controls {
  display: flex;
  gap: 3px;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 10px;
  flex-shrink: 0;
}

.size-btn {
  padding: 0.35rem 0.85rem;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #64748b;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}

.size-btn:hover:not(.active) { color: #475569; }
.size-btn.active {
  background: white;
  color: #667eea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 危险按钮 */
.btn-outline-danger {
  flex-shrink: 0;
  padding: 0.4rem 1rem;
  background: transparent;
  border: 1.5px solid rgba(239, 68, 68, 0.35);
  border-radius: 10px;
  color: #ef4444;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}

.btn-outline-danger:hover {
  background: rgba(239, 68, 68, 0.06);
  border-color: #ef4444;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
}

/* 分隔线 */
.item-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #f1f5f9, transparent);
  margin: 0 1.2rem;
}

/* ========== 关于卡片 ========== */
.about-section { margin-top: 0.25rem; }

.about-card {
  background: white;
  border-radius: 18px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.04),
    0 10px 30px -5px rgba(102, 126, 234, 0.07);
  border: 1px solid rgba(99, 102, 241, 0.05);
}

.about-logo {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.about-logo span:first-child { font-size: 1.5rem; }

.about-name {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.about-version {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.73rem;
  color: #94a3b8;
}

.version-divider { opacity: 0.4; }

.version-tech {
  color: #a5b4fc;
  font-weight: 500;
}

/* ========== 危险区（登出）========== */
.danger-zone-group { margin-top: 0.5rem; }

.danger-card {
  background: linear-gradient(135deg, #fef2f2, #fff1f2) !important;
  border-color: rgba(239, 68, 68, 0.12) !important;
  padding: 1.25rem 1.35rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.danger-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #ef4444;
  font-size: 0.78rem;
  font-weight: 500;
  flex: 1;
}

.btn-logout {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.6rem 1.4rem;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border: none;
  border-radius: 11px;
  color: white;
  font-size: 0.87rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
  flex-shrink: 0;
  white-space: nowrap;
}

.btn-logout:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
}

/* ========== Toast ========== */
.toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.8rem 1.6rem;
  border-radius: 14px;
  font-weight: 500;
  font-size: 0.88rem;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}

.toast.success { background: linear-gradient(135deg, #10b981, #059669); color: white; }
.toast.error { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }

.toast-enter-active,
.toast-leave-active { transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1); }
.toast-enter-from,
.toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(-16px); }

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .settings-page { padding: 1.25rem; }

  .page-header { flex-direction: column; align-items: flex-start; gap: 0.5rem; }

  .setting-item { padding: 0.9rem 0.95rem; flex-wrap: wrap; }

  .setting-select,
  .font-size-controls { width: 100%; margin-top: 0.4rem; }

  .font-size-controls { justify-content: stretch; }

  .size-btn { flex: 1; text-align: center; }

  .about-card { flex-direction: column; gap: 0.85rem; text-align: center; }

  .about-version { flex-wrap: wrap; justify-content: center; }

  .danger-card { flex-direction: column; text-align: center; }

  .btn-logout { width: 100%; justify-content: center; }
}
</style>
