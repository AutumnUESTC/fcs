<template>
  <div class="chat-page">
    <div class="chat-content">
      <div class="chat-section" @click="onChatAreaClick">
        <!-- 服务选择器（可点击展开） -->
        <div class="service-selector" :class="{ expanded: showServicePicker }">
          <!-- 当前服务标签行（点击切换） -->
          <div class="service-bar" @click.stop="toggleServicePicker">
            <div class="service-current">
              <span class="svc-icon">{{ currentService.icon }}</span>
              <span class="svc-name">{{ currentService.title }}</span>
              <svg :class="['svc-chevron', { open: showServicePicker }]" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>

            <!-- 展开的服务列表 -->
            <transition name="picker-expand">
              <div v-if="showServicePicker" class="service-picker-list">
                <button
                  v-for="s in serviceList"
                  :key="s.id"
                  :class="['svc-option', { active: selectedServiceId === s.id }]"
                  @click.stop="selectService(s.id)"
                >
                  <span class="opt-icon">{{ s.icon }}</span>
                  <span class="opt-name">{{ s.title }}</span>
                  <svg v-if="selectedServiceId === s.id" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                </button>
              </div>
            </transition>
          </div>

        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-icon">⚖️</div>
            <p class="welcome-text">{{ currentService.welcome }}</p>
            <div class="quick-actions">
              <button 
                v-for="(q, i) in quickQuestions" :key="i"
                class="quick-btn"
                @click="inputText = q; sendMessage()"
              >{{ q }}</button>
            </div>
          </div>
          
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">
              <span v-if="msg.role === 'user'">👤</span>
              <span v-else>🤖</span>
            </div>
            <div class="message-content">
              {{ msg.content }}
              <span v-if="msg.loading" class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <!-- 文件上传按钮 -->
          <label class="upload-btn" title="上传文件（PDF、DOC、TXT等）">
            <input
              type="file"
              ref="fileInput"
              @change="handleFileUpload"
              accept=".pdf,.doc,.docx,.txt,.md"
              hidden
            />
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
            </svg>
          </label>
          
          <!-- 已上传文件显示 -->
          <div v-if="uploadedFile" class="uploaded-file">
            <span class="file-icon">📄</span>
            <span class="file-name">{{ uploadedFile.name }}</span>
            <button @click="removeFile" class="remove-file">×</button>
          </div>
          
          <input
            v-model="inputText"
            type="text"
            class="input-field"
            :placeholder="currentService.placeholder"
            :disabled="isLoading"
            @keyup.enter="sendMessage"
          />
          <button class="send-btn" :disabled="isLoading || (!inputText.trim() && !uploadedFile)" @click="sendMessage">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sendChatMessage, getServiceList, resetResponseIndex, getConversationDetail, saveConversation } from '@/api/chat'

const route = useRoute()
const router = useRouter()

// 服务列表
const serviceList = ref(getServiceList())

// 默认选择法律问答
const selectedServiceId = ref('qa')
const inputText = ref('')
const messages = ref([])
const messagesContainer = ref(null)
const isLoading = ref(false)
const currentConversationId = ref(null)
const showServicePicker = ref(false)

// 文件上传相关
const uploadedFile = ref(null)
const fileInput = ref(null)

// 快捷问题（根据服务类型）
const quickQuestions = computed(() => {
  const map = {
    qa: ['劳动纠纷怎么处理？', '合同违约怎么办？', '离婚需要什么材料？'],
    contract: ['生成租赁合同', '起草买卖合同', '制作借款协议'],
    compliance: ['电商合规检查', '企业合规自查', '数据隐私审查'],
    complaint: ['消费维权投诉', '物业纠纷举报', '环境污染投诉'],
    laws: ['查询民法典', '搜索公司法', '查找劳动法条款'],
    lawfirm: ['推荐刑事律师', '找婚姻家事律师', '咨询知识产权律师']
  }
  return map[selectedServiceId.value] || map.qa
})

