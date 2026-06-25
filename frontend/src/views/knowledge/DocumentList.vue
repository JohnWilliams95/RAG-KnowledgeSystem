<script setup lang="ts">
import { onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDocumentStore } from '@/stores/document'
import { deleteDocument } from '@/api/document'
import { initKnowledgeBase } from '@/api/knowledgeBase'
import { formatFileSize, formatTime, getStatusType } from '@/utils/format'

const documentStore = useDocumentStore()

onMounted(() => {
  documentStore.refreshAll()
})

async function handleDelete(docId: string, fileName: string) {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${fileName}" 吗？删除后不可恢复。`,
      '确认删除',
      { type: 'warning' },
    )
    await deleteDocument(docId)
    ElMessage.success('删除成功')
    documentStore.refreshAll()
  } catch {
    // cancelled or error
  }
}

async function handleInitKB() {
  try {
    await ElMessageBox.confirm(
      '初始化知识库将创建 Qdrant 向量集合。已有集合不受影响。是否继续？',
      '初始化知识库',
      { type: 'info' },
    )
    await initKnowledgeBase()
    ElMessage.success('知识库初始化成功')
    documentStore.refreshAll()
  } catch {
    // cancelled or error
  }
}

function handleRefresh() {
  documentStore.refreshAll()
  ElMessage.success('已刷新')
}
</script>

<template>
  <div class="document-list">
    <div class="page-header">
      <div class="header-left">
        <h2>知识库文档</h2>
        <p class="subtitle" v-if="documentStore.stats">
          共 {{ documentStore.stats.total_documents }} 个文档，
          {{ documentStore.stats.collection.points_count ?? 0 }} 个向量分块
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="handleRefresh" :loading="documentStore.loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="handleInitKB">
          <el-icon><Setting /></el-icon>
          初始化知识库
        </el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table
        :data="documentStore.documents"
        v-loading="documentStore.loading"
        stripe
        style="width: 100%"
        empty-text="暂无文档，请先上传文档到知识库"
      >
        <el-table-column prop="file_name" label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="file-name-cell">
              <el-icon :size="16"><Document /></el-icon>
              <span>{{ row.file_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="file_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.file_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>

        <el-table-column prop="chunk_count" label="分块数" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.chunk_count }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status === 'completed' ? '完成' : row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="入库时间" width="140">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              text
              size="small"
              @click="handleDelete(row.doc_id, row.file_name)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped lang="scss">
.document-list {
  padding: 24px 32px;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  .header-left {
    h2 {
      font-size: 22px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    .subtitle {
      color: #909399;
      font-size: 14px;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.table-container {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;

  .el-icon {
    color: #909399;
    flex-shrink: 0;
  }

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
