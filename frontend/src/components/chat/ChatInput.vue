<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const modelValue = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isComposing = ref(false)

const emit = defineEmits<{
  send: [text: string]
}>()

defineProps<{
  disabled?: boolean
}>()

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !isComposing.value) {
    e.preventDefault()
    handleSend()
  }
}

function handleSend() {
  const text = modelValue.value.trim()
  if (!text) return
  emit('send', text)
  modelValue.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}

onMounted(() => {
  textareaRef.value?.focus()
})
</script>

<template>
  <div class="chat-input">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="modelValue"
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        rows="1"
        :disabled="disabled"
        @input="autoResize"
        @keydown="handleKeydown"
        @compositionstart="isComposing = true"
        @compositionend="isComposing = false"
      />
      <el-button
        type="primary"
        :icon="'Promotion'"
        circle
        :disabled="disabled || !modelValue.trim()"
        @click="handleSend"
        class="send-btn"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-input {
  padding: 16px 24px 20px;
  background: #fff;
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: #f5f7fa;
  border-radius: 16px;
  padding: 8px 8px 8px 16px;
  border: 1px solid #dcdfe6;
  transition: border-color 0.2s;

  &:focus-within {
    border-color: #409eff;
  }

  textarea {
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    resize: none;
    font-size: 14px;
    line-height: 1.5;
    color: #303133;
    font-family: inherit;
    max-height: 160px;

    &::placeholder {
      color: #c0c4cc;
    }

    &:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }
  }
}

.send-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
}
</style>
