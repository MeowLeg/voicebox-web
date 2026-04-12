<template>
  <div class="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
    <header class="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-4">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <h1 class="text-xl font-semibold">舟传媒科技部TTS</h1>
        <div class="flex items-center gap-4">
          <button
            @click="showModelsModal = true; loadModels()"
            class="text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
          >
            模型管理
          </button>
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full" :class="{
              'bg-green-500': backendOnline === true,
              'bg-red-500': backendOnline === false,
              'bg-yellow-500': backendOnline === null
            }"></span>
            <span class="text-xs text-zinc-400 dark:text-zinc-500">
              {{ backendOnline === true ? '后端已连接' : backendOnline === false ? '后端未连接' : '连接中...' }}
            </span>
          </div>
        </div>
      </div>
    </header>

    <main class="flex-1 max-w-7xl w-full mx-auto px-6 py-6">
      <div class="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 flex overflow-hidden" style="height: calc(100vh - 120px)">
        
        <!-- 左侧：文章选择 -->
        <div class="w-72 shrink-0 border-r border-zinc-200 dark:border-zinc-800 p-4 flex flex-col">
          <h2 class="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide shrink-0">文章选择</h2>
          
          <!-- News Type Tabs -->
          <div class="flex gap-1 mt-3 mb-2">
            <div
              @click="newsType = 'newspaper'"
              :class="['flex-1 py-1.5 text-xs text-center cursor-pointer', 
                newsType === 'newspaper' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 dark:text-zinc-400']"
            >
              报纸新闻
            </div>
            <div
              @click="newsType = 'tv'"
              :class="['flex-1 py-1.5 text-xs text-center cursor-pointer',
                newsType === 'tv' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 dark:text-zinc-400']"
            >
              电视新闻
            </div>
          </div>
          
          <div class="shrink-0 flex items-center gap-2">
            <label class="block text-xs text-zinc-400 mb-1">日期</label>
            <input
              type="date"
              v-model="beginDate"
              :max="todayStr()"
              @change="endDate = beginDate; loadArticles()"
              class="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              @click="loadArticles"
              :disabled="articlesLoading"
              class="p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-50"
              title="刷新"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
          </div>

          <div class="flex-1 overflow-y-auto mt-2 space-y-1">
            <div v-if="articlesLoading" class="text-sm text-zinc-400 text-center py-4">加载中...</div>
            <div v-else-if="error" class="text-sm text-red-500 text-center py-4">{{ error }}</div>
            <div v-else-if="articles.length === 0" class="text-sm text-zinc-400 text-center py-4">暂无文章</div>
            <div
              v-else
              v-for="article in articles"
              :key="article.ID || article.id"
              @click="handleArticleClick(article)"
              :class="[
                'w-full text-left px-3 py-2 rounded-lg text-sm truncate cursor-pointer',
                isSelected(article) ? 'text-zinc-900 dark:text-zinc-100 font-medium' : 'text-zinc-500 dark:text-zinc-400'
              ]"
            >
              {{ article.TITLE || article.title }}
            </div>
          </div>
        </div>

        <!-- 中间：内容编辑区 -->
        <div class="flex-1 flex flex-col p-4 min-w-0">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">
              {{ newsType === 'tv' ? '电视新闻' : '报纸新闻' }}内容
            </h2>
            <span v-if="selectedArticle" class="text-xs text-zinc-400">
              {{ selectedArticle.TITLE || selectedArticle.title }}
            </span>
          </div>

          <div class="mb-3 flex items-center gap-2">
            <label class="text-sm text-zinc-500 dark:text-zinc-400">音色:</label>
            <select
              v-model="selectedProfile"
              class="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
                {{ profile.name }}
              </option>
            </select>
            <button
              @click="showCreateProfileModal = true"
              class="px-2 py-1.5 text-sm rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700"
              title="新建音色"
            >
              +
            </button>
            <button
              @click="confirmDeleteProfile"
              :disabled="!selectedProfile || profiles.length === 0"
              class="px-2 py-1.5 text-sm rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-red-100 dark:hover:bg-red-900/30 disabled:opacity-50 disabled:hover:bg-zinc-100"
              title="删除音色"
            >
              <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>

          <!-- TV模式：分段选择 -->
          <div v-if="newsType === 'tv'" class="flex-1 flex flex-col min-h-0">
            <div v-if="tvNewsItemsLoading" class="flex-1 flex items-center justify-center text-zinc-400 text-sm">
              加载中...
            </div>
            <div v-else-if="tvParagraphs.length === 0" class="flex-1 flex items-center justify-center text-zinc-400 text-sm">
              请在左侧选择电视新闻稿件
            </div>
            <div v-else class="flex-1 overflow-y-auto space-y-2 pr-2">
              <div class="flex items-center gap-2 mb-2">
                <button
                  @click="selectAllTvParagraphs"
                  class="text-xs px-2 py-1 rounded bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                >
                  {{ tvParagraphs.filter(p => !p.isLabel).every(p => p.checked) ? '取消全选' : '全选' }}
                </button>
                <span class="text-xs text-zinc-400">
                  已选中 {{ checkedTvParagraphs.length }} 段，共 {{ getCheckedTvText.length }} 字符
                </span>
              </div>
              <template
                v-for="(p, idx) in tvParagraphs"
                :key="idx"
              >
                <div v-if="p.isLabel" class="text-sm font-medium text-blue-600 dark:text-blue-400 px-2 py-1">
                  {{ p.text }}
                </div>
                <div v-else class="flex gap-2 items-start">
                  <input
                    type="checkbox"
                    v-model="p.checked"
                    class="mt-1 shrink-0 w-4 h-4"
                  />
                  <div class="flex-1">
                    <div v-if="p.label" class="text-xs text-zinc-400 mb-1">{{ p.label }}</div>
                    <textarea
                      v-model="p.text"
                      @input="autoResize($event)"
                      class="tv-textarea w-full min-h-[24px] rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none overflow-hidden"
                    ></textarea>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- 报纸模式：文本框 -->
          <div v-else class="flex-1 flex flex-col min-h-0">
            <textarea
              v-model="text"
              class="flex-1 w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              :placeholder="selectedArticle ? '请输入要生成语音的文本' : '请在左侧选择报纸文章'"
              :disabled="!selectedArticle"
            ></textarea>
          </div>

          <!-- 参数配置 -->
          <div class="mt-3 flex flex-wrap items-center gap-3 text-sm">
            <div class="flex items-center gap-2">
              <label class="text-zinc-500 dark:text-zinc-400">语言:</label>
              <select
                v-model="language"
                class="rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="zh">中文</option>
                <option value="en">英文</option>
              </select>
            </div>

            <div class="flex items-center gap-2">
              <label class="text-zinc-500 dark:text-zinc-400">模型:</label>
              <select
                v-model="selectedModel"
                @change="handleModelChange"
                :disabled="loadingModel"
                class="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option v-for="m in models" :key="m.model_name" :value="m.model_name">
                  {{ m.display_name }}{{ m.loaded ? ' (已加载)' : '' }}
                </option>
              </select>
              <span v-if="loadingModel" class="text-xs text-blue-500">加载中...</span>
            </div>

            <div class="flex items-center gap-2">
              <label class="text-zinc-500 dark:text-zinc-400">语调:</label>
              <select
                v-model="tone"
                class="rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">正常</option>
                <option value="播音腔">播音腔</option>
                <option value="新闻播报">新闻播报</option>
                <option value="讲故事">讲故事</option>
                <option value="激动">激动</option>
                <option value="舒缓">舒缓</option>
              </select>
            </div>
          </div>

          <!-- 生成按钮 -->
          <div class="mt-3 flex items-center gap-3">
            <button
              @click="handleGenerate"
              :disabled="loading || !selectedProfile || (newsType === 'tv' ? getCheckedTvText.length === 0 : !text.trim()) || backendOnline === false"
              class="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 disabled:cursor-not-allowed text-white font-medium transition-colors"
            >
              {{ loading ? '生成中...' : '生成' }}
            </button>
            <button
              v-if="loading"
              @click="handleStop"
              class="px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              停止
            </button>
            <span v-if="loading" class="text-sm text-zinc-500">
              {{ statusText }} ({{ formatTime(elapsedTime) }})
            </span>
            <span v-if="error" class="text-sm text-red-500">{{ error }}</span>
          </div>

          <!-- 音频播放 -->
          <div v-if="currentAudio || currentAudioBlob" class="mt-3 flex items-center gap-3">
            <audio v-if="currentAudio" :src="currentAudio" controls class="flex-1"></audio>
            <audio v-else-if="currentAudioBlob" :src="URL.createObjectURL(currentAudioBlob)" controls class="flex-1"></audio>
            <a
              v-if="currentAudio"
              :href="currentAudio"
              download
              class="shrink-0 px-3 py-1.5 text-sm rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700"
            >
              下载
            </a>
            <span v-if="success" class="shrink-0 text-xs text-green-600 dark:text-green-400">
              生成成功
            </span>
          </div>
        </div>

        <!-- 右侧：历史记录 -->
        <div class="w-72 shrink-0 border-l border-zinc-200 dark:border-zinc-800 p-4 flex flex-col">
          <h2 class="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide shrink-0">历史记录</h2>
          <div class="flex-1 overflow-y-auto mt-2 space-y-2">
            <div v-if="historyLoading" class="text-sm text-zinc-400 text-center py-4">加载中...</div>
            <div v-else-if="history.length === 0" class="text-sm text-zinc-400 text-center py-4">暂无记录</div>
            <div
              v-else
              v-for="item in history"
              :key="item.id"
              class="relative p-2 rounded-lg bg-zinc-50 dark:bg-zinc-800 text-xs group"
            >
              <div
                class="cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded p-1 -m-1"
                @click="handleHistoryClick(item)"
              >
                <div class="truncate">{{ item.text }}</div>
                <div class="flex items-center gap-2 text-zinc-400 mt-1">
                  <span>{{ new Date(item.created_at).toLocaleString() }}</span>
                  <span v-if="item.duration" class="text-blue-500">{{ item.duration.toFixed(1) }}s</span>
                  <span v-if="item.status === 'failed'" class="text-red-500">失败</span>
                </div>
              </div>
              <button
                @click.stop="confirmDeleteHistory(item)"
                class="absolute top-1 right-1 p-1 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-opacity"
                title="删除"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 模型管理弹窗 -->
    <div v-if="showModelsModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModelsModal = false">
      <div class="bg-white dark:bg-zinc-900 rounded-xl p-6 w-[500px] max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">模型管理</h3>
          <button @click="showModelsModal = false" class="text-zinc-400 hover:text-zinc-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div v-if="modelsLoading" class="text-center py-4 text-zinc-400">加载中...</div>
        <div v-else class="space-y-3">
          <div
            v-for="model in models"
            :key="model.model_name"
            class="flex items-center justify-between p-3 rounded-lg border border-zinc-200 dark:border-zinc-700"
          >
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{{ model.display_name }}</div>
              <div class="text-xs text-zinc-400 mt-1">
                <span v-if="model.loaded" class="text-green-600">已加载</span>
                <span v-else-if="model.downloaded" class="text-yellow-600">已下载</span>
                <span v-else class="text-zinc-400">
                  {{ model.size_mb ? (model.size_mb / 1024).toFixed(1) + ' GB' : '' }}
                </span>
              </div>
            </div>
            <button
              v-if="!model.downloaded"
              @click="handleDownloadModel(model.model_name)"
              :disabled="model.downloading"
              class="px-3 py-1 text-sm rounded-lg border border-zinc-300 dark:border-zinc-600 hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-50"
            >
              {{ model.downloading ? '下载中...' : '下载' }}
            </button>
            <span v-else-if="!model.loaded" class="text-sm text-yellow-600">点击模型列表加载</span>
            <span v-else class="text-sm text-green-600"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建音色弹窗 -->
    <div v-if="showCreateProfileModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="closeCreateProfileModal">
      <div class="bg-white dark:bg-zinc-900 rounded-xl p-6 w-[500px] max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">新建音色</h3>
          <button @click="closeCreateProfileModal" class="text-zinc-400 hover:text-zinc-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">音色名称 *</label>
            <input
              v-model="newProfile.name"
              type="text"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="请输入音色名称"
            />
          </div>
          <div>
            <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">描述</label>
            <textarea
              v-model="newProfile.description"
              rows="2"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="可选描述"
            />
          </div>
          <div>
            <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">语言</label>
            <select
              v-model="newProfile.language"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="zh">中文</option>
              <option value="en">英文</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">音频 *</label>
            <div class="flex gap-2 mb-2">
              <button
                @click="toggleRecording"
                :class="[
                  'flex-1 px-3 py-2 text-sm rounded-lg border',
                  isRecording 
                    ? 'bg-red-100 border-red-300 text-red-600 dark:bg-red-900/30 dark:border-red-700 dark:text-red-400' 
                    : 'border-zinc-300 dark:border-zinc-600 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                ]"
              >
                {{ isRecording ? '停止录音' : '开始录音' }}
              </button>
              <button
                @click="triggerFileInput"
                class="flex-1 px-3 py-2 text-sm rounded-lg border border-zinc-300 dark:border-zinc-600 hover:bg-zinc-50 dark:hover:bg-zinc-800"
              >
                上传文件
              </button>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept="audio/*,.wav,.mp3,.m4a,.flac"
              class="hidden"
              @change="handleFileSelect"
            />
            <div
              v-if="newProfile.audioFile"
              class="text-sm text-green-600 dark:text-green-400 flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
              {{ newProfile.audioFile.name || '录音文件' }}
            </div>
            <div v-else class="text-xs text-zinc-400">
              建议10-30秒的清晰语音
            </div>
          </div>
          <div>
            <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">音频对应的文字 *</label>
            <textarea
              v-model="newProfile.referenceText"
              rows="3"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="请输入音频中朗读的文字内容"
            />
          </div>
          <div class="flex justify-end gap-2">
            <button
              @click="closeCreateProfileModal"
              class="px-4 py-2 text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            >
              取消
            </button>
            <button
              @click="handleCreateProfile"
              :disabled="creatingProfile || !canCreateProfile"
              class="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 text-white"
            >
              {{ creatingProfile ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { fetchProfiles, generateSpeech, getGenerationStatus, fetchHistory, fetchModels, downloadModel, loadModel, createProfile, uploadProfileSample, deleteProfile, deleteHistoryItem } from '@/api'
import { fetchPaperArticles, fetchTvNewsLists, fetchTvNewsDetail, fetchTvArticle, fetchArticleDetail } from '@/api'

const newsType = ref<'newspaper' | 'tv'>('newspaper')
const articles = ref<any[]>([])
const articlesLoading = ref(false)
const selectedArticle = ref<any>(null)
const beginDate = ref(new Date().toISOString().split('T')[0])
const endDate = ref(new Date().toISOString().split('T')[0])
const error = ref<string | null>(null)

const profiles = ref<any[]>([])
const selectedProfile = ref<string | null>(null)
const showModelsModal = ref(false)

const text = ref('')
const language = ref('zh')
const modelSize = ref('')
const selectedModel = ref('')
const loadingModel = ref(false)
const tone = ref('')

const loading = ref(false)
const statusText = ref('')
const elapsedTime = ref(0)
const currentAudio = ref<string | null>(null)
const currentAudioBlob = ref<Blob | null>(null)
const success = ref(false)
const backendOnline = ref<boolean | null>(null)
const loadingFromHistory = ref(false)
const showCreateProfileModal = ref(false)
const creatingProfile = ref(false)
const newProfile = ref({
  name: '',
  description: '',
  language: 'zh',
  audioFile: null as File | null,
  referenceText: ''
})
const fileInput = ref<HTMLInputElement | null>(null)
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedChunks = ref<Blob[]>([])
const audioContext = ref<AudioContext | null>(null)
const mediaStreamSource = ref<MediaStreamAudioSourceNode | null>(null)
const audioChunks = ref<Float32Array[]>([])
const recordingStartTime = ref(0)

const history = ref<any[]>([])
const historyLoading = ref(false)

const models = ref<any[]>([])
const modelsLoading = ref(false)

const loadedModels = computed(() => models.value.filter(m => m.loaded))

const abortController = ref<AbortController | null>(null)
let elapsedInterval: ReturnType<typeof setInterval> | null = null

function isSelected(article: any): boolean {
  if (!selectedArticle.value) return false
  if (newsType.value === 'tv') {
    return selectedArticle.value.docid === article.docid
  }
  const selectedId = selectedArticle.value.METADATAID || selectedArticle.value.ID || selectedArticle.value.id
  const articleId = article.METADATAID || article.ID || article.id
  return selectedId === articleId
}

interface TvParagraph {
  text: string
  checked: boolean
  isLabel?: boolean
  label?: string
}
const tvParagraphs = ref<TvParagraph[]>([])
const tvNewsItemsLoading = ref(false)

const checkedTvParagraphs = computed(() => {
  return tvParagraphs.value.filter(p => !p.isLabel && p.checked && p.text.trim())
})

const getCheckedTvText = computed(() => {
  return checkedTvParagraphs.value.map(p => p.text.trim()).join('\n')
})

function todayStr() {
  return new Date().toISOString().split('T')[0]
}

function selectAllTvParagraphs() {
  const contentParagraphs = tvParagraphs.value.filter(p => !p.isLabel)
  const allChecked = contentParagraphs.every(p => p.checked)
  tvParagraphs.value.forEach(p => { if (!p.isLabel) p.checked = !allChecked })
}

function autoResize(event: Event) {
  const textarea = event.target as HTMLTextAreaElement
  textarea.style.height = 'auto'
  textarea.style.height = textarea.scrollHeight + 'px'
}

function resizeAllTextareas() {
  nextTick(() => {
    const textareas = document.querySelectorAll('.tv-textarea')
    textareas.forEach((ta: any) => {
      ta.style.height = 'auto'
      ta.style.height = ta.scrollHeight + 'px'
    })
  })
}

async function loadProfiles() {
  try {
    profiles.value = await fetchProfiles()
    if (profiles.value.length > 0 && !selectedProfile.value) {
      selectedProfile.value = profiles.value[0].id
    }
  } catch (err) {
    console.error('Failed to load profiles:', err)
  }
}

async function handleCreateProfile() {
  if (!newProfile.value.name.trim() || !newProfile.value.audioFile || !newProfile.value.referenceText.trim()) return
  creatingProfile.value = true
  try {
    const profile = await createProfile({
      name: newProfile.value.name.trim(),
      description: newProfile.value.description.trim() || undefined,
      language: newProfile.value.language,
    })
    await uploadProfileSample(profile.id, newProfile.value.audioFile, newProfile.value.referenceText.trim())
    await loadProfiles()
    selectedProfile.value = profile.id
    closeCreateProfileModal()
  } catch (err) {
    console.error('Failed to create profile:', err)
  } finally {
    creatingProfile.value = false
  }
}

async function confirmDeleteProfile() {
  if (!selectedProfile.value) return
  const profileName = profiles.value.find(p => p.id === selectedProfile.value)?.name || ''
  if (!confirm(`确定要删除音色"${profileName}"吗？此操作不可恢复。`)) return
  try {
    await deleteProfile(selectedProfile.value)
    await loadProfiles()
    if (profiles.value.length > 0) {
      selectedProfile.value = profiles.value[0].id
    } else {
      selectedProfile.value = null
    }
  } catch (err) {
    console.error('Failed to delete profile:', err)
    alert('删除失败: ' + (err as Error).message)
  }
}

async function confirmDeleteHistory(item: any) {
  if (!confirm('确定要删除此历史记录吗？')) return
  try {
    await deleteHistoryItem(item.id)
    await loadHistory()
    if (currentAudio.value?.includes(item.id)) {
      currentAudio.value = null
    }
  } catch (err) {
    console.error('Failed to delete history:', err)
    alert('删除失败: ' + (err as Error).message)
  }
}

function closeCreateProfileModal() {
  showCreateProfileModal.value = false
  if (isRecording.value) {
    isRecording.value = false
    if (audioContext.value) {
      audioContext.value.close()
    }
    const stream = (mediaRecorder.value as any)?.getAudioTracks?.()?.[0]
    if (stream) {
      stream.stop()
    }
    audioChunks.value = []
  }
  newProfile.value = {
    name: '',
    description: '',
    language: 'zh',
    audioFile: null,
    referenceText: ''
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    newProfile.value.audioFile = input.files[0]
  }
}

function handleFileDrop(event: DragEvent) {
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    newProfile.value.audioFile = event.dataTransfer.files[0]
  }
}

const canCreateProfile = computed(() => {
  return newProfile.value.name.trim() && newProfile.value.audioFile && newProfile.value.referenceText.trim()
})

async function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContext.value = new AudioContext({ sampleRate: 24000 })
    mediaStreamSource.value = audioContext.value.createMediaStreamSource(stream)
    
    const scriptProcessor = audioContext.value.createScriptProcessor(4096, 1, 1)
    mediaStreamSource.value.connect(scriptProcessor)
    scriptProcessor.connect(audioContext.value.destination)
    
    audioChunks.value = []
    
    scriptProcessor.onaudioprocess = (event) => {
      if (isRecording.value) {
        const inputData = event.inputBuffer.getChannelData(0)
        audioChunks.value.push(new Float32Array(inputData))
      }
    }
    
    recordingStartTime.value = Date.now()
    isRecording.value = true
    
    mediaRecorder.value = stream as any
  } catch (err) {
    console.error('Failed to start recording:', err)
  }
}

