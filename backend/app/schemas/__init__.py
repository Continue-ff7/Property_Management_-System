from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ============= 用户相关 =============
class UserBase(BaseModel):
    username: str
    name: str
    phone: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str
    role: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ============= 房产相关 =============
class PropertyBase(BaseModel):
    unit: str
    floor: int
    room_number: str
    area: Decimal


class PropertyCreate(PropertyBase):
    building_id: int
    owner_id: Optional[int] = None


class PropertyResponse(PropertyBase):
    id: int
    building_id: int
    owner_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PropertyWithOwner(PropertyResponse):
    owner_name: Optional[str] = None
    building_name: str


# ============= 楼栋相关 =============
class BuildingBase(BaseModel):
    name: str
    floors: int
    units_per_floor: int


class BuildingCreate(BuildingBase):
    pass


class BuildingResponse(BuildingBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 账单相关 =============
class BillBase(BaseModel):
    fee_type: str
    amount: Decimal
    billing_period: str
    due_date: date


class BillCreate(BillBase):
    owner_id: int
    property_id: int


class BillResponse(BillBase):
    id: int
    owner_id: int
    property_id: int
    status: str
    paid_at: Optional[datetime]
    invoice_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BillWithDetails(BillResponse):
    owner_name: str
    property_info: str  # 例如: "1栋2单元301"


class PaymentRequest(BaseModel):
    bill_id: int
    payment_method: str  # "alipay", "wechat", "bank"


# ============= 报修相关 =============
class RepairOrderCreate(BaseModel):
    property_id: int
    description: str
    urgency_level: str
    images: List[str] = []


class RepairOrderUpdate(BaseModel):
    status: Optional[str] = None
    maintenance_worker_id: Optional[int] = None
    repair_images: Optional[List[str]] = None


class RepairOrderResponse(BaseModel):
    id: int
    order_number: str
    owner_id: int
    property_id: int
    description: str
    images: List[str]
    urgency_level: str
    status: str
    maintenance_worker_id: Optional[int]
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    repair_images: List[str]
    rating: Optional[int]
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RepairOrderWithDetails(RepairOrderResponse):
    owner_name: str
    owner_phone: str
    property_info: str
    maintenance_worker_name: Optional[str] = None


class RepairEvaluation(BaseModel):
    rating: int  # 1-5
    comment: str


# ============= 公告相关 =============
class AnnouncementCreate(BaseModel):
    title: str
    content: str


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    publisher_id: int
    is_published: bool
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnnouncementWithPublisher(AnnouncementResponse):
    publisher_name: str


# ============= 收费标准相关 =============
class FeeStandardCreate(BaseModel):
    fee_type: str
    name: str
    unit_price: Decimal
    unit: str
    description: Optional[str] = None


class FeeStandardUpdate(BaseModel):
    name: Optional[str] = None
    unit_price: Optional[Decimal] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FeeStandardResponse(BaseModel):
    id: int
    fee_type: str
    name: str
    unit_price: Decimal
    unit: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= AI客服相关 =============
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    reply: str
    created_at: datetime


# ============= 统计报表相关 =============
class RevenueStatistics(BaseModel):
    total_revenue: Decimal
    paid_revenue: Decimal
    unpaid_revenue: Decimal
    overdue_revenue: Decimal
    payment_rate: float


class RepairStatistics(BaseModel):
    total_orders: int
    pending_orders: int
    in_progress_orders: int
    completed_orders: int
    average_rating: Optional[float]


class OwnerStatistics(BaseModel):
    total_owners: int
    active_owners: int
    total_properties: int


# ============= 通用响应 =============
class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List
