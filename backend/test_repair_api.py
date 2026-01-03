"""测试维修订单接口"""
import asyncio
import sys
sys.path.insert(0, 'd:/property-management-system/backend')

async def test_repair_orders():
    from tortoise import Tortoise
    from app.core.config import settings
    from app.models import RepairOrder, User
    
    try:
        # 初始化数据库
        await Tortoise.init(
            db_url=settings.DATABASE_URL,
            modules={'models': ['app.models']}
        )
        
        print("✅ 数据库连接成功")
        
        # 查找一个业主用户
        owner = await User.filter(role='owner').first()
        if not owner:
            print("❌ 没有找到业主用户")
            return
        
        print(f"✅ 找到业主: {owner.name} (ID: {owner.id})")
        
        # 查询该业主的工单
        orders = await RepairOrder.filter(owner_id=owner.id).prefetch_related(
            "property", "property__building", "maintenance_worker"
        ).limit(5)
        
        print(f"✅ 找到 {len(orders)} 个工单")
        
        # 尝试序列化第一个工单
        if orders:
            order = orders[0]
            print(f"\n--- 工单信息 ---")
            print(f"ID: {order.id}")
            print(f"工单号: {order.order_number}")
            print(f"状态: {order.status}")
            print(f"维修费用: {order.repair_cost} (类型: {type(order.repair_cost)})")
            print(f"已支付: {order.cost_paid}")
            print(f"支付时间: {order.paid_at}")
            
            # 测试转换
            try:
                if order.repair_cost:
                    cost_float = float(order.repair_cost)
                    print(f"✅ 费用转换成功: {cost_float}")
                else:
                    print("✅ 费用为空，转换为 None")
            except Exception as e:
                print(f"❌ 费用转换失败: {e}")
            
            # 构造返回数据
            try:
                property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
                result = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "repair_cost": float(order.repair_cost) if order.repair_cost else None,
                    "cost_paid": order.cost_paid,
                    "paid_at": order.paid_at,
                    "property_info": property_info
                }
                print(f"\n✅ 数据构造成功:")
                print(result)
            except Exception as e:
                print(f"\n❌ 数据构造失败: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_repair_orders())