function stopRecording() {
  if (isRecording.value && audioContext.value && mediaStreamSource.value) {
    mediaStreamSource.value.disconnect()
    audioContext.value.close()
    
    const stream = (mediaRecorder.value as any)?.getAudioTracks?.()?.[0]
    if (stream) {
      stream.stop()
    }
    
    const wavBlob = createWavBlob(audioChunks.value, 24000)
    const file = new File([wavBlob], 'recording.wav', { type: 'audio/wav' })
    newProfile.value.audioFile = file
    
    isRecording.value = false
    audioChunks.value = []
  }
}

function createWavBlob(chunks: Float32Array[], sampleRate: number): Blob {
  const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0)
  const buffer = new ArrayBuffer(44 + totalLength * 2)
  const view = new DataView(buffer)
  
  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }
  
  writeString(0, 'RIFF')
  view.setUint32(4, 36 + totalLength * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, totalLength * 2, true)
  
  let offset = 44
  for (const chunk of chunks) {
    for (let i = 0; i < chunk.length; i++) {
      const sample = Math.max(-1, Math.min(1, chunk[i]))
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
      offset += 2
    }
  }
  
  return new Blob([buffer], { type: 'audio/wav' })
}

async function loadHistory() {
  try {
    historyLoading.value = true
    history.value = await fetchHistory()
  } catch (err) {
    console.error('Failed to load history:', err)
  } finally {
    historyLoading.value = false
  }
}

