import { ref } from 'vue'
import { uploadDocument } from '@/api/document'
import type { IngestResponse } from '@/api/types'

export interface UploadItem {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  result?: IngestResponse
  error?: string
}

export function useUpload() {
  const uploadList = ref<UploadItem[]>([])

  function addToQueue(files: File[]) {
    for (const file of files) {
      uploadList.value.push({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        file,
        progress: 0,
        status: 'pending',
      })
    }
  }

  async function startUpload(item: UploadItem) {
    item.status = 'uploading'
    item.progress = 0

    try {
      const { data } = await uploadDocument(item.file, (percent) => {
        item.progress = percent
        if (percent >= 100) {
          item.status = 'processing'
        }
      })

      item.status = 'completed'
      item.progress = 100
      item.result = data
    } catch (error) {
      item.status = 'failed'
      item.error = (error as Error).message
    }
  }

  async function uploadAll() {
    const pending = uploadList.value.filter((i) => i.status === 'pending')
    await Promise.all(pending.map((item) => startUpload(item)))
  }

  function removeItem(id: string) {
    const idx = uploadList.value.findIndex((i) => i.id === id)
    if (idx !== -1) uploadList.value.splice(idx, 1)
  }

  function clearCompleted() {
    uploadList.value = uploadList.value.filter((i) => i.status !== 'completed')
  }

  return {
    uploadList,
    addToQueue,
    startUpload,
    uploadAll,
    removeItem,
    clearCompleted,
  }
}
