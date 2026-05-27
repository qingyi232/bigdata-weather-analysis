import request from './request'

// 用户登录
export function login(username: string, password: string) {
  return request({
    url: '/user/login',
    method: 'post',
    data: {
      username,
      password
    }
  })
}

// 用户注册
export function register(username: string, password: string, email: string) {
  return request({
    url: '/user/register',
    method: 'post',
    data: {
      username,
      password,
      email
    }
  })
}

// 获取用户信息
export function getUserProfile() {
  return request({
    url: '/user/profile',
    method: 'get'
  })
}


