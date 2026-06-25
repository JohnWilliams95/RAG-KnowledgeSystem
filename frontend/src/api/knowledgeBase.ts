import api from './index'
import type { DocumentInfo, KnowledgeBaseInfo, KnowledgeBaseStats } from './types'

export function getKnowledgeBaseInfo() {
  return api.get<KnowledgeBaseInfo>('/api/v1/knowledge-base/info')
}

export function getKnowledgeBaseStats() {
  return api.get<KnowledgeBaseStats>('/api/v1/knowledge-base/stats')
}

export function getDocuments(params?: { limit?: number; offset?: number; status?: string }) {
  return api.get<{ documents: DocumentInfo[]; total: number }>(
    '/api/v1/knowledge-base/documents',
    { params },
  )
}

export function getDocumentDetail(docId: string) {
  return api.get<DocumentInfo>(`/api/v1/knowledge-base/documents/${docId}`)
}

export function initKnowledgeBase() {
  return api.post('/api/v1/knowledge-base/init')
}
