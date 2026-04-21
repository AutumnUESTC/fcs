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
  color: #fff;
  margin-bottom: 1rem;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.page-description {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 3rem;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 3rem;
}

.service-item {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s ease;
  cursor: pointer;
}

.service-item:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(212, 175, 55, 0.4);
}

.service-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.service-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #d4af37;
  margin-bottom: 0.5rem;
}

.service-desc {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
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
