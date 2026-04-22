<template>
  <div class="user-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo" @click="navigateTo('/')">
          <span class="logo-icon">⚖️</span>
          <span class="logo-text">法脉智联</span>
        </div>
      </div>

      <!-- 新建对话按钮 -->
      <button class="new-chat-btn" @click="startNewChat">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        <span>{{ $t('sidebar.newChat') }}</span>
      </button>

      <!-- 历史会话列表 -->
      <div class="conversations-section">
        <div class="section-title">{{ $t('sidebar.historyTitle') }}</div>
        <div class="conversations-list" v-if="conversations.length > 0">
          <div 
            v-for="conv in conversations" 
            :key="conv.conversation_id"
            class="conversation-item"
            :class="{ active: currentConversationId === conv.conversation_id, pinned: conv.is_pinned }"
            @click="loadConversation(conv.conversation_id)"
            @contextmenu.prevent="showContextMenu($event, conv)"
          >
            <div class="conv-icon">
              <svg v-if="!conv.is_pinned" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2">
                <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 16.8l-6.2 4.5 2.4-7.4L2 9.4h7.6L12 2z"></path>
              </svg>
            </div>
            <div class="conv-info">
              <div class="conv-title" v-if="editingId !== conv.conversation_id">{{ conv.title }}</div>
              <input
                v-else
                class="rename-input"
                v-model="renameValue"
                @keyup.enter="confirmRename"
                @keyup.escape="cancelRename"
                @blur="confirmRename"
                ref="renameInput"
                @click.stop
              />
              <div class="conv-time">{{ conv.updated_at || conv.updatedAt }}</div>
            </div>
            <div class="conv-actions" @click.stop>
              <button class="action-btn" @click="showContextMenu($event, conv)" title="更多操作">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="5" r="1"></circle>
                  <circle cx="12" cy="12" r="1"></circle>
                  <circle cx="12" cy="19" r="1"></circle>
                </svg>
              </button>
            </div>
          </div>
        </div>
        <div class="empty-conversations" v-else>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span>暂无历史会话</span>
        </div>
      </div>

      <!-- 右键菜单 -->
      <div 
        v-if="contextMenu.visible" 
        class="context-menu" 
        :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
      >
        <div class="ctx-item" @click="handlePin">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 16.8l-6.2 4.5 2.4-7.4L2 9.4h7.6L12 2z"></path>
          </svg>
          <span>{{ contextMenu.conv?.is_pinned ? '取消置顶' : '置顶会话' }}</span>
        </div>
        <div class="ctx-item" @click="handleRename">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
          <span>重命名</span>
        </div>
        <div class="ctx-divider"></div>
        <div class="ctx-item danger" @click="handleDelete">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          <span>删除会话</span>
        </div>
      </div>

      <!-- 侧边栏底部 -->
      <div class="sidebar-footer">
        <div class="user-info" @click="showUserMenu = !showUserMenu">
          <div class="user-avatar">用</div>
          <div class="user-details">
            <div class="user-name">用户名</div>
            <div class="user-status">在线</div>
          </div>
          <svg class="dropdown-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>

        <!-- 用户菜单 -->
        <div class="user-menu" v-if="showUserMenu">
          <div class="menu-item" @click="navigateTo('/chat/user-center')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>用户中心</span>
          </div>
          <div class="menu-item" @click="navigateTo('/chat/settings')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            <span>{{ $t('sidebar.settings') }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu-item logout" @click="handleLogout">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            <span>退出登录</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content" @click="closeContextMenu">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { getConversationList, deleteConversation, pinConversation, renameConversation, clearUserInfo } from '@/api/chat'

const router = useRouter()
const showUserMenu = ref(false)
const conversations = ref([])
const currentConversationId = ref(null)

// 右键菜单状态
const contextMenu = ref({ visible: false, x: 0, y: 0, conv: null })

// 重命名状态
const editingId = ref(null)
const renameValue = ref('')
const renameInput = ref(null)

