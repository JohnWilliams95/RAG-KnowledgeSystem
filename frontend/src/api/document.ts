import api from './client'
import type { IngestResponse, DocumentInfo, KnowledgeBaseStats } from './types'

export function uploadDocument(file: File, onProgress?: (percent: number) => void) {
  console.log('[API] uploadDocument called for file:', file.name, 'size:', file.size)
  const formData = new FormData()
  formData.append('file', file)

  return api.post<IngestResponse>('/api/v1/documents/ingest/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000,
    onUploadProgress: (e) => {
      if (e.total) {
        const percent = Math.round((e.loaded * 100) / e.total)
        console.log('[API] upload progress:', percent)
        onProgress?.(percent)
      }
    },
  })
}

export function deleteDocument(docId: string) {
  console.log('[API] deleteDocument called for:', docId)
  return api.delete('/api/v1/documents/', {
    data: { doc_id: docId },
  })
}

export function getDocuments(params?: { limit?: number; offset?: number; status?: string }) {
  console.log('[API] getDocuments called with params:', params)
  return api.get<{ documents: DocumentInfo[]; total: number }>(
    '/api/v1/knowledge-base/documents',
    { params },
  )
}

export function getKnowledgeBaseStats() {
  console.log('[API] getKnowledgeBaseStats called')
  return api.get<KnowledgeBaseStats>('/api/v1/knowledge-base/stats')
}

export function initKnowledgeBase() {
  console.log('[API] initKnowledgeBase called')
  return api.post('/api/v1/knowledge-base/init')
}
