<template>
  <router-view />
</template>

<script setup>
const fontSize = localStorage.getItem('fontSize') || 'medium'
const fontSizeMap = { small: '14px', medium: '16px', large: '18px' }
document.documentElement.style.setProperty('--base-font-size', fontSizeMap[fontSize])
document.documentElement.style.fontSize = fontSizeMap[fontSize]
</script>

<style>
:root {
  --base-font-size: 16px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  overflow-x: hidden;
}

#app {
  width: 100%;
  min-height: 100vh;
}
</style>
