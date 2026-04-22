<template>
  <div class="user-center">
    <div class="user-content">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="title-icon-wrap">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        </div>
        <h1 class="page-title">用户中心</h1>
        <p class="page-subtitle">管理您的账号信息与安全设置</p>
      </div>

      <!-- 用户信息卡片 -->
      <div class="profile-card">
        <div class="profile-header">
          <div class="avatar-ring">
            <div class="avatar">{{ userInitial }}</div>
            <span class="status-dot"></span>
          </div>
          <div class="profile-info">
            <h2 class="display-name">{{ displayName }}</h2>
            <div class="meta-row">
              <span class="meta-badge free-badge">免费版</span>
              <span class="meta-divider"></span>
              <span class="meta-text online-text">
                <span class="dot-sm"></span>在线
              </span>
            </div>
          </div>
        </div>

        <div class="profile-stats">
          <div class="stat-box">
            <div class="stat-num">{{ stats.conversations }}</div>
            <div class="stat-label">对话</div>
          </div>
          <div class="stat-line"></div>
          <div class="stat-box">
            <div class="stat-num">{{ stats.days }}</div>
            <div class="stat-label">天活跃</div>
          </div>
        </div>
      </div>

      <!-- 功能选项卡 -->
      <div class="tabs-container">
        <button :class="['tab-btn', { active: activeTab === 'profile' }]" @click="activeTab = 'profile'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          账号信息
        </button>
        <button :class="['tab-btn', { active: activeTab === 'password' }]" @click="activeTab = 'password'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          安全设置
        </button>
        <div class="tab-indicator" :style="{ transform: `translateX(${activeTab === 'profile' ? '0' : '100'}%)` }"></div>
      </div>

      <!-- 面板内容 -->
      <transition name="fade" mode="out-in">

        <!-- ===== 账号信息面板 ===== -->
        <div v-if="activeTab === 'profile'" key="profile" class="panel">
          <div class="panel-header-bar">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            编辑个人资料
          </div>

          <div class="form-grid">
            <div class="form-group">
              <label><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>用户名</label>
              <input type="text" v-model="profileForm.username" placeholder="请输入用户名" :disabled="!isEditing" />
            </div>

            <div class="form-group">
              <label><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>邮箱地址</label>
              <input type="email" v-model="profileForm.email" placeholder="请输入邮箱" :disabled="!isEditing" />
            </div>

            <div class="form-group full-width">
              <label><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>手机号码</label>
              <input type="tel" v-model="profileForm.phone" placeholder="请输入手机号" :disabled="!isEditing" />
            </div>
          </div>

          <div class="form-actions">
            <button v-if="!isEditing" class="btn-primary" @click="isEditing = true">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>编辑资料
            </button>
            <template v-else>
              <button class="btn-secondary" @click="cancelEdit">取消</button>
              <button class="btn-primary" @click="saveProfile" :disabled="isSubmitting">
                {{ isSubmitting ? '保存中...' : '保存更改' }}
              </button>
            </template>
          </div>
        </div>

        <!-- ===== 安全设置面板 ===== -->
        <div v-else key="password" class="panel">
          <div class="panel-header-bar security-header">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            修改登录密码
          </div>

          <div class="form-group">
            <label>当前密码</label>
            <div class="pw-input">
              <input :type="showPw.current ? 'text' : 'password'" v-model="pwForm.current" placeholder="请输入当前密码" />
              <button class="pw-toggle" @click="showPw.current = !showPw.current">
                <svg v-if="!showPw.current" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>新密码</label>
            <div class="pw-input">
              <input :type="showPw.new ? 'text' : 'password'" v-model="pwForm.new" placeholder="至少6位字符" />
              <button class="pw-toggle" @click="showPw.new = !showPw.new">
                <svg v-if="!showPw.new" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>确认新密码</label>
            <div class="pw-input">
              <input :type="showPw.confirm ? 'text' : 'password'" v-model="pwForm.confirm" placeholder="再次输入新密码" />
              <button class="pw-toggle" @click="showPw.confirm = !showPw.confirm">
                <svg v-if="!showPw.confirm" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              </button>
            </div>
          </div>

          <!-- 密码强度 -->
          <div class="strength-box" v-if="pwForm.new">
            <div class="strength-top">
              <span>密码强度</span>
              <span :class="['strength-tag', pwStrength.level]">{{ pwStrength.text }}</span>
            </div>
            <div class="strength-track">
              <div class="strength-fill" :style="{ width: pwStrength.percent + '%' }" :class="pwStrength.level"></div>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn-primary security-btn" @click="changePassword" :disabled="isSubmitting">
              <svg v-if="!isSubmitting" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              {{ isSubmitting ? '提交中...' : '更新密码' }}
            </button>
          </div>
        </div>
      </transition>

      <!-- Toast 消息 -->
      <transition name="toast">
        <div v-if="message" :class="['toast', messageType]">
          <svg v-if="messageType === 'success'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          {{ message }}
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

