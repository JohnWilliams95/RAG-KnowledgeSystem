<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import type { Message } from '@/stores/chat'

const props = defineProps<{
  message: Message
}>()

const isUser = computed(() => props.message.role === 'user')
const renderedContent = computed(() => {
  if (isUser.value) return props.message.content
  return renderMarkdown(props.message.content)
})
</script>

<template>
  <div class="chat-message" :class="{ 'is-user': isUser, 'is-assistant': !isUser }">
    <div class="message-avatar">
      <el-avatar :size="36" :style="{ backgroundColor: isUser ? '#409eff' : '#67c23a' }">
        <el-icon v-if="isUser"><User /></el-icon>
        <el-icon v-else><ChatDotRound /></el-icon>
      </el-avatar>
    </div>

    <div class="message-body">
      <div class="message-role">{{ isUser ? '你' : 'AI 助手' }}</div>

      <div class="message-content">
        <div
          v-if="!isUser"
          class="markdown-body"
          v-html="renderedContent"
        />
        <div v-else class="user-text">{{ message.content }}</div>

        <div v-if="message.isStreaming" class="typing-cursor" />
      </div>

      <div v-if="!isUser && message.rewrittenQueries && message.rewrittenQueries.length > 0" class="message-meta">
        <el-collapse>
          <el-collapse-item title="查询重写结果" name="queries">
            <ul class="rewritten-list">
              <li v-for="(q, i) in message.rewrittenQueries" :key="i">{{ q }}</li>
            </ul>
          </el-collapse-item>
        </el-collapse>
      </div>

      <div v-if="!isUser && message.numDocuments" class="message-stats">
        <el-icon><Document /></el-icon>
        <span>引用了 {{ message.numDocuments }} 个文档片段</span>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 0;

  &.is-user {
    flex-direction: row-reverse;

    .message-body {
      align-items: flex-end;
    }

    .message-content {
      background: var(--chat-user-bg);
      border-color: #b3d8ff;
    }

    .message-role {
      text-align: right;
    }
  }

  &.is-assistant {
    .message-content {
      background: var(--chat-ai-bg);
    }
  }
}

.message-avatar {
  flex-shrink: 0;
}

.message-body {
  display: flex;
  flex-direction: column;
  max-width: 75%;
  min-width: 0;
}

.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  word-break: break-word;
  position: relative;
}

.user-text {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #303133;
  margin-left: 2px;
  vertical-align: middle;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.message-meta {
  margin-top: 8px;

  :deep(.el-collapse) {
    border: none;
  }

  :deep(.el-collapse-item__header) {
    font-size: 12px;
    color: #909399;
    height: 28px;
    line-height: 28px;
    background: transparent;
    border: none;
  }

  :deep(.el-collapse-item__wrap) {
    border: none;
    background: transparent;
  }

  :deep(.el-collapse-item__content) {
    padding-bottom: 0;
  }
}

.rewritten-list {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    font-size: 12px;
    color: #606266;
    padding: 2px 0;

    &::before {
      content: '•';
      color: #409eff;
      margin-right: 6px;
    }
  }
}

.message-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
</style>