// 当前选中的服务
const currentService = computed(() => {
  return serviceList.value.find(s => s.id === selectedServiceId.value) || serviceList.value[0]
})

// 根据服务ID获取消息前缀
const getServicePrefix = () => {
  const prefixes = {
    contract: '[合同文书生成] ',
    compliance: '[合规自查] ',
    complaint: '[维权投诉] ',
    qa: '',
    laws: '[法规查询] ',
    lawfirm: '[律所推荐] '
  }
  return prefixes[selectedServiceId.value] || ''
}

// 切换服务时重置回复索引
const onServiceChange = () => {
  resetResponseIndex()
}

// 服务选择器
const toggleServicePicker = () => {
  showServicePicker.value = !showServicePicker.value
}

const selectService = (id) => {
  if (id === selectedServiceId.value) return
  selectedServiceId.value = id
  showServicePicker.value = false
  onServiceChange()
}

const closeServicePicker = () => {
  showServicePicker.value = false
}

// 点击聊天区域其他位置关闭选择器
const onChatAreaClick = (e) => {
  if (!e.target.closest('.service-selector')) {
    showServicePicker.value = false
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 加载历史会话
const loadConversation = async (conversationId) => {
  try {
    const response = await getConversationDetail(conversationId)
    if (response.code === 200 && response.data) {
      const data = response.data
      messages.value = data.messages || []
      selectedServiceId.value = data.service_id || 'qa'
      currentConversationId.value = data.conversation_id || conversationId
      setTimeout(scrollToBottom, 100)
    }
    // code=404 表示会话尚未保存到后端（新对话），静默忽略
  } catch (error) {
    // 其他错误也静默处理，避免影响用户创建新对话
    console.warn('加载会话跳过:', error.message || error)
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputText.value.trim() && !uploadedFile.value) return

  // 如果没有会话ID，说明是新对话
  if (!currentConversationId.value) {
    currentConversationId.value = `conv_${Date.now()}`
    isNewLocalConversation.value = true  // 标记为本地新创建，避免 watch 触发 loadConversation
    router.replace({
      path: '/chat',
      query: { conversationId: currentConversationId.value }
    })
  }

  // 获取原始输入和带前缀的消息
  const rawQuestion = inputText.value.trim()
  const question = getServicePrefix() + rawQuestion
  const timestamp = new Date().toLocaleString('zh-CN')

  // 处理文件上传
  let fileMessage = ''
  if (uploadedFile.value) {
    fileMessage = `\n\n[已上传文件: ${uploadedFile.value.name} (${(uploadedFile.value.size / 1024).toFixed(1)}KB)]`
  }

  // 添加用户消息（显示原始内容）
  messages.value.push({
    role: 'user',
    content: rawQuestion + (uploadedFile.value ? ` 📎 ${uploadedFile.value.name}` : ''),
    serviceId: selectedServiceId.value
  })

  inputText.value = ''
  
  // 清除文件引用（但保留用于发送）
  const fileToSend = uploadedFile.value
  uploadedFile.value = null
  
  scrollToBottom()

  // 添加AI回复占位
  const assistantMessageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    serviceId: selectedServiceId.value,
    loading: true
  })

  isLoading.value = true
  scrollToBottom()

  try {
    // 调用API（发送带前缀的问题和文件信息）
    const response = await sendChatMessage(
      currentConversationId.value,
      selectedServiceId.value,
      question + fileMessage,
      timestamp
    )

    messages.value[assistantMessageIndex].loading = false
    const fullResponse = response.data.answer
    await typeWriter(assistantMessageIndex, fullResponse)
    await handleSaveConversation()

  } catch (error) {
    console.error('Chat API error:', error)
    messages.value[assistantMessageIndex].content = '抱歉，服务出现了一点问题：' + (error.message || error)
    messages.value[assistantMessageIndex].loading = false
  }

  isLoading.value = false
}

// 文件上传处理
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 文件大小限制（10MB）
  if (file.size > 10 * 1024 * 1024) {
    alert('文件大小不能超过10MB')
    return
  }

  // 支持的格式
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown'
  ]
  
  if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|txt|md)$/i)) {
    alert('仅支持 PDF、DOC、DOCX、TXT、MD 格式')
    return
  }

  uploadedFile.value = file
}

