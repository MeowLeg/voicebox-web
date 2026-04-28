<template>
  <div class="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
    <!-- Toast 提示 -->
    <div
      v-if="toast.show"
      class="fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-lg shadow-lg text-white"
      :class="toast.type === 'error' ? 'bg-red-500' : toast.type === 'success' ? 'bg-green-500' : 'bg-blue-500'"
    >
      {{ toast.message }}
    </div>

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
          <div class="w-px h-5 bg-zinc-200 dark:bg-zinc-700"></div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-zinc-600 dark:text-zinc-300">{{ auth.user?.username }}</span>
            <button
              @click="auth.logout"
              class="text-sm text-zinc-500 dark:text-zinc-400 hover:text-red-600 dark:hover:text-red-400"
            >
              退出
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- 标签页导航 -->
    <div class="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <div class="max-w-7xl mx-auto px-6">
        <div class="flex gap-1">
          <button
            @click="activeTab = 'generate'"
            :class="['px-6 py-3 text-sm font-medium transition-colors',
              activeTab === 'generate' 
                ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400' 
                : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200']"
          >
            新闻生成
          </button>
          <button
            @click="activeTab = 'history'"
            :class="['px-6 py-3 text-sm font-medium transition-colors',
              activeTab === 'history' 
                ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400' 
                : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200']"
          >
            历史记录
          </button>
        </div>
      </div>
    </div>

    <main class="flex-1 max-w-7xl w-full mx-auto px-6 py-6">
      <!-- 新闻生成标签页 -->
      <div v-show="activeTab === 'generate'">

        <div class="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 flex overflow-hidden" style="height: calc(100vh - 180px)">
        
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
              @change="selectedProfileName = profiles.find(p => p.id === selectedProfile)?.name || null"
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
            <button
              @click="openEffectsModal"
              :disabled="!selectedProfile || profiles.length === 0"
              class="px-2 py-1.5 text-sm rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-blue-100 dark:hover:bg-blue-900/30 disabled:opacity-50 disabled:hover:bg-zinc-100"
              title="效果配置"
            >
              <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path>
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
               <label class="text-zinc-500 dark:text-zinc-400">模型:</label>
               <select
                 v-model="selectedModel"
                 @change="handleModelChange"
                 :disabled="loadingModel"
                 class="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option v-for="m in models" :key="m.model_name" :value="m.model_name">
                    {{ m.display_name }}{{ m.loaded ? ' (已加载)' : '' }}{{ m.supports_clone === false ? ' [固定音色]' : '' }}
                  </option>
                </select>
               <span v-if="loadingModel" class="text-xs text-blue-500">加载中...</span>
              </div>

              <div v-if="!currentModelSupportsClone && currentPresetVoices.length > 0" class="flex items-center gap-2">
                <label class="text-zinc-500 dark:text-zinc-400">音色:</label>
                <select
                  v-model="selectedVoiceId"
                  class="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option v-for="v in currentPresetVoices" :key="v.voice_id" :value="v.voice_id">
                    {{ v.name }} ({{ v.gender }}, {{ v.language }})
                  </option>
                </select>
              </div>

              <div class="flex items-center gap-2">
                <label class="text-zinc-500 dark:text-zinc-400">最大分段字符:</label>
               <input
                 type="number"
                 v-model.number="maxChunkChars"
                 min="100"
                 max="1000"
                 class="w-24 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
              </div>

              <div class="flex items-center gap-2">
                <label class="text-zinc-500 dark:text-zinc-400">语速:</label>
                <input
                  type="range"
                  v-model.number="selectedSpeed"
                  min="0.8"
                  max="1.2"
                  step="0.05"
                  class="w-24"
                />
                <span class="text-sm w-12 text-right">{{ selectedSpeed.toFixed(2) }}x</span>
              </div>
            </div>

           <!-- 生成按钮 -->
          <div class="mt-3 flex items-center gap-3">
            <button
              @click="handleGenerate"
              :disabled="loading || (currentModelSupportsClone ? !selectedProfile : !selectedVoiceId) || (newsType === 'tv' ? getCheckedTvText.length === 0 : !text.trim()) || backendOnline === false"
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
      </div>
      </div>

      <!-- 历史记录标签页 -->
      <div v-show="activeTab === 'history'" class="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 p-6" style="height: calc(100vh - 180px)">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold">历史记录</h2>
          <div class="text-sm text-zinc-400">共 {{ history.length }} 条记录</div>
        </div>
        <div class="h-full overflow-y-auto space-y-3">
          <div v-if="historyLoading" class="text-center py-12 text-zinc-400">加载中...</div>
          <div v-else-if="history.length === 0" class="text-center py-12 text-zinc-400">暂无记录</div>
          <div
            v-else
            v-for="item in history"
            :key="item.id"
            class="p-4 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800"
          >
            <div class="flex items-start gap-3">
              <div class="flex-1 min-w-0">
                <div 
                  class="text-sm mb-2"
                  :class="{ 'line-clamp-3': !item.expanded }"
                >
                  {{ item.text }}
                </div>
                <button
                  v-if="item.text.length > 100"
                  @click="item.expanded = !item.expanded"
                  class="text-xs text-blue-500 hover:text-blue-600"
                >
                  {{ item.expanded ? '收起' : '展开' }}
                </button>
                <div class="flex items-center gap-3 text-xs text-zinc-400">
                  <span>{{ new Date(new Date(item.created_at).getTime() + 8 * 60 * 60 * 1000).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }) }}</span>
                  <span v-if="item.duration" class="text-blue-500">{{ item.duration.toFixed(1) }}s</span>
                  <span v-if="item.status === 'failed'" class="text-red-500">失败</span>
                  <span v-else-if="item.status === 'completed'" class="text-green-500">成功</span>
                </div>
                
                <!-- 音频播放器 -->
                <div v-if="item.status === 'completed' && getHistoryAudioUrl(item)" class="mt-3">
                  <audio :src="getHistoryAudioUrl(item)" controls class="w-full" preload="none"></audio>
                </div>
              </div>
              
              <!-- 操作按钮 -->
              <div class="flex flex-col gap-2">
                <a
                  v-if="item.status === 'completed' && getHistoryAudioUrl(item)"
                  :href="getHistoryAudioUrl(item)"
                  download
                  class="p-2 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600 dark:text-green-400"
                  title="下载"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                  </svg>
                </a>
                <button
                  @click="confirmDeleteHistory(item)"
                  class="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
                  title="删除"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </button>
              </div>
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
                <span v-if="model.supports_clone" class="ml-2 text-blue-500">支持音色克隆</span>
                <span v-else class="ml-2 text-zinc-500">固定音色</span>
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

    <!-- 效果配置弹窗 -->
    <div
      v-if="showEffectsModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showEffectsModal = false"
    >
      <div class="bg-white dark:bg-zinc-900 rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <h3 class="text-lg font-semibold">效果配置</h3>
          <button @click="showEffectsModal = false" class="text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[calc(80vh-130px)]">
          <div v-if="effectsLoading" class="text-center py-8 text-zinc-500">加载中...</div>
          <div v-else class="space-y-6">
            <div v-for="effect in availableEffects" :key="effect.type" class="border border-zinc-200 dark:border-zinc-700 rounded-lg p-4">
              <div class="flex items-center gap-3 mb-3">
                <input
                  type="checkbox"
                  :id="'effect-' + effect.type"
                  :checked="isEffectEnabled(effect.type)"
                  @change="toggleEffect(effect.type)"
                  class="w-4 h-4 rounded"
                />
                <label :for="'effect-' + effect.type" class="font-medium cursor-pointer">
                  {{ effectLabels[effect.type] || effect.label }}
                </label>
              </div>
              <p class="text-sm text-zinc-500 mb-3">{{ effect.description }}</p>
              <div v-if="isEffectEnabled(effect.type)" class="grid grid-cols-2 gap-4">
                <div v-for="(param, paramKey) in effect.params" :key="paramKey" class="space-y-1">
                  <label class="text-xs text-zinc-500">{{ effectLabelsZh[effect.type]?.[String(paramKey)] || param.description }}</label>
            <div class="hidden">
              <label class="text-zinc-500 dark:text-zinc-400">语言:</label>
              <select
                v-model="language"
                class="rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="zh">中文</option>
                <option value="en">英文</option>
              </select>
            </div>

             <div class="hidden">
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

             <div class="flex items-center gap-2">
                    <template v-if="param.options">
                      <select
                        :value="getEffectParam(effect.type, String(paramKey))"
                        @change="setEffectParam(effect.type, String(paramKey), ($event.target as HTMLSelectElement).value)"
                        class="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option v-for="opt in param.options" :key="opt" :value="opt">{{ opt }}</option>
                      </select>
                    </template>
                    <template v-else>
                      <input
                        type="range"
                        :min="param.min"
                        :max="param.max"
                        :step="param.step"
                        :value="getEffectParam(effect.type, String(paramKey))"
                        @input="setEffectParam(effect.type, String(paramKey), Number(($event.target as HTMLInputElement).value))"
                        class="flex-1"
                      />
                      <span class="text-sm w-16 text-right">{{ getEffectParam(effect.type, String(paramKey)) }}</span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-zinc-200 dark:border-zinc-800 flex justify-end gap-2">
          <button
            @click="resetEffects"
            class="px-4 py-2 text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            重置
          </button>
          <button
            @click="saveEffects"
            :disabled="effectsLoading"
            class="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { fetchProfiles, generateSpeech, getGenerationStatus, fetchModels, downloadModel, loadModel, createProfile, uploadProfileSample, deleteProfile, fetchAvailableEffects, fetchProfileEffects, updateProfileEffects, fetchPresetVoices, createAudioRecord, listAudioRecords, deleteAudioRecord, type AvailableEffect, type EffectConfig } from '@/api'
