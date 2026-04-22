/**
 * 聊天 API 模块
 * 
 * 连接真实后端 API
 * 
 * ================================================================================
 *                              API 接口文档
 * ================================================================================
 * 
 * 【接口总览】
 * ┌─────────────────────────┬───────┬──────────────────────────────────────────────┐
 * │ 接口                    │ 方法  │ 说明                                         │
 * ├─────────────────────────┼───────┼──────────────────────────────────────────────┤
 * │ sendChatMessage         │ POST │ 发送聊天消息，触发法律分析                     │
 * │ getConversationList     │ GET  │ 获取会话列表                                  │
 * │ getConversationDetail   │ GET  │ 获取会话详情（包含消息）                       │
 * │ saveConversation        │ POST │ 保存会话                                      │
 * └─────────────────────────┴───────┴──────────────────────────────────────────────┘
 * 
 * 【服务 ID 对照】
 * ┌────────────┬─────────────────┬──────┐
 * │ ID         │ 服务名称         │ 图标 │
 * ├────────────┼─────────────────┼──────┤
 * │ contract   │ 合同文书生成     │ 📋   │
 * │ compliance │ 合规自查         │ ✅   │
 * │ complaint  │ 维权投诉         │ 🛡️   │
 * │ qa         │ 智能问答         │ 🤖   │
 * │ laws       │ 法规查询         │ 📚   │
 * │ lawfirm    │ 律所推荐         │ 🏢   │
 * └────────────┴─────────────────┴──────┘
 * 
 * ================================================================================
 *                              请求/响应格式
 * ================================================================================
 * 
 * 【1. sendChatMessage - 发送聊天消息】
 * 
 *   请求参数：
 *     - conversationId: string  // 会话ID
 *     - serviceId: string       // 服务ID
 *     - question: string        // 用户问题
 * 
 *   响应格式：
 *     {
 *       code: 200,
 *       message: 'success',
 *       data: {
 *         answer: string,           // AI 回复内容
 *         conversationId: string,   // 会话ID
 *         status: 'completed' | 'need_info'  // 分析状态
 *       }
 *     }
 * 
 * -------------------------------------------------------------------------------
 * 
 * 【2. getConversationList - 获取会话列表】
 * 
 *   响应格式：
 *     {
 *       code: 200,
 *       message: 'success',
 *       data: [
 *         {
 *           id: number,
 *           conversation_id: string,
 *           service_id: string,
 *           title: string,
 *           created_at: string,
 *           updated_at: string
 *         }
 *       ]
 *     }
 * 
 * -------------------------------------------------------------------------------
 * 
 * 【3. getConversationDetail - 获取会话详情】
 * 
 *   响应格式：
 *     {
 *       code: 200,
 *       message: 'success',
 *       data: {
 *         id: number,
 *         conversation_id: string,
 *         service_id: string,
 *         title: string,
 *         created_at: string,
 *         updated_at: string,
 *         messages: [{ role: string, content: string }]
 *       }
 *     }
 * 
 * ================================================================================
 */

// ============ API 配置 ============

const API_BASE_URL = '/api'

// ============ Token 管理 ============

/**
 * 获取存储的 Token
 */
export const getToken = () => {
  return localStorage.getItem('fcs_token')
}

/**
 * 保存 Token
 */
export const saveToken = (token) => {
  localStorage.setItem('fcs_token', token)
}

/**
 * 清除 Token
 */
export const clearToken = () => {
  localStorage.removeItem('fcs_token')
}

/**
 * 获取当前用户 ID
 */
export const getUserId = () => {
  return localStorage.getItem('fcs_user_id')
}

/**
 * 保存用户信息
 */
export const saveUserInfo = (user) => {
  localStorage.setItem('fcs_user_id', user.id)
  localStorage.setItem('fcs_username', user.username)
  localStorage.setItem('fcs_nickname', user.nickname)
}

/**
 * 清除用户信息
 */
