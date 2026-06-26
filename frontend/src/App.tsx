import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ChatPage from './pages/ChatPage'
import DocumentUpload from './pages/DocumentUpload'
import DocumentList from './pages/DocumentList'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/chat" replace />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="knowledge/upload" element={<DocumentUpload />} />
        <Route path="knowledge/documents" element={<DocumentList />} />
      </Route>
    </Routes>
  )
}

export default App
