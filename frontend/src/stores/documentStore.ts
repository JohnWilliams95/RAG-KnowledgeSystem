import { create } from 'zustand'
import { getDocuments, getKnowledgeBaseStats, deleteDocument, initKnowledgeBase } from '@/api/document'
import type { DocumentInfo, KnowledgeBaseStats } from '@/api/types'

interface DocumentState {
  documents: DocumentInfo[]
  stats: KnowledgeBaseStats | null
  loading: boolean
  total: number
  fetchDocuments: (params?: { limit?: number; offset?: number; status?: string }) => Promise<void>
  fetchStats: () => Promise<void>
  refreshAll: () => Promise<void>
  deleteDocument: (docId: string) => Promise<void>
  initKB: () => Promise<void>
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  stats: null,
  loading: false,
  total: 0,

  fetchDocuments: async (params) => {
    set({ loading: true })
    try {
      const { data } = await getDocuments(params)
      set({ documents: data.documents, total: data.total })
    } finally {
      set({ loading: false })
    }
  },

  fetchStats: async () => {
    try {
      const { data } = await getKnowledgeBaseStats()
      set({ stats: data })
    } catch { /* ignore */ }
  },

  refreshAll: async () => {
    await Promise.all([get().fetchDocuments(), get().fetchStats()])
  },

  deleteDocument: async (docId: string) => {
    await deleteDocument(docId)
    await get().refreshAll()
  },

  initKB: async () => {
    await initKnowledgeBase()
    await get().refreshAll()
  },
}))
