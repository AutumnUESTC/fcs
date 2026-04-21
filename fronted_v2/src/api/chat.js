/**
 * 聊天 API 模块
 * 
 * 目前为模拟后端，后续替换为真实 API 时只需修改本文件
 * 
 * ================================================================================
 *                              API 接口文档
 * ================================================================================
 * 
 * 【接口总览】
 * ┌─────────────────────────┬───────┬──────────────────────────────────────────────┐
 * │ 接口                    │ 方法  │ 说明                                         │
 * ├─────────────────────────┼───────┼──────────────────────────────────────────────┤
 * │ sendChatMessage         │ POST │ 发送聊天消息                                  │
 * │ getConversationList     │ GET  │ 获取会话列表                                  │
 * │ getConversationDetail    │ GET │ 获取会话详情（包含消息）                       │
 * │ saveConversation         │ POST │ 保存会话（发送消息后自动调用）                  │
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
 *     - timestamp: string       // 时间戳
 * 
 *   响应格式：
 *     {
 *       code: 200,
 *       message: 'success',
 *       data: {
 *         answer: string,           // AI 回复内容
 *         conversationId: string    // 会话ID
 *       }
 *     }
 * 
 * -------------------------------------------------------------------------------
 * 
 * 【2. getConversationList - 获取会话列表】
 * 
 *   请求参数：无
 * 
 *   响应格式：
 *     {
 *       code: 200,
 *       message: 'success',
 *       data: [
 *         {
 *           id: string,
 *           title: string,
 *           serviceId: string,
 *           updatedAt: string
 *         }
 *       ]
 *     }
 * 
 * -------------------------------------------------------------------------------
 * 
 * 【3. getConversationDetail - 获取会话详情】
 * 
 *   请求参数：
 *     - conversationId: string  // 会话ID
 * 
 *   响应格式：
 *     {
 *       code: 200,
 *       message: 'success',
 *       data: {
 *         id: string,
 *         title: string,
 *         serviceId: string,
 *         updatedAt: string,
 *         messages: [{ role: string, content: string }]
 *       }
 *     }
 * 
 * -------------------------------------------------------------------------------
 * 
 * 【4. saveConversation - 保存会话】
 * 
 *   请求参数：
 *     - conversationId: string  // 会话ID
 *     - serviceId: string       // 服务ID
 *     - messages: Array         // 消息列表 [{role, content}]
 * 
 *   响应格式：
 *     {
 *       code: 200,
 *       message: 'success',
 *       data: {
 *         id: string,
 *         title: string,
 *         updatedAt: string
 *       }
 *     }
 * 
 * ================================================================================
 */

// ============ 模拟数据 ============

const mockResponses = {
  contract: [
    '好的，根据您的需求，我可以为您生成一份专业的合同文书。请提供以下信息：\n1. 合同类型（劳动合同/租赁合同/采购合同等）\n2. 双方当事人信息\n3. 主要条款和条件\n4. 特殊约定事项',
    '感谢您的补充信息。我已记录您的要求，正在为您生成合同文本。合同将包含以下章节：\n• 合同双方基本信息\n• 合同标的及范围\n• 权利义务条款\n• 违约责任\n• 争议解决方式',
    '生成的合同草案已完成初版，请您仔细审核以下内容。如有需要修改的地方，请随时告诉我。'
  ],
  compliance: [
    '您好！合规审查可以帮助您识别潜在的法律风险。我将根据您提供的信息进行全面评估。\n\n请告诉我：\n1. 您的企业类型（有限责任公司/合伙企业等）\n2. 主要业务范围\n3. 员工数量\n4. 是否涉及特殊行业许可',
    '根据您的企业情况，我开始进行合规风险评估...\n\n已识别以下潜在风险领域：\n• 劳动人事合规\n• 税务合规\n• 数据安全合规（如适用）\n• 行业特定法规\n\n建议您重点关注以上领域的制度建设。',
    '合规审查报告已完成。建议您按照上述风险等级逐步完善企业合规体系。如需详细的整改方案，请告诉我。'
  ],
  complaint: [
    '您好！遇到纠纷不要慌张，我来帮您分析情况和提供维权建议。\n\n请详细描述您的问题：\n1. 纠纷类型（消费纠纷/合同纠纷/侵权纠纷等）\n2. 对方身份\n3. 纠纷经过\n4. 您掌握的证据',
    '根据您描述的情况，建议您按以下步骤维权：\n\n1️⃣ 证据保全：保留好合同、聊天记录、转账凭证等\n2️⃣ 协商解决：先尝试与对方沟通\n3️⃣ 投诉渠道：可向消费者协会、市场监管部门反映\n4️⃣ 法律途径：必要时通过仲裁或诉讼解决',
    '如果您需要，我可以帮您起草投诉信或法律文书，以便您更好地维护自身权益。请问还有什么需要帮助的吗？'
  ],
  qa: [
    '您好！关于您的法律问题，我来为您解答。请具体描述您的情况，我将根据相关法律法规为您提供专业的法律意见。',
    '根据您描述的情况，我的分析如下：\n\n📌 法律依据：相关法律规定...\n\n📌 风险提示：可能存在的法律风险...\n\n📌 建议措施：\n1. ...\n2. ...\n3. ...\n\n如需更详细的法律建议，建议咨询专业律师。',
    '如果您还有其他法律问题，欢迎继续咨询。我会尽力为您提供有帮助的参考意见。'
  ],
  laws: [
    '您好！我是法规查询助手。请告诉我您想了解哪方面的法律法规：\n\n• 劳动法相关\n• 合同法相关\n• 知识产权相关\n• 税务法规相关\n• 其他特定领域',
    '为您查询到以下相关法律法规：\n\n📖 《中华人民共和国民法典》\n相关条款：第XXX条至第XXX条\n主要内容：...\n\n📖 相关司法解释\n发布时间：...\n适用条件：...\n\n如需了解更详细的条文内容，请告诉我。',
    '以上就是与您查询主题相关的主要法律法规。如需了解具体条款的详细解读，或需要PDF版本的法律文件，请告诉我。'
  ],
  lawfirm: [
    '您好！根据您的法律需求，我可以为您匹配合适的律师事务所和律师。\n\n请告诉我：\n1. 您遇到的法律问题类型\n2. 您的所在地区\n3. 预算范围\n4. 是否需要特定领域的律师（如婚姻家事/刑事辩护/商业诉讼等）',
    '根据您的需求，我为您推荐以下律师：\n\n🏛️ 律师姓名：张律师\n📚 专业领域：劳动纠纷、合同纠纷\n📅 执业年限：12年\n⭐ 用户评分：4.9/5.0\n📍 所在地区：北京\n\n🏛️ 律师姓名：李律师\n📚 专业领域：知识产权、公司法务\n📅 执业年限：8年\n⭐ 用户评分：4.8/5.0\n📍 所在地区：北京\n\n如需了解更多律师信息或预约咨询，请告诉我。',
    '如果您确定了想要的律师，我可以帮您预约在线咨询或线下见面。请问还有其他需要帮助的吗？'
  ]
}

