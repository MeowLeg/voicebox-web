import { getToken } from '@/utils/auth'

const QUEUE_BASE = '/voicebox-web/queue'

export interface QueueTaskRequest {
  profile_id?: string
  voice_id?: string
  text: string
  language?: string
  seed?: number
  instruct?: string
  engine?: string
  model_size?: string
  max_chunk_chars?: number
  speed?: number
}

export interface QueueSubmitResponse {
  id: string
  status: string
  position: number
  message: string
}

export interface QueueTaskStatus {
  id: string
  user_id: string
  status: string
  position: number
  progress: number
  error: string | null
  audio_url: string | null
  duration: number | null
  voicebox_generation_id: string | null
  request_data: Record<string, any>
  text: string
  created_at: string
  updated_at: string
}

export interface QueueOverview {
  pending_count: number
  processing: {
    id: string
    progress: number
    text: string
    created_at: string
  } | null
}

export interface QueueTaskListResponse {
  tasks: QueueTaskStatus[]
  active_count: number
}

function queueFetch(url: string, init?: RequestInit): Promise<Response> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const existingHeaders = init?.headers
  const newHeaders = new Headers(existingHeaders)
  newHeaders.set('Authorization', `Bearer ${token}`)
  newHeaders.set('Content-Type', 'application/json')
  return fetch(url, { ...init, headers: newHeaders })
}

export async function submitQueueTask(data: QueueTaskRequest): Promise<QueueSubmitResponse> {
  const res = await queueFetch(`${QUEUE_BASE}/submit`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '提交任务失败')
  }
  return res.json()
}

export async function getQueueTaskStatus(taskId: string): Promise<QueueTaskStatus> {
  const res = await queueFetch(`${QUEUE_BASE}/tasks/${taskId}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '获取任务状态失败')
  }
  return res.json()
}

export async function getQueueOverview(): Promise<QueueOverview> {
  const res = await queueFetch(`${QUEUE_BASE}/status`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '获取队列状态失败')
  }
  return res.json()
}

export async function listQueueTasks(status?: string, limit = 50): Promise<QueueTaskListResponse> {
  const query = new URLSearchParams()
  if (status) query.set('status', status)
  query.set('limit', String(limit))
  const res = await queueFetch(`${QUEUE_BASE}/tasks?${query.toString()}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '获取任务列表失败')
  }
  return res.json()
}

export async function cancelQueueTask(taskId: string): Promise<void> {
  const res = await queueFetch(`${QUEUE_BASE}/tasks/${taskId}`, { method: 'DELETE' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '取消任务失败')
  }
}
