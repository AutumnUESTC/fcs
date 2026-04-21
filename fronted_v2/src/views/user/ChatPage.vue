<template>
  <div class="chat-page">
    <div class="chat-content">
      <div class="chat-section">
        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome-message">
            <p class="welcome-text">{{ currentService.welcome }}</p>
          </div>
          
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
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
          <!-- 服务选择下拉框 -->
          <div class="service-select-wrapper">
            <select v-model="selectedServiceId" class="service-select" @change="onServiceChange">
              <option 
                v-for="service in serviceList" 
                :key="service.id" 
                :value="service.id"
              >
                {{ service.icon }} {{ service.title }}
              </option>
            </select>
            <svg class="select-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>

          <input
            v-model="inputText"
            type="text"
            class="input-field"
            :placeholder="currentService.placeholder"
            :disabled="isLoading"
            @keyup.enter="sendMessage"
          />
          <button class="send-btn" :disabled="isLoading || !inputText.trim()" @click="sendMessage">
            {{ isLoading ? '等待回复...' : '发送' }}
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

// 当前选中的服务
const currentService = computed(() => {
  return serviceList.value.find(s => s.id === selectedServiceId.value) || serviceList.value[0]
})

// 切换服务时重置回复索引
const onServiceChange = () => {
  resetResponseIndex()
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
    if (response.code === 200) {
      const data = response.data
      // 加载消息历史
      messages.value = data.messages || []
      // 设置对应的服务
      selectedServiceId.value = data.serviceId
      currentConversationId.value = data.id
      // 滚动到底部
      setTimeout(scrollToBottom, 100)
    }
  } catch (error) {
    console.error('加载会话失败:', error)
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputText.value.trim() || isLoading.value) return

  // 如果没有会话ID，说明是新对话，此时生成临时ID
  if (!currentConversationId.value) {
    currentConversationId.value = `conv_${Date.now()}`
    // 更新 URL，把 ID 带上（replace 不创建新的浏览器历史记录）
    router.replace({
      path: '/chat',
      query: { conversationId: currentConversationId.value }
    })
  }

  const serviceId = selectedServiceId.value
  const question = inputText.value
  const timestamp = new Date().toLocaleString('zh-CN')

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: question,
    serviceId: serviceId
  })

  inputText.value = ''
  scrollToBottom()

  // 添加一条空的消息占位
  const assistantMessageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    serviceId: serviceId,
    loading: true
  })

  isLoading.value = true
  scrollToBottom()

  try {
    // 调用 API（传入 conversationId + message + timestamp）
    const response = await sendChatMessage(
      currentConversationId.value,
      serviceId,
      question,
      timestamp
    )

    // 移除 loading 状态
    messages.value[assistantMessageIndex].loading = false

    // 打字机效果显示回复
    const fullResponse = response.data.answer
    await typeWriter(assistantMessageIndex, fullResponse)

    // 保存会话（此时一定有 ID）
    await handleSaveConversation()

  } catch (error) {
    messages.value[assistantMessageIndex].content = '抱歉，服务出现了一点问题，请稍后再试。'
    messages.value[assistantMessageIndex].loading = false
  }

  isLoading.value = false
}

// 保存会话（一定有 conversationId，无需检查）
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
    // 通知侧边栏刷新会话列表
    refreshConversationList()
  } catch (error) {
    console.error('保存会话失败:', error)
  }
}

// 刷新会话列表
const refreshConversationList = () => {
  // 通过 emit 或 provide/inject 通知父组件刷新
  // 这里暂时用最简单的方案：手动触发
  const event = new CustomEvent('conversation-updated')
  window.dispatchEvent(event)
}

// 打字机效果
const typeWriter = async (messageIndex, text) => {
  const chars = text.split('')
  for (let i = 0; i < chars.length; i++) {
    messages.value[messageIndex].content += chars[i]
    // 每输入几个字符后滚动一次
    if (i % 10 === 0) {
      scrollToBottom()
    }
    // 控制打字速度
    await new Promise(resolve => setTimeout(resolve, 20))
  }
  scrollToBottom()
}

// 监听路由变化，加载历史会话
watch(() => route.query.conversationId, (newId) => {
  currentConversationId.value = newId
  if (newId) {
    loadConversation(newId)
  } else {
    // 无 ID，清空消息
    messages.value = []
  }
}, { immediate: true })

// 组件挂载时检查是否有会话ID
onMounted(() => {
  const id = route.query.conversationId
  if (id) {
    currentConversationId.value = id
    loadConversation(id)
  }
})
</script>

<style scoped>
.chat-page {
  padding: 2rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.chat-content {
  max-width: 1000px;
  width: 100%;
  margin: 0 auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-section {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 消息列表 */
.messages-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1.5rem;
}

/* 自定义滚动条 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(212, 175, 55, 0.4);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(212, 175, 55, 0.6);
}

.welcome-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.welcome-text {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  max-width: 500px;
  line-height: 1.8;
}

.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #d4af37, #f4d03f);
  color: #212121;
}

.message.assistant .message-avatar {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.message-content {
  max-width: 70%;
  padding: 1rem 1.25rem;
  border-radius: 16px;
  font-size: 0.95rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message.user .message-content {
  background: linear-gradient(135deg, #d4af37, #f4d03f);
  color: #212121;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-bottom-left-radius: 4px;
}

/* 打字指示器 */
.typing-indicator {
  display: inline-flex;
  gap: 4px;
  padding: 4px 8px;
  margin-left: 8px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

/* 输入区域 */
.chat-input {
  display: flex;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  align-items: center;
}

/* 服务选择下拉框 */
.service-select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.service-select {
  appearance: none;
  padding: 0.6rem 2rem 0.6rem 0.75rem;
  font-size: 0.85rem;
  color: #d4af37;
  background: rgba(212, 175, 55, 0.15);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
}

.service-select:hover {
  background: rgba(212, 175, 55, 0.2);
  border-color: rgba(212, 175, 55, 0.5);
}

.service-select:focus {
  border-color: #d4af37;
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2);
}

.service-select option {
  background: #2a2a2a;
  color: #fff;
  padding: 0.5rem;
}

.select-arrow {
  position: absolute;
  right: 0.5rem;
  pointer-events: none;
  color: #d4af37;
  opacity: 0.7;
}

.input-field {
  flex: 1;
  padding: 0.875rem 1.25rem;
  font-size: 0.95rem;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  outline: none;
  transition: all 0.3s ease;
}

.input-field::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.input-field:focus {
  border-color: #d4af37;
  background: rgba(255, 255, 255, 0.15);
}

.input-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-btn {
  padding: 0.875rem 1.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: #212121;
  background: linear-gradient(135deg, #d4af37, #f4d03f);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-page {
    padding: 1rem;
  }

  .welcome-text {
    font-size: 1rem;
  }

  .message-content {
    max-width: 85%;
  }

  .chat-input {
    flex-direction: column;
    gap: 0.75rem;
  }

  .service-select-wrapper {
    width: 100%;
  }

  .service-select {
    width: 100%;
  }

  .input-field {
    width: 100%;
  }

  .send-btn {
    width: 100%;
  }
}
</style>
