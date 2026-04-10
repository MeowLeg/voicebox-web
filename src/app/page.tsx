'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchProfiles, generateSpeech, waitForCompletion, getAudioUrl, splitText, concatWavBlobs, fetchHistory, deleteHistoryItem, fetchModels, downloadModel, loadModel, type VoiceProfile, type GenerationResponse, type ModelInfo } from '@/lib/api'

const STATUS_LABELS: Record<string, string> = {
  pending: '排队中',
  processing: '生成中',
  completed: '已完成',
  failed: '失败',
}

const INSTRUCT_OPTIONS = [
  { label: '默认', value: '' },
  { label: '缓慢清晰', value: 'Speak slowly and clearly' },
  { label: '新闻播报', value: 'Read like a news broadcaster' },
  { label: '讲故事', value: 'Tell a story with emotion' },
  { label: '正式朗读', value: 'Read formally and professionally' },
]

function formatDate(iso?: string): string {
  if (!iso) return ''
  const date = new Date(iso)
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai',
  })
  return formatter.format(date).replace(/\//g, '-')
}

function formatTime(iso?: string): string {
  if (!iso) return '未知'
  const date = new Date(iso)
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai',
  })
  return formatter.format(date)
}

function todayStr(): string {
  const now = new Date()
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'Asia/Shanghai',
  })
  return formatter.format(now).replace(/\//g, '-')
}

async function audioBufferToWav(buffer: AudioBuffer): Promise<Blob> {
  const numChannels = buffer.numberOfChannels
  const sampleRate = buffer.sampleRate
  const format = 1 // PCM
  const bitDepth = 16
  
  const bytesPerSample = bitDepth / 8
  const blockAlign = numChannels * bytesPerSample
  const dataSize = buffer.length * blockAlign
  const headerSize = 44
  const totalSize = headerSize + dataSize
  
  const arrayBuffer = new ArrayBuffer(totalSize)
  const view = new DataView(arrayBuffer)
  
  // RIFF header
  writeString(view, 0, 'RIFF')
  view.setUint32(4, totalSize - 8, true)
  writeString(view, 8, 'WAVE')
  // fmt chunk
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true) // chunk size
  view.setUint16(20, format, true)
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * blockAlign, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, bitDepth, true)
  // data chunk
  writeString(view, 36, 'data')
  view.setUint32(40, dataSize, true)
  
  // Write audio data
  let offset = 44
  for (let i = 0; i < buffer.length; i++) {
    for (let ch = 0; ch < numChannels; ch++) {
      const sample = buffer.getChannelData(ch)[i]
      const clipped = Math.max(-1, Math.min(1, sample))
      view.setInt16(offset, clipped * 0x7FFF, true)
      offset += 2
    }
  }
  
  return new Blob([arrayBuffer], { type: 'audio/wav' })
}

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}

interface Article {
  AUTHOR: string
  CHNLDESC: string
  DOCSTATUS: number
  DOCTYPE: number
  METADATAID: number
  PUBDATE: string
  TITLE: string
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
  articleTitle?: string
  fullText?: string
  generateTime?: number
}

