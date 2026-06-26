import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu } from 'antd'
import { useAppStore } from '@/stores/appStore'

const { Sider, Content } = AntLayout

const menuItems = [
  {
    key: '/chat',
    icon: <span>💬</span>,
    label: '对话',
  },
  {
    key: '/knowledge',
    icon: <span>📁</span>,
    label: '知识库',
    children: [
      {
        key: '/knowledge/upload',
        icon: <span>📤</span>,
        label: '添加文档',
      },
      {
        key: '/knowledge/documents',
        icon: <span>📄</span>,
        label: '文档列表',
      },
    ],
  },
]

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { sidebarCollapsed, toggleSidebar } = useAppStore()

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={sidebarCollapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          background: '#001529',
        }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: sidebarCollapsed ? 16 : 18,
          fontWeight: 600,
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          {sidebarCollapsed ? 'RAG' : 'RAG 知识库'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          defaultOpenKeys={['/knowledge']}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout style={{ marginLeft: sidebarCollapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Content style={{ overflow: 'auto' }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
