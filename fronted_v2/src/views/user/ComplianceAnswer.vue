<template>
  <div class="answer-page">
    <div class="answer-content">
      <button class="back-btn" @click="goBack">
        ← 返回用户中心
      </button>

      <div class="answer-card">
        <h1 class="answer-title">合规审查</h1>
        
        <div class="answer-section">
          <h2 class="answer-label">您的问题：</h2>
          <div class="question-box">{{ question }}</div>
        </div>

        <div class="answer-section">
          <h2 class="answer-label">回答：</h2>
          <div class="answer-box">
            <p>根据您的问题，以下是合规审查分析：</p>
            <p>【合规审查服务】</p>
            <p>1. 我们将根据相关法律法规对您的业务进行全面审查</p>
            <p>2. 重点关注：数据合规、税务合规、劳动法合规、行业特定法规</p>
            <p>3. 建议您上传相关文件，以便我们提供更详细的合规评估</p>
            <p>4. 合规审查可有效降低法律风险，保障企业健康发展</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const question = ref('')

onMounted(() => {
  question.value = route.query.question || '未提供问题'
})

const goBack = () => {
  router.push('/chat/user-center')
}
</script>

<style scoped>
.answer-page {
  padding: 4rem 2rem;
  min-height: calc(100vh);
}

.answer-content {
  max-width: 1000px;
  margin: 0 auto;
}

.back-btn {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: #d4af37;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid #d4af37;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 2rem;
}

.back-btn:hover {
  background: rgba(212, 175, 55, 0.2);
  transform: translateX(-5px);
}

.answer-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 3rem;
}

.answer-title {
  font-size: 3rem;
  font-weight: 800;
  color: #fff;
  text-align: center;
  margin-bottom: 3rem;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.answer-section {
  margin-bottom: 3rem;
}

.answer-label {
  font-size: 1.5rem;
  font-weight: 700;
  color: #d4af37;
  margin-bottom: 1.5rem;
}

.question-box,
.answer-box {
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.95);
  line-height: 2;
  padding: 3rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 20px;
  border-left: 6px solid #d4af37;
  min-height: 300px;
}

.answer-box p {
  margin-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .answer-page {
    padding: 2rem 1rem;
  }

  .answer-card {
    padding: 2rem;
  }

  .answer-title {
    font-size: 2rem;
  }

  .answer-label {
    font-size: 1.2rem;
  }

  .question-box,
  .answer-box {
    font-size: 1.1rem;
    padding: 2rem;
    min-height: 200px;
  }
}
</style>