export default function Home() {
  const [profiles, setProfiles] = useState<VoiceProfile[]>([])
  const [selectedProfile, setSelectedProfile] = useState('')
  const [text, setText] = useState('')
  const [language, setLanguage] = useState('zh')
  const [modelSize, setModelSize] = useState('qwen-1.7B')
  const [instruct, setInstruct] = useState('')
  const [loading, setLoading] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [elapsedTime, setElapsedTime] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [currentAudio, setCurrentAudio] = useState<HistoryItem | null>(null)
  const [currentAudioBlob, setCurrentAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [articles, setArticles] = useState<Article[]>([])
  const [articlesLoading, setArticlesLoading] = useState(false)
  const [beginDate, setBeginDate] = useState(todayStr())
  const [endDate, setEndDate] = useState(todayStr())
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const loadProfiles = useCallback(async () => {
    try {
      const data = await fetchProfiles()
      setProfiles(data)
      setBackendOnline(true)
      if (data.length > 0 && !selectedProfile) {
        setSelectedProfile(data[0].id)
      }
    } catch {
      setBackendOnline(false)
    }
  }, [selectedProfile])

  const loadHistory = useCallback(async () => {
    try {
      const items = await fetchHistory(50)
      console.log('loadHistory:', items.length, 'items')
      setHistory(items)
    } catch (err) {
      console.error('loadHistory error:', err)
    }
  }, [])

  const [showProfileModal, setShowProfileModal] = useState(false)
  const [showModelsModal, setShowModelsModal] = useState(false)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [modelsLoading, setModelsLoading] = useState(false)
  const [profileStep, setProfileStep] = useState<'form' | 'record'>('form')
  const [newProfileName, setNewProfileName] = useState('')
  const [newProfileLanguage, setNewProfileLanguage] = useState('zh')
  const [newProfileDesc, setNewProfileDesc] = useState('')
  const [newProfileVoiceType, setNewProfileVoiceType] = useState<'cloned' | 'preset' | 'designed'>('cloned')
  const [newProfileEngine, setNewProfileEngine] = useState('')
  const [newProfileVoiceId, setNewProfileVoiceId] = useState('')
  const [newProfileText, setNewProfileText] = useState('')
  const [newProfileAudio, setNewProfileAudio] = useState<Blob | null>(null)
  const [recording, setRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [creatingProfile, setCreatingProfile] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)

  const handleCreateProfile = async () => {
    if (!newProfileName.trim()) {
      setProfileError('请输入音色名称')
      return
    }
    if (newProfileVoiceType === 'cloned') {
      setProfileStep('record')
      return
    }
    await createProfileWithAudio()
  }

  const createProfileWithAudio = async () => {
    setCreatingProfile(true)
    setProfileError(null)
    try {
      console.log('Creating profile...')
      const profileRes = await fetch(`${process.env.NEXT_PUBLIC_API_PROXY || '/api/proxy'}?path=profiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newProfileName.trim(),
          description: newProfileDesc.trim() || undefined,
          language: newProfileLanguage,
          voice_type: newProfileVoiceType,
          ...(newProfileVoiceType === 'preset' && {
            preset_engine: newProfileEngine || undefined,
            preset_voice_id: newProfileVoiceId || undefined,
          }),
        }),
      })
      
      if (!profileRes.ok) {
        const err = await profileRes.json()
        throw new Error(err.detail || err.error || '创建profile失败')
      }
      
      const profileData = await profileRes.json()
      console.log('Profile created:', profileData)

      if (newProfileVoiceType === 'cloned' && newProfileAudio && profileData.id) {
        console.log('Uploading sample...', newProfileAudio.size, newProfileAudio.type)
        const sampleFormData = new FormData()
        sampleFormData.append('file', newProfileAudio, 'sample.wav')
        sampleFormData.append('reference_text', newProfileText.trim())
        
        const sampleRes = await fetch(`${process.env.NEXT_PUBLIC_API_PROXY || '/api/proxy'}?path=profiles/${profileData.id}/samples`, {
          method: 'POST',
          body: sampleFormData,
        })
        console.log('Sample upload response:', sampleRes.status)
        
        const sampleData = await sampleRes.json()
        console.log('Sample data:', sampleData)
        
        if (!sampleRes.ok || sampleData.error || sampleData.detail) {
          throw new Error(sampleData.detail || sampleData.error || '上传样本失败')
        }
      }

      await loadProfiles()
      setSelectedProfile(profileData.id)
      setShowProfileModal(false)
      setNewProfileName('')
      setNewProfileLanguage('zh')
      setNewProfileDesc('')
      setNewProfileVoiceType('cloned')
      setNewProfileEngine('')
      setNewProfileVoiceId('')
      setNewProfileText('')
      setNewProfileAudio(null)
      setProfileStep('form')
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setCreatingProfile(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const chunks: Blob[] = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        
        // 转换为 WAV 格式
        const arrayBuffer = await audioBlob.arrayBuffer()
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
        const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer)
        
        const wavBlob = await audioBufferToWav(audioBuffer)
        setNewProfileAudio(wavBlob)
        stream.getTracks().forEach(t => t.stop())
      }

      recorder.start()
      setMediaRecorder(recorder)
      setRecording(true)
    } catch {
      setProfileError('无法访问麦克风，请检查权限')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && recording) {
      mediaRecorder.stop()
      setRecording(false)
    }
  }

  const handleAudioUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      try {
        const arrayBuffer = await file.arrayBuffer()
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
        const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer)
        const wavBlob = await audioBufferToWav(audioBuffer)
        setNewProfileAudio(wavBlob)
      } catch {
        // 如果转换失败，直接使用原文件
        setNewProfileAudio(file)
      }
    }
  }

  useEffect(() => {
    if (currentAudioBlob) {
      const url = URL.createObjectURL(currentAudioBlob)
      setAudioUrl(url)
      return () => URL.revokeObjectURL(url)
    } else {
      setAudioUrl(null)
    }
  }, [currentAudioBlob])

  useEffect(() => {
    loadProfiles()
  }, [loadProfiles])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  useEffect(() => {
    if (!loading) {
      setElapsedTime(0)
      return
    }
    const startTime = Date.now()
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [loading])

  const loadArticles = useCallback(async () => {
    setArticlesLoading(true)
    try {
      const params = new URLSearchParams({ siteId: '111', docstatus: '38' })
      if (beginDate) params.set('beginDate', beginDate)
      if (endDate) params.set('endDate', endDate)
      const res = await fetch(`/api/articles?${params.toString()}`)
      const json = await res.json()
      setArticles(json.data || [])
    } catch {
      setArticles([])
    } finally {
      setArticlesLoading(false)
    }
  }, [beginDate, endDate])

  useEffect(() => {
    loadArticles()
  }, [loadArticles])

  const handleArticleClick = async (article: Article) => {
    if (loading) {
      setError('正在生成中，请稍候...')
      return
    }
    setSelectedArticle(article)
    setCurrentAudio(null)
    setCurrentAudioBlob(null)
    setError(null)
    setSuccess(false)
    try {
      const res = await fetch(`/api/article-detail?metadataId=${article.METADATAID}`)
      const json = await res.json()
      if (json.data?.CONTENT) {
        setText(json.data.CONTENT)
      } else {
        setText(article.TITLE)
      }
    } catch (err) {
      setText(article.TITLE)
      console.error('获取文章详情失败:', err)
    }
  }

  const handleGenerate = async () => {
    if (!selectedProfile || !text.trim()) return
    
    if (abortRef.current) {
      abortRef.current.abort()
    }
    abortRef.current = new AbortController()
    const signal = abortRef.current.signal
    
    setLoading(true)
    setError(null)
    setStatusText('提交任务...')
    setCurrentAudio(null)
    setCurrentAudioBlob(null)
    setSuccess(false)
    const startTime = Date.now()
    try {
      const fullText = text.trim()
      const articleTitle = selectedArticle?.TITLE || fullText.slice(0, 30)
      const startIso = new Date(startTime).toISOString()

      setStatusText('提交任务...')

      const engine = modelSize.startsWith('qwen-') ? 'qwen' : modelSize
      const modelSizeVal = modelSize.startsWith('qwen-') ? modelSize.replace('qwen-', '') : undefined

      const result = await generateSpeech({
        profile_id: selectedProfile,
        text: fullText,
        language,
        engine,
        model_size: modelSizeVal,
        instruct: instruct || undefined,
      }, signal)

      console.log('generateSpeech result:', result)
      if (!result.id) {
        throw new Error('生成失败：无效的返回结果')
      }

      setStatusText('生成中...')

      const completed = await waitForCompletion(result.id, 1000, 600, signal)
      if (signal.aborted) return

      if (completed.status === 'failed') {
        setError(completed.error || '生成失败')
        setStatusText('')
        setSuccess(false)
      } else {
        const generateTime = Date.now() - startTime
        setCurrentAudio({
          ...completed,
          articleTitle,
          fullText,
          generateTime,
          created_at: startIso,
        })
        setStatusText('')
        setSuccess(true)
        loadHistory()
      }
    } catch (err) {
      console.error('Generation error:', err)
      if (!signal.aborted) {
        const errMsg = err instanceof Error ? err.message : '生成失败'
        setError(errMsg)
        setStatusText('')
        setSuccess(false)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleHistoryClick = (item: HistoryItem) => {
    console.log('handleHistoryClick:', item)
    if (item.status === 'completed') {
      setText(item.fullText || item.text || item.profile_name || '')
      setCurrentAudio(item)
      setCurrentAudioBlob(null)
      setSuccess(false)
      setLoading(false)
      setStatusText('')
      console.log('setCurrentAudio done, id:', item.id, 'status:', item.status)
    }
  }

  const handleDeleteHistory = async (id: string) => {
    if (!confirm('确定要删除这条记录吗？')) return
    try {
      await deleteHistoryItem(id)
      setHistory(prev => prev.filter(h => h.id !== id))
      if (currentAudio?.id === id) {
        setCurrentAudio(null)
        setCurrentAudioBlob(null)
      }
    } catch (err) {
      setError('删除失败')
    }
  }

  const handleDownloadModel = async (modelName: string) => {
    try {
      await downloadModel(modelName)
      const data = await fetchModels()
      setModels(data)
    } catch (err) {
      setError('下载失败')
    }
  }

  const handleLoadModel = async (modelName: string) => {
    let size = '1.7B'
    if (modelName.includes('0.6B') || modelName.includes('0.6')) {
      size = '0.6B'
    } else if (modelName.includes('1B')) {
      size = '1B'
    } else if (modelName.includes('3B')) {
      size = '3B'
    }
    try {
      await loadModel(size)
      const data = await fetchModels()
      setModels(data)
    } catch (err) {
      setError('加载失败')
    }
  }

  const handleDownload = async () => {
    if (!currentAudio) return
    try {
      let blob: Blob
      if (currentAudioBlob) {
        blob = currentAudioBlob
      } else {
        const res = await fetch(getAudioUrl(currentAudio.id))
        blob = await res.blob()
      }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `voicebox_${currentAudio.id.slice(0, 8)}.wav`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      setError('下载失败')
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold">舟传媒科技部TTS</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={async () => {
                console.log('Opening models modal')
                setShowModelsModal(true)
                setModelsLoading(true)
                try {
                  const data = await fetchModels()
                  console.log('Fetched models:', data.length)
                  setModels(data)
                  console.log('setModels called with', data.length, 'items')
                } catch (err) {
                  console.error('Failed to fetch models:', err)
                  setError('获取模型列表失败')
                } finally {
                  setModelsLoading(false)
                }
              }}
              className="text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
            >
              模型管理
            </button>
            <div className="flex items-center gap-2 text-sm">
              <span className={`w-2 h-2 rounded-full ${backendOnline === true ? 'bg-green-500' : backendOnline === false ? 'bg-red-500' : 'bg-yellow-500'}`} />
              <span className="text-zinc-500 dark:text-zinc-400">
                {backendOnline === true ? '后端已连接' : backendOnline === false ? '后端未连接' : '连接中...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6">
        <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 flex overflow-hidden" style={{ height: 'calc(100vh - 120px)' }}>
          {/* 左侧：文章选择 */}
          <div className="w-72 shrink-0 border-r border-zinc-200 dark:border-zinc-800 p-4 flex flex-col">
            <h2 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide shrink-0">文章选择</h2>
            <div className="shrink-0 mt-3">
              <label className="block text-xs text-zinc-400 mb-1">日期</label>
              <input
                type="date"
                value={beginDate}
                max={todayStr()}
                onChange={e => { setBeginDate(e.target.value); setEndDate(e.target.value); }}
                className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex-1 min-h-0 mt-3">
              <label className="block text-xs text-zinc-400 mb-1">
                文章 <span className="text-zinc-500">（{articles.length}）</span>
              </label>
              <div className="rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 h-full overflow-y-auto">
                {articlesLoading && (
                  <p className="px-3 py-4 text-xs text-zinc-400 text-center">加载中...</p>
                )}
                {!articlesLoading && articles.length === 0 && (
                  <p className="px-3 py-4 text-xs text-zinc-400 text-center">暂无文章</p>
                )}
                {articles.map((article, i) => (
                  <button
                    key={`${article.METADATAID}-${article.CHNLDESC}-${i}`}
                    onClick={() => handleArticleClick(article)}
                    className={`w-full text-left px-3 py-2.5 text-sm transition-colors border-b border-zinc-100 dark:border-zinc-700 last:border-b-0 hover:bg-zinc-50 dark:hover:bg-zinc-700 ${
                      selectedArticle?.METADATAID === article.METADATAID && selectedArticle?.CHNLDESC === article.CHNLDESC
                        ? 'bg-blue-50 dark:bg-blue-950'
                        : ''
                    }`}
                  >
                    <p className="font-medium leading-snug line-clamp-2">{article.TITLE}</p>
                    <p className="text-xs text-zinc-400 mt-0.5">
                      {article.CHNLDESC}
                      {article.AUTHOR && ` · ${article.AUTHOR}`}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 中间：语音合成 */}
          <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">语音配置</label>
                <div className="flex gap-2">
                  <select
                    value={selectedProfile}
                    onChange={e => setSelectedProfile(e.target.value)}
                    className="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {profiles.length === 0 && <option value="">未找到语音配置</option>}
                    {profiles.map(p => (
                      <option key={p.id} value={p.id}>{p.name} ({p.language})</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => {
                      setNewProfileName('')
                      setNewProfileLanguage('zh')
                      setNewProfileDesc('')
                      setNewProfileVoiceType('cloned')
                      setNewProfileEngine('')
                      setNewProfileVoiceId('')
                      setNewProfileText('')
                      setNewProfileAudio(null)
                      setProfileStep('form')
                      setProfileError(null)
                      setShowProfileModal(true)
                    }}
                    className="shrink-0 px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors"
                    title="新增音色"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1.5">合成文本</label>
                <textarea
                  value={text}
                  onChange={e => setText(e.target.value)}
                  placeholder="请输入或从左侧选择文章..."
                  rows={35}
                  maxLength={50000}
                  className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  style={{ minHeight: '700px' }}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">语言</label>
                  <select
                    value={language}
                    onChange={e => setLanguage(e.target.value)}
                    className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="zh">中文</option>
                    <option value="en">英语</option>
                    <option value="ja">日语</option>
                    <option value="ko">韩语</option>
                    <option value="fr">法语</option>
                    <option value="de">德语</option>
                    <option value="es">西班牙语</option>
                    <option value="it">意大利语</option>
                    <option value="pt">葡萄牙语</option>
                    <option value="ru">俄语</option>
                    <option value="ar">阿拉伯语</option>
                    <option value="hi">印地语</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">模型引擎</label>
                  <select
                    value={modelSize}
                    onChange={e => setModelSize(e.target.value)}
                    className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="qwen-0.6B">Qwen 0.6B（快）</option>
                    <option value="qwen-1.7B">Qwen 1.7B（高质量）</option>
                    <option value="chatterbox_turbo">Chatterbox Turbo</option>
                    <option value="chatterbox">Chatterbox</option>
                    <option value="luxtts">LuxTTS</option>
                    <option value="tada">TADA</option>
                    <option value="kokoro">Kokoro</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">风格指令</label>
                  <select
                    value={instruct}
                    onChange={e => setInstruct(e.target.value)}
                    className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {INSTRUCT_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {(statusText || loading) && (
                <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {statusText || '处理中...'}
                  {loading && ` ${elapsedTime}秒`}
                </div>
              )}

              {error && (
                <div className="rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">
                  {error}
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={loading || !selectedProfile || !text.trim() || backendOnline === false}
                className="w-full rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 dark:disabled:bg-zinc-700 text-white font-medium py-2.5 text-sm transition-colors disabled:cursor-not-allowed"
              >
                {loading ? '生成中...' : '生成语音'}
              </button>
              {!loading && text.length > 500 && (
                <p className="text-xs text-zinc-400 text-center">长文本将自动分段生成，预计耗时较长</p>
              )}
            </div>

            {/* 音频播放器 - 生成完成后显示 */}
            {currentAudio && (currentAudio.status === 'completed' || currentAudioBlob) && (
              <div className="px-6 pb-4">
                <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/50 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">
                      {success ? '生成完成' : '正在播放'}
                    </h2>
                    {success && (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 px-3 py-1 text-xs font-medium text-green-700 dark:text-green-300">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        已完成
                      </span>
                    )}
                  </div>
                  <audio 
                    controls 
                    src={audioUrl || (currentAudio.id ? getAudioUrl(currentAudio.id) : undefined)} 
                    className="w-full"
                    onLoadedMetadata={() => console.log('Audio loaded, duration:', currentAudio.duration)}
                    onError={(e) => console.log('Audio error:', e)}
                  />
                  <div className="flex items-center justify-between text-sm">
                    <div className="text-zinc-500 dark:text-zinc-400 space-y-1">
                      <p>时长：{currentAudio.duration ? `${currentAudio.duration.toFixed(1)}秒` : '未知'}</p>
                      <p>耗时：{currentAudio.generateTime ? `${(currentAudio.generateTime / 1000).toFixed(1)}秒` : '未知'}</p>
                    </div>
                    <button
                      onClick={handleDownload}
                      className="inline-flex items-center gap-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 px-4 py-2 text-sm font-medium transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v12m0 0l-4-4m4 4l4-4M4 18h16" />
                      </svg>
                      下载音频
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 新增音色弹窗 */}
            {showProfileModal && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 w-full max-w-md p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">
                      {profileStep === 'form' ? '新增音色' : '录制音频样本'}
                    </h3>
                    <button
                      onClick={() => { setShowProfileModal(false); setProfileStep('form'); }}
                      className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  
                  {profileStep === 'form' ? (
                    <>
                      <div>
                        <label className="block text-sm font-medium mb-1.5">音色名称 <span className="text-red-500">*</span></label>
                        <input
                          type="text"
                          value={newProfileName}
                          onChange={e => setNewProfileName(e.target.value)}
                          placeholder="请输入音色名称"
                          className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1.5">语言</label>
                        <select
                          value={newProfileLanguage}
                          onChange={e => setNewProfileLanguage(e.target.value)}
                          className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="zh">中文</option>
                          <option value="en">英语</option>
                          <option value="ja">日语</option>
                          <option value="ko">韩语</option>
                          <option value="de">德语</option>
                          <option value="fr">法语</option>
                          <option value="ru">俄语</option>
                          <option value="pt">葡萄牙语</option>
                          <option value="es">西班牙语</option>
                          <option value="it">意大利语</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1.5">音色类型</label>
                        <select
                          value={newProfileVoiceType}
                          onChange={e => setNewProfileVoiceType(e.target.value as 'cloned' | 'preset' | 'designed')}
                          className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="cloned">克隆音色（需录制样本）</option>
                          <option value="preset">预设音色</option>
                          <option value="designed">设计音色</option>
                        </select>
                      </div>

                      {newProfileVoiceType === 'preset' && (
                        <>
                          <div>
                            <label className="block text-sm font-medium mb-1.5">预设引擎</label>
                            <input
                              type="text"
                              value={newProfileEngine}
                              onChange={e => setNewProfileEngine(e.target.value)}
                              placeholder="例如: GPT-SoVITS"
                              className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1.5">预设音色ID</label>
                            <input
                              type="text"
                              value={newProfileVoiceId}
                              onChange={e => setNewProfileVoiceId(e.target.value)}
                              placeholder="请输入预设音色ID"
                              className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                        </>
                      )}

                      <div>
                        <label className="block text-sm font-medium mb-1.5">描述</label>
                        <textarea
                          value={newProfileDesc}
                          onChange={e => setNewProfileDesc(e.target.value)}
                          placeholder="可选描述"
                          rows={2}
                          className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="bg-zinc-50 dark:bg-zinc-800 rounded-lg p-4 space-y-3">
                        <p className="text-sm text-zinc-600 dark:text-zinc-300">
                          请录制一段 2-30 秒的清晰语音，用于训练您的专属音色。录音太短会被拒绝。
                        </p>
                        
                        <div className="flex items-center gap-3">
                          {recording ? (
                            <button
                              onClick={stopRecording}
                              className="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-medium flex items-center gap-2"
                            >
                              <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
                              停止录音
                            </button>
                          ) : (
                            <button
                              onClick={startRecording}
                              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium flex items-center gap-2"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                              </svg>
                              开始录音
                            </button>
                          )}
                          
                          <label className="px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-600 text-sm cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-700">
                            <span>上传音频</span>
                            <input
                              type="file"
                              accept="audio/*"
                              onChange={handleAudioUpload}
                              className="hidden"
                            />
                          </label>
                        </div>

                        {newProfileAudio && (
                          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                            音频已准备
                          </div>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1.5">参考文本 <span className="text-red-500">*</span></label>
                        <textarea
                          value={newProfileText}
                          onChange={e => setNewProfileText(e.target.value)}
                          placeholder="请输入录音中朗读的文本内容..."
                          rows={3}
                          className="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </>
                  )}

                  {profileError && (
                    <div className="text-sm text-red-500">{profileError}</div>
                  )}

                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={() => { setShowProfileModal(false); setProfileStep('form'); }}
                      className="flex-1 px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 text-sm font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                    >
                      取消
                    </button>
                    {profileStep === 'form' ? (
                      <button
                        onClick={handleCreateProfile}
                        className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
                      >
                        {newProfileVoiceType === 'cloned' ? '下一步' : '创建'}
                      </button>
                    ) : (
                      <button
                        onClick={createProfileWithAudio}
                        disabled={creatingProfile || !newProfileAudio || !newProfileText.trim()}
                        className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium transition-colors"
                      >
                        {creatingProfile ? '创建中...' : '创建音色'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 最右侧：历史记录 */}
          <div className="w-64 shrink-0 border-l border-zinc-200 dark:border-zinc-800 flex flex-col">
            <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
              <h2 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">历史记录</h2>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {history.length === 0 && (
                <p className="text-xs text-zinc-400 text-center py-8">暂无记录</p>
              )}
              {history.map(item => (
                <div
                  key={item.id}
                  className={`group relative rounded-lg border px-3 py-2 text-sm transition-colors ${
                    currentAudio?.id === item.id
                      ? 'border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-950'
                      : item.status !== 'completed'
                        ? 'border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 opacity-60'
                        : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-zinc-300 dark:hover:border-zinc-700'
                  }`}
                >
                  <button
                    onClick={() => handleHistoryClick(item)}
                    disabled={item.status !== 'completed'}
                    className="w-full text-left"
                  >
                    <p className="truncate font-medium text-xs leading-snug">{item.text?.slice(0, 30) || item.profile_name || ''}</p>
                    <p className="text-xs text-zinc-400 mt-1">
                      {item.status === 'completed' && item.duration ? `音频${item.duration.toFixed(1)}秒 · ` : ''}
                      {formatDate(item.created_at)}
                      {item.status !== 'completed' && ` · ${STATUS_LABELS[item.status] || item.status}`}
                    </p>
                  </button>
                  <button
                    onClick={() => handleDeleteHistory(item.id)}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 text-zinc-400 hover:text-red-500 transition-opacity"
                    title="删除"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* 模型管理弹窗 */}
      {showModelsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 w-full max-w-2xl p-6 space-y-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">模型管理</h3>
              <button
                onClick={() => setShowModelsModal(false)}
                className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {modelsLoading ? (
              <p className="text-center text-zinc-400 py-8">加载中...</p>
            ) : models.length === 0 ? (
              <p className="text-center text-zinc-400 py-8">暂无模型数据</p>
            ) : (
              <div className="space-y-2">
                {models.map(model => (
                  <div
                    key={model.model_name}
                    className="flex items-center justify-between p-3 rounded-lg border border-zinc-200 dark:border-zinc-700"
                  >
                    <div>
                      <p className="font-medium">{model.display_name}</p>
                      <p className="text-xs text-zinc-400">{model.hf_repo_id}</p>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      {model.loaded && (
                        <span className="px-2 py-1 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs">
                          已加载
                        </span>
                      )}
                      {model.downloaded ? (
                        <span className="text-zinc-400">
                          {model.size_mb ? `${(model.size_mb / 1024).toFixed(1)} GB` : '已下载'}
                        </span>
                      ) : model.downloading ? (
                        <span className="text-blue-500">下载中...</span>
                      ) : (
                        <button 
                          onClick={() => handleDownloadModel(model.model_name)}
                          className="text-blue-500 hover:underline"
                        >
                          下载
                        </button>
                      )}
                      {model.downloaded && !model.loaded && (
                        <button 
                          onClick={() => handleLoadModel(model.model_name)}
                          className="text-green-500 hover:underline"
                        >
                          加载
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
