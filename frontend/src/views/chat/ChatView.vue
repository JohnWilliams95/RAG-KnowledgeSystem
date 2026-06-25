<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ConversationList from '@/components/chat/ConversationList.vue'
import ChatSettings from '@/components/chat/ChatSettings.vue'

const chatStore = useChatStore()
const messagesRef = ref<HTMLElement | null>(null)
const settingsRef = ref<InstanceType<typeof ChatSettings> | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

watch(
  () => chatStore.currentMessages.length,
  () => scrollToBottom(),
)

watch(
  () => {
    const msgs = chatStore.currentMessages
    return msgs.length > 0 ? msgs[msgs.length - 1]?.content : ''
  },
  () => scrollToBottom(),
)

async function handleSend(text: string) {
  if (!settingsRef.value) return
  const settings = settingsRef.value.getSettings()
  await chatStore.sendMessage(text, settings)
}

function handleNewChat() {
  chatStore.createConversation()
}

function openSettings() {
  settingsRef.value?.open()
}
</script>

<template>
  <div class="chat-view">
    <ConversationList />

    <div class="chat-main">
      <div class="chat-header">
        <div class="header-left">
          <h3>{{ chatStore.currentConversation?.title || '新对话' }}</h3>
        </div>
        <div class="header-right">
          <el-tooltip content="新对话">
            <el-button text @click="handleNewChat">
              <el-icon><Plus /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="清空历史">
            <el-button text @click="chatStore.clearCurrentHistory()" :disabled="chatStore.currentMessages.length === 0">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="设置">
            <el-button text @click="openSettings">
              <el-icon><Setting /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <div class="messages-area" ref="messagesRef">
        <div class="messages-container">
          <template v-if="chatStore.currentMessages.length > 0">
            <ChatMessage
              v-for="msg in chatStore.currentMessages"
              :key="msg.id"
              :message="msg"
            />
          </template>

          <div v-else class="welcome-screen">
            <div class="welcome-icon">
              <el-icon :size="64" color="#409eff"><ChatDotRound /></el-icon>
            </div>
            <h2>RAG 知识库问答</h2>
            <p>基于您的知识库文档，智能回答问题</p>
            <div class="welcome-tips">
              <div class="tip-card" @click="handleSend('介绍一下知识库中的主要内容')">
                <el-icon><Document /></el-icon>
                <span>介绍一下知识库中的主要内容</span>
              </div>
              <div class="tip-card" @click="handleSend('帮我总结一下文档的核心要点')">
                <el-icon><Notebook /></el-icon>
                <span>帮我总结一下文档的核心要点</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ChatInput :disabled="chatStore.isStreaming" @send="handleSend" />
    </div>

    <ChatSettings ref="settingsRef" />
  </div>
</template>

<style scoped lang="scss">
.chat-view {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid var(--border-color);

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }

  .header-right {
    display: flex;
    gap: 4px;
  }
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  background: #fff;
}

.messages-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 24px;
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;

  .welcome-icon {
    margin-bottom: 16px;
  }

  h2 {
    font-size: 24px;
    color: #303133;
    margin-bottom: 8px;
  }

  p {
    color: #909399;
    font-size: 14px;
    margin-bottom: 32px;
  }
}

.welcome-tips {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.tip-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #f5f7fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e4e7ed;

  &:hover {
    background: #ecf5ff;
    border-color: #b3d8ff;
    color: #409eff;
  }

  span {
    font-size: 14px;
    color: #606266;
  }

  &:hover span {
    color: #409eff;
  }
}
</style>
