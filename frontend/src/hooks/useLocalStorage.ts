import { useState, useEffect } from 'react'

/**
 * 与 localStorage 双向同步的 useState
 * 页面切换/刷新后自动恢复值
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key)
      return stored !== null ? (JSON.parse(stored) as T) : initialValue
    } catch {
      return initialValue
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // localStorage 不可用时静默失败（隐私模式等）
    }
  }, [key, value])

  return [value, setValue] as const
}
