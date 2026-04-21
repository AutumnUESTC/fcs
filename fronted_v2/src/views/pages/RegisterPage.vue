<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-card">
        <h1 class="register-title">用户注册</h1>
        
        <form class="register-form" @submit.prevent="handleSubmit">
          <!-- 用户名输入框 -->
          <div class="form-group">
            <label class="form-label">
              <span class="label-icon">👤</span>
              <span>用户名</span>
            </label>
            <input
              v-model="formData.username"
              type="text"
              class="form-input"
              placeholder="请输入用户名"
              required
            />
          </div>

          <!-- 昵称输入框 -->
          <div class="form-group">
            <label class="form-label">
              <span class="label-icon">✏️</span>
              <span>昵称</span>
            </label>
            <input
              v-model="formData.nickname"
              type="text"
              class="form-input"
              placeholder="请输入昵称（可选）"
            />
          </div>

          <!-- 密码输入框 -->
          <div class="form-group">
            <label class="form-label">
              <span class="label-icon">🔒</span>
              <span>密码</span>
            </label>
            <input
              v-model="formData.password"
              type="password"
              class="form-input"
              placeholder="请输入密码"
              required
            />
          </div>

          <!-- 确认密码输入框 -->
          <div class="form-group">
            <label class="form-label">
              <span class="label-icon">🔒</span>
              <span>确认密码</span>
            </label>
            <input
              v-model="formData.confirmPassword"
              type="password"
              class="form-input"
              placeholder="请再次输入密码"
              required
            />
          </div>

          <!-- 错误提示 -->
          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

          <!-- 注册按钮 -->
          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '注册中...' : '立即注册' }}
          </button>
        </form>

        <!-- 切换到登录 -->
        <div class="switch-text">
          <span>已有账号？</span>
          <router-link to="/login" class="switch-btn">去登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/user'

const router = useRouter()

const formData = reactive({
  username: '',
  nickname: '',
  password: '',
  confirmPassword: ''
})
const errorMsg = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  errorMsg.value = ''

  // 前端校验
  if (formData.password !== formData.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }
  if (formData.password.length < 6) {
    errorMsg.value = '密码长度不能少于6位'
    return
  }

  isLoading.value = true

  try {
    const res = await register(formData.username, formData.password, formData.nickname)
    if (res.code === 200) {
      router.push('/login')
    }
  } catch (error) {
    errorMsg.value = error.message || '注册失败，请重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px - 80px);
  padding: 2rem;
}

.register-container {
  width: 100%;
  max-width: 500px;
}

.register-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.register-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #fff;
  text-align: center;
  margin-bottom: 2rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.label-icon {
  font-size: 1.2rem;
}

.form-input {
  padding: 1rem 1.25rem;
  font-size: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  color: #fff;
  outline: none;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.form-input:focus {
  border-color: #d4af37;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 20px rgba(212, 175, 55, 0.2);
}

.error-msg {
  color: #ff6b6b;
  font-size: 0.9rem;
  text-align: center;
  margin: -0.5rem 0;
}

.submit-btn {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: #0a3d5f;
  background: linear-gradient(135deg, #d4af37, #f4d03f);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(212, 175, 55, 0.5);
}

.submit-btn:active {
  transform: translateY(0);
}

.switch-text {
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
  margin-top: 1.5rem;
}

.switch-btn {
  background: none;
  border: none;
  color: #d4af37;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
}

.switch-btn:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .register-page {
    padding: 1.5rem 1rem;
  }

  .register-card {
    padding: 2rem 1.5rem;
  }

  .register-title {
    font-size: 2rem;
  }
}

@media (max-width: 480px) {
  .register-title {
    font-size: 1.6rem;
    margin-bottom: 1.5rem;
  }

  .form-input {
    padding: 0.85rem 1rem;
  }

  .submit-btn {
    padding: 0.9rem 1.5rem;
    font-size: 1rem;
  }
}
</style>
