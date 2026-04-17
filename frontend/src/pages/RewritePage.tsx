import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchTemplates, api } from '../lib/api'
import { useApiConfig } from '../contexts/ApiContext'
import MarkdownMessage from '../components/MarkdownMessage'

export default function RewritePage() {
  const { model, temperature } = useApiConfig()
  const { data: templates = [] } = useQuery({ queryKey: ['templates'], queryFn: fetchTemplates })

  const [content, setContent] = useState('')
  const [style, setStyle] = useState('')
  const [useRag, setUseRag] = useState(false)
  const [output, setOutput] = useState('')
  const [hashtags, setHashtags] = useState<string[]>([])
  const [streaming, setStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  async function handleStream() {
    if (!content.trim()) return
    setOutput('')
    setHashtags([])
    setStreaming(true)

    abortRef.current = new AbortController()
    try {
      const resp = await fetch('/api/rewrite/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, style: style || undefined, model, temperature, use_rag: useRag }),
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
          if (chunk.type === 'token') setOutput((p) => p + chunk.content)
          else if (chunk.type === 'done') break
          else if (chunk.type === 'error') setOutput((p) => p + `\n[错误] ${chunk.content}`)
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'AbortError') setOutput((p) => p + `\n[连接错误] ${e.message}`)
    } finally {
      setStreaming(false)
    }
  }

  async function handleHashtags() {
    if (!content.trim()) return
    try {
      const r = await api.post<{ hashtags: string[] }>('/rewrite/hashtags', {
        content: output || content, model,
      })
      setHashtags(r.data.hashtags)
    } catch {
      setHashtags(['获取标签失败'])
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      {/* 页面标题 */}
      <div className="mb-7">
        <h1 className="text-2xl font-bold text-zinc-800 tracking-tight">文案改写</h1>
        <p className="text-sm text-zinc-400 mt-1">输入原始文案，选择风格，AI 帮你改写成爆款小红书内容</p>
      </div>

      {/* 输入卡片 */}
      <div className="bg-white rounded-2xl p-5 mb-4" style={{ border: '1px solid #ffe0e0', boxShadow: '0 2px 12px rgba(255,45,85,0.06)' }}>
        {/* 风格选择 */}
        <div className="mb-4">
          <p className="text-xs font-semibold mb-2.5" style={{ color: '#ffaab8' }}>✦ 写作风格</p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setStyle('')}
              className="px-3.5 py-1.5 rounded-full text-xs font-medium transition-all"
              style={style === '' ? { background: 'linear-gradient(135deg, #ff6b8a 0%, #ff2d55 100%)', color: '#fff', boxShadow: '0 2px 8px rgba(255,45,85,0.3)', border: '1px solid transparent' } : { background: '#fff8f7', color: '#ff8fa3', border: '1px solid #ffd6d6' }}
            >
              ✨ 自动
            </button>
            {templates.map((t) => (
              <button
                key={t.id}
                onClick={() => setStyle(t.id)}
                title={t.desc}
                className="px-3.5 py-1.5 rounded-full text-xs font-medium transition-all"
                style={style === t.id ? { background: 'linear-gradient(135deg, #ff6b8a 0%, #ff2d55 100%)', color: '#fff', boxShadow: '0 2px 8px rgba(255,45,85,0.3)', border: '1px solid transparent' } : { background: '#fff8f7', color: '#ff8fa3', border: '1px solid #ffd6d6' }}
              >
                {t.icon} {t.id}
              </button>
            ))}
          </div>
        </div>

        {/* 输入区 */}
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="粘贴你的原始文案内容…"
          rows={6}
          className="w-full rounded-xl px-4 py-3 text-sm leading-relaxed resize-y"
          style={{ border: '1px solid #ffd6d6', background: '#fff8f7', color: '#333', outline: 'none' }}
        />

        {/* 操作栏 */}
        <div className="flex items-center gap-4 mt-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer select-none" style={{ color: '#999' }}>
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
              className="accent-rose-500 w-3.5 h-3.5"
            />
            参考知识库
          </label>
          <div className="flex-1" />
          {streaming && (
            <button
              onClick={() => abortRef.current?.abort()}
              className="px-4 py-2 rounded-xl text-sm"
              style={{ background: '#fff0ee', color: '#ff8fa3', border: '1px solid #ffd6d6' }}
            >
              ⏹ 停止
            </button>
          )}
          <button
            onClick={handleStream}
            disabled={streaming || !content.trim()}
            className="px-5 py-2 rounded-xl text-sm font-semibold text-white disabled:opacity-40"
            style={{ background: 'linear-gradient(135deg, #ff6b8a 0%, #ff2d55 100%)', boxShadow: '0 3px 10px rgba(255,45,85,0.35)' }}
          >
            {streaming ? '生成中…' : '开始改写 →'}
          </button>
        </div>
      </div>

      {/* 输出卡片 */}
      {(output || streaming) && (
        <div className="bg-white rounded-2xl overflow-hidden" style={{ border: '1px solid #ffe0e0', boxShadow: '0 2px 12px rgba(255,45,85,0.06)' }}>
          {/* 卡片头 */}
          <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: '1px solid #ffe4e4', background: '#fff8f7' }}>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full" style={{ background: '#ff2d55' }} />
              <span className="text-xs font-semibold" style={{ color: '#ff8fa3' }}>改写结果</span>
              {streaming && (
                <span className="text-[10px] animate-pulse" style={{ color: '#ffaab8' }}>生成中…</span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleHashtags}
                className="text-xs font-medium" style={{ color: '#ff2d55' }}
              >
                # 生成标签
              </button>
              <div className="w-px h-3 bg-zinc-200" />
              <button
                onClick={() => navigator.clipboard.writeText(output)}
                className="text-xs text-zinc-400 hover:text-zinc-600 font-medium"
              >
                复制
              </button>
            </div>
          </div>
          {/* 内容 */}
          <div className="px-5 py-4 text-sm text-zinc-700 leading-7">
            <MarkdownMessage content={output} streaming={streaming} />
          </div>
          {/* 标签 */}
          {hashtags.length > 0 && (
            <div className="px-5 py-3 flex flex-wrap gap-1.5" style={{ borderTop: '1px solid #ffe4e4', background: '#fff8f7' }}>
              {hashtags.map((tag) => (
                <span key={tag} className="text-xs px-2.5 py-1 rounded-full font-medium" style={{ background: '#fff0f3', color: '#ff2d55', border: '1px solid #ffd6d6' }}>
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
