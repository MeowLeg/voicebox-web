const API_BASE = '/voicebox-web'
// const API_BASE = 'http://61.153.213.238:17493'  // 直接访问后端（仅开发调试用）

export interface VoiceProfile {
  id: string
  name: string
  language: string
  description?: string
  created_at: string
}

export interface GenerationRequest {
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

export interface GenerationResponse {
  id: string
  profile_id: string
  text: string
  language: string
  audio_path: string | null
  duration: number | null
  seed?: number
  instruct?: string
  engine?: string
  model_size?: string
  status: string
  error: string | null
  created_at: string
  active_version_id?: string
}

export interface HistoryItem {
  id: string
  profile_id: string
  profile_name?: string
  text: string
  language: string
  audio_path: string | null
  duration: number | null
  status: string
  error: string | null
  created_at: string
  versions?: Array<{
    id: string
    audio_path: string
    is_default: boolean
  }>
  active_version_id?: string
}

export interface ModelInfo {
  model_name: string
  display_name: string
  hf_repo_id: string
  downloaded: boolean
  downloading: boolean
  size_mb: number | null
  loaded: boolean
  supports_clone?: boolean
}

export interface PresetVoice {
  voice_id: string
  name: string
  gender: string
  language: string
}

export interface PresetVoicesResponse {
  engine: string
  voices: PresetVoice[]
}

export async function fetchProfiles(signal?: AbortSignal): Promise<VoiceProfile[]> {
  const res = await fetch(`${API_BASE}/profiles`, { signal })
  if (!res.ok) throw new Error('Failed to fetch profiles')
  return res.json()
}

export async function createProfile(data: {
  name: string
  description?: string
  language?: string
  voice_type?: 'cloned' | 'preset' | 'designed'
  preset_engine?: string
  preset_voice_id?: string
}): Promise<VoiceProfile> {
  const res = await fetch(`${API_BASE}/profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Failed to create profile')
  }
  return res.json()
}

export async function deleteProfile(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/profiles/${id}`, {
    method: 'DELETE'
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Failed to delete profile')
  }
}

export async function uploadProfileSample(
  profileId: string,
  audioBlob: Blob,
  referenceText: string
): Promise<void> {
  const formData = new FormData()
  formData.append('file', audioBlob, 'sample.wav')
  formData.append('reference_text', referenceText)
  
  const res = await fetch(`${API_BASE}/profiles/${profileId}/samples`, {
    method: 'POST',
    body: formData
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Failed to upload sample')
  }
}

export async function generateSpeech(
  req: GenerationRequest,
  signal?: AbortSignal
): Promise<GenerationResponse> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Generation failed')
  }
  const text = await res.text()
  let cleanText = text.replace(/^data:\s*/, '').trim()
  cleanText = cleanText.split('\n')[0].trim()
  return JSON.parse(cleanText)
}

export async function getGenerationStatus(id: string, signal?: AbortSignal): Promise<GenerationResponse> {
  const res = await fetch(`${API_BASE}/generate/${id}/status`, { signal })
  if (!res.ok) throw new Error('Failed to get status')
  const text = await res.text()
  let cleanText = text.replace(/^data:\s*/, '').trim()
  cleanText = cleanText.split('\n')[0].trim()
  return JSON.parse(cleanText)
}

export async function fetchHistory(limit = 50): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/history?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch history')
  const data = await res.json()
  return data.items || []
}

export async function deleteHistoryItem(id: string): Promise<void> {
  const url = `${API_BASE}/history/${id}`
  
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 10000)
  
  try {
    const res = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!res.ok) {
      const errorText = await res.text()
      throw new Error(`删除失败 (${res.status}): ${errorText || '未知错误'}`)
    }
  } catch (err: any) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      throw new Error('删除请求超时，请检查后端是否在线')
    }
    throw err
  }
}

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_BASE}/models/status`)
  if (!res.ok) throw new Error('Failed to fetch models')
  const data = await res.json()
  return data.models || []
}

export async function fetchPresetVoices(engine: string): Promise<PresetVoicesResponse> {
  const res = await fetch(`${API_BASE}/profiles/presets/${engine}`)
  if (!res.ok) throw new Error('Failed to fetch preset voices')
  return res.json()
}

export async function downloadModel(modelName: string): Promise<void> {
  const res = await fetch(`${API_BASE}/models/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_name: modelName })
  })
  if (!res.ok) throw new Error('Failed to download model')
}

