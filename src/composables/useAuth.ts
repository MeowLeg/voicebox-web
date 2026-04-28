import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getToken, getUser, clearAuth, UserInfo } from '@/utils/auth'
import { type AuthResponse } from '@/api'

const user = ref<UserInfo | null>(getUser())
const token = ref<string | null>(getToken())
const loading = ref(false)

export function useAuth() {
  const router = useRouter()
  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string): Promise<AuthResponse> {
    loading.value = true
    try {
      const { login } = await import('@/api')
      const res = await login({ username, password })
      token.value = res.access_token
      user.value = res.user
      localStorage.setItem('voicebox_token', res.access_token)
      localStorage.setItem('voicebox_user', JSON.stringify(res.user))
      return res
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, password: string, email?: string): Promise<AuthResponse> {
    loading.value = true
    try {
      const { register } = await import('@/api')
      const res = await register({ username, password, email })
      token.value = res.access_token
      user.value = res.user
      localStorage.setItem('voicebox_token', res.access_token)
      localStorage.setItem('voicebox_user', JSON.stringify(res.user))
      return res
    } finally {
      loading.value = false
    }
  }

  function logout(): void {
    clearAuth()
    token.value = null
    user.value = null
    router.push('/login')
  }

  return {
    user,
    token,
    loading,
    isLoggedIn,
    login,
    register,
    logout
  }
}
