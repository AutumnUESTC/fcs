<template>
  <div class="home">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-icon">⚖️</span>
          <span class="logo-text">法脉智联</span>
        </div>
        <div class="auth-buttons">
          <button class="btn btn-login" @click="handleLogin">登录</button>
          <button class="btn btn-register" @click="handleRegister">注册</button>
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <main class="main-content">
      <!-- 大标题 -->
      <h1 class="main-title">您的随身法律顾问</h1>

      <!-- 副标题 -->
      <p class="subtitle">
        覆盖农贸、美容、电商、邻里、婚姻等13+场景，智能咨询+专业律师支持
      </p>

      <!-- 搜索框 -->
      <div class="search-box">
        <input
          v-model="searchKeyword"
          type="text"
          class="search-input"
          placeholder="输入法律问题，例如'职业打假怎么应对'"
          @keyup.enter="handleSearch"
        />
        <button class="search-btn" @click="handleSearch">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          搜索
        </button>
      </div>

      <!-- 常见问题卡片 -->
      <section class="section">
        <h2 class="section-title">常见问题</h2>
        <div class="cards-container">
          <div
            v-for="(question, index) in commonQuestions"
            :key="index"
            class="card"
            @click="handleCardClick('常见问题', question)"
          >
            <div class="card-content">
              <span class="card-icon">❓</span>
              <span class="card-text">{{ question }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 基础服务卡片 -->
      <section class="section">
        <h2 class="section-title">基础服务</h2>
        <div class="cards-container">
          <div
            v-for="(service, index) in basicServices"
            :key="index"
            class="card service-card"
            @click="handleCardClick('基础服务', service)"
          >
            <div class="card-content">
              <span class="card-icon">🔧</span>
              <span class="card-text">{{ service }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 场景标签 -->
      <section class="section scenarios-section">
        <div class="scenarios-tags">
          <span
            v-for="(scenario, index) in scenarios"
            :key="index"
            class="scenario-tag"
            @click="handleScenarioClick(scenario)"
          >
            {{ scenario }}
          </span>
        </div>
      </section>
    </main>

    <!-- 底部 -->
    <footer class="footer">
      <p class="footer-text">© 2025 法脉智联 | 合作律所：XX律师事务所 | 客服热线：400-XXX-XXXX</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const searchKeyword = ref('')

// 常见问题
const commonQuestions = ref([
  '农村电商遭遇职业打假怎么办？',
  '美容院预付卡如何合规退款？',
  '邻居装修噪音扰民，如何维权？',
  '境外电商遭遇TRO，账户被冻结怎么办？',
  '校园欺凌学校不管，该找谁？',
  '离婚时宅基地如何分割？'
])

// 基础服务
const basicServices = ref([
  '合同文书生成',
  '合规自查',
  '维权投诉',
  '智能问答',
  '法规查询',
  '律所推荐'
])

// 场景标签
const scenarios = ref([
  '农贸市场',
  '美容院',
  '农村电商',
  '境外电商',
  '婚姻家事',
  '邻里物业',
  '刑事风险',
  '教育权益'
])

// 登录
const handleLogin = () => {
  alert('登录功能开发中...')
}

// 注册
const handleRegister = () => {
  alert('注册功能开发中...')
}

// 搜索
const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    alert(`搜索关键词：${searchKeyword.value}`)
  } else {
    alert('请输入搜索关键词')
  }
}

// 卡片点击
const handleCardClick = (type, name) => {
  alert(`您点击了${type}：${name}`)
}

// 场景标签点击
const handleScenarioClick = (scenario) => {
  console.log('场景：', scenario)
  alert(`场景：${scenario}`)
}
</script>

<style scoped>
.home {
  width: 100%;
  min-height: 100vh;
  position: relative;
  background: linear-gradient(135deg, #0a3d5f 0%, #1a5a7a 50%, #0a3d5f 100%);
}

/* 背景遮罩效果 */
.home::before {
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
.home::after {
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

/* 主体内容 */
.main-content {
  position: relative;
  z-index: 10;
  max-width: 1400px;
  margin: 0 auto;
  padding: 8rem 2rem 4rem;
  min-height: 100vh;
}

.main-title {
  text-align: center;
  font-size: 3.5rem;
  font-weight: 800;
  color: #fff;
  margin-bottom: 1rem;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  line-height: 1.2;
}

.subtitle {
  text-align: center;
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 3rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

/* 搜索框 */
.search-box {
  display: flex;
  gap: 0.5rem;
  max-width: 700px;
  margin: 0 auto 4rem;
  position: relative;
}

.search-input {
  flex: 1;
  padding: 1rem 1.5rem;
  font-size: 1rem;
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: #fff;
  outline: none;
  transition: all 0.3s ease;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.search-input:focus {
  border-color: #d4af37;
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 20px rgba(212, 175, 55, 0.2);
}

.search-btn {
  padding: 0 1.5rem;
  background: linear-gradient(135deg, #d4af37, #f4d03f);
  color: #0a3d5f;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.search-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.5);
}

/* 区块样式 */
.section {
  margin-bottom: 3rem;
}

.section-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: #d4af37;
  margin-bottom: 1.5rem;
  text-align: center;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

/* 卡片容器 */
.cards-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  min-height: 120px;
  display: flex;
  align-items: center;
}

.card:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(212, 175, 55, 0.4);
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  text-align: center;
  width: 100%;
}

.card-icon {
  font-size: 2rem;
}

.card-text {
  font-size: 1rem;
  color: #fff;
  line-height: 1.5;
  font-weight: 500;
}

/* 服务卡片特殊样式 */
.service-card {
  min-height: 140px;
}

.service-card .card-icon {
  font-size: 2.5rem;
}

.service-card .card-text {
  font-size: 1.1rem;
  font-weight: 600;
}

/* 场景标签 */
.scenarios-section {
  margin-top: 3rem;
}

.scenarios-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

.scenario-tag {
  padding: 0.75rem 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 25px;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.scenario-tag:hover {
  background: rgba(212, 175, 55, 0.2);
  border-color: #d4af37;
  transform: scale(1.08);
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
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
  .main-title {
    font-size: 2.8rem;
  }

  .subtitle {
    font-size: 1.1rem;
  }

  .cards-container {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0.75rem 1rem;
  }

  .logo-text {
    font-size: 1.2rem;
  }

  .auth-buttons {
    gap: 0.5rem;
  }

  .btn {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }

  .main-content {
    padding: 7rem 1rem 3rem;
  }

  .main-title {
    font-size: 2rem;
  }

  .subtitle {
    font-size: 1rem;
    margin-bottom: 2rem;
  }

  .search-box {
    flex-direction: column;
    margin-bottom: 3rem;
  }

  .search-btn {
    width: 100%;
    justify-content: center;
    padding: 0.8rem;
  }

  .section-title {
    font-size: 1.5rem;
    margin-bottom: 1rem;
  }

  .cards-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }

  .card {
    padding: 1.25rem;
    min-height: 100px;
  }

  .card-text {
    font-size: 0.9rem;
  }

  .service-card {
    min-height: 110px;
  }

  .scenarios-tags {
    gap: 0.75rem;
  }

  .scenario-tag {
    padding: 0.6rem 1.2rem;
    font-size: 0.9rem;
  }

  .footer-text {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.6rem;
  }

  .subtitle {
    font-size: 0.9rem;
  }

  .cards-container {
    grid-template-columns: 1fr;
  }

  .card {
    min-height: 90px;
  }

  .scenario-tag {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }
}
</style>
