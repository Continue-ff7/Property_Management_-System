#!/usr/bin/env python3
"""
数据库迁移脚本：修改楼栋表结构，支持房产批量生成
执行前会清空所有相关数据（房产、账单、报修工单、投诉）
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tortoise import Tortoise
from app.core.config import settings
import re

# 解析 DATABASE_URL
# 格式: mysql://user:password@host:port/database
db_url = settings.DATABASE_URL
match = re.match(r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.*)', db_url)
if not match:
    print(f"无法解析数据库URL: {db_url}")
    sys.exit(1)

DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = match.groups()
DB_PORT = int(DB_PORT)

# 数据库配置
DB_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": DB_HOST,
                "port": DB_PORT,
                "user": DB_USER,
                "password": DB_PASSWORD,
                "database": DB_NAME,
            }
        }
    },
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        }
    }
}


async def migrate():
    """执行数据库迁移"""
    print("=" * 50)
    print("开始数据库迁移")
    print("=" * 50)
    
    # 连接数据库
    await Tortoise.init(config=DB_CONFIG)
    conn = Tortoise.get_connection("default")
    
    try:
        # 1. 清空相关数据表（按依赖顺序）
        print("\n[1/4] 清空数据表...")
        
        tables_to_clear = [
            "repair_chat_messages",  # 工单聊天记录
            "chat_messages",          # AI聊天记录
            "complaints",             # 投诉
            "repair_orders",          # 维修工单
            "bills",                  # 账单
            "properties",             # 房产
        ]
        
        for table in tables_to_clear:
            try:
                await conn.execute_query(f"DELETE FROM {table}")
                print(f"  ✓ 清空表: {table}")
            except Exception as e:
                print(f"  ⚠ 跳过表: {table} ({e})")
        
        # 2. 修改 buildings 表结构
        print("\n[2/4] 修改楼栋表结构...")
        
        # 检查字段是否存在
        result = await conn.execute_query("SHOW COLUMNS FROM buildings LIKE 'units_per_floor'")
        if result[1]:  # 有数据说明字段存在
            # 重命名字段
            await conn.execute_query("""
                ALTER TABLE buildings 
                CHANGE units_per_floor units INT
            """)
            print("  ✓ 重命名字段: units_per_floor -> units")
        else:
            # 字段不存在，直接添加
            await conn.execute_query("""
                ALTER TABLE buildings 
                ADD units INT AFTER name
            """)
            print("  ✓ 添加字段: units")
        
        # 添加 rooms_per_floor 字段
        result = await conn.execute_query("SHOW COLUMNS FROM buildings LIKE 'rooms_per_floor'")
        if not result[1]:  # 字段不存在
            await conn.execute_query("""
                ALTER TABLE buildings 
                ADD rooms_per_floor INT AFTER floors
            """)
            print("  ✓ 添加字段: rooms_per_floor")
        
        # 3. 修改 properties 表 area 字段为可空
        print("\n[3/4] 修改房产表结构...")
        await conn.execute_query("ALTER TABLE properties MODIFY COLUMN area DECIMAL(10,2) NULL")
        print("  ✓ area 字段改为可空")
        
        # 设置默认值
        await conn.execute_query("UPDATE buildings SET units = 1 WHERE units IS NULL")
        await conn.execute_query("UPDATE buildings SET rooms_per_floor = 2 WHERE rooms_per_floor IS NULL")
        print("  ✓ 默认值设置完成")
        
        # 4. 清空楼栋数据（可选，如果需要重新创建）
        print("\n[4/4] 清空楼栋数据...")
        await conn.execute_query("DELETE FROM buildings")
        print("  ✓ 楼栋数据已清空")
        
        print("\n" + "=" * 50)
        print("迁移完成！")
        print("=" * 50)
        print("\n现在可以：")
        print("1. 重启后端服务")
        print("2. 重新编译前端")
        print("3. 在管理员端添加楼栋，自动生成房产")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    # 确认提示
    print("警告：此脚本将清空以下数据：")
    print("  - 所有房产")
    print("  - 所有账单")
    print("  - 所有维修工单")
    print("  - 所有投诉")
    print("  - 所有聊天记录")
    print("  - 所有楼栋")
    print("\n数据清空后无法恢复！")
    
    confirm = input("\n确认执行迁移吗？输入 'yes' 继续: ")
    if confirm.lower() != 'yes':
        print("已取消")
        sys.exit(0)
    
    asyncio.run(migrate())
