<template>
  <div class="default-layout">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-content">
        <div class="logo" @click="navigateToHome">
          <span class="logo-icon">⚖️</span>
          <span class="logo-text">智法精灵</span>
        </div>
        <nav class="nav-menu">
          <router-link to="/" class="nav-link" exact-active-class="active">首页</router-link>
          <router-link to="/services" class="nav-link" exact-active-class="active">服务</router-link>
          <router-link to="/about" class="nav-link" exact-active-class="active">关于</router-link>
        </nav>
        <div class="auth-buttons">
          <button class="btn btn-login" @click="handleLogin">登录</button>
        </div>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="main-container">
      <router-view />
    </main>

    <!-- 底部 -->
    <footer class="footer">
      <p class="footer-text">{{ $t('footer.text') }}</p>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

// 点击Logo跳转到首页
const navigateToHome = () => {
  router.push('/')
}

// 登录
const handleLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.default-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #0a3d5f 0%, #1a5a7a 50%, #0a3d5f 100%);
  position: relative;
}

/* 背景遮罩效果 */
.default-layout::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 0;
}

/* 抽象背景图案 */
.default-layout::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(212, 175, 55, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(212, 175, 55, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.03) 0%, transparent 30%);
  z-index: 0;
  pointer-events: none;
}

/* 顶部导航栏 */
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(10, 61, 95, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.logo:hover {
  transform: scale(1.05);
}

.logo-icon {
  font-size: 2rem;
  filter: drop-shadow(0 0 10px rgba(212, 175, 55, 0.5));
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #d4af37, #f4d03f);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  position: relative;
}

.nav-link:hover {
  color: #d4af37;
  background: rgba(212, 175, 55, 0.1);
}

.nav-link.active {
  color: #d4af37;
  background: rgba(212, 175, 55, 0.2);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 2px;
  background: linear-gradient(90deg, #d4af37, #f4d03f);
  border-radius: 2px;
}

.auth-buttons {
  display: flex;
  gap: 1rem;
}

.btn {
  padding: 0.6rem 1.5rem;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.btn-login {
  background: rgba(212, 175, 55, 0.2);
  color: #d4af37;
  border-color: #d4af37;
}

.btn-login:hover {
  background: rgba(212, 175, 55, 0.3);
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
}

.btn-register {
  background: linear-gradient(135deg, #d4af37, #f4d03f);
  color: #0a3d5f;
}

.btn-register:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.5);
}

/* 主内容容器 */
.main-container {
  position: relative;
  z-index: 10;
  flex: 1;
  margin-top: 80px;
}

/* 底部 */
.footer {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 2rem;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .nav-menu {
    gap: 1.5rem;
  }

  .nav-link {
    font-size: 0.95rem;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0.75rem 1rem;
  }

  .logo-text {
    font-size: 1.2rem;
  }

  .logo-icon {
    font-size: 1.6rem;
  }

  .nav-menu {
    display: none;
  }

  .auth-buttons {
    gap: 0.5rem;
  }

  .btn {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }

  .main-container {
    margin-top: 70px;
  }

  .footer-text {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 0.6rem 0.75rem;
  }

  .logo-text {
    font-size: 1rem;
  }

  .logo-icon {
    font-size: 1.4rem;
  }

  .btn {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
  }
}
</style>
