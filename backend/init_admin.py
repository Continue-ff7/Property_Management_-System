#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化管理员账号脚本
运行方式：python3 init_admin.py
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import User, UserRole
from app.core.security import get_password_hash
from tortoise import Tortoise
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def init_db():
    """初始化数据库连接"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL 未配置！请检查 .env 文件")
    
    await Tortoise.init(
        db_url=database_url,
        modules={'models': ['app.models']}
    )
    await Tortoise.generate_schemas()


async def init_admin():
    """初始化管理员账号"""
    try:
        await init_db()
        
        # 检查是否已存在admin用户
        existing_admin = await User.get_or_none(username='admin')
        
        if existing_admin:
            print("=" * 50)
            print("❌ 管理员账号已存在！")
            print(f"   用户名: {existing_admin.username}")
            print(f"   姓名: {existing_admin.name}")
            print(f"   手机: {existing_admin.phone}")
            print(f"   角色: {existing_admin.role}")
            print(f"   状态: {'激活' if existing_admin.is_active else '未激活'}")
            print("=" * 50)
            return
        
        # 创建管理员账号
        hashed_password = get_password_hash('admin123')
        admin_user = await User.create(
            username='admin',
            password=hashed_password,
            name='系统管理员',
            phone='13800138000',
            email=None,
            avatar=None,
            role=UserRole.MANAGER,
            is_active=True
        )
        
        print("=" * 50)
        print("✅ 管理员账号创建成功！")
        print(f"   用户名: {admin_user.username}")
        print(f"   密码: admin123")
        print(f"   姓名: {admin_user.name}")
        print(f"   手机: {admin_user.phone}")
        print(f"   角色: {admin_user.role}")
        print(f"   ID: {admin_user.id}")
        print("=" * 50)
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ 创建失败: {str(e)}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == '__main__':
    print("\n开始初始化管理员账号...")
    asyncio.run(init_admin())
