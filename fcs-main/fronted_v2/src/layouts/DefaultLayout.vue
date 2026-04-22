<template>
  <div class="default-layout">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-content">
        <div class="logo" @click="navigateTo('/')">
          <span class="logo-icon">⚖️</span>
          <span class="logo-text">法脉智联</span>
        </div>

        <nav class="nav-menu" v-if="showNav">
          <router-link to="/" class="nav-link" exact-active-class="active">首页</router-link>
          <router-link to="/services" class="nav-link">服务</router-link>
          <router-link to="/about" class="nav-link">关于</router-link>
        </nav>

        <div class="auth-buttons">
          <button class="btn btn-register" @click="navigateTo('/register')">注册</button>
          <button class="btn btn-login" @click="navigateTo('/login')">登录</button>
        </div>

        <button class="mobile-menu-btn" @click="showNav = !showNav" v-if="!showNav">☰</button>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="main-container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showNav = ref(true)

const navigateTo = (path) => {
  router.push(path)
}
</script>

<style scoped>
.default-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef0ff 50%, #faf5ff 100%);
}

.header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.9rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  transition: transform 0.25s ease;
}

.logo:hover { transform: scale(1.03); }

.logo-icon { font-size: 1.7rem; }

.logo-text {
  font-size: 1.3rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 导航菜单 */
.nav-menu { display: flex; gap: 0.25rem; align-items: center; }
.nav-link {
  color: #4b5563;
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 500;
  transition: all 0.25s ease;
  padding: 0.55rem 1.05rem;
  border-radius: 10px;
}

.nav-link:hover { color: #6366f1; background: rgba(99, 102, 241, 0.08); }
.nav-link.active { color: white; background: linear-gradient(135deg, #667eea, #764ba2); }

.auth-buttons { display: flex; gap: 0.75rem; }
.btn { padding: 0.55rem 1.35rem; border-radius: 10px; font-size: .88rem; font-weight:600; cursor: pointer; transition: all .25s ease; border: 1.5px solid transparent; }
.btn-login { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-color: transparent; }
.btn-login:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35); }
.btn-register { background: white; color: #6366f1; border-color: rgba(99, 102, 241, 0.3); }
.btn-register:hover { background: rgba(99, 102, 241, 0.06); transform: translateY(-1px); }
.mobile-menu-btn { display: none; background:none; border:none; font-size:1.4rem; color:#374151; cursor:pointer; padding:.3rem; }

.main-container { flex: 1; margin-top: 70px; position: relative; z-index: 10; }

@media (max-width: 768px) {
  .header-content { padding: .75rem 1rem; }
  .logo-text { font-size: 1.15rem; }
  .logo-icon { font-size: 1.45rem; }
  .nav-menu { display: none; position: absolute; top: 100%; left: 0; right: 0; background: white; border-radius: 0 12px 12px; padding: .5rem; box-shadow: 0 8px 30px rgba(0,0,0,.12); border: 1px solid rgba(0,0,0,.06); z-index: 1001; flex-direction: column; }
  .nav-link { padding:.65rem 1rem; text-align:center; }
  .mobile-menu-btn { display: block; position:absolute; right:1rem; top: .85rem; }
  .auth-buttons { gap: .5rem; }
  .btn { padding: .45rem 1rem; font-size: .82rem; }
}
</style>