<template>
  <div class="layout">
    <router-view class="content" />
    
    <van-tabbar v-model="active" route>
      <van-tabbar-item to="/home/index" icon="wap-home">首页</van-tabbar-item>
      <van-tabbar-item to="/bills" icon="balance-list">账单</van-tabbar-item>
      <van-tabbar-item to="/repairs" icon="service">报修</van-tabbar-item>
      <van-tabbar-item to="/profile" icon="user">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'Layout',
  setup() {
    const route = useRoute()
    const active = ref(0)
    
    const tabMap = {
      '/home/index': 0,
      '/bills': 1,
      '/repairs': 2,
      '/profile': 3
    }
    
    watch(() => route.path, (path) => {
      active.value = tabMap[path] || 0
    }, { immediate: true })
    
    return {
      active
    }
  }
}
</script>

<style scoped>
.layout {
  width: 100%;
  min-height: 100vh;
  padding-bottom: 50px;
}

.content {
  min-height: calc(100vh - 50px);
}
</style>
