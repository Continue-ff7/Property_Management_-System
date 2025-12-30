from fastapi import APIRouter, HTTPException, status
from app.schemas import UserLogin, Token, UserResponse, UserRegister
from app.models import User, UserRole
from app.core.security import verify_password, create_access_token, get_password_hash

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
            avatar=user.avatar,  # 添加头像字段
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """用户注册（业主/维修人员）"""
    try:
        # 检查用户名是否已存在
        existing_user = await User.get_or_none(username=user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 根据角色创建用户
        user_role = UserRole.OWNER if user_data.role == 'owner' else UserRole.MAINTENANCE
        
        user = await User.create(
            username=user_data.username,
            password=get_password_hash(user_data.password),
            name=user_data.name,
            phone=user_data.phone,
            email=user_data.email,  # 直接使用None，不转空字符串
            role=user_role
        )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"注册错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )
