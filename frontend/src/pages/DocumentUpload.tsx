import { useState } from 'react'
import { Upload, Button, List, Progress, Typography, message, Space } from 'antd'
import { InboxOutlined, DeleteOutlined, CloudUploadOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { uploadDocument } from '@/api/document'
import { formatFileSize } from '@/utils/format'
import { useDocumentStore } from '@/stores/documentStore'

const { Title, Text } = Typography

interface UploadItem {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  result?: any
  error?: string
}

export default function DocumentUpload() {
  const [uploadList, setUploadList] = useState<UploadItem[]>([])
  const { refreshAll } = useDocumentStore()

  const addToQueue = (files: File[]) => {
    console.log('[DocumentUpload] addToQueue called with', files.length, 'files')
    const newItems: UploadItem[] = files.map((file) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      file,
      progress: 0,
      status: 'pending',
    }))
    setUploadList((prev) => {
      const updated = [...prev, ...newItems]
      console.log('[DocumentUpload] uploadList updated, total items:', updated.length)
      return updated
    })
  }

  const startUpload = async (item: UploadItem) => {
    console.log('[DocumentUpload] startUpload called for:', item.file.name)
    setUploadList((prev) =>
      prev.map((i) => (i.id === item.id ? { ...i, status: 'uploading' as const, progress: 0 } : i))
    )

    try {
      console.log('[DocumentUpload] Calling uploadDocument API...')
      const { data } = await uploadDocument(item.file, (percent) => {
        console.log('[DocumentUpload] Upload progress:', percent)
        setUploadList((prev) =>
          prev.map((i) =>
            i.id === item.id
              ? { ...i, progress: percent, status: percent >= 100 ? ('processing' as const) : i.status }
              : i
          )
        )
      })

      console.log('[DocumentUpload] Upload completed:', data)
      setUploadList((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, status: 'completed' as const, progress: 100, result: data } : i))
      )
      message.success(`${item.file.name} 上传成功`)
      refreshAll()
    } catch (error: any) {
      console.error('[DocumentUpload] Upload failed:', error)
      setUploadList((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, status: 'failed' as const, error: error.message } : i))
      )
      message.error(`${item.file.name} 上传失败: ${error.message}`)
    }
  }

  const uploadAll = async () => {
    console.log('[DocumentUpload] uploadAll called')
    const pending = uploadList.filter((i) => i.status === 'pending')
    console.log('[DocumentUpload] Pending items:', pending.length)
    await Promise.all(pending.map((item) => startUpload(item)))
  }

  const removeItem = (id: string) => {
    setUploadList((prev) => prev.filter((i) => i.id !== id))
  }

  const clearCompleted = () => {
    setUploadList((prev) => prev.filter((i) => i.status !== 'completed'))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#52c41a'
      case 'failed': return '#ff4d4f'
      case 'uploading':
      case 'processing': return '#1677ff'
      default: return '#999'
    }
  }

  const getStatusText = (item: UploadItem) => {
    switch (item.status) {
      case 'pending': return '等待中'
      case 'uploading': return `${item.progress}%`
      case 'processing': return '处理中...'
      case 'completed': return `完成 (${item.result?.chunks_created || 0} 个分块)`
      case 'failed': return `失败: ${item.error}`
      default: return ''
    }
  }

  return (
    <div style={{ padding: '24px 32px', maxWidth: 900 }}>
      <Title level={2}>添加文档</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        支持 PDF、Word、Excel、PPT、Markdown、图片、代码等 35 种格式
      </Text>

      <Upload.Dragger
        multiple
        showUploadList={false}
        beforeUpload={(file) => {
          addToQueue([file])
          return false
        }}
        style={{ marginBottom: 24 }}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">拖拽文件到此处，或点击选择</p>
        <p className="ant-upload-hint">支持批量上传</p>
      </Upload.Dragger>

      {uploadList.length > 0 && (
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<CloudUploadOutlined />}
            onClick={uploadAll}
            loading={uploadList.some((i) => i.status === 'uploading' || i.status === 'processing')}
          >
            全部上传 ({uploadList.filter((i) => i.status === 'pending').length})
          </Button>
          <Button onClick={clearCompleted}>清除已完成</Button>
        </Space>
      )}

      <List
        dataSource={uploadList}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => removeItem(item.id)}
              />,
            ]}
          >
            <List.Item.Meta
              title={item.file.name}
              description={
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text type="secondary">{formatFileSize(item.file.size)}</Text>
                  {(item.status === 'uploading' || item.status === 'processing') && (
                    <Progress percent={item.progress} size="small" status="active" />
                  )}
                  <Text style={{ color: getStatusColor(item.status) }}>
                    {getStatusText(item)}
                  </Text>
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </div>
  )
}
