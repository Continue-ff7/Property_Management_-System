"""
添加新的维修工单状态：pending_payment、pending_evaluation、finished
执行时间：2026-01-03

执行方式：
python add_new_repair_statuses.py
"""

import asyncio
from tortoise import Tortoise
from app.core.config import settings


async def migrate():
    """添加新状态枚举值"""
    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]}
    )
    
    conn = Tortoise.get_connection("default")
    
    try:
        print("📋 开始添加新的维修工单状态...")
        
        # 修改枚举类型，添加新的状态值
        await conn.execute_query("""
            ALTER TABLE repair_orders 
            MODIFY COLUMN status ENUM(
                'pending', 
                'assigned', 
                'in_progress', 
                'completed',
                'pending_payment',
                'pending_evaluation', 
                'finished',
                'cancelled'
            ) DEFAULT 'pending'
        """)
        
        print("✅ 成功添加新状态：pending_payment, pending_evaluation, finished")
        
        # 迁移现有数据：将已完成且已评价的工单改为 finished
        result = await conn.execute_query("""
            UPDATE repair_orders 
            SET status = 'finished'
            WHERE status = 'completed' 
            AND rating IS NOT NULL
        """)
        print(f"✅ 已将 {result} 个已评价的工单状态改为 finished")
        
        # 迁移现有数据：将已完成且有费用未支付的工单改为 pending_payment
        result = await conn.execute_query("""
            UPDATE repair_orders 
            SET status = 'pending_payment'
            WHERE status = 'completed' 
            AND repair_cost > 0 
            AND cost_paid = FALSE
        """)
        print(f"✅ 已将 {result} 个待支付的工单状态改为 pending_payment")
        
        # 迁移现有数据：将已完成且无费用或已支付但未评价的工单改为 pending_evaluation
        result = await conn.execute_query("""
            UPDATE repair_orders 
            SET status = 'pending_evaluation'
            WHERE status = 'completed' 
            AND rating IS NULL
        """)
        print(f"✅ 已将 {result} 个待评价的工单状态改为 pending_evaluation")
        
        print("\n🎉 数据库迁移成功！")
        print("\n📊 状态说明：")
        print("  - pending_payment: 维修完成，有费用，待支付")
        print("  - pending_evaluation: 维修完成，无费用或已支付，待评价")
        print("  - finished: 已评价，工单完结")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
