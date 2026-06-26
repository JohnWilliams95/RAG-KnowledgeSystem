import { create } from 'zustand'
import { streamChat, clearHistory } from '@/api/chat'
import type { ChatRequest, ChatStreamEvent } from '@/api/types'

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

interface ChatState {
  conversations: Map<string, Conversation>
  currentConversationId: string
  isStreaming: boolean
  currentConversation: () => Conversation | undefined
  currentMessages: () => Message[]
  conversationList: () => Conversation[]
  createConversation: () => string
  switchConversation: (id: string) => void
  deleteConversation: (id: string) => void
  sendMessage: (question: string, options?: Partial<ChatRequest>) => Promise<void>
  clearCurrentHistory: () => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: new Map(),
  currentConversationId: '',
  isStreaming: false,

  currentConversation: () => {
    const { conversations, currentConversationId } = get()
    return currentConversationId ? conversations.get(currentConversationId) : undefined
  },

  currentMessages: () => {
    return get().currentConversation()?.messages || []
  },

  conversationList: () => {
    return Array.from(get().conversations.values()).sort((a, b) => b.createdAt - a.createdAt)
  },

  createConversation: () => {
    const id = crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    const conv: Conversation = {
      id,
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
    }
    set((state) => {
      const newConvs = new Map(state.conversations)
      newConvs.set(id, conv)
      return { conversations: newConvs, currentConversationId: id }
    })
    return id
  },

  switchConversation: (id: string) => {
    if (get().conversations.has(id)) {
      set({ currentConversationId: id })
    }
  },

  deleteConversation: (convId: string) => {
    set((state) => {
      const newConvs = new Map(state.conversations)
      newConvs.delete(convId)
      const remaining = Array.from(newConvs.keys())
      return {
        conversations: newConvs,
        currentConversationId: state.currentConversationId === convId
          ? remaining[0] || ''
          : state.currentConversationId,
      }
    })
  },

  sendMessage: async (question: string, options?: Partial<ChatRequest>) => {
    const state = get()
    let convId = state.currentConversationId
    if (!convId || !state.conversations.has(convId)) {
      convId = get().createConversation()
    }

    // Update title if first message
    const conv = get().conversations.get(convId)!
    if (conv.title === '新对话') {
      conv.title = question.slice(0, 30) + (question.length > 30 ? '...' : '')
    }

    const userMsg: Message = {
      id: crypto.randomUUID?.() || `${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: Date.now(),
    }

    const aiMsg: Message = {
      id: crypto.randomUUID?.() || `${Date.now() + 1}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    }

    conv.messages.push(userMsg, aiMsg)
    set((state) => {
      const newConvs = new Map(state.conversations)
      newConvs.set(convId, { ...conv })
      return { conversations: newConvs, isStreaming: true }
    })

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
      (event: ChatStreamEvent) => {
        if (event.event_type === 'token' || event.event_type === 'chunk') {
          aiMsg.content += event.data
          set((state) => {
            const newConvs = new Map(state.conversations)
            const c = newConvs.get(convId)
            if (c) newConvs.set(convId, { ...c, messages: [...c.messages] })
            return { conversations: newConvs }
          })
        } else if (event.event_type === 'rewritten_queries') {
          try {
            aiMsg.rewrittenQueries = JSON.parse(event.data)
          } catch { /* ignore */ }
        } else if (event.event_type === 'metadata') {
          try {
            const meta = JSON.parse(event.data)
            aiMsg.numDocuments = meta.num_documents
          } catch { /* ignore */ }
        }
      },
      () => {
        aiMsg.isStreaming = false
        set({ isStreaming: false })
      },
      (error: Error) => {
        aiMsg.content += `\n\n[错误: ${error.message}]`
        aiMsg.isStreaming = false
        set({ isStreaming: false })
      },
    )
  },

  clearCurrentHistory: async () => {
    const { currentConversationId, conversations } = get()
    if (!currentConversationId) return
    const conv = conversations.get(currentConversationId)
    if (conv) {
      conv.messages = []
      set((state) => {
        const newConvs = new Map(state.conversations)
        newConvs.set(currentConversationId, { ...conv })
        return { conversations: newConvs }
      })
      try {
        await clearHistory(currentConversationId)
      } catch { /* ignore */ }
    }
  },
}))
