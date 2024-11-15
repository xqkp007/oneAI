import os
import json

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)

def create_project():
    # 创建项目结构
    create_directory('project')
    create_directory('project/frontend')
    create_directory('project/frontend/public')
    create_directory('project/frontend/src')
    create_directory('project/frontend/src/components')
    create_directory('project/backend')

    # 前端文件
    write_file('project/frontend/public/index.html', '''
<!DOCTYPE html>
<html lang="zh">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>DeepSeek对话窗口</title>
  </head>
  <body>
    <div id="app"></div>
    <!-- built files will be auto injected -->
  </body>
</html>
    '''.strip())

    write_file('project/frontend/src/main.js', '''
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
    '''.strip())

    write_file('project/frontend/src/App.vue', '''
<template>
  <div id="app">
    <ChatWindow />
  </div>
</template>

<script>
import ChatWindow from './components/ChatWindow.vue'

export default {
  name: 'App',
  components: {
    ChatWindow
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
    '''.strip())

    write_file('project/frontend/src/components/ChatWindow.vue', '''
<template>
  <div class="chat-window">
    <div class="messages">
      <div v-for="(message, index) in messages" :key="index" :class="message.type">
        {{ message.content }}
      </div>
    </div>
    <div class="input-area">
      <input v-model="userInput" @keyup.enter="sendMessage" placeholder="请输入您的消息...">
      <button @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ChatWindow',
  data() {
    return {
      messages: [],
      userInput: ''
    }
  },
  methods: {
    async sendMessage() {
      if (this.userInput.trim() === '') return

      // 添加用户消息到消息列表
      this.messages.push({ type: 'user', content: this.userInput })

      try {
        // 发送消息到后端
        const response = await axios.post('5000/chat', { message: this.userInput })
        
        // 添加AI回复到消息列表
        this.messages.push({ type: 'ai', content: response.data.reply })
      } catch (error) {
        console.error('Error:', error)
        this.messages.push({ type: 'error', content: '抱歉,出现了一个错误。' })
      }

      // 清空输入框
      this.userInput = ''
    }
  }
}
</script>

<style scoped>
.chat-window {
  width: 400px;
  margin: 0 auto;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.messages {
  height: 300px;
  overflow-y: auto;
  padding: 10px;
}

.user, .ai, .error {
  margin-bottom: 10px;
  padding: 5px;
  border-radius: 5px;
}

.user {
  background-color: #e6f3ff;
  text-align: right;
}

.ai {
  background-color: #f0f0f0;
  text-align: left;
}

.error {
  background-color: #ffe6e6;
  text-align: center;
}

.input-area {
  display: flex;
  padding: 10px;
}

input {
  flex-grow: 1;
  padding: 5px;
}

button {
  margin-left: 10px;
}
</style>
'''.strip())

    write_file('project/frontend/package.json', json.dumps({
        "name": "deepseek-chat-frontend",
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "serve": "vue-cli-service serve",
            "build": "vue-cli-service build",
            "lint": "vue-cli-service lint"
        },
        "dependencies": {
            "axios": "^0.21.1",
            "core-js": "^3.6.5",
            "vue": "^3.0.0"
        },
        "devDependencies": {
            "@vue/cli-plugin-babel": "~4.5.0",
            "@vue/cli-plugin-eslint": "~4.5.0",
            "@vue/cli-service": "~4.5.0",
            "@vue/compiler-sfc": "^3.0.0",
            "babel-eslint": "^10.1.0",
            "eslint": "^6.7.2",
            "eslint-plugin-vue": "^7.0.0"
        }
    }, indent=2))

    # 后端文件
    write_file('project/backend/app.py', '''
from flask import Flask, request, jsonify
from flask_cors import CORS
from intent_recognition import recognize_intent
from llm_prompt_manager import get_prompt, generate_response

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    intent = recognize_intent(user_message)
    prompt = get_prompt(intent)
    response = generate_response(prompt, user_message)
    return jsonify({'reply': response})

if __name__ == '__main__':
    app.run(debug=True)
''')

    write_file('project/backend/intent_recognition.py', '''
def recognize_intent(message):
    # 这里应该实现实际的意图识别逻辑
    # 现在只是一个简单的示例
    if '问题' in message or '如何' in message:
        return 'question'
    elif '谢谢' in message:
        return 'gratitude'
    else:
        return 'general'
''')

    write_file('project/backend/llm_prompt_manager.py', '''
def get_prompt(intent):
    prompts = {
        'question': "用户有一个问题。请提供一个有帮助的回答：",
        'gratitude': "用户表示感谢。请给出适当的回应：",
        'general': "请对用户的消息做出回应："
    }
    return prompts.get(intent, prompts['general'])

def generate_response(prompt, user_message):
    # 这里应该实现实际的LLM调用逻辑
    # 现在只是一个简单的示例
    return f"这是对'{user_message}'的模拟回复。实际使用时，这里将是LLM生成的回复。"
''')

    write_file('project/backend/requirements.txt', '''
flask==2.0.1
flask-cors==3.0.10
''')

if __name__ == "__main__":
    create_project()