export async function loadModel(modelName: string): Promise<void> {
  const res = await fetch(`${API_BASE}/models/load?model_name=${modelName}`, {
    method: 'POST'
  })
  if (!res.ok) throw new Error('Failed to load model')
}

export function getAudioUrl(id: string): string {
  return `${API_BASE}/audio/${id}`
}

export async function waitForCompletion(
  id: string,
  intervalMs = 1000,
  maxAttempts = 300,
  signal?: AbortSignal
): Promise<GenerationResponse> {
  for (let i = 0; i < maxAttempts; i++) {
    signal?.throwIfAborted()
    const status = await getGenerationStatus(id)
    if (status.status === 'completed' || status.status === 'failed') {
      return status
    }
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(resolve, intervalMs)
      signal?.addEventListener('abort', () => {
        clearTimeout(timeout)
        reject(new DOMException('Aborted', 'AbortError'))
      })
    })
  }
  throw new Error('Generation timed out')
}

export function splitText(text: string, maxLen = 500): string[] {
  const segments: string[] = []
  let remaining = text.trim()
  while (remaining.length > 0) {
    if (remaining.length <= maxLen) {
      segments.push(remaining)
      break
    }
    let splitPoint = maxLen
    const chunk = remaining.slice(0, maxLen)
    const punctuations = ['。', '！', '？', '；', '\n', '.', '!', '?', ';', '，', ',']
    for (const p of punctuations) {
      const idx = chunk.lastIndexOf(p)
      if (idx > maxLen * 0.3) {
        splitPoint = idx + 1
        break
      }
    }
    segments.push(remaining.slice(0, splitPoint))
    remaining = remaining.slice(splitPoint).trimStart()
  }
  return segments
}

function readUint32(view: DataView, offset: number): number {
  return view.getUint32(offset, true)
}

function readUint16(view: DataView, offset: number): number {
  return view.getUint16(offset, true)
}

function writeUint32(view: DataView, offset: number, value: number): void {
  view.setUint32(offset, value, true)
}

function writeUint16(view: DataView, offset: number, value: number): void {
  view.setUint16(offset, value, true)
}

export async function concatWavBlobs(blobs: Blob[]): Promise<Blob> {
  if (blobs.length === 0) return new Blob()
  if (blobs.length === 1) return blobs[0]

  return new Promise((resolve, reject) => {
    Promise.all(blobs.map(b => b.arrayBuffer())).then(buffers => {
      try {
        const views = buffers.map(b => new DataView(b))
        const sampleRate = readUint32(views[0], 24)
        const numChannels = readUint16(views[0], 22)
        const bitsPerSample = readUint16(views[0], 34)

        const dataBuffers: Uint8Array[] = []
        let totalDataLength = 0

        for (let i = 0; i < buffers.length; i++) {
          const buffer = buffers[i]
          const view = views[i]
          
          let dataSize = 0
          let dataOffset = 0
          
          let offset = 12
          while (offset < buffer.byteLength - 8) {
            const id = String.fromCharCode(...new Uint8Array(buffer, offset, 4))
            const chunkSize = readUint32(view, offset + 4)
            
            if (id === 'data') {
              dataOffset = offset + 8
              dataSize = chunkSize
              break
            }
            offset += 8 + chunkSize
            if (offset % 2 !== 0) offset++
          }
          
          if (dataSize === 0 || dataOffset === 0) {
            dataOffset = 44
            dataSize = buffer.byteLength - 44
          }
          
          totalDataLength += dataSize
          dataBuffers.push(new Uint8Array(buffer, dataOffset, dataSize))
        }

        const headerSize = 44
        const totalSize = headerSize + totalDataLength
        const result = new Uint8Array(totalSize)
        const resultView = new DataView(result.buffer)

        result.set(new TextEncoder().encode('RIFF'), 0)
        writeUint32(resultView, 4, totalSize - 8)
        result.set(new TextEncoder().encode('WAVE'), 8)
        result.set(new TextEncoder().encode('fmt '), 12)
        writeUint32(resultView, 16, 16)
        writeUint16(resultView, 20, 1)
        writeUint16(resultView, 22, numChannels)
        writeUint32(resultView, 24, sampleRate)
        writeUint32(resultView, 28, sampleRate * numChannels * (bitsPerSample / 8))
        writeUint16(resultView, 32, numChannels * (bitsPerSample / 8))
        writeUint16(resultView, 34, bitsPerSample)
        result.set(new TextEncoder().encode('data'), 36)
        writeUint32(resultView, 40, totalDataLength)

        let offset = headerSize
        for (const buf of dataBuffers) {
          result.set(buf, offset)
          offset += buf.length
        }

        resolve(new Blob([result], { type: 'audio/wav' }))
      } catch (err) {
        reject(err)
      }
    }).catch(reject)
  })
}