// 加载历史会话列表
const loadConversationList = async () => {
  try {
    const response = await getConversationList()
    if (response.code === 200) {
      conversations.value = response.data
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 加载指定会话
const loadConversation = (conversationId) => {
  currentConversationId.value = conversationId
  router.push({
    path: '/chat',
    query: { conversationId }
  })
}

const navigateTo = (path) => {
  router.push(path)
  showUserMenu.value = false
}

const startNewChat = () => {
  currentConversationId.value = null
  router.push('/chat')
}

const handleLogout = () => {
  showUserMenu.value = false
  clearUserInfo()
  router.push('/login')
}

// 右键菜单
const showContextMenu = (event, conv) => {
  event.preventDefault()
  event.stopPropagation()
  // 计算菜单位置，防止超出屏幕
  const sidebar = event.currentTarget.closest('.sidebar') || event.currentTarget.closest('.user-layout')
  const rect = sidebar ? sidebar.getBoundingClientRect() : { left: 0, top: 0 }
  let x = event.clientX - rect.left
  let y = event.clientY - rect.top
  // 防止超出底部
  if (y > (rect.height || 600) - 150) y = (rect.height || 600) - 150
  contextMenu.value = { visible: true, x, y, conv }
}

const closeContextMenu = () => {
  contextMenu.value.visible = false
}

// 置顶
const handlePin = async () => {
  const conv = contextMenu.value.conv
  if (!conv) return
  try {
    await pinConversation(conv.conversation_id, !conv.is_pinned)
    await loadConversationList()
  } catch (error) {
    console.error('置顶操作失败:', error)
  }
  closeContextMenu()
}

// 重命名
const handleRename = () => {
  const conv = contextMenu.value.conv
  if (!conv) return
  editingId.value = conv.conversation_id
  renameValue.value = conv.title
  closeContextMenu()
  nextTick(() => {
    if (renameInput.value) {
      const input = Array.isArray(renameInput.value) ? renameInput.value[0] : renameInput.value
      if (input) input.focus()
    }
  })
}

const confirmRename = async () => {
  if (!editingId.value || !renameValue.value.trim()) {
    cancelRename()
    return
  }
  try {
    await renameConversation(editingId.value, renameValue.value.trim())
    await loadConversationList()
  } catch (error) {
    console.error('重命名失败:', error)
  }
  editingId.value = null
  renameValue.value = ''
}

const cancelRename = () => {
  editingId.value = null
  renameValue.value = ''
}

// 删除
const handleDelete = async () => {
  const conv = contextMenu.value.conv
  if (!conv) return
  if (!confirm(`确定删除会话"${conv.title}"吗？`)) return
  try {
    await deleteConversation(conv.conversation_id)
    // 如果删除的是当前会话，跳转到新对话
    if (currentConversationId.value === conv.conversation_id) {
      startNewChat()
    }
    await loadConversationList()
  } catch (error) {
    console.error('删除会话失败:', error)
  }
  closeContextMenu()
}

// 点击其他区域关闭菜单
const handleClickOutside = () => {
  closeContextMenu()
  if (showUserMenu.value) showUserMenu.value = false
}

// 组件挂载时加载会话列表
onMounted(() => {
  loadConversationList()
  window.addEventListener('conversation-updated', loadConversationList)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('conversation-updated', loadConversationList)
  document.removeEventListener('click', handleClickOutside)
})

// 暴露方法给子组件调用
defineExpose({
  loadConversationList
})
</script>

<style scoped>
.user-layout {
  display: flex;
  height: 100vh;
  background: #f0f4f8;
  color: #374151;
  position: relative;
}

/* 侧边栏样式 */
.sidebar {
  width: 280px;
  height: 100vh;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.03);
  position: relative;
}

.sidebar-header {
  padding: 1.25rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  background: white;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.logo:hover {
  transform: scale(1.02);
}

.logo-icon {
  font-size: 1.6rem;
}

.logo-text {
  font-size: 1.3rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 新建对话按钮 */
.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: calc(100% - 1.5rem);
  margin: 1rem 0.75rem;
  padding: 0.85rem 1.1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.45);
}

/* 历史会话列表 */
.conversations-section {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.75rem;
}

.conversations-section::-webkit-scrollbar {
  width: 4px;
}

.conversations-section::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 10px;
}

.section-title {
  font-size: 0.75rem;
  color: #9ca3af;
  padding: 0.75rem 0.5rem 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  font-weight: 600;
}

.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.conversation-item:hover {
  background: rgba(99, 102, 241, 0.08);
  transform: translateX(3px);
}

.conversation-item.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.12) 100%);
  border: 1px solid rgba(99, 102, 241, 0.25);
}

