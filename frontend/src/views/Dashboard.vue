<template>
  <div class="dashboard">
    <div class="header">
      <h1>基于大数据的天气数据分析与可视化系统</h1>
      <div class="time">{{ currentTime }}</div>
    </div>

    <div class="content">
      <!-- 第一行：实时数据卡片 -->
      <div class="row-1">
        <div class="card" v-for="station in realtimeData" :key="station.station_id">
          <div class="card-title">{{ station.station_name }}</div>
          <div class="card-content">
            <div class="temperature">{{ station.temperature }}°C</div>
            <div class="weather-info">
              <div>{{ station.weather_text }}</div>
              <div>湿度: {{ station.humidity }}%</div>
              <div>风速: {{ station.wind_speed }} m/s</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第二行：图表 -->
      <div class="row-2">
        <div class="chart-card">
          <h3>温度趋势图</h3>
          <v-chart class="chart" :option="temperatureOption" autoresize />
        </div>

        <div class="chart-card">
          <h3>降水量分布</h3>
          <v-chart class="chart" :option="precipitationOption" autoresize />
        </div>
      </div>

      <!-- 第三行：地图和统计 -->
      <div class="row-3">
        <div class="map-card">
          <h3>地图热力图</h3>
          <v-chart class="chart" :option="mapOption" autoresize />
        </div>

        <div class="stats-card">
          <h3>系统统计</h3>
          <div class="stat-item">
            <span class="stat-label">气象站数量:</span>
            <span class="stat-value">{{ stats.total_stations }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">数据记录:</span>
            <span class="stat-value">{{ stats.total_records }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">实时速率:</span>
            <span class="stat-value">{{ stats.realtime_data_rate }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">存储使用:</span>
            <span class="stat-value">{{ stats.storage_used }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, MapChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent
} from 'echarts/components'
import dayjs from 'dayjs'
import axios from 'axios'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  MapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent
])

const currentTime = ref('')
const realtimeData = ref([])
const stats = ref({
  total_stations: 0,
  total_records: 0,
  realtime_data_rate: '',
  storage_used: ''
})

// 温度趋势图配置
const temperatureOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
  },
  yAxis: {
    type: 'value',
    name: '温度(℃)'
  },
  series: [{
    name: '温度',
    type: 'line',
    data: [22, 20, 21, 25, 28, 26, 24],
    smooth: true,
    itemStyle: {
      color: '#FF6B6B'
    },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(255, 107, 107, 0.5)' },
          { offset: 1, color: 'rgba(255, 107, 107, 0.1)' }
        ]
      }
    }
  }]
})

// 降水量图配置
const precipitationOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['北京', '上海', '广州', '深圳', '成都', '杭州']
  },
  yAxis: {
    type: 'value',
    name: '降水量(mm)'
  },
  series: [{
    name: '降水量',
    type: 'bar',
    data: [15, 32, 28, 45, 20, 18],
    itemStyle: {
      color: '#4ECDC4'
    }
  }]
})

// 地图配置
const mapOption = ref({
  tooltip: {
    trigger: 'item'
  },
  visualMap: {
    min: 0,
    max: 100,
    text: ['高', '低'],
    realtime: false,
    calculable: true,
    inRange: {
      color: ['lightskyblue', 'yellow', 'orangered']
    }
  },
  series: [{
    name: '温度',
    type: 'scatter',
    coordinateSystem: 'geo',
    data: [
      { name: '北京', value: [116.4, 39.9, 25] },
      { name: '上海', value: [121.5, 31.2, 28] },
      { name: '广州', value: [113.3, 23.1, 32] },
      { name: '深圳', value: [114.1, 22.5, 30] }
    ],
    symbolSize: 15
  }]
})

// 更新时间
function updateTime() {
  currentTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

// 加载实时数据
async function loadRealtimeData() {
  try {
    const res = await axios.get('/api/v1/weather/realtime?limit=6')
    if (res.data.code === 200) {
      realtimeData.value = res.data.data
    }
  } catch (error) {
    console.error('加载实时数据失败:', error)
  }
}

// 加载统计数据
async function loadStats() {
  try {
    const res = await axios.get('/api/v1/stats', {
      headers: {
        Authorization: `Bearer demo-token`
      }
    })
    if (res.data) {
      stats.value = res.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

let timer: any = null

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  
  // 加载数据
  loadRealtimeData()
  loadStats()
  
  // 每30秒刷新一次数据
  setInterval(() => {
    loadRealtimeData()
    loadStats()
  }, 30000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.dashboard {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header h1 {
  color: white;
  font-size: 32px;
  font-weight: bold;
}

.time {
  color: white;
  font-size: 24px;
  font-family: 'Courier New', monospace;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.row-1 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.card:hover {
  transform: translateY(-5px);
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 15px;
}

.temperature {
  font-size: 48px;
  font-weight: bold;
  color: #FF6B6B;
  margin-bottom: 10px;
}

.weather-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
  color: #666;
  font-size: 14px;
}

.row-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 20px;
}

.chart {
  width: 100%;
  height: 300px;
}

.row-3 {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.map-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.map-card h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 20px;
}

.stats-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.stats-card h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.stat-value {
  color: #333;
  font-size: 16px;
  font-weight: bold;
}
</style>


