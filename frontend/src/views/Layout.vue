<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'
</script>

<template>
  <div class="layout">
    <Sidebar />
    <div class="layout-main">
      <router-view />
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.layout-main {
  flex: 1;
  overflow: hidden;
  background-color: var(--bg-color);
}
</style>
