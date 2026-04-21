<template>
  <div class="user-center">
    <div class="user-content">
      <h1 class="page-title">用户中心</h1>
      
      <!-- 用户信息卡片 -->
      <div class="user-info-card">
        <div class="avatar-section">
          <div class="avatar">
            {{ userInfo.username ? userInfo.username.charAt(0).toUpperCase() : 'U' }}
          </div>
          <div class="user-details">
            <h2 class="username">{{ userInfo.username || '未登录' }}</h2>
            <p class="email">{{ userInfo.email || '请绑定邮箱' }}</p>
          </div>
        </div>
      </div>

      <!-- 功能选项卡 -->
      <div class="tabs">
        <button 
          :class="['tab-btn', { active: activeTab === 'profile' }]" 
          @click="activeTab = 'profile'"
        >
          账号信息
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'password' }]" 
          @click="activeTab = 'password'"
        >
          修改密码
        </button>
      </div>

      <!-- 账号信息面板 -->
      <div v-if="activeTab === 'profile'" class="panel">
        <div class="form-group">
          <label>用户名</label>
          <input 
            type="text" 
            v-model="profileForm.username" 
            placeholder="请输入用户名"
            :disabled="!isEditing"
          />
        </div>
        
        <div class="form-group">
          <label>邮箱</label>
          <input 
            type="email" 
            v-model="profileForm.email" 
            placeholder="请输入邮箱"
            :disabled="!isEditing"
          />
        </div>
        
        <div class="form-group">
          <label>手机号</label>
          <input 
            type="tel" 
            v-model="profileForm.phone" 
            placeholder="请输入手机号"
            :disabled="!isEditing"
          />
        </div>

        <div class="form-actions">
          <button v-if="!isEditing" class="btn-primary" @click="isEditing = true">
            编辑资料
          </button>
          <template v-else>
            <button class="btn-primary" @click="saveProfile">保存</button>
            <button class="btn-secondary" @click="cancelEdit">取消</button>
          </template>
        </div>
      </div>

      <!-- 修改密码面板 -->
      <div v-if="activeTab === 'password'" class="panel">
        <div class="form-group">
          <label>当前密码</label>
          <div class="password-input">
            <input 
              :type="showPassword.current ? 'text' : 'password'" 
              v-model="passwordForm.currentPassword" 
              placeholder="请输入当前密码"
            />
            <button class="toggle-btn" @click="showPassword.current = !showPassword.current">
              {{ showPassword.current ? '隐藏' : '显示' }}
            </button>
          </div>
        </div>
        
        <div class="form-group">
          <label>新密码</label>
          <div class="password-input">
            <input 
              :type="showPassword.new ? 'text' : 'password'" 
              v-model="passwordForm.newPassword" 
              placeholder="请输入新密码（至少6位）"
            />
            <button class="toggle-btn" @click="showPassword.new = !showPassword.new">
              {{ showPassword.new ? '隐藏' : '显示' }}
            </button>
          </div>
        </div>
        
        <div class="form-group">
          <label>确认新密码</label>
          <div class="password-input">
            <input 
              :type="showPassword.confirm ? 'text' : 'password'" 
              v-model="passwordForm.confirmPassword" 
              placeholder="请再次输入新密码"
            />
            <button class="toggle-btn" @click="showPassword.confirm = !showPassword.confirm">
              {{ showPassword.confirm ? '隐藏' : '显示' }}
            </button>
          </div>
        </div>

        <div class="password-strength" v-if="passwordForm.newPassword">
          <div class="strength-label">密码强度：</div>
          <div class="strength-bar">
            <div 
              class="strength-fill" 
              :style="{ width: passwordStrength.percent + '%' }"
              :class="passwordStrength.level"
            ></div>
          </div>
          <span class="strength-text" :class="passwordStrength.level">
            {{ passwordStrength.text }}
          </span>
        </div>

        <div class="form-actions">
          <button class="btn-primary" @click="changePassword" :disabled="isSubmitting">
            {{ isSubmitting ? '提交中...' : '修改密码' }}
          </button>
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
import { ref, reactive, computed } from 'vue'

// 用户信息（从本地存储或API获取）
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))

// 当前激活的标签页
const activeTab = ref('profile')

// 是否在编辑模式
const isEditing = ref(false)

// 是否正在提交
const isSubmitting = ref(false)

// 消息提示
const message = ref('')
const messageType = ref('success')

