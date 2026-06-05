<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white dark:bg-zinc-900 rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
      <div class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
        <h3 class="text-lg font-semibold">效果配置</h3>
        <button @click="$emit('close')" class="text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      <div class="p-6 overflow-y-auto max-h-[calc(80vh-130px)]">
        <div v-if="loading" class="text-center py-8 text-zinc-500">加载中...</div>
        <div v-else class="space-y-6">
          <div v-for="effect in effects" :key="effect.type" class="border border-zinc-200 dark:border-zinc-700 rounded-lg p-4">
            <div class="flex items-center gap-3 mb-3">
              <input
                type="checkbox"
                :id="'effect-' + effect.type"
                :checked="isEnabled(effect.type)"
                @change="toggle(effect.type)"
                class="w-4 h-4 rounded"
              />
              <label :for="'effect-' + effect.type" class="font-medium cursor-pointer">
                {{ labels[effect.type] || effect.label }}
              </label>
            </div>
            <p class="text-sm text-zinc-500 mb-3">{{ effect.description }}</p>
            <div v-if="isEnabled(effect.type)" class="grid grid-cols-2 gap-4">
              <div v-for="(param, paramKey) in effect.params" :key="paramKey" class="space-y-1">
                <label class="text-xs text-zinc-500">{{ labelsZh[effect.type]?.[String(paramKey)] || param.description }}</label>
                <div class="flex items-center gap-2">
                  <template v-if="param.options">
                    <select
                      :value="getParam(effect.type, String(paramKey))"
                      @change="setParam(effect.type, String(paramKey), ($event.target as HTMLSelectElement).value)"
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
                      :value="getParam(effect.type, String(paramKey))"
                      @input="setParam(effect.type, String(paramKey), Number(($event.target as HTMLInputElement).value))"
                      class="flex-1"
                    />
                    <span class="text-sm w-16 text-right">{{ getParam(effect.type, String(paramKey)) }}</span>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="px-6 py-4 border-t border-zinc-200 dark:border-zinc-800 flex justify-end gap-2">
        <button @click="$emit('reset')" class="px-4 py-2 text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800">重置</button>
        <button @click="$emit('save')" :disabled="loading" class="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EffectConfig, AvailableEffect } from '@/api'

const props = defineProps<{
  show: boolean
  loading: boolean
  effects: AvailableEffect[]
  modelValue: EffectConfig[]
  labels: Record<string, string>
  labelsZh: Record<string, Record<string, string>>
}>()

const emit = defineEmits<{
  close: []
  save: []
  reset: []
  'update:modelValue': [val: EffectConfig[]]
}>()

const configs = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

function isEnabled(type: string) {
  return configs.value.some(e => e.type === type)
}

function toggle(type: string) {
  const idx = configs.value.findIndex(e => e.type === type)
  if (idx >= 0) {
    const arr = [...configs.value]
    arr.splice(idx, 1)
    emit('update:modelValue', arr)
  } else {
    const effectDef = props.effects.find(e => e.type === type)
    if (effectDef) {
      const params: Record<string, number> = {}
      for (const key of Object.keys(effectDef.params)) {
        params[key] = effectDef.params[key].default
      }
      emit('update:modelValue', [...configs.value, { type, params }])
    }
  }
}

function getParam(type: string, key: string) {
  const e = configs.value.find(e => e.type === type)
  return e?.params?.[key] ?? ''
}

function setParam(type: string, key: string, value: number | string) {
  const arr = configs.value.map(e => {
    if (e.type === type) {
      return { ...e, params: { ...e.params, [key]: value } }
    }
    return e
  })
  emit('update:modelValue', arr)
}
</script>
