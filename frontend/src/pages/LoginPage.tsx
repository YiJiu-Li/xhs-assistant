import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(username.trim(), password)
      } else {
        await register(username.trim(), password)
      }
    } catch (err: unknown) {
      const data = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
      let msg = ''
      if (typeof data?.detail === 'string') {
        msg = data.detail
      } else if (Array.isArray(data?.detail)) {
        // Pydantic 422 validation errors: [{msg, loc, ...}]
        msg = (data!.detail as { msg: string }[]).map((e) => e.msg).join('；')
      }
      if (mode === 'login') {
        setError(msg || '用户名或密码错误')
      } else {
        setError(msg || '注册失败，请检查输入')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'linear-gradient(135deg, #fff0f3 0%, #fff8f7 100%)' }}
    >
      <div
        className="w-full max-w-sm bg-white rounded-3xl p-8 shadow-xl"
        style={{ border: '1px solid #ffd6d6' }}
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-2">🌸</div>
          <h1 className="text-xl font-bold" style={{ color: '#ff2d55' }}>小红书文案助手</h1>
          <p className="text-xs text-zinc-400 mt-1">登录后使用完整功能</p>
        </div>

        {/* Tab */}
        <div className="flex gap-1 p-1 rounded-xl mb-6" style={{ background: '#fff0f3' }}>
          {(['login', 'register'] as const).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setError('') }}
              className="flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all"
              style={
                mode === m
                  ? { background: '#fff', color: '#ff2d55', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }
                  : { color: '#ff8fa3' }
              }
            >
              {m === 'login' ? '登录' : '注册'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold block mb-1.5" style={{ color: '#ffaab8' }}>用户名</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="2-30 个字符"
              autoComplete="username"
              className="w-full rounded-xl px-4 py-2.5 text-sm"
              style={{ border: '1px solid #ffd6d6', background: '#fff8f7', color: '#333', outline: 'none' }}
            />
          </div>
          <div>
            <label className="text-xs font-semibold block mb-1.5" style={{ color: '#ffaab8' }}>密码</label>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              placeholder="至少 6 位"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              className="w-full rounded-xl px-4 py-2.5 text-sm"
              style={{ border: '1px solid #ffd6d6', background: '#fff8f7', color: '#333', outline: 'none' }}
            />
            {mode === 'register' && password.length > 0 && password.length < 6 && (
              <p className="text-[10px] mt-1" style={{ color: '#ffaab8' }}>密码至少 6 位，还差 {6 - password.length} 位</p>
            )}
          </div>

          {error && (
            <p className="text-xs text-red-500 font-medium">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !username.trim() || password.length < 6}
            className="w-full py-2.5 rounded-xl text-sm font-bold text-white mt-2 disabled:opacity-40 transition-opacity"
            style={{ background: '#ff2d55', boxShadow: '0 4px 12px rgba(255,45,85,0.25)' }}
          >
            {loading ? '请稍候…' : mode === 'login' ? '登录' : '注册并登录'}
          </button>
        </form>

        <p className="text-center text-xs text-zinc-400 mt-5">
          文案改写和批量处理无需登录即可使用
        </p>
      </div>
    </div>
  )
}
