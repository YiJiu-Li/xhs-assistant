import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })

// ---- types ----
export interface ModelInfo {
  id: string
  description: string
  default: boolean
}

export interface TemplateInfo {
  id: string
  icon: string
  desc: string
  tone: string
  structure: string
}

export interface ConversationSession {
  session_id: string
  created_at: string
  message_count: number
}

export interface ChatMessage {
  role: 'human' | 'ai'
  content: string
}

export interface KBStats {
  total_documents: number
  collection_name: string
}

export interface KBDocument {
  id: string
  title: string
  style: string
  source: string
  hashtags: string
  content_preview: string
}

// ---- helpers ----
export async function fetchModels(): Promise<ModelInfo[]> {
  const r = await api.get<{ models: ModelInfo[] }>('/config/models')
  return r.data.models
}

export async function fetchTemplates(): Promise<TemplateInfo[]> {
  const r = await api.get<{ templates: TemplateInfo[] }>('/config/templates')
  return r.data.templates
}

export async function fetchSessions(): Promise<ConversationSession[]> {
  const r = await api.get<{ sessions: ConversationSession[] }>('/conversation')
  return r.data.sessions
}

export async function createSession(title?: string): Promise<{ session_id: string }> {
  const r = await api.post<{ session_id: string }>('/conversation', { title })
  return r.data
}

export async function fetchHistory(sessionId: string): Promise<ChatMessage[]> {
  const r = await api.get<{ session_id: string; messages: ChatMessage[] }>(`/conversation/${sessionId}`)
  return r.data.messages
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/conversation/${sessionId}`)
}

export async function fetchKBStats(): Promise<KBStats> {
  const r = await api.get<KBStats>('/knowledge/stats')
  return r.data
}

export async function fetchKBDocs(): Promise<KBDocument[]> {
  const r = await api.get<KBDocument[]>('/knowledge/list')
  return r.data
}
