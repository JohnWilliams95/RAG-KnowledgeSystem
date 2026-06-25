import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DocumentInfo, KnowledgeBaseStats } from '@/api/types'
import * as kbApi from '@/api/knowledgeBase'

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<DocumentInfo[]>([])
  const stats = ref<KnowledgeBaseStats | null>(null)
  const loading = ref(false)
  const total = ref(0)

  async function fetchDocuments(params?: { limit?: number; offset?: number; status?: string }) {
    loading.value = true
    try {
      const { data } = await kbApi.getDocuments(params)
      documents.value = data.documents
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      const { data } = await kbApi.getKnowledgeBaseStats()
      stats.value = data
    } catch {
      // ignore
    }
  }

  async function refreshAll() {
    await Promise.all([fetchDocuments(), fetchStats()])
  }

  return { documents, stats, loading, total, fetchDocuments, fetchStats, refreshAll }
})
