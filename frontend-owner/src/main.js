import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// Vant UI
import Vant from 'vant'
import 'vant/lib/index.css'
import './registerServiceWorker'

const app = createApp(App)

app.use(store)
app.use(router)
app.use(Vant)

app.mount('#app')
