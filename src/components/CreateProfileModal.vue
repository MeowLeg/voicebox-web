<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white dark:bg-zinc-900 rounded-xl p-6 w-[500px] max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold">新建音色</h3>
        <button @click="$emit('close')" class="text-zinc-400 hover:text-zinc-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">音色名称 *</label>
          <input
            :value="profile.name"
            @input="$emit('update:profile', { ...profile, name: ($event.target as HTMLInputElement).value })"
            type="text"
            class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入音色名称"
          />
        </div>
        <div>
          <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">描述</label>
          <textarea
            :value="profile.description"
            @input="$emit('update:profile', { ...profile, description: ($event.target as HTMLTextAreaElement).value })"
            rows="2"
            class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="可选描述"
          />
        </div>
        <div>
          <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">语言</label>
          <select
            :value="profile.language"
            @change="$emit('update:profile', { ...profile, language: ($event.target as HTMLSelectElement).value })"
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
              @click="$emit('toggleRecord')"
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
              @click="$emit('triggerUpload')"
              class="flex-1 px-3 py-2 text-sm rounded-lg border border-zinc-300 dark:border-zinc-600 hover:bg-zinc-50 dark:hover:bg-zinc-800"
            >
              上传文件
            </button>
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept="audio/*,.wav,.mp3,.m4a,.flac"
            class="hidden"
            @change="$emit('fileSelected', $event)"
          />
          <div
            v-if="audioFileName"
            class="text-sm text-green-600 dark:text-green-400 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            {{ audioFileName }}
          </div>
          <div v-else class="text-xs text-zinc-400">
            建议10-30秒的清晰语音
          </div>
        </div>
        <div>
          <label class="block text-sm text-zinc-500 dark:text-zinc-400 mb-1">音频对应的文字 *</label>
          <textarea
            :value="profile.referenceText"
            @input="$emit('update:profile', { ...profile, referenceText: ($event.target as HTMLTextAreaElement).value })"
            rows="3"
            class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="请输入音频中朗读的文字内容"
          />
        </div>
        <div class="flex justify-end gap-2">
          <button
            @click="$emit('close')"
            class="px-4 py-2 text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            取消
          </button>
          <button
            @click="$emit('create')"
            :disabled="creating || !canCreate"
            class="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 text-white"
          >
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  show: boolean
  creating: boolean
  canCreate: boolean
  profile: { name: string; description: string; language: string; audioFile: File | null; referenceText: string }
  isRecording: boolean
  audioFileName: string
}>()

defineEmits<{
  close: []
  'update:profile': [val: typeof props.profile]
  toggleRecord: []
  triggerUpload: []
  fileSelected: [event: Event]
  create: []
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)

watch(() => props.show, (val) => {
  if (!val) {
    const input = fileInputRef.value
    if (input) input.value = ''
  }
})
</script>
