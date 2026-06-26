import { useEffect } from 'react'
import { Table, Button, Tag, Space, Typography, message, Popconfirm, Card, Statistic } from 'antd'
import { DeleteOutlined, ReloadOutlined, SettingOutlined, FileOutlined } from '@ant-design/icons'
import { useDocumentStore } from '@/stores/documentStore'
import { formatFileSize, formatTime, getStatusColor, getStatusText } from '@/utils/format'

const { Title, Text } = Typography

export default function DocumentList() {
  const { documents, stats, loading, total, fetchDocuments, refreshAll, deleteDocument, initKB } =
    useDocumentStore()

  useEffect(() => {
    refreshAll()
  }, [])

  const handleDelete = async (docId: string, fileName: string) => {
    try {
      await deleteDocument(docId)
      message.success(`已删除 ${fileName}`)
    } catch {
      message.error('删除失败')
    }
  }

  const handleInitKB = async () => {
    try {
      await initKB()
      message.success('知识库初始化成功')
    } catch {
      message.error('初始化失败')
    }
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      render: (text: string) => (
        <Space>
          <FileOutlined />
          <Text>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 100,
      render: (text: string) => <Tag>{text.toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 100,
      align: 'center' as const,
      render: (count: number) => <Tag>{count}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '入库时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => formatTime(time),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Popconfirm
          title="确定删除此文档？"
          description="删除后不可恢复"
          onConfirm={() => handleDelete(record.doc_id, record.file_name)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="text" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px 32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <Title level={2} style={{ marginBottom: 8 }}>知识库文档</Title>
          <Text type="secondary">
            共 {stats?.total_documents || 0} 个文档，{stats?.collection?.points_count || 0} 个向量分块
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refreshAll()} loading={loading}>
            刷新
          </Button>
          <Button type="primary" icon={<SettingOutlined />} onClick={handleInitKB}>
            初始化知识库
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={documents}
        rowKey="doc_id"
        loading={loading}
        pagination={{ pageSize: 20 }}
        locale={{ emptyText: '暂无文档，请先上传文档到知识库' }}
      />
    </div>
  )
}
