"""清理停用业主脚本"""
import asyncio
from tortoise import Tortoise
from app.models import User, Property, Bill, RepairOrder, UserRole


async def clean_inactive_owners():
    """清理停用的业主"""
    # 初始化数据库连接
    await Tortoise.init(
        db_url="mysql://root:123456@localhost:3306/property_management",
        modules={"models": ["app.models"]}
    )
    
    # 查找ID为5和6的业主
    target_ids = [5, 6]
    users = await User.filter(id__in=target_ids, role=UserRole.OWNER)
    
    print(f"\n找到 {len(users)} 个目标业主:")
    for user in users:
        print(f"  ID: {user.id}, 姓名: {user.name}, 状态: {'停用' if not user.is_active else '正常'}")
        
        # 检查关联数据
        property_count = await Property.filter(owner_id=user.id).count()
        bill_count = await Bill.filter(owner_id=user.id).count()
        repair_count = await RepairOrder.filter(owner_id=user.id).count()
        
        print(f"    - 关联房产: {property_count}个")
        print(f"    - 关联账单: {bill_count}条")
        print(f"    - 关联报修: {repair_count}个")
        
        if property_count > 0 or bill_count > 0 or repair_count > 0:
            print(f"    ⚠️  需要先清理关联数据")
            
            # 解绑房产
            if property_count > 0:
                await Property.filter(owner_id=user.id).update(owner_id=None)
                print(f"    ✓ 已解绑 {property_count} 个房产")
            
            # 删除账单
            if bill_count > 0:
                await Bill.filter(owner_id=user.id).delete()
                print(f"    ✓ 已删除 {bill_count} 条账单")
            
            # 删除报修
            if repair_count > 0:
                await RepairOrder.filter(owner_id=user.id).delete()
                print(f"    ✓ 已删除 {repair_count} 个报修工单")
        
        # 删除业主
        await user.delete()
        print(f"    ✅ 业主 {user.name} 已删除\n")
    
    print("✅ 清理完成!")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(clean_inactive_owners())
