from fastapi import Depends, HTTPException, status, UploadFile, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from app.models import User, UserRole
from typing import Optional
import uuid
import os
import aiofiles
from app.core.config import settings

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前登录用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 将sub从字符串转换为整数
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    return user


async def get_current_owner(current_user: User = Depends(get_current_user)) -> User:
    """获取当前业主用户"""
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要业主权限"
        )
    return current_user


async def get_current_owner_optional_token(
    token: Optional[str] = Query(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> User:
    """获取当前业主用户（支持URL参数token）"""
    # 优先使用Header中的token，其次使用URL参数中的token
    auth_token = None
    if credentials:
        auth_token = credentials.credentials
    elif token:
        auth_token = token
    
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(auth_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 将sub从字符串转换为整数
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    if user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要业主权限"
        )
    
    return user


async def get_current_manager(current_user: User = Depends(get_current_user)) -> User:
    """获取当前物业管理员"""
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要物业管理员权限"
        )
    return current_user


async def get_current_maintenance(current_user: User = Depends(get_current_user)) -> User:
    """获取当前维修人员"""
    if current_user.role != UserRole.MAINTENANCE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要维修人员权限"
        )
    return current_user


async def save_upload_file(file: UploadFile, folder: str = "images") -> str:
    """保存上传的文件"""
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，仅支持 JPEG、PNG、WebP 格式"
        )
    
    # 验证文件大小
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（最大 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB）"
        )
    
    # 生成唯一文件名
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    
    # 确保目录存在
    upload_path = os.path.join(settings.UPLOAD_DIR, folder)
    os.makedirs(upload_path, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(upload_path, filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)
    
    # 返回访问URL
    return f"/uploads/{folder}/{filename}"


def generate_order_number() -> str:
    """生成工单号"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = uuid.uuid4().hex[:6].upper()
    return f"WO{timestamp}{random_str}"