async function loadModels() {
  try {
    modelsLoading.value = true
    models.value = await fetchModels()
    if (!selectedModel.value) {
      const loaded = models.value.find(m => m.loaded)
      selectedModel.value = loaded?.model_name || models.value[0]?.model_name || ''
    }
    updateModelSize()
  } catch (err) {
    console.error('Failed to load models:', err)
  } finally {
    modelsLoading.value = false
  }
}

function updateModelSize() {
  const model = models.value.find(m => m.model_name === selectedModel.value)
  modelSize.value = model ? getModelSize(model.model_name) : ''
}

async function handleModelChange() {
  updateModelSize()
  const model = models.value.find(m => m.model_name === selectedModel.value)
  if (model && !model.loaded) {
    loadingModel.value = true
    try {
      await loadModel(getModelSize(model.model_name))
      await loadModels()
    } catch (err) {
      console.error('Load model error:', err)
    } finally {
      loadingModel.value = false
    }
  }
}

async function handleDownloadModel(modelName: string) {
  try {
    await downloadModel(modelName)
    await loadModels()
  } catch (err) {
    console.error('Download model error:', err)
  }
}

function getModelSize(modelName: string): string {
  const match = modelName.match(/(\d+\.?\d*B)/i)
  return match ? match[1] : modelName
}

