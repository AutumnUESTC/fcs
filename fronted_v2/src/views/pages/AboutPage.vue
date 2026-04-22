<template>
  <div class="about-page">
    <div class="page-content">
      <h1 class="page-title">关于法脉智联</h1>
      <p class="page-description">用科技让法律服务触手可及</p>
      
      <div class="about-sections">
        <div class="about-card">
          <div class="card-icon">🎯</div>
          <h3 class="card-title">我们的使命</h3>
          <p class="card-text">
            法脉智联致力于通过人工智能技术，为用户提供便捷、高效、专业的法律服务。
            我们相信，每个人都应该能够轻松获取法律咨询和支持。
          </p>
        </div>
        
        <div class="about-card">
          <div class="card-icon">🌟</div>
          <h3 class="card-title">核心优势</h3>
          <p class="card-text">
            专业的律师团队、智能的AI系统、覆盖多场景的法律服务，
            让您在任何时间、任何地点都能获得及时的法律帮助。
          </p>
        </div>
        
        <div class="about-card">
          <div class="card-icon">🤝</div>
          <h3 class="card-title">合作网络</h3>
          <p class="card-text">
            与全国多家知名律师事务所建立深度合作，
            确保为用户提供最专业、最可靠的法律服务。
          </p>
        </div>
      </div>
      
      <div class="stats-container">
        <div class="stat-item">
          <div class="stat-number">xx个</div>
          <div class="stat-label">服务场景</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">xx万</div>
          <div class="stat-label">服务用户</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">24/7</div>
          <div class="stat-label">在线支持</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">xx%</div>
          <div class="stat-label">用户满意度</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.about-page {
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
  margin-bottom: 4rem;
}

.about-sections {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-bottom: 4rem;
}

.about-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(91, 58, 140, 0.15);
  border-radius: 16px;
  padding: 2.5rem;
  text-align: left;
  transition: all 0.3s ease;
}

.about-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 40px rgba(59, 31, 110, 0.15);
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(91, 58, 140, 0.3);
}

.card-icon {
  font-size: 3rem;
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #5b3a8c;
  margin-bottom: 1rem;
}

.card-text {
  font-size: 1rem;
  color: #4a3560;
  line-height: 1.8;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  margin-top: 4rem;
}

.stat-item {
  background: rgba(91, 58, 140, 0.08);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(91, 58, 140, 0.2);
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 30px rgba(91, 58, 140, 0.2);
  background: rgba(91, 58, 140, 0.12);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 800;
  color: #5b3a8c;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1rem;
  color: #6b4c8a;
}

@media (max-width: 1024px) {
  .about-sections {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .stats-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .about-page {
    padding: 3rem 1rem;
  }

  .page-title {
    font-size: 2rem;
  }

  .page-description {
    font-size: 1rem;
    margin-bottom: 3rem;
  }

  .about-sections {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .about-card {
    padding: 2rem;
  }

  .stats-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }

  .stat-item {
    padding: 1.5rem;
  }

  .stat-number {
    font-size: 2rem;
  }
}

@media (max-width: 480px) {
  .stats-container {
    grid-template-columns: 1fr;
  }
}
</style>
