<template>
  <div class="app-container">
    <div class="menu-container">
      <div 
        v-for="menu in menus" 
        :key="menu.path"
        :class="['menu-item', { active: currentPath === menu.path }]"
        @click="navigateTo(menu.path)"
      >
        {{ menu.name }}
      </div>
    </div>
    <div class="content-container">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const currentPath = ref(route.path)

const menus = [
  { name: 'LOAD', path: '/load' },
  { name: 'CHUNK', path: '/chunk' },
  { name: 'PARSE', path: '/parse' }
]

const navigateTo = (path) => {
  router.push(path)
  currentPath.value = path
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  margin: 0;
}

.menu-container {
  width: 200px;
  background-color: #1a237e;
  padding: 20px 0;
}

.menu-item {
  color: white;
  padding: 15px 20px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.menu-item:hover {
  background-color: #283593;
}

.menu-item.active {
  background-color: #3949ab;
}

.content-container {
  flex: 1;
  background-color: #f5f5f5;
  padding: 20px;
}
</style> 