import { fetchPaperArticles, fetchTvNewsLists, fetchTvNewsDetail, fetchTvArticle, fetchArticleDetail } from '@/api'
import { useAuth } from '@/composables/useAuth'

const auth = useAuth()

const activeTab = ref<'generate' | 'history'>('generate')
const newsType = ref<'newspaper' | 'tv'>('newspaper')
const articles = ref<any[]>([])
const articlesLoading = ref(false)
const selectedArticle = ref<any>(null)
const beginDate = ref(todayStr())
const endDate = ref(todayStr())
const error = ref<string | null>(null)
const toast = ref<{ show: boolean; message: string; type: 'error' | 'success' | 'info' }>({ show: false, message: '', type: 'info' })

function showToast(message: string, type: 'error' | 'success' | 'info' = 'info') {
  toast.value = { show: true, message, type }
  setTimeout(() => { toast.value.show = false }, 3000)
}

const profiles = ref<any[]>([])
const selectedProfile = ref<string | null>(null)
const selectedProfileName = ref<string | null>(null)
const showModelsModal = ref(false)

const text = ref('')
const language = ref('zh')
const selectedModel = ref('')
const selectedVoiceId = ref<string>('')
const selectedSpeed = ref<number>(1.0)
const presetVoices = ref<{ engine: string; voices: any[] }[]>([])
const loadingModel = ref(false)
const tone = ref('')
const maxChunkChars = ref(500)

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
const showEffectsModal = ref(false)
const availableEffects = ref<AvailableEffect[]>([])
const profileEffects = ref<EffectConfig[]>([])
const effectsLoading = ref(false)

