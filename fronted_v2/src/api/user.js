/**
 * 用户 API 模块
 *
 * 目前为模拟后端，后续替换为真实 API 时只需修改本文件
 */

// ============ API 配置 ============
const API_BASE_URL = '/api'

// ============ API 方法 ============

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} nickname - 昵称
 * @returns {Promise<{code: number, message: string, data: {id: string, username: string, nickname: string}}> }
 *
 * ---- 真实后端写法（替换下方函数体即可） ----
 * export const register = async (username, password, nickname) => {
 *   const response = await fetch(`${API_BASE_URL}/register`, {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json' },
 *     body: JSON.stringify({ username, password, nickname })
 *   })
 *   const result = await response.json()
 *   if (result.code !== 200) throw result
 *   return result
 * }
 * -------------------------------------------
 */
export const register = (username, password, nickname) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: '注册成功',
        data: {
          id: `user_${Date.now()}`,
          username: username,
          nickname: nickname || username
        }
      })
    }, 800)
  })
}

/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<{code: number, message: string, data: {token: string, user: {id: string, username: string, nickname: string}}}>}
 *
 * ---- 真实后端写法（替换下方函数体即可） ----
 * export const login = async (username, password) => {
 *   const response = await fetch(`${API_BASE_URL}/login`, {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json' },
 *     body: JSON.stringify({ username, password })
 *   })
 *   const result = await response.json()
 *   if (result.code !== 200) throw result
 *   return result
 * }
 * -------------------------------------------
 */
export const login = (username, password) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: '登录成功',
        data: {
          token: `token_${Date.now()}`,
          user: {
            id: 'user_001',
            username: username,
            nickname: username
          }
        }
      })
    }, 800)
  })
}
