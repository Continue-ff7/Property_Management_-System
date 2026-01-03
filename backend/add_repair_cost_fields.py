"""
添加维修费用相关字段的数据库迁移脚本
执行方式: python add_repair_cost_fields.py
"""
import asyncio
from tortoise import Tortoise
from app.core.config import settings


async def migrate():
    """添加维修费用相关字段"""
    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]}
    )
    
    # 获取数据库连接
    conn = Tortoise.get_connection("default")
    
    try:
        print("开始添加维修费用相关字段...")
        
        # 添加 repair_cost 字段
        await conn.execute_query(
            """
            ALTER TABLE repair_orders 
            ADD COLUMN repair_cost DECIMAL(10, 2) NULL COMMENT '维修费用（元）'
            """
        )
        print("✅ 添加 repair_cost 字段成功")
        
        # 添加 cost_paid 字段
        await conn.execute_query(
            """
            ALTER TABLE repair_orders 
            ADD COLUMN cost_paid TINYINT(1) DEFAULT 0 NOT NULL COMMENT '费用是否已支付'
            """
        )
        print("✅ 添加 cost_paid 字段成功")
        
        # 添加 paid_at 字段
        await conn.execute_query(
            """
            ALTER TABLE repair_orders 
            ADD COLUMN paid_at DATETIME NULL COMMENT '支付时间'
            """
        )
        print("✅ 添加 paid_at 字段成功")
        
        print("\n🎉 所有字段添加完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        print(f"详细错误: {str(e)}")
        
        # 检查字段是否已存在
        if "Duplicate column name" in str(e):
            print("\n⚠️  字段可能已经存在，请检查数据库")
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