const effectLabels: Record<string, string> = {
  chorus: '合唱/镶边',
  reverb: '混响',
  delay: '延迟',
  compressor: '压缩器',
  gain: '增益',
  highpass: '高通滤波',
  lowpass: '低通滤波',
  pitch_shift: '音调调整',
  speed: '语速'
}

const effectLabelsZh: Record<string, Record<string, string>> = {
  chorus: { rate_hz: '速度(Hz)', depth: '深度', feedback: '反馈', centre_delay_ms: '中心延迟(ms)', mix: '混合' },
  reverb: { room_size: '房间大小', damping: '阻尼', wet_level: '混响电平', dry_level: '干声电平', width: '宽度' },
  delay: { delay_seconds: '延迟时间(s)', feedback: '反馈', mix: '混合' },
  compressor: { threshold_db: '阈值(dB)', ratio: '压缩比', attack_ms: '启动时间(ms)', release_ms: '释放时间(ms)' },
  gain: { gain_db: '增益(dB)' },
  highpass: { cutoff_frequency_hz: '截止频率(Hz)' },
  lowpass: { cutoff_frequency_hz: '截止频率(Hz)' },
  pitch_shift: { semitones: '半音程' },
  speed: { speed: '倍率', algorithm: '算法' }
}

const newProfile = ref({
  name: '',
  description: '',
  language: 'zh',
  audioFile: null as File | null,
  referenceText: ''
})
const fileInput = ref<HTMLInputElement | null>(null)
const isRecording = ref(false)
const recordingStream = ref<MediaStream | null>(null)
const audioContext = ref<AudioContext | null>(null)
const scriptProcessor = ref<ScriptProcessorNode | null>(null)
const audioChunks = ref<Float32Array[]>([])