// Article API
export interface Article {
  AUTHOR: string
  CHNLDESC: string
  DOCSTATUS: number
  DOCTYPE: number
  METADATAID: number
  PUBDATE: string
  TITLE: string
}

export async function fetchPaperArticles(params: {
  siteId: string
  docstatus: string
  beginDate?: string
  endDate?: string
}): Promise<Article[]> {
  const query = new URLSearchParams()
  query.set('siteId', params.siteId)
  query.set('docstatus', params.docstatus)
  if (params.beginDate) query.set('beginDate', params.beginDate)
  if (params.endDate) query.set('endDate', params.endDate)
  
  const res = await fetch(`${API_BASE}/articles/get_paper_articles?${query.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch articles')
  const json = await res.json()
  return json.data || []
}

export async function fetchArticleDetail(metadataId: string): Promise<any> {
  const url = `${API_BASE}/articles/get_paper_article_detail?metadataId=${metadataId}`
  console.log('Fetching article detail from:', url)
  const res = await fetch(url)
  console.log('Response status:', res.status)
  const json = await res.json()
  console.log('Response data:', json)
  return json
}

export async function fetchTvNewsLists(startTime: string, endTime: string, columnId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/articles/get_tv_newslists?startTime=${startTime}&endTime=${endTime}&columnId=${columnId}`)
  if (!res.ok) throw new Error('Failed to fetch TV news lists')
  return res.json()
}

export async function fetchTvNewsDetail(listId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/articles/get_tv_newslist_detail?llistid=${listId}`)
  if (!res.ok) throw new Error('Failed to fetch TV news detail')
  return res.json()
}

export async function fetchTvArticle(docId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/articles/get_tv_article?docid=${docId}`)
  if (!res.ok) throw new Error('Failed to fetch TV article')
  return res.json()
}

export interface AvailableEffect {
  type: string
  label: string
  description: string
  params: Record<string, {
    default: number
    min: number
    max: number
    step: number
    description: string
  }>
}

export interface EffectConfig {
  type: string
  enabled?: boolean
  params: Record<string, number | string | boolean>
}

export async function fetchAvailableEffects(): Promise<AvailableEffect[]> {
  const res = await fetch(`${API_BASE}/effects/available`)
  if (!res.ok) throw new Error('Failed to fetch effects')
  const data = await res.json()
  return data.effects
}

export async function fetchProfileEffects(profileId: string): Promise<EffectConfig[] | null> {
  const res = await fetch(`${API_BASE}/profiles/${profileId}`)
  if (!res.ok) throw new Error('Failed to fetch profile')
  const data = await res.json()
  return data.effects_chain || null
}

export async function updateProfileEffects(profileId: string, effectsChain: EffectConfig[] | null): Promise<VoiceProfile> {
  const res = await fetch(`${API_BASE}/profiles/${profileId}/effects`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ effects_chain: effectsChain })
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Failed to update effects')
  }
  return res.json()
}