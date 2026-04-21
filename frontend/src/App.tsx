import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import RewritePage from './pages/RewritePage'
import ConversationPage from './pages/ConversationPage'
import BatchPage from './pages/BatchPage'
import KnowledgePage from './pages/KnowledgePage'
import { AuthProvider } from './contexts/AuthContext'
import RequireAuth from './components/RequireAuth'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/rewrite" replace />} />
          {/* 全部需要登录 */}
          <Route path="rewrite" element={<RequireAuth><RewritePage /></RequireAuth>} />
          <Route path="batch" element={<RequireAuth><BatchPage /></RequireAuth>} />
          <Route path="conversation" element={<RequireAuth><ConversationPage /></RequireAuth>} />
          <Route path="knowledge" element={<RequireAuth><KnowledgePage /></RequireAuth>} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
