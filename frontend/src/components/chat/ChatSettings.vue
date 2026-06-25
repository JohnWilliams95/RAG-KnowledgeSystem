<script setup lang="ts">
import { ref } from 'vue'

const visible = ref(false)

const promptStyle = ref<'concise' | 'detailed' | 'academic'>('detailed')
const enableQueryRewriting = ref(true)
const enableReranking = ref(true)
const enableHyde = ref(true)
const enableStepback = ref(false)
const enableDecomposition = ref(false)

function open() {
  visible.value = true
}

function getSettings() {
  return {
    prompt_style: promptStyle.value,
    enable_query_rewriting: enableQueryRewriting.value,
    enable_reranking: enableReranking.value,
    enable_hyde: enableHyde.value,
    enable_stepback: enableStepback.value,
    enable_decomposition: enableDecomposition.value,
  }
}

defineExpose({ open, getSettings })
</script>

<template>
  <el-drawer v-model="visible" title="对话设置" direction="rtl" size="320px">
    <el-form label-position="top">
      <el-form-item label="回答风格">
        <el-radio-group v-model="promptStyle">
          <el-radio-button value="concise">简洁</el-radio-button>
          <el-radio-button value="detailed">详细</el-radio-button>
          <el-radio-button value="academic">学术</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-divider />

      <el-form-item label="查询重写">
        <el-switch v-model="enableQueryRewriting" />
        <div class="setting-desc">多角度改写查询，提高召回率</div>
      </el-form-item>

      <el-form-item label="重排序">
        <el-switch v-model="enableReranking" />
        <div class="setting-desc">Cross-Encoder 精排，提高准确率</div>
      </el-form-item>

      <el-form-item label="HyDE">
        <el-switch v-model="enableHyde" />
        <div class="setting-desc">生成假设文档嵌入，提高检索精度</div>
      </el-form-item>

      <el-form-item label="Step-Back">
        <el-switch v-model="enableStepback" />
        <div class="setting-desc">回溯到更抽象的背景问题</div>
      </el-form-item>

      <el-form-item label="问题分解">
        <el-switch v-model="enableDecomposition" />
        <div class="setting-desc">将复杂问题分解为子问题</div>
      </el-form-item>
    </el-form>
  </el-drawer>
</template>

<style scoped lang="scss">
.setting-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-radio-group) {
  width: 100%;

  .el-radio-button {
    flex: 1;

    :deep(.el-radio-button__inner) {
      width: 100%;
    }
  }
}
</style>