const history = ref<any[]>([])
const historyLoading = ref(false)

const models = ref<any[]>([])
const modelsLoading = ref(false)

const loadedModels = computed(() => models.value.filter(m => m.loaded))
const currentModelSupportsClone = computed(() => {
  const model = models.value.find(m => m.model_name === selectedModel.value)
  if (model?.supports_clone === true) return true
  if (model?.supports_clone === false) return false
  return true
})
const currentPresetVoices = computed(() => {
  const engine = getEngine(selectedModel.value)
  const preset = presetVoices.value.find(p => p.engine === engine)
  return preset?.voices || []
})

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
  const now = new Date()
  const offset = 8 * 60 * 60 * 1000
  const beijing = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) + offset)
  return beijing.getFullYear() + '-' +
    String(beijing.getMonth() + 1).padStart(2, '0') + '-' +
    String(beijing.getDate()).padStart(2, '0')
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
      selectedProfileName.value = profiles.value[0].name
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
    selectedProfileName.value = profile.name
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
      selectedProfileName.value = profiles.value[0].name
    } else {
      selectedProfile.value = null
      selectedProfileName.value = null
    }
  } catch (err) {
    console.error('Failed to delete profile:', err)
    alert('删除失败: ' + (err as Error).message)
  }
}

async function confirmDeleteHistory(item: any) {
  if (!confirm('确定要删除此历史记录吗？')) return
  
  try {
    await deleteAudioRecord(item.id)
    await loadHistory()
    if (currentAudio.value?.includes(item.id)) {
      currentAudio.value = null
    }
  } catch (err: any) {
    alert('删除失败: ' + err.message)
  }
}

function closeCreateProfileModal() {
  showCreateProfileModal.value = false
  if (isRecording.value) {
    stopRecording()
  }
  if (audioContext.value) {
    audioContext.value.close()
    audioContext.value = null
  }
  if (recordingStream.value) {
    recordingStream.value.getTracks().forEach(t => t.stop())
    recordingStream.value = null
  }
  audioChunks.value = []
  newProfile.value = {
    name: '',
    description: '',
    language: 'zh',
    audioFile: null,
    referenceText: ''
  }
}

async function openEffectsModal() {
  if (!selectedProfile.value) return
  showEffectsModal.value = true
  effectsLoading.value = true
  try {
    const [effects, profileEffs] = await Promise.all([
      fetchAvailableEffects(),
      fetchProfileEffects(selectedProfile.value)
    ])
    availableEffects.value = effects
    profileEffects.value = profileEffs || []
  } catch (err) {
    console.error('Failed to load effects:', err)
    showToast('加载效果失败', 'error')
    showEffectsModal.value = false
  } finally {
    effectsLoading.value = false
  }
}

function isEffectEnabled(type: string): boolean {
  return profileEffects.value.some(e => e.type === type)
}

function getEffectParam(type: string, paramKey: string): number {
  const effect = profileEffects.value.find(e => e.type === type)
  return (effect?.params?.[paramKey] as number) ?? 
    availableEffects.value.find(e => e.type === type)?.params?.[paramKey]?.default ?? 0
}

function toggleEffect(type: string) {
  const idx = profileEffects.value.findIndex(e => e.type === type)
  if (idx >= 0) {
    profileEffects.value.splice(idx, 1)
  } else {
    const effectDef = availableEffects.value.find(e => e.type === type)
    if (effectDef) {
      const params: Record<string, number> = {}
      for (const key in effectDef.params) {
        params[key] = effectDef.params[key].default
      }
      profileEffects.value.push({ type, params })
    }
  }
}

function setEffectParam(type: string, paramKey: string, value: number | string) {
  let effect = profileEffects.value.find(e => e.type === type)
  if (!effect) {
    effect = { type, params: {} }
    profileEffects.value.push(effect)
  }
  if (!effect.params) effect.params = {}
  effect.params[paramKey] = value
}

async function saveEffects() {
  if (!selectedProfile.value) return
  effectsLoading.value = true
  try {
    await updateProfileEffects(selectedProfile.value, profileEffects.value.length > 0 ? profileEffects.value : null)
    showEffectsModal.value = false
    showToast('效果保存成功', 'success')
  } catch (err) {
    console.error('Failed to save effects:', err)
    showToast('保存效果失败', 'error')
  } finally {
    effectsLoading.value = false
  }
}

