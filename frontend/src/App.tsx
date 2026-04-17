import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import RewritePage from './pages/RewritePage'
import ConversationPage from './pages/ConversationPage'
import BatchPage from './pages/BatchPage'
import KnowledgePage from './pages/KnowledgePage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/rewrite" replace />} />
        <Route path="rewrite" element={<RewritePage />} />
        <Route path="conversation" element={<ConversationPage />} />
        <Route path="batch" element={<BatchPage />} />
        <Route path="knowledge" element={<KnowledgePage />} />
      </Route>
    </Routes>
  )
}
