/**
 * 仿小红书帖子卡片预览组件
 * 将 AI 输出的改写结果渲染成接近真实 XHS 界面的样式
 */

interface XhsPreviewCardProps {
  text: string
  streaming?: boolean
}

/** 从 AI 输出中解析标题、正文、话题标签 */
function parseXhsOutput(text: string) {
  let title = ''
  let body = text.trim()
  let tags: string[] = []

  // 提取标题：【标题】后面的内容（到换行为止）
  const titleMatch = text.match(/【标题】\s*(.+?)(?:\n|$)/)
  if (titleMatch) {
    title = titleMatch[1].trim()
    body = text.slice(titleMatch.index! + titleMatch[0].length).trim()
  } else {
    // fallback：第一行作为标题
    const lines = text.split('\n').filter(Boolean)
    if (lines.length > 0) {
      title = lines[0].trim()
      body = lines.slice(1).join('\n').trim()
    }
  }

  // 提取话题标签：找最后若干行中 #开头的 token
  const tagPattern = /(#[\u4e00-\u9fa5\w]+)/g
  // 取正文最后200字符判断是否集中了大量 # 标签
  const lastPart = body.slice(-300)
  const tagDenseLines = lastPart.split('\n').filter(l => {
    const matches = l.match(tagPattern)
    // 这一行超过60%是标签内容
    return matches && matches.join('').length / (l.trim().length || 1) > 0.5
  })

  if (tagDenseLines.length > 0) {
    const tagSection = tagDenseLines.join(' ')
    tags = (tagSection.match(tagPattern) || [])
    // 从正文末尾移除标签行
    const firstTagLine = tagDenseLines[0]
    const idx = body.lastIndexOf(firstTagLine)
    if (idx !== -1) body = body.slice(0, idx).trim()
  }

  return { title, body, tags }
}

/** 将正文按段落拆分，保留换行结构 */
function renderBodyParagraphs(body: string) {
  const paragraphs = body.split(/\n{2,}/).filter(Boolean)
  return paragraphs.map((para, i) => (
    <p key={i} className="mb-3 last:mb-0 leading-7 text-[15px]" style={{ color: '#1a1a1a' }}>
      {para.split('\n').map((line, j) => (
        <span key={j}>
          {line}
          {j < para.split('\n').length - 1 && <br />}
        </span>
      ))}
    </p>
  ))
}

export default function XhsPreviewCard({ text, streaming }: XhsPreviewCardProps) {
  const { title, body, tags } = parseXhsOutput(text)

  return (
    /* 手机屏幕容器 */
    <div className="flex justify-center">
      <div
        className="w-full max-w-sm rounded-3xl overflow-hidden shadow-2xl"
        style={{ background: '#fff', border: '1px solid #eee', fontFamily: '-apple-system, "PingFang SC", sans-serif' }}
      >
        {/* 状态栏模拟 */}
        <div className="flex items-center justify-between px-5 pt-3 pb-1" style={{ background: '#fff' }}>
          <span className="text-xs font-semibold" style={{ color: '#111' }}>9:41</span>
          <div className="flex items-center gap-1">
            <div className="w-4 h-2.5 rounded-sm border border-zinc-400 relative">
              <div className="absolute inset-0.5 right-1.5 rounded-sm" style={{ background: '#111' }} />
              <div className="absolute right-0.5 top-1/2 -translate-y-1/2 w-0.5 h-1.5 rounded-r-sm" style={{ background: '#111' }} />
            </div>
          </div>
        </div>

        {/* 顶部导航栏 */}
        <div className="flex items-center justify-between px-4 pb-2 pt-1" style={{ background: '#fff' }}>
          <button className="w-8 h-8 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="2.5" strokeLinecap="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <div className="flex items-center gap-1">
            <button className="w-8 h-8 flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="5" r="1" fill="#111"/><circle cx="12" cy="12" r="1" fill="#111"/><circle cx="12" cy="19" r="1" fill="#111"/>
              </svg>
            </button>
          </div>
        </div>

        {/* 封面图占位（渐变色模拟图片）*/}
        <div
          className="w-full relative overflow-hidden"
          style={{
            height: 220,
            background: 'linear-gradient(135deg, #ffd6e0 0%, #ffb3c6 40%, #ff85a1 70%, #ff4d7d 100%)',
          }}
        >
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2" style={{ background: 'rgba(255,255,255,0.08)' }}>
            <div className="text-4xl">🌸</div>
            {title && (
              <div className="text-sm font-bold text-white text-center px-6 leading-snug drop-shadow" style={{ textShadow: '0 1px 4px rgba(0,0,0,0.3)' }}>
                {title.replace(/^[^\w\u4e00-\u9fa5]+/, '').slice(0, 28)}
              </div>
            )}
          </div>
          {/* 页码指示 */}
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1">
            {[0,1,2].map(i => (
              <div key={i} className="rounded-full" style={{ width: i === 0 ? 16 : 6, height: 6, background: i === 0 ? '#fff' : 'rgba(255,255,255,0.5)' }} />
            ))}
          </div>
        </div>

        {/* 正文区域 */}
        <div className="px-4 pt-4 pb-2">
          {/* 用户信息栏 */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              {/* 头像 */}
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                style={{ background: 'linear-gradient(135deg, #ff6b8a, #ff2d55)' }}
              >
                我
              </div>
              <div>
                <div className="text-sm font-semibold" style={{ color: '#1a1a1a' }}>小红书创作者</div>
                <div className="text-[11px]" style={{ color: '#999' }}>刚刚 · 杭州</div>
              </div>
            </div>
            <button
              className="px-4 py-1.5 rounded-full text-xs font-semibold text-white"
              style={{ background: '#ff2d55' }}
            >
              关注
            </button>
          </div>

          {/* 标题 */}
          {title && (
            <h2 className="font-bold text-base leading-snug mb-2.5" style={{ color: '#1a1a1a' }}>
              {title}
            </h2>
          )}

          {/* 正文 */}
          <div className="text-sm" style={{ color: '#333' }}>
            {renderBodyParagraphs(body)}
            {streaming && (
              <span className="inline-block w-0.5 h-4 ml-0.5 animate-pulse" style={{ background: '#ff2d55', verticalAlign: 'middle' }} />
            )}
          </div>

          {/* 话题标签 */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-x-1 gap-y-1.5 mt-3">
              {tags.map((tag) => (
                <span key={tag} className="text-xs font-medium" style={{ color: '#1a7ae0' }}>
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* 时间 */}
          <div className="mt-3 mb-1 text-[11px]" style={{ color: '#bbb' }}>2026-04-20 发布于杭州</div>
        </div>

        {/* 底部互动栏 */}
        <div
          className="flex items-center justify-between px-5 py-3"
          style={{ borderTop: '1px solid #f5f5f5' }}
        >
          {/* 点赞 */}
          <button className="flex flex-col items-center gap-0.5">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#333" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
            <span className="text-[11px]" style={{ color: '#666' }}>189</span>
          </button>
          {/* 收藏 */}
          <button className="flex flex-col items-center gap-0.5">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#333" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            <span className="text-[11px]" style={{ color: '#666' }}>169</span>
          </button>
          {/* 评论 */}
          <button className="flex flex-col items-center gap-0.5">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#333" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span className="text-[11px]" style={{ color: '#666' }}>13</span>
          </button>
          {/* 分享 */}
          <button className="flex flex-col items-center gap-0.5">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#333" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
            <span className="text-[11px]" style={{ color: '#666' }}>分享</span>
          </button>
        </div>
      </div>
    </div>
  )
}
