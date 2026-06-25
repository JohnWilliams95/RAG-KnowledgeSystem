import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generateId } from '@/utils/format'
import { sendChat, streamChat, clearHistory } from '@/api/chat'
import type { ChatRequest } from '@/api/types'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  rewrittenQueries?: string[]
  numDocuments?: number
  isStreaming?: boolean
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Map<string, Conversation>>(new Map())
  const currentConversationId = ref<string>('')
  const isStreaming = ref(false)

  const currentConversation = computed(() =>
    currentConversationId.value ? conversations.value.get(currentConversationId.value) : undefined,
  )

  const currentMessages = computed(() => currentConversation.value?.messages || [])

  const conversationList = computed(() =>
    Array.from(conversations.value.values()).sort((a, b) => b.createdAt - a.createdAt),
  )

  function createConversation(): string {
    const id = generateId()
    const conv: Conversation = {
      id,
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
    }
    conversations.value.set(id, conv)
    currentConversationId.value = id
    return id
  }

  function ensureConversation(): string {
    if (!currentConversationId.value || !conversations.value.has(currentConversationId.value)) {
      return createConversation()
    }
    return currentConversationId.value
  }

  function updateConversationTitle(convId: string, firstQuestion: string) {
    const conv = conversations.value.get(convId)
    if (conv && conv.title === '新对话') {
      conv.title = firstQuestion.slice(0, 30) + (firstQuestion.length > 30 ? '...' : '')
    }
  }

  async function sendMessage(
    question: string,
    options?: Partial<Omit<ChatRequest, 'question'>>,
  ) {
    const convId = ensureConversation()
    updateConversationTitle(convId, question)

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: Date.now(),
    }

    const conv = conversations.value.get(convId)!
    conv.messages.push(userMsg)

    const aiMsg: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    }
    conv.messages.push(aiMsg)

    isStreaming.value = true

    const requestData: ChatRequest = {
      question,
      conversation_id: convId,
      enable_query_rewriting: true,
      enable_reranking: true,
      prompt_style: 'detailed',
      ...options,
    }

    await streamChat(
      requestData,
      (event) => {
        if (event.event_type === 'token' || event.event_type === 'chunk') {
          aiMsg.content += event.data
        } else if (event.event_type === 'rewritten_queries') {
          try {
            aiMsg.rewrittenQueries = JSON.parse(event.data)
          } catch {
            // ignore
          }
        } else if (event.event_type === 'metadata') {
          try {
            const meta = JSON.parse(event.data)
            aiMsg.numDocuments = meta.num_documents
          } catch {
            // ignore
          }
        } else {
          aiMsg.content += event.data
        }
      },
      () => {
        aiMsg.isStreaming = false
        isStreaming.value = false
      },
      (error) => {
        aiMsg.content += `\n\n[错误: ${error.message}]`
        aiMsg.isStreaming = false
        isStreaming.value = false
      },
    )
  }

  async function sendMessageSync(question: string, options?: Partial<Omit<ChatRequest, 'question'>>) {
    const convId = ensureConversation()
    updateConversationTitle(convId, question)

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: Date.now(),
    }

    const conv = conversations.value.get(convId)!
    conv.messages.push(userMsg)

    isStreaming.value = true

    try {
      const requestData: ChatRequest = {
        question,
        conversation_id: convId,
        enable_query_rewriting: true,
        enable_reranking: true,
        prompt_style: 'detailed',
        ...options,
      }

      const { data } = await sendChat(requestData)

      const aiMsg: Message = {
        id: generateId(),
        role: 'assistant',
        content: data.answer,
        timestamp: Date.now(),
        rewrittenQueries: data.rewritten_queries,
        numDocuments: data.num_documents,
      }
      conv.messages.push(aiMsg)
    } catch (error) {
      const errMsg: Message = {
        id: generateId(),
        role: 'assistant',
        content: `[请求失败: ${(error as Error).message}]`,
        timestamp: Date.now(),
      }
      conv.messages.push(errMsg)
    } finally {
      isStreaming.value = false
    }
  }

  async function clearCurrentHistory() {
    if (!currentConversationId.value) return
    const conv = conversations.value.get(currentConversationId.value)
    if (conv) {
      conv.messages = []
      try {
        await clearHistory(currentConversationId.value)
      } catch {
        // ignore
      }
    }
  }

  function deleteConversation(convId: string) {
    conversations.value.delete(convId)
    if (currentConversationId.value === convId) {
      const remaining = Array.from(conversations.value.keys())
      currentConversationId.value = remaining[0] || ''
    }
  }

  function switchConversation(convId: string) {
    if (conversations.value.has(convId)) {
      currentConversationId.value = convId
    }
  }

  return {
    conversations,
    currentConversationId,
    currentConversation,
    currentMessages,
    conversationList,
    isStreaming,
    createConversation,
    sendMessage,
    sendMessageSync,
    clearCurrentHistory,
    deleteConversation,
    switchConversation,
  }
})
