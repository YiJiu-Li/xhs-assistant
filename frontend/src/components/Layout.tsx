import { NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchModels } from '../lib/api'
import { useApiConfig } from '../contexts/ApiContext'

const FALLBACK_MODELS = [
  'gpt-5.4', 'gpt-5.3-codex', 'gpt-5.2-codex',
  'gpt-5.3-codex-spark', 'gpt-5.1-codex-mini', 'codex-mini-latest',
]

const navItems = [
  { to: '/rewrite',      icon: '✍️', label: '文案改写',  desc: '智能风格改写' },
  { to: '/conversation', icon: '💬', label: '对话优化',  desc: '多轮对话打磨' },
  { to: '/batch',        icon: '⚡', label: '批量处理',  desc: '批量生成文案' },
  { to: '/knowledge',   icon: '📚', label: '知识库',    desc: '参考案例管理' },
]

export default function Layout() {
  const { model, temperature, setModel, setTemperature } = useApiConfig()
  const { data: remoteModels = [] } = useQuery({ queryKey: ['models'], queryFn: fetchModels })
  const modelIds = remoteModels.length > 0
    ? remoteModels.map((m) => m.id)
    : FALLBACK_MODELS

  return (
    <div className="flex h-screen" style={{ background: '#fff8f7' }}>
      {/* 侧边栏 — 国内风格：暖白色 */}
      <aside className="w-60 flex flex-col select-none border-r" style={{ background: '#fff', borderColor: '#ffe4e4' }}>

        {/* Logo */}
        <div className="px-5 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-2xl flex items-center justify-center text-white text-base font-bold"
              style={{ background: 'linear-gradient(135deg, #ff6b8a 0%, #ff2d55 100%)', boxShadow: '0 4px 12px rgba(255,45,85,0.35)' }}
            >
              小
            </div>
            <div>
              <div className="font-bold text-sm leading-tight" style={{ color: '#1a1a1a' }}>小红书助手</div>
              <div className="text-[10px] mt-0.5" style={{ color: '#ff8fa3' }}>AI 文案创作工具</div>
            </div>
          </div>
        </div>

        {/* 分割线 */}
        <div className="mx-4 border-t" style={{ borderColor: '#ffe4e4' }} />

        {/* 导航 */}
        <nav className="flex-1 px-3 py-3 space-y-0.5">
          {navItems.map(({ to, icon, label, desc }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive ? '' : ''
                }`
              }
              style={({ isActive }) => isActive
                ? { background: 'linear-gradient(90deg, #fff0f3 0%, #fff8fa 100%)', color: '#ff2d55', borderLeft: '3px solid #ff2d55' }
                : { color: '#666', borderLeft: '3px solid transparent' }
              }
            >
              {({ isActive }) => (
                <>
                  <span className="text-base w-5 text-center">{icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="leading-tight">{label}</div>
                    {isActive && (
                      <div className="text-[10px] mt-0.5 font-normal" style={{ color: '#ff8fa3' }}>{desc}</div>
                    )}
                  </div>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* 底部设置 */}
        <div className="px-4 py-4 space-y-4" style={{ borderTop: '1px solid #ffe4e4' }}>
          <div>
            <label className="text-xs font-medium block mb-1.5" style={{ color: '#999' }}>模型选择</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full text-xs rounded-xl px-2.5 py-2 cursor-pointer"
              style={{ color: '#333', background: '#fff5f5', border: '1px solid #ffd6d6', outline: 'none' }}
            >
              {modelIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium" style={{ color: '#999' }}>创意度</label>
              <span className="text-xs font-mono" style={{ color: '#ff2d55' }}>{temperature.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-[9px] mt-1" style={{ color: '#ccc' }}>
              <span>严谨</span>
              <span>创意</span>
            </div>
          </div>
        </div>

      </aside>

      {/* 主内容 */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