async function handleLoadModel(modelName: string) {
  try {
    await loadModel(getModelSize(modelName))
    await loadModels()
  } catch (err) {
    console.error('Load model error:', err)
  }
}

async function handleHistoryClick(item: any) {
  currentAudioBlob.value = null
  success.value = false
  selectedArticle.value = null
  loadingFromHistory.value = true
  newsType.value = 'newspaper'
  
  await nextTick()
  
  let audioId = ''
  if (item.versions && item.versions.length > 0) {
    const defaultVersion = item.versions.find((v: any) => v.is_default) || item.versions[0]
    audioId = defaultVersion.audio_path.split('/').pop()?.replace('.wav', '') || ''
  } else if (item.audio_path) {
    audioId = item.audio_path.split('/').pop()?.replace('.wav', '') || ''
  }
  
  if (audioId) {
    currentAudio.value = `/voicebox-web/audio/${audioId}`
    text.value = item.text
    tvParagraphs.value = []
    nextTick(() => {
      loadingFromHistory.value = false
    })
  } else {
    currentAudio.value = null
    loadingFromHistory.value = false
  }
}

async function checkBackend() {
  try {
    const res = await fetch('/voicebox-web/')
    if (res.ok) {
      backendOnline.value = true
    } else {
      backendOnline.value = false
    }
  } catch {
    backendOnline.value = false
  }
}