// ========== 动态用户信息 ==========
const storedUsername = ref(localStorage.getItem('fcs_username') || '')
const displayName = computed(() => storedUsername.value || '未登录用户')
const userInitial = computed(() => (storedUsername.value || 'U').charAt(0).toUpperCase())

// 统计数据
const stats = ref({ conversations: 12, days: 30 })

const activeTab = ref('profile')
const isEditing = ref(false)
const isSubmitting = ref(false)

// 消息提示
const message = ref('')
const messageType = ref('success')

// 表单
const profileForm = reactive({ username: storedUsername.value || '', email: '', phone: '' })
const pwForm = reactive({ current: '', new: '', confirm: '' })
const showPw = reactive({ current: false, new: false, confirm: false })

// 密码强度
const pwStrength = computed(() => {
  const p = pwForm.new; if (!p) return { percent: 0, level: '', text: '' }
  let s = 0; if (p.length >= 6) s += 25; if (p.length >= 10) s += 25; if (/[a-z]/.test(p) && /[A-Z]/.test(p)) s += 25; if (/\d/.test(p)) s += 15; if (/[^a-zA-Z0-9]/.test(p)) s += 10
  const l = s >= 75 ? 'strong' : s >= 50 ? 'medium' : 'weak'
  return { percent: Math.min(s, 100), level: l, text: l === 'strong' ? '强' : l === 'medium' ? '中' : '弱' }
})

