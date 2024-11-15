<template>
  <div class="chat-window flex flex-col h-screen bg-gradient-to-b from-blue-50 to-blue-100">
    <header class="bg-white p-4 flex items-center shadow-md">
      <h1 class="text-xl font-semibold text-center text-blue-600 flex-grow">必要-许愿管家 🥣Libra</h1>
    </header>

    <main class="flex-grow overflow-y-auto p-4">
      <div v-for="(message, index) in messages" :key="index" class="mb-4 animate-fade-in">
        <div v-if="showTimestamp(index)" class="text-xs text-gray-400 text-center mb-2">
          {{ formatTimestamp(message.timestamp) }}
        </div>
        <div :class="['flex', message.type === 'user' ? 'justify-end' : 'justify-start']">
          <div v-if="message.type !== 'user'" class="w-10 h-10 rounded-full mr-2 flex-shrink-0 shadow-md overflow-hidden">
            <img src="/xuyuan.jpg" alt="AI" class="w-full h-full object-cover">
          </div>
          <div :class="['max-w-3/4 p-3 rounded-lg shadow-lg', 
            message.type === 'user' ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' : 'bg-white text-gray-800']">
            <div v-html="formatMessage(message.content)" class="break-words"></div>
          </div>
          <div v-if="message.type === 'user'" class="w-10 h-10 rounded-full bg-gray-200 ml-2 flex-shrink-0 shadow-md overflow-hidden">
            <img src="/user-avatar.png" alt="User" class="w-full h-full object-cover">
          </div>
        </div>
      </div>
    </main>

    <footer class="bg-white p-4 shadow-md">
      <div class="max-w-3xl mx-auto flex items-center">
        <input
          v-model="userInput"
          type="text"
          placeholder="请输入您的消息..."
          class="flex-grow p-3 border rounded-l-full focus:outline-none focus:ring-2 focus:ring-blue-300 transition-all duration-300"
          @keyup.enter="sendMessage"
        />
        <button
          @click="sendMessage"
          class="bg-blue-500 text-white p-3 rounded-r-full hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 transition-all duration-300"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ChatWindow',
  data() {
    return {
      messages: [],
      userInput: '',
      isAiThinking: false
    }
  },
  methods: {
    async sendMessage() {
      if (this.userInput.trim() === '' || this.isAiThinking) return

      const timestamp = new Date()
      this.messages.push({ type: 'user', content: this.userInput, timestamp })
      this.isAiThinking = true
      const userInput = this.userInput
      this.userInput = ''

      try {
        const response = await axios.post('http://10.6.16.151:5000/api/chat', { 
          message: userInput,
          user_id: 'default_user'
        })
        
        this.messages.push({ 
          type: 'ai', 
          content: response.data.message,
          timestamp: response.data.timestamp 
        })
      } catch (error) {
        console.error('Error:', error)
        this.messages.push({ 
          type: 'error', 
          content: '抱歉,出现了一个错误。', 
          timestamp: new Date() 
        })
      } finally {
        this.isAiThinking = false
      }
    },
    goBack() {
      // 实现返回逻辑
    },
    showTimestamp(index) {
      if (index === 0) return true
      const prevMessage = this.messages[index - 1]
      const currentMessage = this.messages[index]
      return new Date(currentMessage.timestamp) - new Date(prevMessage.timestamp) > 300000 // 5分钟
    },
    formatTimestamp(timestamp) {
      const date = new Date(timestamp)
      return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    },
    formatMessage(content) {
      if (!content) return ''
      return content.replace(/\n/g, '<br>')
    }
  }
}
</script>

<style scoped>
.chat-window {
  width: 750px;
  height: 1334px;
  margin: 0 auto;
  font-family: 'Arial', sans-serif;
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 添加响应式设计 */
@media (max-width: 768px) {
  .chat-window {
    width: 100%;
    height: 100vh;
  }
}
</style>
