<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

function handleMenuSelect(index: string) {
  router.push(index)
}

function getActiveMenu(): string {
  return route.path
}
</script>

<template>
  <div class="sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
    <div class="sidebar-header">
      <div class="logo" v-show="!appStore.sidebarCollapsed">
        <el-icon :size="24"><ChatDotRound /></el-icon>
        <span>RAG 知识库</span>
      </div>
      <div class="logo-collapsed" v-show="appStore.sidebarCollapsed">
        <el-icon :size="24"><ChatDotRound /></el-icon>
      </div>
    </div>

    <el-menu
      :default-active="getActiveMenu()"
      :collapse="appStore.sidebarCollapsed"
      class="sidebar-menu"
      background-color="#1d1e1f"
      text-color="#bfcbd9"
      active-text-color="#ffffff"
      @select="handleMenuSelect"
    >
      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>对话</template>
      </el-menu-item>

      <el-sub-menu index="/knowledge">
        <template #title>
          <el-icon><Folder /></el-icon>
          <span>知识库</span>
        </template>
        <el-menu-item index="/knowledge/upload">
          <el-icon><Upload /></el-icon>
          <template #title>添加文档</template>
        </el-menu-item>
        <el-menu-item index="/knowledge/documents">
          <el-icon><Document /></el-icon>
          <template #title>文档列表</template>
        </el-menu-item>
      </el-sub-menu>
    </el-menu>

    <div class="sidebar-footer">
      <el-button
        :icon="appStore.sidebarCollapsed ? 'Expand' : 'Fold'"
        text
        class="collapse-btn"
        @click="appStore.toggleSidebar"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background-color: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;

  &.collapsed {
    width: 64px;
  }
}

.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  border-bottom: 1px solid #2d2e2f;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.logo-collapsed {
  color: #fff;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  overflow-y: auto;

  :deep(.el-menu-item.is-active) {
    background-color: var(--sidebar-active-bg) !important;
  }

  :deep(.el-menu-item:hover) {
    background-color: var(--sidebar-hover-bg) !important;
  }

  :deep(.el-sub-menu__title:hover) {
    background-color: var(--sidebar-hover-bg) !important;
  }
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid #2d2e2f;
  display: flex;
  justify-content: center;
}

.collapse-btn {
  color: var(--sidebar-text) !important;

  &:hover {
    color: #fff !important;
  }
}
</style>