function resetEffects() {
  profileEffects.value = []
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
    recordingStream.value = stream
    audioContext.value = new AudioContext({ sampleRate: 24000 })
    const source = audioContext.value.createMediaStreamSource(stream)
    
    const sp = audioContext.value.createScriptProcessor(4096, 1, 1)
    source.connect(sp)
    scriptProcessor.value = sp
    
    audioChunks.value = []
    
    sp.onaudioprocess = (event) => {
      if (isRecording.value) {
        const inputData = event.inputBuffer.getChannelData(0)
        audioChunks.value.push(new Float32Array(inputData))
      }
    }
    
    isRecording.value = true
  } catch (err) {
    console.error('Failed to start recording:', err)
  }
}

function stopRecording() {
  if (!isRecording.value) return
  
  isRecording.value = false
  
  if (scriptProcessor.value) {
    scriptProcessor.value.disconnect()
    scriptProcessor.value = null
  }
  if (audioContext.value) {
    audioContext.value.close()
    audioContext.value = null
  }
  if (recordingStream.value) {
    recordingStream.value.getTracks().forEach(t => t.stop())
    recordingStream.value = null
  }
  
  if (audioChunks.value.length > 0) {
    const wavBlob = createWavBlob(audioChunks.value, 24000)
    const file = new File([wavBlob], 'recording.wav', { type: 'audio/wav' })
    newProfile.value.audioFile = file
  }
  audioChunks.value = []
}

function createWavBlob(chunks: Float32Array[], sampleRate: number): Blob {
  let maxGain = 1.0
  for (const chunk of chunks) {
    for (let i = 0; i < chunk.length; i++) {
      const abs = Math.abs(chunk[i])
      if (abs > maxGain) maxGain = abs
    }
  }
  const gain = maxGain > 0.95 ? 0.9 / maxGain : 1.0
  
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
  view.setUint32(28, sampleRate * numChannels * (bitsPerSample / 8), true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, totalLength * 2, true)
  
  let offset = 44
  for (const chunk of chunks) {
    for (let i = 0; i < chunk.length; i++) {
      const sample = Math.max(-1, Math.min(1, chunk[i] * gain))
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
      offset += 2
    }
  }
  
  return new Blob([buffer], { type: 'audio/wav' })
}

async function loadHistory() {
  try {
    historyLoading.value = true
    const res = await listAudioRecords({ page: 1, page_size: 100 })
    history.value = res.items.map((item: any) => ({
      ...item,
      expanded: false,
      audio_path: item.audio_url || null,
    }))
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
  } catch (err) {
    console.error('Failed to load models:', err)
  } finally {
    modelsLoading.value = false
  }
}

async function handleModelChange() {
  const model = models.value.find(m => m.model_name === selectedModel.value)
  if (model && !model.loaded) {
    loadingModel.value = true
    try {
      await loadModel(model.model_name)
      await loadModels()
    } catch (err) {
      console.error('Load model error:', err)
    } finally {
      loadingModel.value = false
    }
  }
  selectedVoiceId.value = ''
  await loadPresetVoices()
}

