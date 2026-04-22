/**
 * 用户 API 模块
 * 
 * 连接真实后端 API
 */

import { saveToken, saveUserInfo, clearUserInfo, getToken } from './chat.js'

// ============ API 配置 ============

const API_BASE_URL = '/api'

/**
 * 获取请求头
 */
const getHeaders = () => {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json'
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

// ============ API 方法 ============

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} nickname - 昵称
 * @returns {Promise<{code: number, message: string, data: {id: number, username: string, nickname: string}}>}
 */
export const register = async (username, password, nickname) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, nickname })
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || result.detail || '注册失败')
    }
    
    return result
  } catch (error) {
    console.error('注册失败:', error)
    throw error
  }
}

/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<{code: number, message: string, data: {token: string, user: {id: number, username: string, nickname: string}}}>}
 */
export const login = async (username, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || result.detail || '登录失败')
    }
    
    // 保存登录信息
    if (result.data && result.data.token) {
      saveToken(result.data.token)
      saveUserInfo(result.data.user)
    }
    
    return result
  } catch (error) {
    console.error('登录失败:', error)
    throw error
  }
}

/**
 * 获取当前用户信息
 * @returns {Promise<{code: number, message: string, data: {id: number, username: string, nickname: string}}>}
 */
export const getCurrentUser = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: getHeaders()
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || '获取用户信息失败')
    }
    
    return result
  } catch (error) {
    console.error('获取用户信息失败:', error)
    throw error
  }
}

/**
 * 登出
 */
export const logout = () => {
  clearUserInfo()
}

/**
 * 检查是否已登录
 * @returns {boolean}
 */
export const isLoggedIn = () => {
  return !!getToken()
}
