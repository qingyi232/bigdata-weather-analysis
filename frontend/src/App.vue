<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('基于大数据的天气数据分析与可视化系统')
  console.log('版本: 1.0.0')
})
</script>

<style scoped>
</style>


