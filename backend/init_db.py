"""
初始化数据库脚本
创建初始管理员账户和示例数据
"""
import asyncio
from tortoise import Tortoise
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, UserRole, Building, Property, FeeStandard, FeeType
from decimal import Decimal


async def init_database():
    """初始化数据库"""
    # 初始化Tortoise ORM
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['app.models']}
    )
    
    # 生成数据库表
    await Tortoise.generate_schemas()
    
    print("数据库表创建成功！")
    
    # 创建默认管理员账户
    admin = await User.get_or_none(username="admin")
    if not admin:
        admin = await User.create(
            username="admin",
            password=get_password_hash("admin123"),
            name="系统管理员",
            phone="13800138000",
            email="admin@property.com",
            role=UserRole.MANAGER,
            is_active=True
        )
        print(f"创建管理员账户: username=admin, password=admin123")
    
    # 创建示例业主
    owner1 = await User.get_or_none(username="owner001")
    if not owner1:
        owner1 = await User.create(
            username="owner001",
            password=get_password_hash("123456"),
            name="张三",
            phone="13900139001",
            email="zhangsan@example.com",
            role=UserRole.OWNER,
            is_active=True
        )
        print(f"创建业主账户: username=owner001, password=123456")
    
    owner2 = await User.get_or_none(username="owner002")
    if not owner2:
        owner2 = await User.create(
            username="owner002",
            password=get_password_hash("123456"),
            name="李四",
            phone="13900139002",
            email="lisi@example.com",
            role=UserRole.OWNER,
            is_active=True
        )
        print(f"创建业主账户: username=owner002, password=123456")
    
    # 创建示例维修人员
    maintenance1 = await User.get_or_none(username="repair001")
    if not maintenance1:
        maintenance1 = await User.create(
            username="repair001",
            password=get_password_hash("123456"),
            name="王师傅",
            phone="13900139003",
            email="wangshifu@example.com",
            role=UserRole.MAINTENANCE,
            is_active=True
        )
        print(f"创建维修人员账户: username=repair001, password=123456")
    
    # 创建楼栋
    building1 = await Building.get_or_none(name="1号楼")
    if not building1:
        building1 = await Building.create(
            name="1号楼",
            floors=6,
            units_per_floor=2
        )
        print("创建楼栋: 1号楼")
    
    building2 = await Building.get_or_none(name="2号楼")
    if not building2:
        building2 = await Building.create(
            name="2号楼",
            floors=10,
            units_per_floor=4
        )
        print("创建楼栋: 2号楼")
    
    # 创建房产
    property1 = await Property.get_or_none(building_id=building1.id, unit="1", floor=3, room_number="301")
    if not property1:
        property1 = await Property.create(
            building_id=building1.id,
            unit="1",
            floor=3,
            room_number="301",
            area=Decimal("95.5"),
            owner_id=owner1.id
        )
        print("创建房产: 1号楼1单元301")
    
    property2 = await Property.get_or_none(building_id=building2.id, unit="2", floor=5, room_number="502")
    if not property2:
        property2 = await Property.create(
            building_id=building2.id,
            unit="2",
            floor=5,
            room_number="502",
            area=Decimal("120.0"),
            owner_id=owner2.id
        )
        print("创建房产: 2号楼2单元502")
    
    # 创建收费标准
    fee_standards = [
        {
            "fee_type": FeeType.PROPERTY,
            "name": "物业管理费",
            "unit_price": Decimal("2.5"),
            "unit": "元/平方米/月",
            "description": "包含公共区域清洁、绿化养护、秩序维护等服务"
        },
        {
            "fee_type": FeeType.PARKING,
            "name": "停车费",
            "unit_price": Decimal("200.0"),
            "unit": "元/月",
            "description": "地下停车场车位月租"
        },
        {
            "fee_type": FeeType.WATER,
            "name": "水费",
            "unit_price": Decimal("3.5"),
            "unit": "元/吨",
            "description": "居民生活用水"
        },
        {
            "fee_type": FeeType.ELECTRICITY,
            "name": "电费",
            "unit_price": Decimal("0.6"),
            "unit": "元/度",
            "description": "居民生活用电"
        }
    ]
    
    for standard in fee_standards:
        existing = await FeeStandard.get_or_none(fee_type=standard["fee_type"])
        if not existing:
            await FeeStandard.create(**standard)
            print(f"创建收费标准: {standard['name']}")
    
    print("\n初始化完成！")
    print("\n账户信息:")
    print("管理员 - username: admin, password: admin123")
    print("业主1 - username: owner001, password: 123456")
    print("业主2 - username: owner002, password: 123456")
    print("维修人员 - username: repair001, password: 123456")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(init_database())
