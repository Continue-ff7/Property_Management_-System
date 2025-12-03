import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import store from './store'
import './styles/index.scss'

// 全局处理 ResizeObserver 错误
const resizeObserverLoopErr = (e) => {
  if (e.message && e.message.includes('ResizeObserver loop')) {
    const resizeObserverErrDiv = document.getElementById('webpack-dev-server-client-overlay-div')
    const resizeObserverErr = document.getElementById('webpack-dev-server-client-overlay')
    if (resizeObserverErr) {
      resizeObserverErr.setAttribute('style', 'display: none')
    }
    if (resizeObserverErrDiv) {
      resizeObserverErrDiv.setAttribute('style', 'display: none')
    }
  }
}
window.addEventListener('error', resizeObserverLoopErr)

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(store)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
