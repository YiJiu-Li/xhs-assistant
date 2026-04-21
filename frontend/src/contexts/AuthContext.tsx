import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api } from '../lib/api'

interface Quota {
  used: number
  limit: number
}

interface User {
  username: string
  token: string
  quota: Quota
}

interface AuthContextValue {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshQuota: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('auth:user')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  // 每次 user 变化时同步 axios Authorization header
  useEffect(() => {
    if (user?.token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${user.token}`
    } else {
      delete api.defaults.headers.common['Authorization']
    }
  }, [user])

  function saveUser(u: User) {
    setUser(u)
    localStorage.setItem('auth:user', JSON.stringify(u))
    api.defaults.headers.common['Authorization'] = `Bearer ${u.token}`
  }

  const refreshQuota = useCallback(async () => {
    if (!user) return
    try {
      const r = await api.get<{ quota: Quota }>('/auth/me')
      setUser((prev) => prev ? { ...prev, quota: r.data.quota } : prev)
      const saved = localStorage.getItem('auth:user')
      if (saved) {
        const parsed = JSON.parse(saved)
        localStorage.setItem('auth:user', JSON.stringify({ ...parsed, quota: r.data.quota }))
      }
    } catch {
      // ignore
    }
  }, [user])

  // 登录后定期刷新配额（每2分钟）
  useEffect(() => {
    if (!user) return
    const id = setInterval(refreshQuota, 2 * 60 * 1000)
    return () => clearInterval(id)
  }, [user, refreshQuota])

  async function login(username: string, password: string) {
    const r = await api.post<{ access_token: string; username: string }>('/auth/login', {
      username,
      password,
    })
    // 获取配额
    api.defaults.headers.common['Authorization'] = `Bearer ${r.data.access_token}`
    const meR = await api.get<{ quota: Quota }>('/auth/me')
    saveUser({ username: r.data.username, token: r.data.access_token, quota: meR.data.quota })
  }

  async function register(username: string, password: string) {
    const r = await api.post<{ access_token: string; username: string }>('/auth/register', {
      username,
      password,
    })
    api.defaults.headers.common['Authorization'] = `Bearer ${r.data.access_token}`
    const meR = await api.get<{ quota: Quota }>('/auth/me')
    saveUser({ username: r.data.username, token: r.data.access_token, quota: meR.data.quota })
  }

  function logout() {
    setUser(null)
    localStorage.removeItem('auth:user')
    delete api.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, refreshQuota }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}