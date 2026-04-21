<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <h1 class="login-title">用户登录</h1>
        
        <form class="login-form" @submit.prevent="handleSubmit">
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

          <!-- 错误提示 -->
          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

          <!-- 登录按钮 -->
          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '登录中...' : '立即登录' }}
          </button>
        </form>

        <!-- 切换到注册 -->
        <div class="switch-text">
          <span>没有账号？</span>
          <router-link to="/register" class="switch-btn">去注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/user'

const router = useRouter()

const formData = reactive({
  username: '',
  password: ''
})
const errorMsg = ref('')
const isLoading = ref(false)

// 提交表单
const handleSubmit = async () => {
  errorMsg.value = ''
  isLoading.value = true

  try {
    const res = await login(formData.username, formData.password)
    if (res.code === 200) {
      router.push('/chat')
    }
  } catch (error) {
    errorMsg.value = error.message || '登录失败，请重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px - 80px);
  padding: 2rem;
}

.login-container {
  width: 100%;
  max-width: 500px;
}

.login-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.login-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #fff;
  text-align: center;
  margin-bottom: 2rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.login-form {
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
  margin-top: 0.5rem;
}

.switch-btn {
  background: none;
  border: none;
  color: #d4af37;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-page {
    padding: 1.5rem 1rem;
  }

  .login-card {
    padding: 2rem 1.5rem;
  }

  .login-title {
    font-size: 2rem;
  }
}

@media (max-width: 480px) {
  .login-title {
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
