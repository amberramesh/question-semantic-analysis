import Vue from 'vue'
import App from './App.vue'
import router from './router'
import VueRouter from 'vue-router'
import Vuetify from 'vuetify'
import axios from 'axios'

Vue.config.productionTip = false
Vue.use(VueRouter)
Vue.use(Vuetify)

axios.defaults.baseURL = 'http://127.0.0.1:5001'

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
