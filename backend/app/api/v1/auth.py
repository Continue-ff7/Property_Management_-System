from fastapi import APIRouter, HTTPException, status
from app.schemas import UserLogin, Token, UserResponse
from app.models import User
from app.core.security import verify_password, create_access_token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """用户登录"""
    user = await User.get_or_none(username=user_data.username)
    
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            name=user.name,
            phone=user.phone,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }
