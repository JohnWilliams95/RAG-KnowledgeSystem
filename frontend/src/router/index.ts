import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      children: [
        {
          path: 'chat',
          name: 'chat',
          component: () => import('@/views/chat/ChatView.vue'),
          meta: { title: '对话' },
        },
        {
          path: 'knowledge/upload',
          name: 'document-upload',
          component: () => import('@/views/knowledge/DocumentUpload.vue'),
          meta: { title: '添加文档' },
        },
        {
          path: 'knowledge/documents',
          name: 'document-list',
          component: () => import('@/views/knowledge/DocumentList.vue'),
          meta: { title: '知识库列表' },
        },
      ],
    },
  ],
})

export default router
