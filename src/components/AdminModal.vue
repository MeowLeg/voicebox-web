<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white dark:bg-zinc-900 rounded-xl p-6 w-[580px] max-h-[85vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold">用户权限管理</h3>
        <div class="flex items-center gap-2">
          <button @click="openCreateForm" class="px-3 py-1 text-xs rounded-lg bg-blue-600 hover:bg-blue-700 text-white">新建用户</button>
          <button @click="$emit('close')" class="text-zinc-400 hover:text-zinc-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <div v-if="showForm" class="mb-4 p-3 rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 space-y-2">
        <div class="flex gap-2">
          <input v-model="form.username" placeholder="用户名" class="flex-1 rounded border border-zinc-300 dark:border-zinc-600 px-2 py-1 text-sm" />
          <input v-model="form.password" :placeholder="editing ? '留空不修改' : '密码'" class="flex-1 rounded border border-zinc-300 dark:border-zinc-600 px-2 py-1 text-sm" />
        </div>
        <div class="flex gap-2">
          <input v-model="form.email" placeholder="邮箱（可选）" class="flex-1 rounded border border-zinc-300 dark:border-zinc-600 px-2 py-1 text-sm" />
          <select v-model="form.role" class="w-24 rounded border border-zinc-300 dark:border-zinc-600 px-2 py-1 text-sm">
            <option value="user">user</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="showForm = false" class="px-3 py-1 text-xs rounded border border-zinc-300 dark:border-zinc-600">取消</button>
          <button @click="$emit('saveUser', { ...form })" :disabled="saving" class="px-3 py-1 text-xs rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50">{{ saving ? '保存中...' : editing ? '更新' : '创建' }}</button>
        </div>
      </div>

      <div v-if="loading" class="text-center py-4 text-zinc-400">加载中...</div>
      <div v-else class="space-y-2">
        <div v-for="u in users" :key="u.id" class="flex items-center justify-between p-3 rounded-lg border border-zinc-200 dark:border-zinc-700">
          <div>
            <div class="font-medium text-sm">{{ u.username }} <span v-if="u.role === 'admin'" class="text-xs text-blue-500 ml-1">(admin)</span></div>
            <div class="text-xs text-zinc-400">{{ u.email || '' }}</div>
          </div>
          <div class="flex items-center gap-2">
            <label class="flex items-center gap-1 text-xs cursor-pointer" v-for="perm in ['broadcast']" :key="perm">
              <input type="checkbox" :checked="u.permissions.includes(perm)" @change="$emit('togglePermission', u, perm)" class="w-3.5 h-3.5" />
              {{ perm === 'broadcast' ? '广播推送' : perm }}
            </label>
            <button @click="editUserForm(u)" class="text-xs text-blue-500 hover:text-blue-600 ml-1">编辑</button>
            <button @click="$emit('deleteUser', u)" :disabled="u._deleting" class="text-xs text-red-500 hover:text-red-600 ml-1">{{ u._deleting ? '...' : '删除' }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  show: boolean
  loading: boolean
  users: any[]
  saving: boolean
}>()

const emit = defineEmits<{
  close: []
  saveUser: [form: { username: string; password: string; email: string; role: string }]
  togglePermission: [user: any, perm: string]
  deleteUser: [user: any]
}>()

const showForm = ref(false)
const editing = ref(false)
const form = ref({ username: '', password: '', email: '', role: 'user' })

function openCreateForm() {
  editing.value = false
  form.value = { username: '', password: '', email: '', role: 'user' }
  showForm.value = true
}

function editUserForm(u: any) {
  editing.value = true
  form.value = { username: u.username, password: '', email: u.email || '', role: u.role }
  showForm.value = true
}

defineExpose({ showForm, editing, form })
</script>
