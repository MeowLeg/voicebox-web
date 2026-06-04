<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white dark:bg-zinc-900 rounded-xl p-6 w-[500px] max-h-[80vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold">模型管理</h3>
        <button @click="$emit('close')" class="text-zinc-400 hover:text-zinc-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      <div v-if="loading" class="text-center py-4 text-zinc-400">加载中...</div>
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
            @click="$emit('download', model.model_name)"
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
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
  loading: boolean
  models: any[]
}>()

defineEmits<{
  close: []
  download: [modelName: string]
}>()
</script>