export const clearUserInfo = () => {
  localStorage.removeItem('fcs_user_id')
  localStorage.removeItem('fcs_username')
  localStorage.removeItem('fcs_nickname')
  clearToken()
}

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
 * 发送聊天消息
 * 
 * @param {string} conversationId - 会话ID
 * @param {string} serviceId - 服务ID
 * @param {string} question - 用户问题
 * @returns {Promise<{code: number, message: string, data: {answer: string, conversationId: string}}>}
 */
export const sendChatMessage = async (conversationId, serviceId, question) => {
  try {
    const response = await fetch(`${API_BASE_URL}/messages`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        conversation_id: conversationId,
        content: question,
        role: 'user'
      })
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || '发送消息失败')
    }
    
    return result
  } catch (error) {
    console.error('发送消息失败:', error)
    throw error
  }
}

/**
 * 获取用户历史会话列表
 * @returns {Promise<{code: number, message: string, data: Array}>}
 */
export const getConversationList = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'GET',
      headers: getHeaders()
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || '获取会话列表失败')
    }
    
    return result
  } catch (error) {
    console.error('获取会话列表失败:', error)
    throw error
  }
}

/**
 * 获取会话详情（包含完整消息）
 * @param {string} conversationId - 会话ID
 * @returns {Promise<{code: number, message: string, data: Object}>}
 */
export const getConversationDetail = async (conversationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
      method: 'GET',
      headers: getHeaders()
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || '获取会话详情失败')
    }
    
    return result
  } catch (error) {
    console.error('获取会话详情失败:', error)
    throw error
  }
}

/**
 * 保存会话（创建或更新）
 * @param {string} conversationId - 会话ID
 * @param {string} serviceId - 服务ID
 * @returns {Promise<{code: number, message: string, data: Object}>}
 */
export const saveConversation = async (conversationId, serviceId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        conversation_id: conversationId,
        service_id: serviceId
      })
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || '保存会话失败')
    }
    
    return result
  } catch (error) {
    console.error('保存会话失败:', error)
    throw error
  }
}

/**
 * 重置回复索引（切换服务时调用）
 */
export const resetResponseIndex = () => {
  // 此函数用于兼容旧版模拟数据逻辑，新版不需要
}

/**
 * 获取服务列表（包含 ID、图标、标题等配置）
 * @returns {Array<{id: string, icon: string, title: string, welcome: string, placeholder: string}>}
 */
export const getServiceList = () => [
  {
    id: 'contract',
    icon: '📋',
    title: '合同文书生成',
    welcome: '您好！我是合同文书生成助手。请告诉我您需要的合同类型和具体要求，我将为您生成专业的法律文书。',
    placeholder: '请描述您需要的合同类型...'
  },
  {
    id: 'compliance',
    icon: '✅',
    title: '合规自查',
    welcome: '您好！我是合规审查助手。请告诉我您的企业类型和需要审查的领域，我将为您进行全面的合规风险评估。',
    placeholder: '请描述您的企业情况和审查需求...'
  },
  {
    id: 'complaint',
    icon: '🛡️',
    title: '维权投诉',
    welcome: '您好！我是维权投诉助手。请告诉我您遇到的问题和投诉对象，我将为您提供专业的维权建议和指导。',
    placeholder: '请描述您遇到的问题...'
  },
  {
    id: 'qa',
    icon: '🤖',
    title: '智能问答',
    welcome: '您好！我是法律智能问答助手。请问您有什么法律问题需要咨询？',
    placeholder: '请输入您的法律问题...'
  },
  {
    id: 'laws',
    icon: '📚',
    title: '法规查询',
    welcome: '您好！我是法规查询助手。请告诉我您想查询的法律法规关键词或具体条款。',
    placeholder: '请输入要查询的法规关键词...'
  },
  {
    id: 'lawfirm',
    icon: '🏢',
    title: '律所推荐',
    welcome: '您好！我是律所推荐助手。请告诉我您的法律需求和所在地区，我将为您匹配合适的专业律师。',
    placeholder: '请描述您的法律需求...'
  }
]

/**
 * 删除会话
 * @param {string} conversationId - 会话ID
 * @returns {Promise<{code: number, message: string}>}
 */
export const deleteConversation = async (conversationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || '删除会话失败')
    }
    
    return result
  } catch (error) {
    console.error('删除会话失败:', error)
    throw error
  }
}
