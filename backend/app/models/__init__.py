from tortoise import fields
from tortoise.models import Model
from enum import Enum


class UserRole(str, Enum):
    OWNER = "owner"  # 业主
    MANAGER = "manager"  # 物业管理人员
    MAINTENANCE = "maintenance"  # 维修人员


class User(Model):
    """用户基础表"""
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password = fields.CharField(max_length=255, description="密码哈希")
    name = fields.CharField(max_length=50, description="真实姓名")
    phone = fields.CharField(max_length=20, description="手机号")
    email = fields.CharField(max_length=100, null=True, description="邮箱")
    role = fields.CharEnumField(UserRole, description="用户角色")
    is_active = fields.BooleanField(default=True, description="是否激活")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "users"


class Building(Model):
    """楼栋表"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, description="楼栋名称")
    floors = fields.IntField(description="楼层数")
    units_per_floor = fields.IntField(description="每层单元数")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "buildings"


class Property(Model):
    """房产表"""
    id = fields.IntField(pk=True)
    building = fields.ForeignKeyField("models.Building", related_name="properties", description="所属楼栋")
    unit = fields.CharField(max_length=20, description="单元号")
    floor = fields.IntField(description="楼层")
    room_number = fields.CharField(max_length=20, description="房间号")
    area = fields.DecimalField(max_digits=10, decimal_places=2, description="面积（平方米）")
    owner = fields.ForeignKeyField("models.User", related_name="properties", null=True, description="业主")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "properties"
        unique_together = (("building", "unit", "floor", "room_number"),)


class FeeType(str, Enum):
    PROPERTY = "property"  # 物业费
    PARKING = "parking"  # 停车费
    WATER = "water"  # 水费
    ELECTRICITY = "electricity"  # 电费
    GAS = "gas"  # 燃气费
    HEATING = "heating"  # 供暖费
    OTHER = "other"  # 其他


class BillStatus(str, Enum):
    UNPAID = "unpaid"  # 未支付
    PAID = "paid"  # 已支付
    OVERDUE = "overdue"  # 逾期


class Bill(Model):
    """账单表"""
    id = fields.IntField(pk=True)
    owner = fields.ForeignKeyField("models.User", related_name="bills", description="业主")
    property = fields.ForeignKeyField("models.Property", related_name="bills", description="房产")
    fee_type = fields.CharEnumField(FeeType, description="费用类型")
    amount = fields.DecimalField(max_digits=10, decimal_places=2, description="金额")
    billing_period = fields.CharField(max_length=50, description="账期（如：2024年1月）")
    due_date = fields.DateField(description="截止日期")
    status = fields.CharEnumField(BillStatus, default=BillStatus.UNPAID, description="支付状态")
    paid_at = fields.DatetimeField(null=True, description="支付时间")
    invoice_url = fields.CharField(max_length=500, null=True, description="发票URL")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "bills"


class UrgencyLevel(str, Enum):
    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    URGENT = "urgent"  # 紧急


class RepairStatus(str, Enum):
    PENDING = "pending"  # 待处理
    ASSIGNED = "assigned"  # 已分配
    IN_PROGRESS = "in_progress"  # 维修中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class RepairOrder(Model):
    """报修工单表"""
    id = fields.IntField(pk=True)
    order_number = fields.CharField(max_length=50, unique=True, description="工单号")
    owner = fields.ForeignKeyField("models.User", related_name="repair_orders", description="业主")
    property = fields.ForeignKeyField("models.Property", related_name="repair_orders", description="房产")
    description = fields.TextField(description="问题描述")
    images = fields.JSONField(default=list, description="图片URL列表")
    urgency_level = fields.CharEnumField(UrgencyLevel, description="紧急程度")
    status = fields.CharEnumField(RepairStatus, default=RepairStatus.PENDING, description="工单状态")
    maintenance_worker = fields.ForeignKeyField("models.User", related_name="assigned_orders", null=True, description="维修人员")
    assigned_at = fields.DatetimeField(null=True, description="分配时间")
    started_at = fields.DatetimeField(null=True, description="开始时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    repair_images = fields.JSONField(default=list, description="维修现场图片")
    rating = fields.IntField(null=True, description="评分（1-5）")
    comment = fields.TextField(null=True, description="评价")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "repair_orders"


class Announcement(Model):
    """公告表"""
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200, description="标题")
    content = fields.TextField(description="内容")
    publisher = fields.ForeignKeyField("models.User", related_name="announcements", description="发布人")
    is_published = fields.BooleanField(default=True, description="是否发布")
    published_at = fields.DatetimeField(null=True, description="发布时间")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "announcements"


class FeeStandard(Model):
    """收费标准表"""
    id = fields.IntField(pk=True)
    fee_type = fields.CharEnumField(FeeType, description="费用类型")
    name = fields.CharField(max_length=100, description="费用名称")
    unit_price = fields.DecimalField(max_digits=10, decimal_places=2, description="单价")
    unit = fields.CharField(max_length=20, description="单位（如：元/平方米/月）")
    description = fields.TextField(null=True, description="说明")
    is_active = fields.BooleanField(default=True, description="是否启用")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "fee_standards"


class ChatMessage(Model):
    """AI客服聊天记录"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="chat_messages", description="用户")
    message = fields.TextField(description="用户消息")
    reply = fields.TextField(description="AI回复")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "chat_messages"
