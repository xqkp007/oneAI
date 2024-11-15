from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chat_engine import ChatEngine

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# 初始化聊天引擎
chat_engine = ChatEngine(
    api_key="sk-9eabf391ac3241718d01d2ab50087209",
    base_url="https://api.deepseek.com"
)

# 注册路由
app.include_router(chat_engine.router, prefix="/api")