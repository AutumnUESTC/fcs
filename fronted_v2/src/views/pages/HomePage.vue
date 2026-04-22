<template>
  <div class="home-page">
    <div class="hero-content">
      <!-- 大标题区域 -->
      <div class="hero-section">
        <div class="badge">AI 驱动 · 专业可靠</div>
        <h1 class="main-title">
          您的<span class="highlight">智能</span>法律顾问
        </h1>
        <p class="subtitle">覆盖农贸、美容、电商、婚姻等13+场景，智能咨询 + 专业律师支持</p>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <input v-model="searchKeyword" type="text" class="search-input" placeholder="输入法律问题，例如'职业打假怎么应对'" @keyup.enter="handleSearch" />
        <button class="search-btn" @click="handleSearch">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          搜索咨询
        </button>
      </div>

      <!-- 基础服务 -->
      <section class="section services-section">
        <h2 class="section-title"><span class="title-icon">✨</span> 基础服务</h2>
        <div class="service-grid">
          <div v-for="(service, index) in basicServices" :key="index" class="service-tile" @click="handleServiceClick(service)">
            <span class="tile-icon">{{ service.icon }}</span>
            <span class="tile-name">{{ service.name }}</span>
          </div>
        </div>
      </section>

      <!-- 常见问题 -->
      <section class="section questions-section">
        <h2 class="section-title"><span class="title-icon">💡</span> 热门问题</h2>
        <div class="cards-container grid-3">
          <div v-for="(question, index) in commonQuestions" :key="index" class="card question-card" @click="handleCardClick('常见问题', question)">
            <div class="question-number">{{ String(index + 1).padStart(2, '0') }}</div>
            <span class="card-text">{{ question }}</span>
          </div>
        </div>
      </section>

      <!-- 场景标签 -->
      <section class="section scenarios-section">
        <h2 class="section-title"><span class="title-icon">🏷️</span> 场景标签</h2>
        <div class="scenarios-tags">
          <span v-for="(scenario, index) in scenarios" :key="index" class="scenario-tag" @click="handleScenarioClick(scenario)">{{ scenario }}</span>
        </div>
      </section>

      <!-- 底部特性 -->
      <div class="features-bar">
        <div class="feature-item">
          <span class="feature-icon">⚡</span>
          <span>秒级响应</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">🔒</span>
          <span>隐私保护</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">📚</span>
          <span>法规库覆盖</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">💬</span>
          <span>多轮对话</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const searchKeyword = ref('')

// 基础服务
const basicServices = ref([
  { id: 'contract', name: '合同文书生成', icon: '📋' },
  { id: 'compliance', name: '合规自查', icon: '✅' },
  { id: 'complaint', name: '维权投诉', icon: '🛡️' },
  { id: 'qa', name: '智能问答', icon: '🤖' },
  { id: 'laws', name: '法规查询', icon: '📚' },
  { id: 'lawfirm', name: '律所推荐', icon: '🏢' }
])

// 常见问题
const commonQuestions = ref([
  '农村电商遭遇职业打假怎么办？',
  '美容院预付卡如何合规退款？',
  '邻居装修噪音扰民，如何维权？',
  '境外电商遭遇TRO，账户被冻结怎么办？',
  '校园欺凌学校不管，该找谁？',
  '离婚时宅基地如何分割？'
])

// 场景标签
const scenarios = ref(['农贸市场', '美容院', '农村电商', '境外电商', '婚姻家事', '邻里物业', '刑事风险', '教育权益'])

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/chat', query: { question: searchKeyword.value.trim() } })
  } else {
    alert('请输入搜索关键词')
  }
}

const handleCardClick = (type, name) => {
  router.push({ path: '/chat', query: { question: name } })
}

const handleServiceClick = (service) => {
  router.push({ path: '/chat', query: { serviceId: service.id } })
}

const handleScenarioClick = (scenario) => {
  router.push({ path: '/chat', query: { question: scenario + '相关的法律问题' } })
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 50%, #faf5ff 100%);
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 2rem;
}

/* Hero 区域 */
.hero-section {
  text-align: center;
  padding: 3rem 0 2rem;
}

.badge {
  display: inline-block;
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  color: #6366f1;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.45rem 1.25rem;
  border-radius: 50px;
  letter-spacing: 0.5px;
  margin-bottom: 1.25rem;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.12);
}

