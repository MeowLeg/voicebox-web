const PROXY = '/api/v1'

export interface VoiceProfile {
  id: string
  name: string
  language: string
  description?: string
  created_at: string
}

export interface GenerationRequest {
  profile_id: string
  text: string
  language?: string
  seed?: number
  model_size?: string
  instruct?: string
  engine?: string
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

export async function fetchProfiles(signal?: AbortSignal): Promise<VoiceProfile[]> {
  const res = await fetch(`${PROXY}?path=profiles`, { signal })
  if (!res.ok) throw new Error('Failed to fetch profiles')
  return res.json()
}

export interface CreateProfileRequest {
  name: string
  description?: string
  language?: string
  voice_type?: 'cloned' | 'preset' | 'designed'
  preset_engine?: string
  preset_voice_id?: string
  design_prompt?: string
  default_engine?: string
}

export async function createProfile(req: CreateProfileRequest): Promise<VoiceProfile> {
  const res = await fetch(`${PROXY}?path=profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Failed to create profile')
  }
  return res.json()
}

export async function generateSpeech(req: GenerationRequest, signal?: AbortSignal): Promise<GenerationResponse> {
  const res = await fetch(`${PROXY}?path=generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal,
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || 'Generation failed')
  }
  const data = await res.json()
  console.log('generateSpeech response:', data)
  return data
}

export async function getGenerationStatus(id: string): Promise<GenerationResponse> {
  const res = await fetch(`${PROXY}?path=generate/${id}/status`)
  if (!res.ok) throw new Error('Failed to get status')
  return res.json()
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

export async function fetchHistory(limit = 50): Promise<HistoryItem[]> {
  const res = await fetch(`${PROXY}?path=history?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch history')
  const data = await res.json()
  return data.items || []
}

export async function deleteHistoryItem(id: string): Promise<void> {
  const res = await fetch(`${PROXY}?path=history/${id}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('Failed to delete history item')
}

export interface ModelInfo {
  model_name: string
  display_name: string
  hf_repo_id: string
  downloaded: boolean
  downloading: boolean
  size_mb: number | null
  loaded: boolean
}

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${PROXY}?path=models/status`)
  if (!res.ok) throw new Error('Failed to fetch models')
  const data = await res.json()
  return data.models || []
}

export async function downloadModel(modelName: string): Promise<void> {
  const res = await fetch(`${PROXY}?path=models/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_name: modelName }),
  })
  if (!res.ok) throw new Error('Failed to download model')
}

export async function loadModel(modelSize: string): Promise<void> {
  const res = await fetch(`${PROXY}?path=models/load?model_size=${modelSize}`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error('Failed to load model')
}

export function getAudioUrl(id: string): string {
  return `/api/audio/${id}`
}

export async function waitForCompletion(id: string, intervalMs = 1000, maxAttempts = 300, signal?: AbortSignal): Promise<GenerationResponse> {
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
            console.error(`Chunk ${i}: No data chunk found, using fallback`)
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

function readUint16(view: DataView, offset: number): number {
  return view.getUint16(offset, true)
}
