import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import LoginPage from '../pages/LoginPage'

/** 需要登录才能访问的路由守卫 */
export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  if (!user) return <LoginPage />
  return <>{children}</>
}