// 回复索引（用于循环）
let responseIndex = 0

// ============ 历史会话模拟数据 ============

const mockConversations = [
  {
    id: 'conv_001',
    title: '劳动合同纠纷咨询',
    serviceId: 'qa',
    updatedAt: '2026-03-31 14:30',
    messages: [
      { role: 'user', content: '公司拖欠工资三个月了，我该怎么办？' },
      { role: 'assistant', content: '您好！根据《劳动合同法》规定，用人单位应当按时足额支付劳动报酬。\n\n建议您按以下步骤处理：\n1️⃣ 收集证据：劳动合同、工资条、考勤记录、公司拖欠工资的书面证明等\n2️⃣ 与公司协商：要求支付拖欠工资\n3️⃣ 向劳动监察部门投诉\n4️⃣ 申请劳动仲裁\n\n请问您有保留相关证据吗？' },
      { role: 'user', content: '有合同和银行转账记录' },
      { role: 'assistant', content: '很好！这些证据非常关键。\n\n📌 银行转账记录可以证明实际发放的工资数额\n📌 劳动合同可以证明劳动关系和约定的工资标准\n\n建议您先向当地劳动监察大队投诉，他们可以帮您协调解决。如果协商不成，再申请劳动仲裁。注意劳动仲裁的时效是一年。' }
    ]
  },
  {
    id: 'conv_002',
    title: '租房合同审核',
    serviceId: 'contract',
    updatedAt: '2026-03-30 09:15',
    messages: [
      { role: 'user', content: '我想签一份租房合同，需要注意什么？' },
      { role: 'assistant', content: '签订租房合同需要注意以下关键条款：\n\n1️⃣ 房屋基本信息：地址、面积、用途\n2️⃣ 租金及支付方式：金额、付款周期、押金数额\n3️⃣ 租赁期限：起止日期、续租条款\n4️⃣ 维修责任：自然损坏vs人为损坏\n5️⃣ 提前解约条款\n6️⃣ 违约金约定\n\n请问您是房东还是租客？我可以帮您生成针对性的合同。' }
    ]
  },
  {
    id: 'conv_003',
    title: '企业合规自查',
    serviceId: 'compliance',
    updatedAt: '2026-03-28 16:45',
    messages: [
      { role: 'user', content: '我们是科技公司，员工50人，需要注意哪些合规问题？' },
      { role: 'assistant', content: '科技公司常见的合规风险领域包括：\n\n🔐 数据安全合规（等保2.0、个人信息保护法）\n• 网络安全等级保护\n• 用户数据收集和存储\n• 隐私政策合规\n\n👥 劳动人事合规\n• 劳动合同签订\n• 社保公积金缴纳\n• 竞业限制协议\n\n💼 知识产权合规\n• 软件著作权保护\n• 源代码保密\n• 专利申请' }
    ]
  }
]

// ============ API 配置 ============

// 设置 API 地址（后续替换为真实后端时修改此处）
const API_BASE_URL = '/api'

// ============ API 方法 ============

