import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchKBStats, fetchKBDocs, api } from '../lib/api'
import type { KBDocument } from '../lib/api'

type Tab = 'stats' | 'add' | 'search' | 'manage'

export default function KnowledgePage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('stats')

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['kb-stats'],
    queryFn: fetchKBStats,
  })
  const { data: docs = [], refetch: refetchDocs } = useQuery({
    queryKey: ['kb-docs'],
    queryFn: fetchKBDocs,
    enabled: tab === 'manage',
  })

  // Add tab
  const [addContent, setAddContent] = useState('')
  const [addMeta, setAddMeta] = useState('')
  const [addMsg, setAddMsg] = useState('')

  async function handleAdd() {
    if (!addContent.trim()) return
    try {
      let metadata: Record<string, unknown> = {}
      if (addMeta.trim()) {
        try { metadata = JSON.parse(addMeta) } catch { metadata = { note: addMeta } }
      }
      await api.post('/knowledge/add', { content: addContent, metadata })
      setAddContent('')
      setAddMeta('')
      setAddMsg('✅ 添加成功')
      qc.invalidateQueries({ queryKey: ['kb-stats'] })
    } catch {
      setAddMsg('❌ 添加失败')
    }
  }

  async function handleInitSamples() {
    await api.post('/knowledge/init-samples')
    refetchStats()
    setAddMsg('✅ 示例文档已初始化')
  }

  // Search tab
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<{ content: string; score: number }[]>([])

  async function handleSearch() {
    if (!query.trim()) return
    const r = await api.post<{ results: { content: string; score: number }[] }>('/knowledge/search', { query, k: 5 })
    setSearchResults(r.data.results)
  }

  // Manage tab
  async function handleDelete(id: string) {
    await api.delete(`/knowledge/delete/${id}`)
    refetchDocs()
    refetchStats()
  }

  async function handleClear() {
    if (!window.confirm('确定要清空知识库吗？')) return
    await api.post('/knowledge/clear')
    refetchDocs()
    refetchStats()
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'stats', label: '📊 概览' },
    { key: 'add', label: '➕ 添加' },
    { key: 'search', label: '🔍 搜索' },
    { key: 'manage', label: '🗂️ 管理' },
  ]

  return (
    <div className="p-8 max-w-3xl mx-auto">
      {/* 页面标题 */}
      <div className="mb-7">
        <h1 className="text-2xl font-bold text-zinc-800 tracking-tight">知识库管理</h1>
        <p className="text-sm text-zinc-400 mt-1">管理 AI 参考的小红书案例，提升改写质量</p>
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-1 p-1 rounded-xl mb-5 w-fit" style={{ background: '#fff0f3' }}>
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all ${
              tab === key ? 'bg-white shadow-sm' : ''
            }`}
            style={tab === key ? { color: '#ff2d55' } : { color: '#ff8fa3' }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 概览 */}
      {tab === 'stats' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-2xl p-5" style={{ border: '1px solid #ffe0e0', boxShadow: '0 1px 6px rgba(255,45,85,0.06)' }}>
              <p className="text-3xl font-bold" style={{ color: '#ff2d55' }}>{stats?.total_documents ?? '—'}</p>
              <p className="text-sm mt-1" style={{ color: '#999' }}>文档总数</p>
            </div>
            <div className="bg-white rounded-2xl p-5" style={{ border: '1px solid #ffe0e0', boxShadow: '0 1px 6px rgba(255,45,85,0.06)' }}>
              <p className="text-sm font-semibold truncate" style={{ color: '#444' }}>{stats?.collection_name ?? '—'}</p>
              <p className="text-sm mt-1" style={{ color: '#999' }}>集合名称</p>
            </div>
          </div>
          <button
            onClick={() => { refetchStats() }}
            className="text-xs px-3.5 py-2 rounded-xl border border-zinc-200 hover:bg-zinc-50 text-zinc-500 font-medium"
          >
            ↻ 刷新
          </button>
        </div>
      )}

      {/* 添加 */}
      {tab === 'add' && (
        <div className="bg-white rounded-2xl p-5 space-y-4" style={{ border: '1px solid #ffe0e0', boxShadow: '0 2px 12px rgba(255,45,85,0.06)' }}>
          <div>
            <label className="text-xs font-semibold block mb-2" style={{ color: '#ffaab8' }}>文档内容</label>
            <textarea
              value={addContent}
              onChange={(e) => setAddContent(e.target.value)}
              rows={6}
              placeholder="输入要添加到知识库的内容…"
              className="w-full rounded-xl px-4 py-3 text-sm resize-y leading-relaxed"
              style={{ border: '1px solid #ffd6d6', background: '#fff8f7', color: '#333' }}
            />
          </div>
          <div>
            <label className="text-xs font-semibold block mb-2" style={{ color: '#ffaab8' }}>元数据（可选，JSON 或纯文本）</label>
            <input
              value={addMeta}
              onChange={(e) => setAddMeta(e.target.value)}
              placeholder='{"source": "手动", "category": "种草"}'
              className="w-full rounded-xl px-4 py-2.5 text-sm"
              style={{ border: '1px solid #ffd6d6', background: '#fff8f7', color: '#333' }}
            />
          </div>
          {addMsg && (
            <p className={`text-sm font-medium ${addMsg.startsWith('✅') ? 'text-emerald-600' : 'text-red-500'}`}>
              {addMsg}
            </p>
          )}
          <div className="flex gap-3 pt-1">
            <button
              onClick={handleAdd}
              disabled={!addContent.trim()}
              className="px-5 py-2 rounded-xl text-sm font-semibold text-white disabled:opacity-40"
              style={{ background: '#ff2d55', boxShadow: '0 2px 8px rgba(255,45,85,0.2)' }}
            >
              添加文档
            </button>
            <button
              onClick={handleInitSamples}
              className="px-4 py-2 rounded-xl text-sm font-medium"
              style={{ border: '1px solid #ffd6d6', color: '#ff8fa3', background: '#fff8f7' }}
            >
              初始化示例文档
            </button>
          </div>
        </div>
      )}

      {/* 搜索 */}
      {tab === 'search' && (
        <div className="space-y-4">
          <div className="flex gap-2 bg-white rounded-2xl p-2" style={{ border: '1px solid #ffe0e0', boxShadow: '0 1px 6px rgba(255,45,85,0.06)' }}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="输入关键词搜索知识库…"
              className="flex-1 px-3 py-1.5 text-sm text-zinc-700 placeholder-zinc-300 bg-transparent"
              style={{ outline: 'none', border: 'none', boxShadow: 'none' }}
            />
            <button
              onClick={handleSearch}
              className="px-4 py-1.5 rounded-xl text-sm font-semibold text-white"
              style={{ background: '#ff2d55', boxShadow: '0 2px 6px rgba(255,45,85,0.2)' }}
            >
              搜索
            </button>
          </div>
          <div className="space-y-2.5">
            {searchResults.map((r, i) => (
              <div key={i} className="bg-white rounded-2xl p-4" style={{ border: '1px solid #ffe0e0', boxShadow: '0 1px 6px rgba(255,45,85,0.06)' }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-semibold" style={{ color: '#ffaab8' }}>结果 {i + 1}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: '#fff0f3', color: '#ff2d55', border: '1px solid #ffd6d6' }}>
                    相关度 {(r.score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: '#444' }}>{r.content}</p>
              </div>
            ))}
            {searchResults.length === 0 && query && (
              <p className="text-sm text-zinc-400 text-center py-8">未找到相关内容</p>
            )}
          </div>
        </div>
      )}

      {/* 管理 */}
      {tab === 'manage' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={handleClear}
              className="text-xs px-3.5 py-2 rounded-xl bg-red-50 hover:bg-red-100 text-red-500 border border-red-100 font-medium"
            >
              清空知识库
            </button>
          </div>
          <div className="space-y-2.5">
            {(docs as KBDocument[]).map((doc) => (
              <div key={doc.id} className="bg-white rounded-2xl p-4 flex gap-3" style={{ border: '1px solid #ffe0e0', boxShadow: '0 1px 6px rgba(255,45,85,0.06)' }}>
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] text-zinc-400 font-mono mb-1.5 truncate">ID: {doc.id}</p>
                  <p className="text-sm text-zinc-600 leading-relaxed line-clamp-3">{doc.content}</p>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="text-xs text-zinc-400 hover:text-red-400 shrink-0 hover:bg-red-50 w-7 h-7 rounded-lg flex items-center justify-center"
                >
                  ✕
                </button>
              </div>
            ))}
            {docs.length === 0 && (
              <div className="text-center py-12 text-zinc-400">
                <div className="text-3xl mb-2">📭</div>
                <p className="text-sm">知识库为空</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