async function loadPresetVoices() {
  const engine = getEngine(selectedModel.value)
  if (!currentModelSupportsClone.value && !presetVoices.value.some(p => p.engine === engine)) {
    try {
      const data = await fetchPresetVoices(engine)
      const existing = presetVoices.value.findIndex(p => p.engine === engine)
      if (existing >= 0) {
        presetVoices.value[existing] = data
      } else {
        presetVoices.value.push(data)
      }
      if (data.voices.length > 0) {
        selectedVoiceId.value = data.voices[0].voice_id
      } else {
        selectedVoiceId.value = ''
        showToast('该模型暂无可用音色', 'info')
      }
    } catch (err) {
      console.error('Load preset voices error:', err)
      showToast('加载预设音色失败', 'error')
      selectedVoiceId.value = ''
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

function getModelSize(modelName: string): string | null {
  const match = modelName.match(/\b(\d+\.?\d*B)\b/i)
  return match ? match[1].toUpperCase() : null
}

function getEngine(modelName: string): string {
  const engineMap: Record<string, string> = {
    'qwen-tts-1.7B': 'qwen',
    'qwen-tts-0.6B': 'qwen',
    'qwen-custom-voice-1.7B': 'qwen_custom_voice',
    'qwen-custom-voice-0.6B': 'qwen_custom_voice',
    'luxtts': 'luxtts',
    'chatterbox-tts': 'chatterbox',
    'chatterbox-turbo': 'chatterbox_turbo',
    'tada-1b': 'tada',
    'tada-3b-ml': 'tada',
    'kokoro': 'kokoro'
  }
  return engineMap[modelName] || modelName
}

async function handleLoadModel(modelName: string) {
  try {
    await loadModel(modelName)
    await loadModels()
  } catch (err) {
    console.error('Load model error:', err)
  }
}

function getHistoryAudioUrl(item: any): string | null {
  // auth_backend 记录直接保存了 audio_url
  if (item.audio_url) return item.audio_url
  
  // 兼容 voicebox 后端格式
  let audioId = ''
  if (item.versions && item.versions.length > 0) {
    const defaultVersion = item.versions.find((v: any) => v.is_default) || item.versions[0]
    const name = defaultVersion.audio_path.split('/').pop()?.replace('.wav', '') || ''
    audioId = name.replace(/_processed$/, '').replace(/_speed$/, '')
  } else if (item.audio_path) {
    const name = item.audio_path.split('/').pop()?.replace('.wav', '') || ''
    audioId = name.replace(/_processed$/, '').replace(/_speed$/, '')
  }
  return audioId ? `/voicebox-web/audio/${audioId}` : null
}

async function handleHistoryClick(item: any) {
  activeTab.value = 'generate'
  currentAudioBlob.value = null
  success.value = false
  selectedArticle.value = null
  loadingFromHistory.value = true
  newsType.value = 'newspaper'
  
  await nextTick()
  
  const audioUrl = getHistoryAudioUrl(item)
  if (audioUrl) {
    currentAudio.value = audioUrl
  } else {
    currentAudio.value = null
  }
  
  text.value = item.text
  tvParagraphs.value = []
  nextTick(() => {
    loadingFromHistory.value = false
  })
}

async function checkBackend() {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)
    const res = await fetch('/voicebox-web/profiles', { signal: controller.signal })
    clearTimeout(timeoutId)

    if (res.ok) {
      const data = await res.json()
      backendOnline.value = Array.isArray(data)
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
    showToast('加载文章列表失败', 'error')
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
    text.value = ''
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
    const status = await getGenerationStatus(id, signal)
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
  if (currentModelSupportsClone.value && !selectedProfile.value) {
    showToast('请选择音色', 'error')
    return
  }
  if (!currentModelSupportsClone.value && !selectedVoiceId.value) {
    showToast('请选择预设音色', 'error')
    return
  }
  if (!targetText.trim()) {
    showToast('请输入文本', 'error')
    return
  }
  
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
    const engine = getEngine(selectedModel.value)
    const req: any = {
      text: targetText.trim(),
      language: language.value,
      engine: engine,
      instruct: tone.value || undefined,
      max_chunk_chars: maxChunkChars.value,
    }
    if (currentModelSupportsClone.value) {
      req.profile_id = selectedProfile.value
    } else {
      req.voice_id = selectedVoiceId.value
    }
    if (selectedSpeed.value !== 1.0) {
      req.speed = selectedSpeed.value
    }
    const ms = getModelSize(selectedModel.value)
    if (ms) req.model_size = ms
    const result = await generateSpeech(req, signal)
    
    statusText.value = '等待生成完成...'
    const final = await waitForCompletion(result.id, signal)
    
    if (signal.aborted) return
    
    const audioId = final.id
    currentAudio.value = `/voicebox-web/audio/${audioId}`
    statusText.value = '完成!'
    success.value = true
    
    // 保存到用户记录
    try {
      await createAudioRecord({
        voicebox_generation_id: audioId,
        profile_id: req.profile_id || req.voice_id || undefined,
        profile_name: req.profile_id ? (selectedProfileName.value || undefined) : undefined,
        text: targetText.trim(),
        language: language.value || undefined,
        audio_url: `/voicebox-web/audio/${audioId}`,
        duration: final.duration || undefined,
        seed: final.seed || undefined,
        instruct: final.instruct || undefined,
        engine: final.engine || undefined,
        model_size: final.model_size || undefined,
        status: final.status || 'completed',
      })
    } catch (e) {
      console.error('保存用户记录失败:', e)
    }
    
    await loadHistory()
  } catch (err: any) {
    if (err.name === 'AbortError') {
      statusText.value = '已取消'
    } else {
      showToast(err.message || '生成失败', 'error')
      statusText.value = '失败'
      console.error('生成失败:', err.message || err)
    }
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
  }
})
</script>