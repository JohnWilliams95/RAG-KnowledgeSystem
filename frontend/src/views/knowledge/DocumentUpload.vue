<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadRawFile } from 'element-plus'
import { useUpload } from '@/composables/useUpload'
import { useDocumentStore } from '@/stores/document'
import { formatFileSize } from '@/utils/format'

const documentStore = useDocumentStore()
const { uploadList, addToQueue, uploadAll, removeItem, clearCompleted } = useUpload()
const isDragover = ref(false)

const acceptTypes = '.pdf,.doc,.docx,.xlsx,.xls,.csv,.pptx,.ppt,.md,.txt,.log,.rst,.html,.htm,.py,.js,.ts,.tsx,.java,.go,.rs,.cpp,.c,.h,.json,.yaml,.yml,.png,.jpg,.jpeg,.bmp,.tiff'

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragover.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length) addToQueue(files)
}

function handleDragover(e: DragEvent) {
  e.preventDefault()
  isDragover.value = true
}

function handleDragleave() {
  isDragover.value = false
}

function handleChange(file: UploadFile) {
  if (file.raw) {
    addToQueue([file.raw])
  }
}

function handleExceed(files: File[]) {
  addToQueue(files)
}

async function handleUploadAll() {
  if (uploadList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  await uploadAll()
  const successCount = uploadList.value.filter((i) => i.status === 'completed').length
  if (successCount > 0) {
    ElMessage.success(`成功上传 ${successCount} 个文件`)
    documentStore.refreshAll()
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return 'CircleCheckFilled'
    case 'failed':
      return 'CircleCloseFilled'
    case 'uploading':
    case 'processing':
      return 'Loading'
    default:
      return 'Clock'
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'completed':
      return '#67c23a'
    case 'failed':
      return '#f56c6c'
    case 'uploading':
    case 'processing':
      return '#409eff'
    default:
      return '#909399'
  }
}
</script>

<template>
  <div class="document-upload">
    <div class="page-header">
      <h2>添加文档</h2>
      <p class="subtitle">支持 PDF、Word、Excel、PPT、Markdown、图片、代码等 35 种格式</p>
    </div>

    <div
      class="upload-area"
      :class="{ dragover: isDragover }"
      @drop="handleDrop"
      @dragover="handleDragover"
      @dragleave="handleDragleave"
    >
      <el-upload
        drag
        :auto-upload="false"
        :accept="acceptTypes"
        :show-file-list="false"
        multiple
        @change="handleChange"
        @exceed="handleExceed"
        class="upload-trigger"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">拖拽文件到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="upload-tip">支持批量上传，单个文件最大 100MB</div>
        </template>
      </el-upload>
    </div>

    <div class="actions" v-if="uploadList.length > 0">
      <el-button type="primary" @click="handleUploadAll" :loading="uploadList.some(i => i.status === 'uploading' || i.status === 'processing')">
        <el-icon><Upload /></el-icon>
        全部上传 ({{ uploadList.length }})
      </el-button>
      <el-button @click="clearCompleted">清除已完成</el-button>
    </div>

    <div class="upload-list" v-if="uploadList.length > 0">
      <div class="upload-item" v-for="item in uploadList" :key="item.id">
        <div class="item-icon">
          <el-icon :size="20" :color="getStatusColor(item.status)">
            <component :is="getStatusIcon(item.status)" />
          </el-icon>
        </div>
        <div class="item-info">
          <div class="item-name">{{ item.file.name }}</div>
          <div class="item-meta">
            <span>{{ formatFileSize(item.file.size) }}</span>
            <span v-if="item.result">
              · {{ item.result.chunks_created }} 个分块
            </span>
          </div>
          <el-progress
            v-if="item.status === 'uploading' || item.status === 'processing'"
            :percentage="item.progress"
            :stroke-width="4"
            :show-text="false"
            class="item-progress"
          />
        </div>
        <div class="item-status">
          <el-tag
            v-if="item.status === 'completed'"
            type="success"
            size="small"
          >
            完成
          </el-tag>
          <el-tag
            v-else-if="item.status === 'failed'"
            type="danger"
            size="small"
          >
            失败
          </el-tag>
          <el-tag
            v-else-if="item.status === 'processing'"
            type="warning"
            size="small"
          >
            处理中...
          </el-tag>
          <el-tag
            v-else-if="item.status === 'uploading'"
            type="info"
            size="small"
          >
            {{ item.progress }}%
          </el-tag>
          <el-tag v-else type="info" size="small">等待中</el-tag>
        </div>
        <div class="item-actions">
          <el-button
            type="danger"
            text
            size="small"
            @click="removeItem(item.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <div class="error-details" v-if="uploadList.some(i => i.status === 'failed')">
      <el-collapse>
        <el-collapse-item title="查看错误详情" name="errors">
          <div v-for="item in uploadList.filter(i => i.status === 'failed')" :key="item.id" class="error-item">
            <strong>{{ item.file.name }}:</strong> {{ item.error }}
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<style scoped lang="scss">
.document-upload {
  padding: 24px 32px;
  max-width: 900px;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 24px;

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

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  transition: all 0.3s;
  background: #fff;

  &:hover,
  &.dragover {
    border-color: #409eff;
    background: #ecf5ff;
  }
}

.upload-trigger {
  width: 100%;

  :deep(.el-upload-dragger) {
    border: none;
    background: transparent;
    padding: 20px;
    width: 100%;
  }
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 16px;
  color: #606266;

  em {
    color: #409eff;
    font-style: normal;
    cursor: pointer;
  }
}

.upload-tip {
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}

.actions {
  margin: 20px 0;
  display: flex;
  gap: 12px;
}

.upload-list {
  margin-top: 16px;
}

.upload-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
}

.item-icon {
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.item-progress {
  margin-top: 8px;
}

.item-status {
  flex-shrink: 0;
}

.item-actions {
  flex-shrink: 0;
}

.error-details {
  margin-top: 16px;

  .error-item {
    padding: 8px 0;
    font-size: 13px;
    color: #606266;
    border-bottom: 1px solid #ebeef5;

    &:last-child {
      border-bottom: none;
    }

    strong {
      color: #303133;
    }
  }
}
</style>