.conversation-item.pinned {
  background: rgba(250, 230, 180, 0.15);
}

.conversation-item.pinned:hover {
  background: rgba(250, 230, 180, 0.25);
}

.conv-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f0ff, #e8e8ff);
  border-radius: 10px;
  flex-shrink: 0;
  color: #6366f1;
}

.conversation-item.active .conv-icon {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.conversation-item.pinned .conv-icon {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #d97706;
}

.conversation-item.pinned.active .conv-icon {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 0.87rem;
  color: #374151;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-item.pinned .conv-title {
  font-weight: 600;
}

.rename-input {
  width: 100%;
  font-size: 0.87rem;
  padding: 2px 6px;
  border: 1.5px solid #6366f1;
  border-radius: 6px;
  outline: none;
  background: white;
  color: #374151;
}

.conv-time {
  font-size: 0.7rem;
  color: #9ca3af;
  margin-top: 3px;
}

.conv-actions {
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.conversation-item:hover .conv-actions {
  opacity: 1;
}

.action-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.empty-conversations {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: #9ca3af;
  gap: 0.5rem;
}

.empty-conversations span {
  font-size: 0.85rem;
}

/* 右键菜单 */
.context-menu {
  position: absolute;
  z-index: 100;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 0.4rem;
  min-width: 150px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12), 0 0 1px rgba(0, 0, 0, 0.06);
  animation: ctxFadeIn 0.15s ease-out;
}

@keyframes ctxFadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.ctx-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.75rem;
  font-size: 0.83rem;
  color: #4b5563;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.ctx-item:hover {
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
}

.ctx-item svg {
  opacity: 0.5;
}

.ctx-item:hover svg {
  opacity: 1;
}

.ctx-item.danger {
  color: #ef4444;
}

.ctx-item.danger:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #dc2626;
}

.ctx-item.danger svg {
  opacity: 0.6;
}

.ctx-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.08), transparent);
  margin: 0.3rem 0;
}

/* 侧边栏底部 */
.sidebar-footer {
  margin-top: auto;
  padding: 0.85rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  background: rgba(255, 255, 255, 0.6);
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s;
}

.user-info:hover {
  background: rgba(99, 102, 241, 0.06);
}

.user-avatar {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 3px 10px rgba(99, 102, 241, 0.3);
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: #1f2937;
}

.user-status {
  font-size: 0.73rem;
  color: #10b981;
  font-weight: 500;
}

.dropdown-icon {
  opacity: 0.45;
  transition: all 0.2s;
}

.user-info:hover .dropdown-icon {
  opacity: 0.8;
  transform: rotate(90deg);
}

/* 用户菜单 */
.user-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0.85rem;
  right: 0.85rem;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.07);
  border-radius: 14px;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  box-shadow: 
    0 10px 40px rgba(0, 0, 0, 0.12),
    0 0 1px rgba(0, 0, 0, 0.08);
  animation: menuFadeIn 0.2s ease-out;
}

@keyframes menuFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.85rem;
  color: #4b5563;
  font-size: 0.88rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.menu-item:hover {
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
}

.menu-item svg {
  opacity: 0.55;
}

.menu-item:hover svg {
  opacity: 1;
}

.menu-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.08), transparent);
  margin: 0.4rem 0;
}

.menu-item.logout {
  color: #ef4444;
}

.menu-item.logout:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #dc2626;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef0f4 50%, #f0f4f8 100%);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -280px;
    z-index: 1000;
    transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
  }

  .sidebar.open {
    left: 0;
  }

  .main-content {
    width: 100%;
  }
}
</style>
