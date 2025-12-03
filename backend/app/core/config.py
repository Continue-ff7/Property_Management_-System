from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql://root:password@localhost:3306/property_management"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080"]
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # AI客服配置（可选，后续集成）
    AI_SERVICE_URL: str = ""
    AI_SERVICE_KEY: str = ""
    
    class Config:
        env_file = ".env"


settings = Settings()
