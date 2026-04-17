import { useState } from 'react'
import * as XLSX from 'xlsx'
import { useApiConfig } from '../contexts/ApiContext'

interface BatchItem {
  content: string
  style?: string
  result?: string
  status: 'pending' | 'processing' | 'done' | 'error'
}

export default function BatchPage() {
  const { model, temperature } = useApiConfig()
  const [items, setItems] = useState<BatchItem[]>([])
  const [textInput, setTextInput] = useState('')
  const [style, setStyle] = useState('')
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState({ current: 0, total: 0 })

  function loadFromText() {
    const lines = textInput.split('\n').map((l) => l.trim()).filter(Boolean)
    setItems(lines.map((content) => ({ content, status: 'pending' })))
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      const wb = XLSX.read(ev.target?.result, { type: 'binary' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json<{ content?: string; 内容?: string }>(ws)
      const contents = rows
        .map((r) => r.content || r['内容'] || '')
        .filter(Boolean)
      setItems(contents.map((content) => ({ content, status: 'pending' })))
    }
    reader.readAsBinaryString(file)
  }

  async function runBatch() {
    if (!items.length) return
    setRunning(true)
    setProgress({ current: 0, total: items.length })

    const contents = items.map((i) => i.content)
    setItems((prev) => prev.map((i) => ({ ...i, status: 'processing', result: undefined })))

    try {
      const resp = await fetch('/api/batch/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents, style: style || undefined, model, temperature }),
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
          if (chunk.type === 'progress') {
            setProgress({ current: chunk.current, total: chunk.total })
          } else if (chunk.type === 'result') {
            setItems((prev) => {
              const copy = [...prev]
              copy[chunk.index] = {
                ...copy[chunk.index],
                result: chunk.result,
                status: chunk.error ? 'error' : 'done',
              }
              return copy
            })
          } else if (chunk.type === 'done') {
            break
          }
        }
      }
    } catch (e) {
      console.error(e)
    } finally {
      setRunning(false)
    }
  }

  function exportXlsx() {
    const rows = items.map((i, idx) => ({
      序号: idx + 1,
      原文: i.content,
      改写结果: i.result ?? '',
      状态: i.status,
    }))
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows), '批量改写')
    XLSX.writeFile(wb, '批量改写结果.xlsx')
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* 页面标题 */}
      <div className="mb-7">
        <h1 className="text-2xl font-bold text-zinc-800 tracking-tight">批量处理</h1>
        <p className="text-sm text-zinc-400 mt-1">批量输入文案，一键生成小红书风格改写结果</p>
      </div>

      {/* 输入卡片 */}
      <div className="bg-white rounded-2xl p-5 mb-4" style={{ border: '1px solid #ffe0e0', boxShadow: '0 2px 12px rgba(255,45,85,0.06)' }}>
        <div className="grid grid-cols-2 gap-5">
          <div className="space-y-2.5">
            <p className="text-xs font-semibold mb-2.5" style={{ color: '#ffaab8' }}>✦ 文本输入（每行一条）</p>
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={7}
              placeholder="每行输入一段文案…"
              className="w-full rounded-xl px-4 py-3 text-sm resize-none leading-relaxed"
              style={{ border: '1px solid #ffd6d6', background: '#fff8f7', color: '#333' }}
            />
            <button
              onClick={loadFromText}
              className="text-xs px-3.5 py-2 rounded-xl font-medium"
              style={{ border: '1px solid #ffd6d6', color: '#ff8fa3', background: '#fff8f7' }}
            >
              载入文本
            </button>
          </div>
          <div className="space-y-2.5">
            <p className="text-xs font-semibold mb-2.5" style={{ color: '#ffaab8' }}>✦ 上传 Excel / CSV</p>
            <div className="rounded-xl p-5 text-center cursor-pointer transition-colors" style={{ border: '2px dashed #ffd6d6', background: '#fff8f7' }}>
              <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileChange} className="hidden" id="file-input" />
              <label htmlFor="file-input" className="cursor-pointer">
                <div className="text-2xl mb-1.5">📂</div>
                <div className="text-xs" style={{ color: '#999' }}>点击选择文件</div>
                <div className="text-[10px] mt-1" style={{ color: '#bbb' }}>需包含 "content" 或 "内容" 列</div>
              </label>
            </div>
            <div>
              <p className="text-xs font-semibold mb-1.5" style={{ color: '#ffaab8' }}>改写风格（可选）</p>
              <input
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                placeholder="如：种草推荐"
                className="w-full rounded-xl px-3 py-2 text-sm"
                style={{ border: '1px solid #ffd6d6', background: '#fff8f7', color: '#333' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 操作栏 */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-zinc-400">共 <span className="font-semibold text-zinc-600">{items.length}</span> 条</span>
        <div className="flex-1" />
        {items.some((i) => i.status === 'done') && (
          <button
            onClick={exportXlsx}
            className="text-sm px-4 py-2 rounded-xl border border-zinc-200 hover:bg-zinc-50 text-zinc-600 font-medium shadow-sm"
          >
            ↓ 导出 Excel
          </button>
        )}
        <button
          onClick={runBatch}
          disabled={running || !items.length}
          className="text-sm px-5 py-2 rounded-xl font-semibold text-white disabled:opacity-40"
          style={{ background: '#ff2d55', boxShadow: '0 2px 8px rgba(255,45,85,0.2)' }}
        >
          {running ? '处理中…' : '开始批量改写 →'}
        </button>
      </div>

      {/* 进度条 */}
      {running && (
        <div className="mb-4 space-y-1.5">
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#ffe0e0' }}>
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: progress.total ? `${(progress.current / progress.total) * 100}%` : '0%', background: '#ff2d55' }}
            />
          </div>
          <p className="text-xs text-zinc-400">{progress.current} / {progress.total} 条已处理</p>
        </div>
      )}

      {/* 结果列表 */}
      {items.length > 0 && (
        <div className="space-y-2.5">
          {items.map((item, i) => (
            <div key={i} className="bg-white rounded-2xl overflow-hidden" style={{ border: '1px solid #ffe0e0', boxShadow: '0 1px 6px rgba(255,45,85,0.06)' }}>
              <div className="grid grid-cols-2">
                {/* 原文 */}
                <div className="p-4" style={{ borderRight: '1px solid #ffe4e4' }}>
                  <p className="text-[10px] font-semibold mb-2" style={{ color: '#ffaab8' }}>
                    <span className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] mr-1.5" style={{ background: '#fff0f3', color: '#ff8fa3' }}>{i + 1}</span>
                    原文
                  </p>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: '#444' }}>{item.content}</p>
                </div>
                {/* 改写 */}
                <div className="p-4">
                  <p className="text-[10px] font-semibold mb-2" style={{ color: '#ffaab8' }}>改写结果
                    {item.status === 'done' && (
                      <span className="ml-2 text-[9px] bg-emerald-50 text-emerald-500 border border-emerald-100 px-1.5 py-0.5 rounded-full">✓ 完成</span>
                    )}
                    {item.status === 'error' && (
                      <span className="ml-2 text-[9px] bg-red-50 text-red-400 border border-red-100 px-1.5 py-0.5 rounded-full">✕ 错误</span>
                    )}
                  </p>
                  {item.status === 'processing' && (
                    <p className="text-sm text-zinc-400 animate-pulse">生成中…</p>
                  )}
                  {item.status === 'pending' && <p className="text-sm text-zinc-300">待处理</p>}
                  {(item.status === 'done' || item.status === 'error') && (
                    <p className={`text-sm leading-relaxed whitespace-pre-wrap ${item.status === 'error' ? 'text-red-400' : 'text-zinc-700'}`}>
                      {item.result}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
