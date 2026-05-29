import { getToken } from '@/utils/auth'

export interface AuthRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    username: string
    email?: string
    role?: string
  }
}

export function getAuthHeader(): Record<string, string> {
  const token = getToken()
  if (!token) return {}
  return { Authorization: `Bearer ${token}` }
}

export async function login(data: AuthRequest): Promise<AuthResponse> {
  const res = await fetch('/voicebox-web/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '登录失败')
  }
  return res.json()
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const res = await fetch('/voicebox-web/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '注册失败')
  }
  return res.json()
}

export async function fetchCurrentUser(): Promise<AuthResponse['user']> {
  const token = getToken()
  if (!token) throw new Error('未登录')
  const res = await fetch('/voicebox-web/auth/me', {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) {
    throw new Error('登录已过期')
  }
  return res.json()
}

// Audio Record API
export interface AudioRecordRequest {
  voicebox_generation_id?: string
  profile_id?: string
  profile_name?: string
  text: string
  language?: string
  audio_url?: string
  duration?: number
  seed?: number
  instruct?: string
  engine?: string
  model_size?: string
  status?: string
}

export interface AudioRecordItem {
  id: string
  user_id: string
  voicebox_generation_id?: string
  profile_id?: string
  profile_name?: string
  text: string
  language?: string
  audio_url?: string
  duration?: number
  seed?: number
  instruct?: string
  engine?: string
  model_size?: string
  status: string
  created_at: string
}

export interface AudioRecordListResponse {
  items: AudioRecordItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

const RECORDS_BASE = '/voicebox-web/records'

function recordFetch(url: string, init?: RequestInit): Promise<Response> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const existingHeaders = init?.headers
  const newHeaders = new Headers(existingHeaders)
  newHeaders.set('Authorization', `Bearer ${token}`)
  newHeaders.set('Content-Type', 'application/json')
  return fetch(url, { ...init, headers: newHeaders })
}

export async function createAudioRecord(data: AudioRecordRequest): Promise<AudioRecordItem> {
  const res = await recordFetch(RECORDS_BASE, {
    method: 'POST',
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '保存记录失败')
  }
  return res.json()
}

export async function listAudioRecords(params?: {
  page?: number
  page_size?: number
  status?: string
  profile_id?: string
}): Promise<AudioRecordListResponse> {
  const query = new URLSearchParams()
  if (params?.page) query.set('page', String(params.page))
  if (params?.page_size) query.set('page_size', String(params.page_size))
  if (params?.status) query.set('status', params.status)
  if (params?.profile_id) query.set('profile_id', params.profile_id)
  const res = await recordFetch(`${RECORDS_BASE}?${query.toString()}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '获取记录失败')
  }
  return res.json()
}

export async function deleteAudioRecord(id: string): Promise<void> {
  const res = await recordFetch(`${RECORDS_BASE}/${id}`, { method: 'DELETE' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '删除记录失败')
  }
}

// Admin permission management
export interface AdminUserItem {
  id: string
  username: string
  email?: string
  role: string
  permissions: string[]
}

export async function fetchAdminUsers(): Promise<AdminUserItem[]> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const res = await fetch('/voicebox-web/auth/users', {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) throw new Error('获取用户列表失败')
  const data = await res.json()
  return data.users
}

export async function grantPermission(userId: string, permission: string): Promise<void> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const res = await fetch(`/voicebox-web/auth/users/${userId}/permissions`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ permission })
  })
  if (!res.ok) throw new Error('授权失败')
}

export async function revokePermission(userId: string, permission: string): Promise<void> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const res = await fetch(`/voicebox-web/auth/users/${userId}/permissions/${permission}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) throw new Error('撤销权限失败')
}

export async function createUser(data: { username: string; password: string; email?: string; role?: string }): Promise<void> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const res = await fetch('/voicebox-web/auth/users', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '创建失败')
  }
}

export async function updateUser(userId: string, data: { password?: string; email?: string; role?: string }): Promise<void> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const res = await fetch(`/voicebox-web/auth/users/${userId}`, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '更新失败')
  }
}

export async function deleteUser(userId: string): Promise<void> {
  const token = getToken()
  if (!token) throw new Error('请先登录')
  const res = await fetch(`/voicebox-web/auth/users/${userId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '删除失败')
  }
}
