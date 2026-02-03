"""
添加投诉表
"""
import asyncio
from tortoise import Tortoise
from app.core.config import settings

async def migrate():
    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['app.models']}
    )
    
    # 创建表
    await Tortoise.generate_schemas()
    
    print("投诉表创建成功!")
    
    # 关闭连接
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(migrate())