onMounted(() => {
  loadProfiles()
  loadHistory()
  loadArticles()
  loadModels()
  checkBackend()
  setInterval(checkBackend, 30000)
})

onUnmounted(() => {
  if (elapsedInterval) clearInterval(elapsedInterval)
})

async function loadArticles() {
  if (articlesLoading.value) return
  articlesLoading.value = true
  error.value = null
  try {
    if (newsType.value === 'newspaper') {
      const res = await fetchPaperArticles({ siteId: '111', docstatus: '38', beginDate: beginDate.value, endDate: endDate.value })
      const seen = new Set()
      articles.value = (res || []).filter((article: any) => {
        const id = article.METADATAID
        if (seen.has(id)) return false
        seen.add(id)
        return true
      })
    } else {
      const startDate = beginDate.value
      const nextDay = new Date(beginDate.value)
      nextDay.setDate(nextDay.getDate() + 1)
      const endDate = nextDay.toISOString().split('T')[0]
      const res = await fetchTvNewsLists(startDate, endDate, '590f6b165afa45f1bd8fc1ed31756fb7')
      const lists = res.data || []
      
      const allItems: any[] = []
      for (const list of lists) {
        try {
          const detailRes = await fetchTvNewsDetail(list.id)
          if (detailRes.success && detailRes.data && detailRes.data.detail && detailRes.data.detail.list && detailRes.data.detail.list.parentList) {
            const items = detailRes.data.detail.list.parentList
              .filter((item: any) => item.doc?.id && item.doc?.title)
              .map((item: any) => ({
                docid: item.doc.id,
                title: item.doc.title,
                docsubtype: item.doc.docsubtype,
                docsubtypename: item.doc.docsubtypename
              }))
            allItems.push(...items)
          }
        } catch (err) {
          console.error(`获取串联单 ${list.id} 详情失败:`, err)
        }
      }
      articles.value = allItems
    }
  } catch (err) {
    articles.value = []
    error.value = '加载文章列表失败'
    console.error(err)
  } finally {
    articlesLoading.value = false
  }
}

