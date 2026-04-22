<template>
  <div class="services-page">
    <div class="page-content">
      <h1 class="page-title">我们的服务</h1>
      <p class="page-description">为您提供全方位的法律支持服务</p>
      
      <div class="services-grid">
        <div class="service-item">
          <div class="service-icon">📋</div>
          <h3 class="service-name">合同文书生成</h3>
          <p class="service-desc">智能生成各类合同和法律文书</p>
        </div>
        <div class="service-item">
          <div class="service-icon">✅</div>
          <h3 class="service-name">合规自查</h3>
          <p class="service-desc">企业合规风险快速检测</p>
        </div>
        <div class="service-item">
          <div class="service-icon">🛡️</div>
          <h3 class="service-name">维权投诉</h3>
          <p class="service-desc">协助处理各类维权投诉</p>
        </div>
        <div class="service-item">
          <div class="service-icon">🤖</div>
          <h3 class="service-name">智能问答</h3>
          <p class="service-desc">7x24小时法律智能咨询</p>
        </div>
        <div class="service-item">
          <div class="service-icon">📚</div>
          <h3 class="service-name">法规查询</h3>
          <p class="service-desc">全面法律法规数据库</p>
        </div>
        <div class="service-item">
          <div class="service-icon">🏢</div>
          <h3 class="service-name">律所推荐</h3>
          <p class="service-desc">匹配专业律师提供服务</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.services-page {
  padding: 4rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-content {
  text-align: center;
}

.page-title {
  font-size: 3rem;
  font-weight: 800;
  color: #3b1f6e;
  margin-bottom: 1rem;
}

.page-description {
  font-size: 1.2rem;
  color: #5b3a8c;
  margin-bottom: 3rem;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 3rem;
}

.service-item {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(91, 58, 140, 0.15);
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s ease;
  cursor: pointer;
}

.service-item:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 40px rgba(59, 31, 110, 0.15);
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(91, 58, 140, 0.3);
}

.service-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.service-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #5b3a8c;
  margin-bottom: 0.5rem;
}

.service-desc {
  font-size: 1rem;
  color: #4a3560;
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .services-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .services-page {
    padding: 3rem 1rem;
  }

  .page-title {
    font-size: 2rem;
  }

  .page-description {
    font-size: 1rem;
  }

  .services-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .service-item {
    padding: 1.5rem;
  }
}
</style>
