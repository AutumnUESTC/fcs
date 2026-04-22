<template>
  <div class="register-page">
    <div class="register-container">
      <!-- Logo -->
      <div class="logo-area">
        <div class="logo-icon">⚖️</div>
        <h1 class="brand-name">法脉智联</h1>
        <p class="brand-desc">创建您的账户</p>
      </div>

      <div class="register-card">
        <h2 class="card-title">创建账户</h2>
        <p class="card-subtitle">注册后即可使用所有功能</p>
        
        <form class="register-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input v-model="formData.username" type="text" class="form-input" placeholder="请输入用户名" required />
          </div>

          <div class="form-group">
            <label class="form-label">昵称（可选）</label>
            <input v-model="formData.nickname" type="text" class="form-input" placeholder="设置一个昵称" />
          </div>

          <div class="form-group">
            <label class="form-label">密码</label>
            <input v-model="formData.password" type="password" class="form-input" placeholder="请输入密码（至少6位）" required minlength="6" />
          </div>

          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '注册中...' : '创建账户' }}
          </button>
        </form>

        <div class="switch-text">
          已有账户？
          <router-link to="/login" class="link-btn">去登录</router-link>
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
const formData = reactive({ username: '', password: '', nickname: '' })
const errorMsg = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  errorMsg.value = ''
  isLoading.value = true
  try {
    const res = await register(formData.username, formData.password, formData.nickname)
    if (res.code === 200) router.push('/chat')
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
  min-height: calc(100vh - 120px);
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa, #e8ecf4);
}

.register-container { width: 100%; max-width: 420px; }

.logo-area { text-align: center; margin-bottom: 1.75rem; }

.logo-icon { font-size: 3.2rem; margin-bottom: 0.5rem; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.brand-name { font-size: 1.6rem; font-weight: 800; background: linear-gradient(135deg,#667eea,#764ba2); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.brand-desc { color:#64748b; font-size:.88rem; margin-top:.25rem; }

.register-card { background:white; border-radius:24px; padding:2.5rem; box-shadow:0 4px 6px rgba(0,0,0,.04), 0 10px 40px rgba(99,102,241,.12); border:1px solid rgba(0,0,0,.04); }
.card-title { font-size:1.5rem; font-weight:700; color:#1e293b; text-align:center; margin-bottom:.35rem; }
.card-subtitle { color:#9ca3af; font-size:.88rem; text-align:center; margin-bottom:1.75rem; }
.register-form { display:flex; flex-direction:column; gap:1.25rem; }
.form-group { display:flex; flex-direction:column; gap:.45rem; }
.form-label { font-size:.85rem; font-weight:600; color:#374151; }
.form-input { padding:.85rem 1.15rem; font-size:.92rem; border:1.5px solid #e2e8f0; border-radius:10px; background:#f8fafc; color:#1e293b; outline:none; transition:all .25s ease; }
.form-input:focus { border-color:#667eea; box-shadow:0 0 0 3px rgba(99,102,241,.1); background:white; }
.error-msg { color:#ef4444; font-size:.85rem; text-align:center; margin:-.25rem 0; }
.submit-btn { width:100%; padding:.85rem; font-size:.95rem; font-weight:600; color:white; background:linear-gradient(135deg,#667eea,#764ba2); border:none; border-radius:10px; cursor:pointer; transition:all .3s cubic-bezier(.4,0,0.2,1); box-shadow:0 4px 14px rgba(99,102,241,.35); }
.submit-btn:hover:not(:disabled) { transform:translateY(-2px); box-shadow:0 8px 24px rgba(99,102,241,.45); }
.submit-btn:disabled { opacity:.55; cursor:not-allowed; }
.switch-text { text-align:center; margin-top:1.25rem; color:#64748b; font-size:.87rem; }
.link-btn { color:#6366f1; font-weight:600; cursor:pointer; transition:all .2s; text-decoration:underline; text-decoration-style:none; }
.link-btn:hover { color:#4f46e5; }
</style>