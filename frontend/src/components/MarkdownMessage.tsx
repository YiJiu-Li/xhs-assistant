import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  content: string
  streaming?: boolean
}

export default function MarkdownMessage({ content, streaming }: Props) {
  return (
    <div className="markdown-body text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 段落
          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
          // 标题
          h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1">{children}</h1>,
          h2: ({ children }) => <h2 className="text-sm font-bold mt-2 mb-1">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1">{children}</h3>,
          // 列表
          ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          // 粗体 / 斜体
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          // 行内代码
          code: ({ children, className }) => {
            const isBlock = className?.startsWith('language-')
            return isBlock ? (
              <code className={`block bg-zinc-100 rounded-md px-3 py-2 text-xs font-mono my-2 overflow-x-auto ${className}`}>
                {children}
              </code>
            ) : (
              <code className="bg-zinc-100 rounded px-1 py-0.5 text-xs font-mono text-rose-600">{children}</code>
            )
          },
          // 代码块
          pre: ({ children }) => (
            <pre className="bg-zinc-100 rounded-xl px-4 py-3 text-xs font-mono my-3 overflow-x-auto border border-zinc-200">{children}</pre>
          ),
          // 引用
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-rose-300 pl-3 text-zinc-500 italic my-2">{children}</blockquote>
          ),
          // 分隔线
          hr: () => <hr className="border-zinc-200 my-3" />,
          // 表格
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="text-xs border-collapse w-full">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-gray-200 bg-gray-50 px-2 py-1 text-left font-semibold">{children}</th>
          ),
          td: ({ children }) => (
            <td className="border border-gray-200 px-2 py-1">{children}</td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
      {streaming && <span className="inline-block w-0.5 h-4 bg-gray-500 animate-pulse ml-0.5 align-middle" />}
    </div>
  )
}