/**
 * 发送聊天消息
 * 
 * 流程：
 * 1. 根据 conversationId 查找会话
 * 2. 找不到 → new 一个新对象，存入 id
 * 3. 存入 user message
 * 4. AI 生成 answer
 * 5. 存入 answer
 * 6. 返回 answer
 * 
 * @param {string} conversationId - 会话ID（前端生成或URL获取）
 * @param {string} serviceId - 服务ID
 * @param {string} question - 用户问题
 * @param {string} timestamp - 时间戳
 * @returns {Promise<{code: number, message: string, data: {answer: string, conversationId: string}}> }
 */
export const sendChatMessage = (conversationId, serviceId, question, timestamp) => {
  return new Promise((resolve, reject) => {
    // 模拟网络延迟 1-2 秒
    const delay = 1000 + Math.random() * 1000

    setTimeout(() => {
      try {
        // 1. 根据 conversationId 查找会话
        let conversation = mockConversations.find(c => c.id === conversationId)

        // 2. 找不到 → new 一个新对象，存入 id
        if (!conversation) {
          conversation = {
            id: conversationId,
            title: question.slice(0, 20) + (question.length > 20 ? '...' : ''),
            serviceId: serviceId,
            updatedAt: timestamp,
            messages: []
          }
          mockConversations.push(conversation)
        }

        // 3. 存入 user message
        conversation.messages.push({
          role: 'user',
          content: question
        })

        // 4. AI 生成 answer
        const responses = mockResponses[serviceId] || mockResponses.qa
        const answer = responses[responseIndex % responses.length]
        responseIndex++

        // 5. 存入 answer
        conversation.messages.push({
          role: 'assistant',
          content: answer
        })

        // 更新时间
        conversation.updatedAt = timestamp

        // 6. 返回
        resolve({
          code: 200,
          message: 'success',
          data: {
            answer: answer,
            conversationId: conversationId
          }
        })
      } catch (error) {
        reject(error)
      }
    }, delay)
  })
}

/**
 * 获取用户历史会话列表
 * @returns {Promise<{code: number, message: string, data: Array<{id: string, title: string, serviceId: string, updatedAt: string}>>}
 */
export const getConversationList = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        code: 200,
        message: 'success',
        data: mockConversations.map(conv => ({
          id: conv.id,
          title: conv.title,
          serviceId: conv.serviceId,
          updatedAt: conv.updatedAt
        }))
      })
    }, 500)
  })
}

/**
 * 获取会话详情（包含完整消息）
 * @param {string} conversationId - 会话ID
 * @returns {Promise<{code: number, message: string, data: {id: string, title: string, serviceId: string, updatedAt: string, messages: Array}>}
 */
export const getConversationDetail = (conversationId) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const conversation = mockConversations.find(c => c.id === conversationId)
      if (conversation) {
        resolve({
          code: 200,
          message: 'success',
          data: conversation
        })
      } else {
        reject(new Error('会话不存在'))
      }
    }, 300)
  })
}

/**
 * 保存会话（发送消息后自动调用）
 * @param {string} conversationId - 会话ID
 * @param {string} serviceId - 服务ID
 * @param {Array} messages - 消息列表
 * @returns {Promise<{code: number, message: string, data: {id: string, title: string, updatedAt: string}}> }
 */
export const saveConversation = (conversationId, serviceId, messages) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      // 生成会话标题：取第一条用户消息的前20个字符
      const firstUserMessage = messages.find(m => m.role === 'user')
      const conversationTitle = firstUserMessage
        ? firstUserMessage.content.slice(0, 20) + (firstUserMessage.content.length > 20 ? '...' : '')
        : '新对话'

      const updatedAt = new Date().toLocaleString('zh-CN')

      // 查找并更新会话，如果没有则创建
      let conversation = mockConversations.find(c => c.id === conversationId)
      if (conversation) {
        // 找到 → 更新
        conversation.messages = messages
        conversation.title = conversationTitle
        conversation.updatedAt = updatedAt
      } else {
        // 找不到 → new 一个新对象
        conversation = {
          id: conversationId,
          title: conversationTitle,
          serviceId: serviceId,
          updatedAt: updatedAt,
          messages: messages
        }
        mockConversations.push(conversation)
      }

      resolve({
        code: 200,
        message: 'success',
        data: {
          id: conversation.id,
          title: conversation.title,
          updatedAt: conversation.updatedAt
        }
      })
    }, 100)
  })
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
 * 重置回复索引（切换服务时调用）
 */
export const resetResponseIndex = () => {
  responseIndex = 0
}

// ============ 真实后端替换示例 ============

/**
 * 真实后端调用示例（替换 sendChatMessage 时参考）
 * 
 * export const sendChatMessage = async (conversationId, serviceId, question, timestamp) => {
 *   const response = await fetch(`${API_BASE_URL}/chat`, {
 *     method: 'POST',
 *     headers: {
 *       'Content-Type': 'application/json'
 *     },
 *     body: JSON.stringify({ conversationId, serviceId, question, timestamp })
 *   })
 *   return response.json()
 * }
 */