const showToast = (msg, type = 'success') => {
  message.value = msg; messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

const saveProfile = async () => {
  if (!profileForm.username) { showToast('请填写用户名', 'error'); return }
  isSubmitting.value = true
  try { await new Promise(r => setTimeout(r, 1000)); storedUsername.value = profileForm.username; isEditing.value = false; showToast('资料已更新') }
  catch (e) { showToast('保存失败', 'error') } finally { isSubmitting.value = false }
}

const cancelEdit = () => { profileForm.username = storedUsername.value || ''; profileForm.email = ''; profileForm.phone = ''; isEditing.value = false }

const changePassword = async () => {
  if (!pwForm.current) { showToast('请输入当前密码', 'error'); return }
  if (!pwForm.new) { showToast('请输入新密码', 'error'); return }
  if (pwForm.new.length < 6) { showToast('新密码至少6位', 'error'); return }
  if (pwForm.new !== pwForm.confirm) { showToast('两次密码不一致', 'error'); return }
  if (pwForm.current === pwForm.new) { showToast('新密码不能相同', 'error'); return }
  isSubmitting.value = true
  try { await new Promise(r => setTimeout(r, 1500)); pwForm.current = ''; pwForm.new = ''; pwForm.confirm = ''; showToast('密码已更新') }
  catch (e) { showToast(e.message || '失败', 'error') } finally { isSubmitting.value = false }
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.user-center { padding: 1.75rem; min-height: calc(100vh - 80px); background: linear-gradient(135deg, #f5f7fa 0%, #eef0f4 50%, #f0f4f8 100%); }
.user-content { max-width: 700px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.25rem; }

/* ========== 标题区 ========== */
.page-header { display: flex; align-items: center; gap: 0.85rem; padding-bottom: 0.25rem; }
.title-icon-wrap { width: 44px; height: 44px; border-radius: 14px; background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.08)); display: flex; align-items: center; justify-content: center; color: #667eea; flex-shrink: 0; }
.page-title { font-size: 1.55rem; font-weight: 800; color: #1e293b; letter-spacing: -0.02em; line-height: 1.2; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.page-subtitle { font-size: 0.8rem; color: #94a3b8; margin-top: 1px; }

/* ========== 个人信息卡片 ========== */
.profile-card { background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04), 0 10px 30px -5px rgba(102,126,234,0.08); position: relative; }
.profile-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #667eea, #764ba2, #f093fb); }

.profile-header { display: flex; align-items: center; gap: 1.1rem; padding: 1.75rem 1.5rem 1.25rem; }

.avatar-ring { position: relative; flex-shrink: 0; }
.avatar { width: 68px; height: 68px; border-radius: 18px; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; font-size: 1.9rem; font-weight: 700; color: white; box-shadow: 0 6px 20px rgba(102,126,234,0.35); }
.status-dot { position: absolute; bottom: 2px; right: 2px; width: 14px; height: 14px; border-radius: 50%; background: #10b981; border: 3px solid white; box-shadow: 0 2px 8px rgba(16,185,129,0.35); animation: pulse 2.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.profile-info { flex: 1; min-width: 0; }
.display-name { font-size: 1.2rem; font-weight: 700; color: #1e293b; margin-bottom: 0.3rem; }
.meta-row { display: flex; align-items: center; gap: 0.55rem; flex-wrap: wrap; font-size: 0.78rem; }
.meta-badge { padding: 0.15rem 0.55rem; border-radius: 20px; font-weight: 600; background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.06)); color: #667eea; border: 1px solid rgba(99,102,241,0.15); }
.meta-divider { width: 3px; height: 3px; border-radius: 50%; background: #cbd5e1; }
.online-text { color: #10b981 !important; font-weight: 600; }
.dot-sm { width: 6px; height: 6px; border-radius: 50%; background: #10b981; margin-right: 3px; display: inline-block; }

/* 统计 */
.profile-stats { display: flex; justify-content: center; align-items: center; gap: 2.5rem; padding: 1rem 1.5rem 1.5rem; border-top: 1px solid #f1f5f9; }
.stat-box { text-align: center; }
.stat-num { font-size: 1.5rem; font-weight: 800; color: #667eea; }
.stat-label { font-size: 0.73rem; color: #94a3b8; font-weight: 500; margin-top: 2px; }
.stat-line { width: 1px; height: 28px; background: #e2e8f0; border-radius: 1px; }

/* ========== 标签页 ========== */
.tabs-container { display: flex; position: relative; background: #f1f5f9; border-radius: 14px; padding: 4px; gap: 0; }
.tab-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 0.65rem 1.1rem; border: none; background: transparent; color: #64748b; font-size: 0.88rem; font-weight: 600; border-radius: 10px; cursor: pointer; transition: all 0.3s ease; z-index: 1; position: relative; }
.tab-btn:hover:not(.active) { color: #475569; }
.tab-btn.active { color: #fff; }
.tab-indicator { position: absolute; top: 4px; left: 4px; width: calc(50% - 4px); height: calc(100% - 8px); background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 10px; transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 4px 12px rgba(102,126,234,0.3); }

/* ========== 面板 ========== */
.panel { background: white; border-radius: 20px; padding: 1.65rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04), 0 10px 30px -5px rgba(102,126,234,0.06); }

.panel-header-bar { display: flex; align-items: center; gap: 0.55rem; color: #667eea; font-weight: 600; font-size: 0.9rem; margin-bottom: 1.4rem; padding-bottom: 1rem; border-bottom: 1px solid #f1f5f9; }
.panel-header-bar svg { opacity: 0.8; }
.security-header { color: #10b981; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }
.form-group { margin-bottom: 1.15rem; }
.form-group.full-width { grid-column: 1 / -1; }

.form-group label { display: flex; align-items: center; gap: 0.35rem; color: #475569; font-weight: 600; margin-bottom: 0.5rem; font-size: 0.84rem; }
.form-group label svg { color: #94a3b8; }

.form-group input { width: 100%; padding: 0.7rem 0.95rem; border: 2px solid #e2e8f0; border-radius: 11px; background: #fafbfc; color: #1e293b; font-size: 0.9rem; outline: none; transition: all 0.25s ease; }
.form-group input:focus { border-color: #667eea; background: white; box-shadow: 0 0 0 4px rgba(102,126,234,0.1); }
.form-group input:disabled { background: #f8fafc; color: #94a3b8; cursor: not-allowed; }
.form-group input::placeholder { color: #cbd5e1; }

.pw-input { display: flex; gap: 0; }
.pw-input input { border-top-right-radius: 0 !important; border-bottom-right-radius: 0 !important; }
.pw-toggle { padding: 0 0.85rem; background: #f1f5f9; border: 2px solid #e2e8f0; border-left: none; border-radius: 0 11px 11px 0; color: #64748b; cursor: pointer; transition: all 0.25s; display: flex; align-items: center; justify-content: center; }
.pw-toggle:hover { background: #e2e8f0; color: #667eea; }

/* 密码强度 */
.strength-box { margin-bottom: 1.3rem; padding: 1rem; background: #f8fafc; border-radius: 12px; border: 1px solid #f1f5f9; }
.strength-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; font-size: 0.8rem; }
.strength-top span:first-child { color: #64748b; font-weight: 600; }
.strength-tag { font-weight: 700; font-size: 0.8rem; }
.strength-tag.weak { color: #ef4444; } .strength-tag.medium { color: #f59e0b; } .strength-tag.strong { color: #10b981; }
.strength-track { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 3px; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.strength-fill.weak { background: linear-gradient(90deg, #ef4444, #f87171); }
.strength-fill.medium { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.strength-fill.strong { background: linear-gradient(90deg, #10b981, #34d399); }

/* 按钮 */
.form-actions { display: flex; justify-content: flex-end; gap: 0.65rem; margin-top: 1.5rem; padding-top: 1.1rem; border-top: 1px solid #f1f5f9; }

.btn-primary { display: inline-flex; align-items: center; gap: 0.45rem; padding: 0.65rem 1.6rem; background: linear-gradient(135deg, #667eea, #764ba2); border: none; border-radius: 11px; color: #fff; font-size: 0.88rem; font-weight: 600; cursor: pointer; transition: all 0.3s cubic-bezier(0.4,0,0.2,1); box-shadow: 0 4px 14px rgba(102,126,234,0.35); }
.btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(102,126,234,0.45); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

.btn-secondary { padding: 0.65rem 1.6rem; background: white; border: 2px solid #e2e8f0; border-radius: 11px; color: #64748b; font-size: 0.88rem; font-weight: 600; cursor: pointer; transition: all 0.25s; }
.btn-secondary:hover { border-color: #cbd5e1; background: #f8fafc; color: #475569; }
.security-btn { background: linear-gradient(135deg, #10b981, #059669) !important; box-shadow: 0 4px 14px rgba(16,185,129,0.35) !important; }
.security-btn:hover:not(:disabled) { box-shadow: 0 8px 24px rgba(16,185,129,0.45) !important; }

/* Toast */
.toast { position: fixed; top: 24px; left: 50%; transform: translateX(-50%); padding: 0.8rem 1.6rem; border-radius: 14px; font-weight: 500; font-size: 0.88rem; z-index: 1000; display: flex; align-items: center; gap: 0.55rem; box-shadow: 0 10px 40px rgba(0,0,0,0.12); }
.toast.success { background: linear-gradient(135deg, #10b981, #059669); color: white; }
.toast.error { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }

.fade-enter-active,.fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.fade-enter-from,.fade-leave-to { opacity: 0; transform: translateY(8px); }
.toast-enter-active,.toast-leave-active { transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1); }
.toast-enter-from,.toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(-16px); }

/* 响应式 */
@media (max-width: 768px) {
  .user-center { padding: 1.25rem; }
  .page-title { font-size: 1.3rem; }
  .form-grid { grid-template-columns: 1fr; }
  .form-group.full-width { grid-column: auto; }
  .profile-header { flex-direction: column; text-align: center; align-items: center; gap: 0.85rem; padding: 1.5rem 1.25rem 1rem; }
  .meta-row { justify-content: center; }
  .profile-stats { gap: 1.8rem; }
  .form-actions { flex-direction: column-reverse; }
  .btn-primary, .btn-secondary { width: 100%; justify-content: center; }
}
</style>
