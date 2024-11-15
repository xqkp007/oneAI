import { createApp } from 'vue'
import App from './App.vue'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import './index.css'

const vuetify = createVuetify()

const app = createApp(App)
app.use(vuetify)
app.mount('#app')
