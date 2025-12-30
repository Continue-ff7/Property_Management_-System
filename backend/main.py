from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from tortoise import Tortoise
from app.core.config import settings
from app.api.v1 import owner, property_manager, maintenance, auth, common, websocket, chat, ai_assistant
import os
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['app.models']}
    )
    await Tortoise.generate_schemas()
    
    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    yield
    
    # 关闭时清理
    await Tortoise.close_connections()


app = FastAPI(
    title="物业管理系统API",
    description="包含业主端、物业管理端和维修人员端的完整API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"\n[{request.method}] {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"[{request.method}] {request.url.path} - {response.status_code} - {process_time:.2f}s")
    
    return response

# 静态文件服务（用于图片和发票）
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(common.router, prefix="/api/v1/common", tags=["公共"])
app.include_router(owner.router, prefix="/api/v1/owner", tags=["业主端"])
app.include_router(property_manager.router, prefix="/api/v1/manager", tags=["物业管理端"])
app.include_router(maintenance.router, prefix="/api/v1/maintenance", tags=["维修人员端"])

# 注册WebSocket路由
app.include_router(websocket.router, tags=["WebSocket"])

# 注册聊天WebSocket路由（不加前缀）
app.include_router(chat.ws_router, tags=["聊天WebSocket"])

# 注册聊天HTTP API路由（加前缀）
app.include_router(chat.router, prefix="/api/v1", tags=["聊天API"])

# 注册AI助手路由
app.include_router(ai_assistant.router, prefix="/api/v1", tags=["AI助手"])


@app.get("/")
async def root():
    return {"message": "物业管理系统API服务运行中"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
