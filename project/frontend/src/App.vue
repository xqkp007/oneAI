<template>
  <v-app>
    <ChatWindow />
    <div id="log" class="text-xs fixed bottom-0 left-0 bg-gray-100 p-2">
      <p>Vuetify loaded: {{ vuetifyLoaded }}</p>
      <p>Tailwind CSS loaded: {{ tailwindLoaded }}</p>
    </div>
  </v-app>
</template>

<script>
import ChatWindow from './components/ChatWindow.vue'

export default {
  name: 'App',
  components: {
    ChatWindow
  },
  data() {
    return {
      vuetifyLoaded: false,
      tailwindLoaded: false
    }
  },
  mounted() {
    this.checkVuetify()
    this.checkTailwind()
  },
  methods: {
    checkVuetify() {
      this.vuetifyLoaded = !!this.$vuetify
    },
    checkTailwind() {
      const element = document.createElement('div')
      element.classList.add('bg-gray-100')
      document.body.appendChild(element)
      const styles = window.getComputedStyle(element)
      this.tailwindLoaded = styles.backgroundColor !== ''
      document.body.removeChild(element)
    }
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
