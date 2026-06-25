import api from './index'
import type { IngestResponse } from './types'

export function uploadDocument(file: File, onProgress?: (percent: number) => void) {
  const formData = new FormData()
  formData.append('file', file)

  return api.post<IngestResponse>('/api/v1/documents/ingest/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000,
    onUploadProgress: (e) => {
      if (e.total) {
        const percent = Math.round((e.loaded * 100) / e.total)
        onProgress?.(percent)
      }
    },
  })
}

export function deleteDocument(docId: string) {
  return api.delete('/api/v1/documents/', {
    data: { doc_id: docId },
  })
}