// 账号信息表单
const profileForm = reactive({
  username: userInfo.value.username || '',
  email: userInfo.value.email || '',
  phone: userInfo.value.phone || ''
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 密码显示状态
const showPassword = reactive({
  current: false,
  new: false,
  confirm: false
})

// 计算密码强度
const passwordStrength = computed(() => {
  const pwd = passwordForm.newPassword
  if (!pwd) return { percent: 0, level: '', text: '' }
  
  let strength = 0
  if (pwd.length >= 6) strength += 25
  if (pwd.length >= 10) strength += 25
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength += 25
  if (/\d/.test(pwd)) strength += 15
  if (/[^a-zA-Z0-9]/.test(pwd)) strength += 10

  let level = 'weak'
  let text = '弱'
  if (strength >= 75) {
    level = 'strong'
    text = '强'
  } else if (strength >= 50) {
    level = 'medium'
    text = '中'
  }

  return { percent: Math.min(strength, 100), level, text }
})

// 显示消息
const showMessage = (msg, type = 'success') => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

// 保存账号信息
const saveProfile = async () => {
  if (!profileForm.username || !profileForm.email) {
    showMessage('请填写完整信息', 'error')
    return
  }

  isSubmitting.value = true
  
  try {
    // TODO: 调用API保存用户信息
    // await api.updateProfile(profileForm)
    
    // 模拟保存
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    localStorage.setItem('userInfo', JSON.stringify({
      username: profileForm.username,
      email: profileForm.email,
      phone: profileForm.phone
    }))
    
    userInfo.value = { ...profileForm }
    isEditing.value = false
    showMessage('保存成功')
  } catch (error) {
    showMessage('保存失败，请重试', 'error')
  } finally {
    isSubmitting.value = false
  }
}

// 取消编辑
const cancelEdit = () => {
  profileForm.username = userInfo.value.username || ''
  profileForm.email = userInfo.value.email || ''
  profileForm.phone = userInfo.value.phone || ''
  isEditing.value = false
}

// 修改密码
const changePassword = async () => {
  // 验证表单
  if (!passwordForm.currentPassword) {
    showMessage('请输入当前密码', 'error')
    return
  }
  
  if (!passwordForm.newPassword) {
    showMessage('请输入新密码', 'error')
    return
  }
  
  if (passwordForm.newPassword.length < 6) {
    showMessage('新密码至少6位', 'error')
    return
  }
  
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    showMessage('两次密码不一致', 'error')
    return
  }
  
  if (passwordForm.currentPassword === passwordForm.newPassword) {
    showMessage('新密码不能与当前密码相同', 'error')
    return
  }

  isSubmitting.value = true
  
  try {
    // TODO: 调用API修改密码
    // await api.changePassword({
    //   currentPassword: passwordForm.currentPassword,
    //   newPassword: passwordForm.newPassword
    // })
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 清空表单
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    
    showMessage('密码修改成功')
  } catch (error) {
    showMessage(error.message || '密码修改失败', 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.user-center {
  padding: 4rem 2rem;
  min-height: calc(100vh - 80px);
}

.user-content {
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

/* 用户信息卡片 */
.user-info-card {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(139, 90, 43, 0.2));
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(10px);
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #d4af37, #8b5a2b);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 700;
  color: #fff;
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
}

.user-details .username {
  font-size: 1.5rem;
  color: #d4af37;
  margin-bottom: 0.5rem;
}

.user-details .email {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.95rem;
}

/* 标签页 */
.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.tab-btn {
  padding: 0.8rem 2rem;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.tab-btn.active {
  background: linear-gradient(135deg, #d4af37, #8b5a2b);
  color: #fff;
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
}

/* 表单面板 */
.panel {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: #d4af37;
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-group input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #d4af37;
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.2);
}

.form-group input:disabled {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.6);
  cursor: not-allowed;
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

/* 密码输入框 */
.password-input {
  display: flex;
  gap: 0.5rem;
}

.password-input input {
  flex: 1;
}

.toggle-btn {
  padding: 0 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 密码强度 */
.password-strength {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.strength-label {
  color: rgba(255, 255, 255, 0.7);
}

.strength-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.strength-fill.weak {
  background: #ff4d4f;
}

.strength-fill.medium {
  background: #faad14;
}

.strength-fill.strong {
  background: #52c41a;
}

.strength-text {
  font-weight: 600;
}

.strength-text.weak {
  color: #ff4d4f;
}

.strength-text.medium {
  color: #faad14;
}

.strength-text.strong {
  color: #52c41a;
}

/* 按钮 */
.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-primary {
  padding: 0.8rem 2rem;
  background: linear-gradient(135deg, #d4af37, #8b5a2b);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.8rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
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

/* 响应式设计 */
@media (max-width: 768px) {
  .user-center {
    padding: 2rem 1rem;
  }

  .page-title {
    font-size: 1.8rem;
  }

  .avatar {
    width: 60px;
    height: 60px;
    font-size: 1.8rem;
  }

  .tabs {
    flex-wrap: wrap;
  }

  .tab-btn {
    flex: 1;
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
  }

  .panel {
    padding: 1.5rem;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
}
</style>