// 移除已上传文件
const removeFile = () => {
  uploadedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 保存会话
const handleSaveConversation = async () => {
  try {
    const cleanMessages = messages.value.map(m => ({
      role: m.role,
      content: m.content
    }))
    await saveConversation(
      currentConversationId.value,
      selectedServiceId.value,
      cleanMessages
    )
    refreshConversationList()
  } catch (error) {
    console.error('保存会话失败:', error)
  }
}

// 刷新会话列表
const refreshConversationList = () => {
  const event = new CustomEvent('conversation-updated')
  window.dispatchEvent(event)
}

// 打字机效果
const typeWriter = async (messageIndex, text) => {
  const chars = text.split('')
  for (let i = 0; i < chars.length; i++) {
    messages.value[messageIndex].content += chars[i]
    if (i % 10 === 0) scrollToBottom()
    await new Promise(resolve => setTimeout(resolve, 20))
  }
  scrollToBottom()
}

// 标记：当前会话是否是本地新创建的（还未保存到后端）
const isNewLocalConversation = ref(false)

// 监听路由变化
watch(() => route.query.conversationId, (newId) => {
  currentConversationId.value = newId
  if (newId && !isNewLocalConversation.value) {
    loadConversation(newId)
  } else if (!newId) {
    messages.value = []
  }
  // 重置标记
  isNewLocalConversation.value = false
}, { immediate: true })

onMounted(async () => {
  const id = route.query.conversationId
  if (id) {
    currentConversationId.value = id
    loadConversation(id)
    return
  }

  const serviceId = route.query.serviceId
  if (serviceId && serviceList.value.find(s => s.id === serviceId)) {
    selectedServiceId.value = serviceId
    onServiceChange()
  }

  const question = route.query.question
  if (question) {
    inputText.value = question
    await nextTick()
    sendMessage()
  }
})
</script>

<style scoped>
/* ==================== 整体布局 ==================== */
.chat-page {
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.chat-content {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* ==================== 主聊天区域 ==================== */
.chat-section {
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 10px 30px -5px rgba(0, 0, 0, 0.08),
    0 25px 50px -12px rgba(0, 0, 0, 0.06);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

/* ==================== 服务选择器 ==================== */
.service-selector {
  position: relative;
  z-index: 10;
}

.service-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.7rem 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 0.85rem;
  font-weight: 500;
  border-radius: 0; /* 圆角只给底部 */
  cursor: pointer;
  transition: all 0.25s ease;
  user-select: none;
}

/* 未展开时：顶部圆角 */
.chat-section > .service-selector:not(.expanded) > .service-bar {
  border-radius: 24px 24px 0 0;
}
/* 展开时：无圆角 */
.chat-section > .service-selector.expanded > .service-bar {
  border-radius: 12px 12px 0 0;
}

.service-bar:hover { filter: brightness(1.05); }

.service-current {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex: 1;
  min-width: 0;
}

.svc-icon { font-size: 1rem; line-height: 1; }
.svc-name { letter-spacing: 0.3px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.svc-chevron { opacity: 0.6; transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); flex-shrink: 0; margin-left: auto; }
.svc-chevron.open { transform: rotate(180deg); opacity: 1; }

/* 展开的服务列表 */
.service-picker-list {
  display: flex;
  flex-direction: column;
  background: #fafbff;
  border-bottom-left: 1px solid rgba(99,102,241,0.08);
  border-bottom-right: 1px solid rgba(99,102,241,0.08);
  padding: 6px 8px 10px;
  gap: 3px;
  box-shadow: 0 4px 16px rgba(99,102,241,0.06);
}

.svc-option {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: none;
  border-radius: 11px;
  background: transparent;
  color: #4b5563;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  font-family: inherit;
}

.svc-option .opt-icon { font-size: 1rem; flex-shrink: 0; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(255,255,255,0.7); }
.svc-option .opt-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.svc-option svg:last-child { color: transparent; flex-shrink: 0; transition: color 0.2s; }

.svc-option:hover { background: rgba(99, 102, 241, 0.08); color: #667eea; }

.svc-option.active { background: rgba(99, 102, 241, 0.1) !important; color: #667eea !important; font-weight: 700; }
.svc-option.active svg:last-child { color: #667eea; }
.svc-option.active .opt-icon { background: linear-gradient(135deg, #667eea, #764ba2) !important; color: white !important; }

/* 展开动画 */
.picker-expand-enter-active,
.picker-expand-leave-active { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; }
.picker-expand-enter-from,
.picker-expand-leave-to { max-height: 0; opacity: 0; padding-top: 0; padding-bottom: 0; }
.picker-expand-enter-to,
.picker-expand-leave-from { max-height: 320px; opacity: 1; }

/* ==================== 消息列表 ==================== */
.messages-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1.5rem;
  background: linear-gradient(to bottom, #fafbfc, #f8f9fa);
}

.messages-container::-webkit-scrollbar {
  width: 5px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #c7d2fe, #ddd6fe);
  border-radius: 10px;
}

/* ==================== 欢迎界面 ==================== */
.welcome-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  flex-direction: column;
  gap: 1.5rem;
  padding: 2rem;
}

.welcome-icon {
  font-size: 3.5rem;
  filter: drop-shadow(0 4px 12px rgba(102, 126, 234, 0.3));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.welcome-text {
  font-size: 1.15rem;
  color: #4a5568;
  text-align: center;
  max-width: 480px;
  line-height: 1.8;
  font-weight: 400;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
  margin-top: 1rem;
}

.quick-btn {
  padding: 0.6rem 1.2rem;
  background: white;
  border: 1.5px solid #e2e8f0;
  border-radius: 50px;
  color: #4a5568;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.quick-btn:hover {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.35);
}

/* ==================== 消息样式 ==================== */
.message {
  display: flex;
  gap: 0.85rem;
  margin-bottom: 1.5rem;
  animation: slideIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.message-content {
  max-width: 70%;
  padding: 1rem 1.25rem;
  border-radius: 18px;
  font-size: 0.93rem;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 6px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.message.assistant .message-content {
  background: white;
  color: #374151;
  border-bottom-left-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

/* 打字指示器 */
.typing-indicator {
  display: inline-flex;
  gap: 5px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  animation: typingDot 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingDot {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* ==================== 输入区域 ==================== */
.chat-input {
  display: flex;
  gap: 0.85rem;
  padding: 1.25rem 1.5rem;
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  align-items: center;
}

/* 文件上传按钮 */
.upload-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 2px dashed #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.3s ease;
  flex-shrink: 0;
  background: #f9fafb;
}

.upload-btn:hover {
  border-color: #667eea;
  color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

/* 已上传文件显示 */
.uploaded-file {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.08));
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 10px;
  font-size: 0.82rem;
  color: #4f46e5;
  max-width: 200px;
}

.file-icon {
  font-size: 1.1rem;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0 0.25rem;
  line-height: 1;
  transition: color 0.2s;
}

.remove-file:hover {
  color: #ef4444;
}

.input-field {
  flex: 1;
  padding: 0.95rem 1.35rem;
  font-size: 0.95rem;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
  color: #1a202c;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-field::placeholder {
  color: #a0aec0;
}

.input-field:focus {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.input-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #edf2f7;
}

.send-btn {
  padding: 0.95rem 1.4rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.45);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}

.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 768px) {
  .chat-page {
    padding: 0.75rem;
  }

  .welcome-text {
    font-size: 1rem;
  }

  .message-content {
    max-width: 82%;
  }

  .chat-input {
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
  }

  .send-btn {
    padding: 0.95rem;
  }

  .quick-actions {
    gap: 0.5rem;
  }

  .quick-btn {
    font-size: 0.8rem;
    padding: 0.5rem 1rem;
  }
}
</style>