.main-title {
  font-size: 3rem;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.2;
  margin-bottom: 1rem;
  letter-spacing: -0.5px;
}

.main-title .highlight {
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 1.08rem;
  color: #64748b;
  max-width: 550px;
  margin: 0 auto;
  line-height: 1.65;
}

/* 搜索框 */
.search-box {
  display: flex;
  gap: 0.75rem;
  max-width: 650px;
  margin: 2rem auto 3.5rem;
  position: relative;
}

.search-input {
  flex: 1;
  padding: 1rem 1.5rem;
  font-size: 0.95rem;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  background: white;
  color: #1e293b;
  outline: none;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.search-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1), 0 4px 20px rgba(0, 0, 0, 0.06);
}

.search-input::placeholder { color: #94a3b8; }

.search-btn {
  padding: 0.85rem 1.75rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 14px;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.45);
}

/* 区块 */
.section {
  margin-bottom: 2.5rem;
}

.section-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.title-icon {
  font-size: 1.2rem;
}

/* 卡片容器 */
.cards-container {
  display: grid;
  gap: 1.25rem;
}

.grid-3 { grid-template-columns: repeat(3, 1fr); }

/* 服务方块网格 */
.service-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.service-tile {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 14px;
  padding: 1.5rem 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  text-align: center;
}

.service-tile:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 28px rgba(99, 102, 241, 0.18);
  border-color: rgba(99, 102, 241, 0.2);
}

.tile-icon {
  font-size: 1.8rem;
  line-height: 1;
}

.tile-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: #374151;
  line-height: 1.4;
}

/* 问题卡片 */
.question-card {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 16px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.85rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.question-card:hover {
  transform: translateX(6px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.15);
}

.question-number {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #667eea, #8b5cf6);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  flex-shrink: 0;
}

.card-text {
  font-size: 0.92rem;
  color: #374151;
  line-height: 1.5;
  font-weight: 500;
  flex: 1;
  min-width: 0;
}

.card svg {
  color: #a0aec0;
  opacity: 0.4;
  transition: all 0.3s;
  flex-shrink: 0;
}

.service-card:hover .card svg { 
  opacity: 1; 
  color: #6366f1; 
  transform: translateX(2px);
}
.question-card:hover .card svg { 
  opacity: 1; 
  color: #6366f1; 
}

/* 场景标签 */
.scenarios-section { margin-top: 2.5rem; }

.scenarios-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}

.scenario-tag {
  padding: 0.7rem 1.4rem;
  background: white;
  border: 1.5px solid #e2e8f0;
  border-radius: 50px;
  color: #4b5563;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.scenario-tag:hover {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
}

/* 特性栏 */
.features-bar {
  display: flex;
  justify-content: center;
  gap: 3rem;
  padding: 1.75rem;
  background: rgba(255, 255, 255, 0.55);
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  margin-top: 3rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.87rem;
  font-weight: 500;
}

.feature-icon { font-size: 1.15rem; }

/* 响应式 */
@media (max-width: 1024px) {
  .main-title { font-size: 2.4rem; }
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
  .service-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 768px) {
  .hero-content { padding: 2rem 1rem; }
  .main-title { font-size: 1.9rem; }
  .subtitle { font-size: 0.93rem; }
  .search-box { flex-direction: column; margin: 1.5rem auto 2rem; }
  .search-btn { width: 100%; padding: 0.95rem; justify-content: center; }
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
  .service-grid { grid-template-columns: repeat(2, 1fr); }
  .cards-container { grid-template-columns: repeat(2, 1fr); gap: 1rem; }
  .features-bar { flex-direction: column; align-items: center; gap: 1rem; padding: 1.25rem; }
  .scenarios-tags { gap: 0.6rem; }
  .scenario-tag { font-size: 0.82rem; padding: 0.6rem 1.1rem; }
}

@media (max-width: 480px) {
  .main-title { font-size: 1.6rem; }
  .service-grid { grid-template-columns: repeat(2, 1fr); }
  .cards-container { grid-template-columns: 1fr !important; }
  .grid-3 { grid-template-columns: 1fr !important; }
  .features-bar { gap: 1.5rem; flex-wrap: wrap; }
}
</style>