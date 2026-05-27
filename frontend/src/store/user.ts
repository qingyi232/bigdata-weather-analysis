import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getUserProfile } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<any>(null)
  
  const isLoggedIn = computed(() => !!token.value)
  
  // 登录
  async function login(username: string, password: string) {
    try {
      const res = await apiLogin(username, password)
      
      if (res.code === 200) {
        token.value = res.data.access_token
        localStorage.setItem('token', res.data.access_token)
        userInfo.value = res.data.user
        return true
      } else {
        throw new Error(res.message)
      }
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }
  
  // 登出
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }
  
  // 获取用户信息
  async function fetchUserInfo() {
    try {
      const res = await getUserProfile()
      if (res.code === 200) {
        userInfo.value = res.data
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }
  
  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    logout,
    fetchUserInfo
  }
})


