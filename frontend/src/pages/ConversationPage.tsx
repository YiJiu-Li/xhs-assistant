import { useState, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchSessions,
  createSession,
  fetchHistory,
  deleteSession,
} from '../lib/api'
import type { ChatMessage, ConversationSession } from '../lib/api'
import { useApiConfig } from '../contexts/ApiContext'
import MarkdownMessage from '../components/MarkdownMessage'
import { useLocalStorage } from '../hooks/useLocalStorage'

const QUICK_ACTIONS = [
  '请帮我优化这段文案的开头，让它更吸引眼球',
  '帮我把这段内容改成更接地气的小红书风格',
  '这段文案的结尾能更有号召力吗？',
  '给这段内容加入更多情感共鸣的表达',
  '帮我精简这段文案，保留核心卖点',
  '把这段话改成适合种草笔记的语气',
  '给我 5 个相关话题标签建议',
]

export default function ConversationPage() {
  const { model, temperature } = useApiConfig()
  const qc = useQueryClient()
  const { data: sessions = [] } = useQuery({ queryKey: ['sessions'], queryFn: fetchSessions })

  const [activeId, setActiveId] = useLocalStorage<string | null>('conv:activeId', null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!activeId) return
    fetchHistory(activeId)
      .then(setMessages)
      .catch(() => {
        // 会话已不存在（被删除或后端重启），清除失效 id
        setActiveId(null)
        setMessages([])
      })
  }, [activeId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming])

  async function handleNewSession() {
    const { session_id } = await createSession()
    qc.invalidateQueries({ queryKey: ['sessions'] })
    setActiveId(session_id)
    setMessages([])
  }

  async function handleDelete(id: string) {
    await deleteSession(id)
    qc.invalidateQueries({ queryKey: ['sessions'] })
    if (activeId === id) {
      setActiveId(null)
      setMessages([])
    }
  }

  async function send(text: string) {
    if (!activeId || !text.trim() || streaming) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'human', content: text }])
    setStreaming(true)
    let aiContent = ''
    setMessages((prev) => [...prev, { role: 'ai', content: '' }])

    abortRef.current = new AbortController()
    try {
      const resp = await fetch(`/api/conversation/${activeId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, model, temperature }),
        signal: abortRef.current.signal,
      })
      const reader = resp.body!.getReader()
      const dec = new TextDecoder()
      let buf = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += dec.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const chunk = JSON.parse(line.slice(5).trim())
          if (chunk.type === 'token') {
            aiContent += chunk.content
            setMessages((prev) => {
              const copy = [...prev]
              copy[copy.length - 1] = { role: 'ai', content: aiContent }
              return copy
            })
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'AbortError') {
        setMessages((prev) => {
          const copy = [...prev]
          copy[copy.length - 1] = { role: 'ai', content: `[错误] ${e.message}` }
          return copy
        })
      }
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div className="flex h-full">
      {/* 会话列表 */}
      <aside className="w-52 flex flex-col" style={{ borderRight: '1px solid #ffe0e0', background: '#fff8f7' }}>
        <div className="p-3" style={{ borderBottom: '1px solid #ffe0e0' }}>
          <button
            onClick={handleNewSession}
            className="w-full text-xs font-semibold px-3 py-2 rounded-xl text-white"
            style={{ background: 'linear-gradient(135deg, #ff6b8a 0%, #ff2d55 100%)', boxShadow: '0 3px 8px rgba(255,45,85,0.3)' }}
          >
            + 新建对话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {sessions.map((s: ConversationSession, idx: number) => {
            const label = s.created_at
              ? s.created_at.replace(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$/, '$2/$3 $4:$5')
              : `对话 ${sessions.length - idx}`
            const turns = Math.floor(s.message_count / 2)
            return (
              <div
                key={s.session_id}
                onClick={() => setActiveId(s.session_id)}
                style={activeId === s.session_id ? { background: '#fff0f3', boxShadow: '0 1px 4px rgba(255,45,85,0.1)', border: '1px solid #ffd6d6' } : { border: '1px solid transparent' }}
                className={`group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${
                  activeId === s.session_id
                    ? 'text-[#1a1a1a]'
                    : 'text-[#999] hover:text-[#666]'
                }`}
              >
                <div
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: activeId === s.session_id ? '#ff2d55' : '#ffc0c8' }}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium truncate">{label}</div>
                  <div className="text-[10px] text-zinc-400 mt-0.5">
                    {turns > 0 ? `${turns} 轮对话` : '暂无消息'}
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(s.session_id) }}
                  className="hidden group-hover:flex items-center justify-center w-5 h-5 rounded-md text-zinc-400 hover:text-red-400 hover:bg-red-50 text-xs flex-shrink-0"
                >
                  ✕
                </button>
              </div>
            )
          })}
        </div>
      </aside>

      {/* 聊天区 */}
      <div className="flex-1 flex flex-col" style={{ background: '#fff8f7' }}>
        {!activeId ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-8">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl mb-4" style={{ background: '#fff0f3', boxShadow: '0 4px 14px rgba(255,45,85,0.12)' }}>
              💬
            </div>
            <h3 className="text-base font-semibold text-zinc-700 mb-1">开始对话优化</h3>
            <p className="text-sm text-zinc-400 mb-5">创建一个新对话，让 AI 帮你打磨小红书文案</p>
            <button
              onClick={handleNewSession}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white"
              style={{ background: '#ff2d55', boxShadow: '0 2px 8px rgba(255,45,85,0.2)' }}
            >
              + 新建对话
            </button>
          </div>
        ) : (
          <>
            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4 max-w-3xl w-full mx-auto">
              {messages.map((m, i) => (
                <div key={i} className={`flex items-start gap-2.5 ${m.role === 'human' ? 'flex-row-reverse' : ''}`}>
                  {/* 头像 */}
                  {m.role === 'ai' && (
                    <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5" style={{ background: '#fff0f3', color: '#ff2d55', border: '1px solid #ffd6d6' }}>
                      AI
                    </div>
                  )}
                  {/* 气泡 */}
                  {m.role === 'human' ? (
                    <div className="max-w-[72%] px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed text-white" style={{ background: '#2c2c2e', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
                      {m.content}
                    </div>
                  ) : (
                    <div className="max-w-[82%] px-4 py-3 rounded-2xl rounded-tl-sm bg-white" style={{ border: '1px solid #ffe0e0', color: '#333', boxShadow: '0 1px 6px rgba(255,45,85,0.08)' }}>
                      <MarkdownMessage
                        content={m.content}
                        streaming={streaming && i === messages.length - 1}
                      />
                    </div>
                  )}
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            {/* 快捷操作 */}
            <div className="px-6 pb-2 flex gap-1.5 flex-wrap max-w-3xl w-full mx-auto">
              {QUICK_ACTIONS.slice(0, 4).map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white"
                  style={{ color: '#ff8fa3', border: '1px solid #ffd6d6', boxShadow: '0 1px 3px rgba(255,45,85,0.1)' }}
                >
                  {q.slice(0, 12)}…
                </button>
              ))}
            </div>

            {/* 输入框 */}
            <div className="px-6 pb-5 pt-2 max-w-3xl w-full mx-auto">
              <div className="flex gap-2 bg-white rounded-2xl px-4 py-3" style={{ border: '1px solid #ffd6d6', boxShadow: '0 2px 12px rgba(255,45,85,0.08)' }}>
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      send(input)
                    }
                  }}
                  placeholder="输入消息… (Enter 发送，Shift+Enter 换行)"
                  rows={2}
                  className="flex-1 text-sm resize-none bg-transparent"
                  style={{ color: '#333', outline: 'none', boxShadow: 'none', border: 'none' }}
                />
                <div className="flex flex-col justify-end gap-1">
                  {streaming && (
                    <button
                      onClick={() => abortRef.current?.abort()}
                      className="px-3 py-1.5 text-xs rounded-xl"
                    style={{ background: '#fff0ee', color: '#ff8fa3', border: '1px solid #ffd6d6' }}
                    >
                      ⏹
                    </button>
                  )}
                  <button
                    onClick={() => send(input)}
                    disabled={streaming || !input.trim()}
                    className="px-3 py-1.5 text-xs font-semibold rounded-xl text-white disabled:opacity-40"
                    style={{ background: '#ff2d55', boxShadow: '0 2px 6px rgba(255,45,85,0.2)' }}
                  >
                    发送
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