async function handleArticleClick(article: any) {
  console.log('Clicked article:', article)
  selectedArticle.value = article
  currentAudio.value = null
  currentAudioBlob.value = null
  success.value = false
  
  if (newsType.value === 'tv') {
    tvParagraphs.value = [{ text: '加载中...', checked: true }]
    try {
      const res = await fetchTvArticle(article.docid.toString())
      console.log('TV文章详情 response:', res)
      
      let content = ''
      if (res.success && res.data && res.data.content) {
        content = res.data.content
      }
      
      if (content) {
        const parts = content.split(/(?=【[^】]+】)/).filter((p: string) => p.trim())
        tvParagraphs.value = parts.map((p: string) => {
          const trimmed = p.trim()
          const isLabel = /^【[^】]+】$/.test(trimmed)
          if (isLabel) {
            return { text: trimmed, checked: false, isLabel: true }
          }
          const labelMatch = trimmed.match(/^(【[^】]+】)\s*/)
          if (labelMatch) {
            const isZhengwen = labelMatch[1] === '【正文】'
            return { 
              label: labelMatch[1], 
              text: trimmed.slice(labelMatch[0].length).trim(), 
              checked: isZhengwen, 
              isLabel: false 
            }
          }
          return { text: trimmed, checked: false, isLabel: false }
        })
      } else {
        tvParagraphs.value = []
      }
      resizeAllTextareas()
    } catch (err) {
      console.error('获取TV文章详情失败:', err)
      tvParagraphs.value = []
    }
  } else {
    text.value = '加载中...'
    
    const metadataId = article.METADATAID || article.ID || article.id
    console.log('Using metadataId:', metadataId)
    
    try {
      const res = await fetchArticleDetail(metadataId)
      console.log('文章详情 response:', res)
      
      let content = ''
      if (res.success && res.data) {
        content = res.data.CONTENT || res.data.content || ''
        console.log('Extracted content length:', content.length)
      } else {
        console.error('获取文章详情失败:', res.errMsg)
        content = article.TITLE || article.title || '无法获取文章内容'
      }
      
      text.value = content
    } catch (err) {
      text.value = article.TITLE || article.title || ''
      console.error('获取文章详情失败:', err)
    }
  }
}

