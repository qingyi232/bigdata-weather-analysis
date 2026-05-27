import request from './request'

// 获取实时天气
export function getRealtimeWeather(params?: any) {
  return request({
    url: '/weather/realtime',
    method: 'get',
    params
  })
}

// 获取历史天气
export function getHistoricalWeather(params: any) {
  return request({
    url: '/weather/historical',
    method: 'get',
    params
  })
}

// 获取天气预警
export function getWeatherAlerts(params?: any) {
  return request({
    url: '/weather/alerts',
    method: 'get',
    params
  })
}

// 获取气象站列表
export function getStations(params?: any) {
  return request({
    url: '/weather/stations',
    method: 'get',
    params
  })
}

// 获取温度趋势分析
export function getTemperatureTrend(params: any) {
  return request({
    url: '/analysis/temperature-trend',
    method: 'get',
    params
  })
}

// 获取地区统计
export function getRegionalStatistics(params: any) {
  return request({
    url: '/analysis/regional-statistics',
    method: 'get',
    params
  })
}

// 获取极端天气事件
export function getExtremeWeather(params: any) {
  return request({
    url: '/analysis/extreme-weather',
    method: 'get',
    params
  })
}

// 预测温度
export function predictTemperature(data: any) {
  return request({
    url: '/prediction/temperature',
    method: 'post',
    data
  })
}

// 预测降水
export function predictPrecipitation(data: any) {
  return request({
    url: '/prediction/precipitation',
    method: 'post',
    data
  })
}


