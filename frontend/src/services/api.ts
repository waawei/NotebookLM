import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 文档相关 API
export const documentApi = {
  // 上传文档
  upload: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 获取文档列表
  list: async () => {
    const response = await api.get('/documents/list')
    return response.data
  },

  // 获取文档详情
  get: async (docId: string) => {
    const response = await api.get(`/documents/${docId}`)
    return response.data
  },

  // 删除文档
  delete: async (docId: string) => {
    const response = await api.delete(`/documents/${docId}`)
    return response.data
  },

  // 获取文档状态
  getStatus: async (docId: string) => {
    const response = await api.get(`/documents/${docId}/status`)
    return response.data
  },
}

// 对话相关 API
export const chatApi = {
  // 提问
  ask: async (data: {
    question: string
    doc_ids?: string[]
    conversation_id?: string
    history?: Array<{ role: string; content: string }>
  }) => {
    const response = await api.post('/chat/ask', data)
    return response.data
  },

  // 获取对话历史
  getConversation: async (conversationId: string) => {
    const response = await api.get(`/chat/conversations/${conversationId}`)
    return response.data
  },

  // 删除对话
  deleteConversation: async (conversationId: string) => {
    const response = await api.delete(`/chat/conversations/${conversationId}`)
    return response.data
  },
}

export default api