async function waitForCompletion(id: string, signal: AbortSignal): Promise<any> {
  while (true) {
    if (signal.aborted) break
    const status = await getGenerationStatus(id)
    if (status.status === 'completed') {
      return status
    } else if (status.status === 'failed') {
      throw new Error(status.error || 'Generation failed')
    }
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
}

async function handleGenerate() {
  const targetText = newsType.value === 'tv' ? getCheckedTvText.value : text.value
  if (!selectedProfile.value || !targetText.trim()) return
  
  if (abortController.value) {
    abortController.value.abort()
  }
  abortController.value = new AbortController()
  const signal = abortController.value.signal
  
  loading.value = true
  error.value = null
  statusText.value = '提交任务...'
  currentAudio.value = null
  currentAudioBlob.value = null
  success.value = false
  const startTime = Date.now()
  elapsedTime.value = 0
  
  elapsedInterval = setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - startTime) / 1000)
  }, 1000)
  
  try {
    const result = await generateSpeech({
      profile_id: selectedProfile.value,
      text: targetText.trim(),
      language: language.value,
      model_size: modelSize.value,
      instruct: tone.value || undefined,
    }, signal)
    
    statusText.value = '等待生成完成...'
    const final = await waitForCompletion(result.id, signal)
    
    if (signal.aborted) return
    
    const audioId = final.id
    currentAudio.value = `/voicebox-web/audio/${audioId}`
    statusText.value = '完成!'
    success.value = true
    
    await loadHistory()
  } catch (err: any) {
    if (err.name === 'AbortError') {
      statusText.value = '已取消'
    } else {
      error.value = err.message || '生成失败'
      statusText.value = '失败'
    }
    console.error(err)
  } finally {
    loading.value = false
    if (elapsedInterval) {
      clearInterval(elapsedInterval)
      elapsedInterval = null
    }
  }
}

function handleStop() {
  if (abortController.value) {
    abortController.value.abort()
    statusText.value = '已取消'
    loading.value = false
    if (elapsedInterval) {
      clearInterval(elapsedInterval)
      elapsedInterval = null
    }
  }
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

watch(newsType, () => {
  loadArticles()
  text.value = ''
  tvParagraphs.value = []
  selectedArticle.value = null
  currentAudio.value = null
  currentAudioBlob.value = null
})

watch(text, () => {
  if (text.value && !selectedArticle.value && !loadingFromHistory.value) {
    currentAudio.value = null
    currentAudioBlob.value = null
    success.value = false
  }
})

watch(models, () => {
  if (models.value.length > 0 && !selectedModel.value) {
    const loaded = models.value.find(m => m.loaded)
    selectedModel.value = loaded?.model_name || models.value[0]?.model_name || ''
    updateModelSize()
  }
})
</script>