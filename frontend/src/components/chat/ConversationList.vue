<script setup lang="ts">
import { useChatStore } from '@/stores/chat'
import { formatTime } from '@/utils/format'

const chatStore = useChatStore()

function handleSelect(convId: string) {
  chatStore.switchConversation(convId)
}

function handleDelete(convId: string) {
  chatStore.deleteConversation(convId)
}

function handleNew() {
  chatStore.createConversation()
}
</script>

<template>
  <div class="conversation-list">
    <div class="list-header">
      <span>对话历史</span>
      <el-button text size="small" @click="handleNew">
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>

    <div class="list-body">
      <div
        v-for="conv in chatStore.conversationList"
        :key="conv.id"
        class="conv-item"
        :class="{ active: conv.id === chatStore.currentConversationId }"
        @click="handleSelect(conv.id)"
      >
        <div class="conv-title">{{ conv.title }}</div>
        <div class="conv-meta">
          <span>{{ conv.messages.length }} 条消息</span>
          <span>{{ formatTime(new Date(conv.createdAt).toISOString()) }}</span>
        </div>
        <el-button
          class="delete-btn"
          type="danger"
          text
          size="small"
          @click.stop="handleDelete(conv.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <div v-if="chatStore.conversationList.length === 0" class="empty-tip">
        暂无对话记录
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.conversation-list {
  width: 240px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.list-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conv-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  position: relative;
  transition: background 0.2s;

  &:hover {
    background: #ecf5ff;

    .delete-btn {
      opacity: 1;
    }
  }

  &.active {
    background: #ecf5ff;
    border-left: 3px solid #409eff;
  }
}

.conv-title {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 20px;
}

.conv-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
  color: #909399;
}

.delete-btn {
  position: absolute;
  top: 8px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.empty-tip {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 40px 0;
}
</style>
