"""
添加用户头像字段迁移脚本
运行方式: python add_avatar_field.py
"""
import asyncio
import asyncmy
from app.core.config import settings

async def add_avatar_field():
    """添加avatar字段到users表"""
    # 从DATABASE_URL解析连接信息
    db_url = settings.DATABASE_URL
    # mysql://user:pass@host:port/dbname
    parts = db_url.replace("mysql://", "").split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")
    host_port = host_db[0].split(":")
    
    user = user_pass[0]
    password = user_pass[1]
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 3306
    database = host_db[1]
    
    # 连接数据库
    conn = await asyncmy.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        db=database
    )
    
    try:
        async with conn.cursor() as cursor:
            # 检查字段是否已存在
            await cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'avatar'
            """, (database,))
            
            result = await cursor.fetchone()
            
            if result[0] == 0:
                # 字段不存在，添加它
                print("正在添加avatar字段...")
                await cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN avatar VARCHAR(500) NULL COMMENT '头像URL' 
                    AFTER email
                """)
                await conn.commit()
                print("✅ avatar字段添加成功！")
            else:
                print("⚠️ avatar字段已存在，跳过迁移")
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始数据库迁移...")
    asyncio.run(add_avatar_field())
    print("迁移完成！")
