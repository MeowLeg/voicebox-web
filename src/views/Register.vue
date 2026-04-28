<template>
  <div class="flex min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-semibold">舟传媒科技部 TTS</h1>
        <p class="text-sm text-zinc-500 dark:text-zinc-400 mt-2">创建新账号</p>
      </div>

      <div class="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 p-6 shadow-sm">
        <div v-if="error" class="mb-4 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
          {{ error }}
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5">用户名 *</label>
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              required
              minlength="3"
              maxlength="32"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="3-32 个字符"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1.5">邮箱</label>
            <input
              v-model="email"
              type="email"
              autocomplete="email"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="选填"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1.5">密码 *</label>
            <input
              v-model="password"
              type="password"
              autocomplete="new-password"
              required
              minlength="6"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="至少 6 个字符"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1.5">确认密码 *</label>
            <input
              v-model="confirmPassword"
              type="password"
              autocomplete="new-password"
              required
              minlength="6"
              class="w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="再次输入密码"
            />
          </div>

          <button
            type="submit"
            :disabled="loading || !canSubmit"
            class="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
          >
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>

        <div class="mt-4 text-center text-sm text-zinc-500 dark:text-zinc-400">
          已有账号？
          <router-link to="/login" class="text-blue-600 hover:text-blue-700">登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { register } = useAuth()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

const canSubmit = computed(() => {
  return username.value.length >= 3 &&
         password.value.length >= 6 &&
         password.value === confirmPassword.value
})

async function handleSubmit() {
  if (password.value !== confirmPassword.value) {
    error.value = '两次密码不一致'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await register(username.value, password.value, email.value || undefined)
    router.push('/')
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>
