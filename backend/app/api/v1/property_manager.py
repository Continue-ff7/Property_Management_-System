from fastapi import APIRouter, HTTPException, Depends, status
from app.core.dependencies import get_current_manager
from app.core.security import get_password_hash
from app.models import (
    User, Property, Bill, RepairOrder, Announcement, FeeStandard, Building,
    UserRole, BillStatus, RepairStatus
)
from app.schemas import (
    UserCreate, UserResponse, PropertyCreate, PropertyWithOwner,
    BillCreate, BillWithDetails, BillResponse, BillBatchCreateRequest, 
    BillBatchCreateByOwnerRequest, SingleBillCreate,
    RepairOrderWithDetails, RepairOrderUpdate,
    AnnouncementCreate, AnnouncementUpdate, AnnouncementWithPublisher,
    FeeStandardCreate, FeeStandardUpdate, FeeStandardResponse,
    BuildingCreate, BuildingResponse,
    RevenueStatistics, RepairStatistics, OwnerStatistics,
    MessageResponse, OwnerCreate, MaintenanceCreate, OwnerUpdate, MaintenanceUpdate
)
from typing import List
from datetime import datetime, date, timedelta
from decimal import Decimal
from tortoise.functions import Count, Sum
from tortoise.expressions import Q

router = APIRouter()


# ============= 业主管理 =============
@router.get("/owners", response_model=List[UserResponse])
async def get_owners(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_manager)
):
    """查看业主列表"""
    query = User.filter(role=UserRole.OWNER)
    
    # 默认只显示活跃的业主，除非明确指定包含停用的
    if not include_inactive:
        query = query.filter(is_active=True)
    
    if search:
        # 修复搜索逻辑
        query = query.filter(
            Q(name__icontains=search) | Q(phone__icontains=search) | Q(username__icontains=search)
        )
    
    owners = await query.offset(skip).limit(limit).order_by("-created_at")
    return owners


@router.get("/owners/{owner_id}", response_model=UserResponse)
async def get_owner_detail(
    owner_id: int,
    current_user: User = Depends(get_current_manager)
):
    """查看业主详情"""
    owner = await User.get_or_none(id=owner_id, role=UserRole.OWNER)
    if not owner:
        raise HTTPException(status_code=404, detail="业主不存在")
    return owner


@router.post("/owners", response_model=UserResponse)
async def create_owner(
    owner_data: OwnerCreate,
    current_user: User = Depends(get_current_manager)
):
    """创建业主"""
    # 检查用户名是否已存在
    existing_user = await User.get_or_none(username=owner_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    owner = await User.create(
        username=owner_data.username,
        password=get_password_hash(owner_data.password),
        name=owner_data.name,
        phone=owner_data.phone,
        email=owner_data.email,
        role=UserRole.OWNER
    )
    return owner


@router.put("/owners/{owner_id}", response_model=UserResponse)
async def update_owner(
    owner_id: int,
    owner_data: OwnerUpdate,
    current_user: User = Depends(get_current_manager)
):
    """修改业主信息"""
    owner = await User.get_or_none(id=owner_id, role=UserRole.OWNER)
    if not owner:
        raise HTTPException(status_code=404, detail="业主不存在")
    
    owner.name = owner_data.name
    owner.phone = owner_data.phone
    owner.email = owner_data.email
    if owner_data.password:
        owner.password = get_password_hash(owner_data.password)
    
    await owner.save()
    return owner


@router.delete("/owners/{owner_id}", response_model=MessageResponse)
async def delete_owner(
    owner_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_manager)
):
    """删除业主账户（真删除）"""
    owner = await User.get_or_none(id=owner_id, role=UserRole.OWNER)
    if not owner:
        raise HTTPException(status_code=404, detail="业主不存在")
    
    # 检查是否有关联的房产
    property_count = await Property.filter(owner_id=owner_id).count()
    
    # 检查是否有关联的账单
    bill_count = await Bill.filter(owner_id=owner_id).count()
    
    # 检查是否有关联的报修工单
    repair_count = await RepairOrder.filter(owner_id=owner_id).count()
    
    # 如果有任何关联数据且不是强制删除，则不允许删除
    if (property_count > 0 or bill_count > 0 or repair_count > 0) and not force:
        error_msg = []
        if property_count > 0:
            error_msg.append(f"{property_count}个房产")
        if bill_count > 0:
            error_msg.append(f"{bill_count}条账单")
        if repair_count > 0:
            error_msg.append(f"{repair_count}个报修工单")
        
        raise HTTPException(
            status_code=400, 
            detail=f"该业主有{', '.join(error_msg)}，不允许删除。请先处理完相关数据。"
        )
    
    # 如果强制删除，先解绑所有房产、删除账单和报修工单
    if force:
        if property_count > 0:
            await Property.filter(owner_id=owner_id).update(owner_id=None)
        if bill_count > 0:
            await Bill.filter(owner_id=owner_id).delete()
        if repair_count > 0:
            await RepairOrder.filter(owner_id=owner_id).delete()
    
    # 真删除
    await owner.delete()
    return MessageResponse(message="业主账户已删除")


@router.get("/owners/{owner_id}/properties", response_model=List[PropertyWithOwner])
async def get_owner_properties(
    owner_id: int,
    current_user: User = Depends(get_current_manager)
):
    """查看业主房产"""
    owner = await User.get_or_none(id=owner_id, role=UserRole.OWNER)
    if not owner:
        raise HTTPException(status_code=404, detail="业主不存在")
    
    properties = await Property.filter(owner_id=owner_id).prefetch_related("building")
    
    result = []
    for prop in properties:
        result.append({
            "id": prop.id,
            "building_id": prop.building_id,
            "unit": prop.unit,
            "floor": prop.floor,
            "room_number": prop.room_number,
            "area": prop.area,
            "owner_id": prop.owner_id,
            "created_at": prop.created_at,
            "owner_name": owner.name,
            "building_name": prop.building.name
        })
    
    return result


# ============= 房产管理 =============
@router.get("/buildings", response_model=List[BuildingResponse])
async def get_buildings(
    current_user: User = Depends(get_current_manager)
):
    """获取楼栋列表"""
    buildings = await Building.all()
    return buildings


@router.post("/buildings", response_model=BuildingResponse)
async def create_building(
    building_data: BuildingCreate,
    current_user: User = Depends(get_current_manager)
):
    """创建楼栋"""
    building = await Building.create(**building_data.model_dump())
    return building


@router.get("/properties", response_model=List[PropertyWithOwner])
async def get_properties(
    building_id: int = None,
    owner_id: int = None,
    unassigned: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_manager)
):
    """获取房产列表"""
    query = Property.all()
    
    if building_id:
        query = query.filter(building_id=building_id)
    
    if owner_id:
        query = query.filter(owner_id=owner_id)
    
    # 查询未分配的房产
    if unassigned:
        query = query.filter(owner_id__isnull=True)
    
    properties = await query.offset(skip).limit(limit).prefetch_related("building", "owner")
    
    result = []
    for prop in properties:
        result.append({
            "id": prop.id,
            "building_id": prop.building_id,
            "unit": prop.unit,
            "floor": prop.floor,
            "room_number": prop.room_number,
            "area": prop.area,
            "owner_id": prop.owner_id,
            "created_at": prop.created_at,
            "owner_name": prop.owner.name if prop.owner else None,
            "building_name": prop.building.name
        })
    
    return result


@router.post("/properties", response_model=PropertyWithOwner)
async def create_property(
    property_data: PropertyCreate,
    current_user: User = Depends(get_current_manager)
):
    """创建房产"""
    # 验证楼栋存在
    building = await Building.get_or_none(id=property_data.building_id)
    if not building:
        raise HTTPException(status_code=404, detail="楼栋不存在")
    
    # 验证业主存在（如果提供）
    if property_data.owner_id:
        owner = await User.get_or_none(id=property_data.owner_id, role=UserRole.OWNER)
        if not owner:
            raise HTTPException(status_code=404, detail="业主不存在")
    
    property_obj = await Property.create(**property_data.model_dump())
    await property_obj.fetch_related("building", "owner")
    
    return {
        "id": property_obj.id,
        "building_id": property_obj.building_id,
        "unit": property_obj.unit,
        "floor": property_obj.floor,
        "room_number": property_obj.room_number,
        "area": property_obj.area,
        "owner_id": property_obj.owner_id,
        "created_at": property_obj.created_at,
        "owner_name": property_obj.owner.name if property_obj.owner else None,
        "building_name": property_obj.building.name
    }


@router.put("/properties/{property_id}/assign-owner", response_model=MessageResponse)
async def assign_property_owner(
    property_id: int,
    owner_id: int,
    current_user: User = Depends(get_current_manager)
):
    """分配房产给业主"""
    property_obj = await Property.get_or_none(id=property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="房产不存在")
    
    owner = await User.get_or_none(id=owner_id, role=UserRole.OWNER)
    if not owner:
        raise HTTPException(status_code=404, detail="业主不存在")
    
    property_obj.owner_id = owner_id
    await property_obj.save()
    return MessageResponse(message="房产已分配给业主")


@router.delete("/properties/{property_id}/owner", response_model=MessageResponse)
async def unbind_property_owner(
    property_id: int,
    current_user: User = Depends(get_current_manager)
):
    """解绑房产业主"""
    property_obj = await Property.get_or_none(id=property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="房产不存在")
    
    property_obj.owner_id = None
    await property_obj.save()
    return MessageResponse(message="房产已解绑业主")


# ============= 账单管理 =============
@router.get("/fee-standards", response_model=List[FeeStandardResponse])
async def get_fee_standards(
    current_user: User = Depends(get_current_manager)
):
    """获取收费标准列表"""
    standards = await FeeStandard.filter(is_active=True)
    return standards


@router.post("/fee-standards", response_model=FeeStandardResponse)
async def create_fee_standard(
    standard_data: FeeStandardCreate,
    current_user: User = Depends(get_current_manager)
):
    """创建收费标准"""
    standard = await FeeStandard.create(**standard_data.model_dump())
    return standard


@router.put("/fee-standards/{standard_id}", response_model=FeeStandardResponse)
async def update_fee_standard(
    standard_id: int,
    standard_data: FeeStandardUpdate,
    current_user: User = Depends(get_current_manager)
):
    """更新收费标准"""
    standard = await FeeStandard.get_or_none(id=standard_id)
    if not standard:
        raise HTTPException(status_code=404, detail="收费标准不存在")
    
    update_data = standard_data.model_dump(exclude_unset=True)
    await standard.update_from_dict(update_data).save()
    return standard


@router.post("/bills", response_model=BillResponse)
async def create_bill(
    bill_data: BillCreate,
    current_user: User = Depends(get_current_manager)
):
    """生成账单"""
    # 验证业主和房产
    owner = await User.get_or_none(id=bill_data.owner_id, role=UserRole.OWNER)
    if not owner:
        raise HTTPException(status_code=404, detail="业主不存在")
    
    property_obj = await Property.get_or_none(id=bill_data.property_id, owner_id=bill_data.owner_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="房产不存在或不属于该业主")
    
    bill = await Bill.create(**bill_data.model_dump())
    
    return BillResponse(
        id=bill.id,
        owner_id=bill.owner_id,
        property_id=bill.property_id,
        fee_type=bill.fee_type.value,
        amount=bill.amount,
        billing_period=bill.billing_period,
        due_date=bill.due_date,
        status=bill.status.value,
        paid_at=bill.paid_at,
        invoice_url=bill.invoice_url,
        created_at=bill.created_at
    )


@router.post("/bills/batch")
async def create_bills_batch(
    request: BillBatchCreateRequest,
    current_user: User = Depends(get_current_manager)
):
    """批量生成账单（按收费标准）"""
    # 获取收费标准
    standard = await FeeStandard.get_or_none(fee_type=request.fee_type, is_active=True)
    if not standard:
        raise HTTPException(status_code=404, detail="收费标准不存在")
    
    # 构建查询
    query = Property.filter(owner_id__not_isnull=True)
    
    # 如果指定了业主，只为这些业主生成
    if request.owner_ids:
        query = query.filter(owner_id__in=request.owner_ids)
    
    properties = await query.prefetch_related("owner")
    
    created_count = 0
    skipped_count = 0
    
    for property_obj in properties:
        # 计算金额（根据面积）
        amount = property_obj.area * standard.unit_price
        
        # 检查是否已存在相同账期的账单
        existing_bill = await Bill.get_or_none(
            owner_id=property_obj.owner_id,
            property_id=property_obj.id,
            fee_type=request.fee_type,
            billing_period=request.billing_period
        )
        
        if not existing_bill:
            await Bill.create(
                owner_id=property_obj.owner_id,
                property_id=property_obj.id,
                fee_type=request.fee_type,
                amount=amount,
                billing_period=request.billing_period,
                due_date=request.due_date
            )
            created_count += 1
        else:
            skipped_count += 1
    
    return {
        "message": f"成功生成 {created_count} 条账单",
        "created": created_count,
        "skipped": skipped_count,
        "total": created_count + skipped_count
    }


@router.post("/bills/batch-by-owner")
async def create_bills_for_owner(
    request: BillBatchCreateByOwnerRequest,
    current_user: User = Depends(get_current_manager)
):
    """为指定业主批量创建账单（可自定义金额）"""
    # 验证业主存在
    owner = await User.get_or_none(id=request.owner_id, role=UserRole.OWNER)
    if not owner:
        raise HTTPException(status_code=404, detail="业主不存在")
    
    created_count = 0
    errors = []
    
    for bill_data in request.bills:
        # 验证房产存在且属于该业主
        property_obj = await Property.get_or_none(
            id=bill_data.property_id, 
            owner_id=request.owner_id
        )
        if not property_obj:
            errors.append(f"房产ID {bill_data.property_id} 不存在或不属于该业主")
            continue
        
        # 检查是否已存在
        existing_bill = await Bill.get_or_none(
            owner_id=request.owner_id,
            property_id=bill_data.property_id,
            fee_type=bill_data.fee_type,
            billing_period=bill_data.billing_period
        )
        
        if existing_bill:
            errors.append(f"房产ID {bill_data.property_id} 的 {bill_data.fee_type} 账单已存在")
            continue
        
        # 创建账单
        await Bill.create(
            owner_id=request.owner_id,
            property_id=bill_data.property_id,
            fee_type=bill_data.fee_type,
            amount=bill_data.amount,
            billing_period=bill_data.billing_period,
            due_date=bill_data.due_date
        )
        created_count += 1
    
    result = {
        "message": f"成功创建 {created_count} 条账单",
        "created": created_count,
        "total": len(request.bills)
    }
    
    if errors:
        result["errors"] = errors
    
    return result


@router.get("/bills", response_model=List[BillWithDetails])
async def get_all_bills(
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_manager)
):
    """查看所有账单"""
    query = Bill.all()
    
    if status:
        query = query.filter(status=status)
    
    bills = await query.order_by("-created_at").offset(skip).limit(limit).prefetch_related(
        "owner", "property", "property__building"
    )
    
    result = []
    for bill in bills:
        property_info = f"{bill.property.building.name}{bill.property.unit}单元{bill.property.room_number}"
        result.append({
            "id": bill.id,
            "owner_id": bill.owner_id,
            "property_id": bill.property_id,
            "fee_type": bill.fee_type.value,
            "amount": bill.amount,
            "billing_period": bill.billing_period,
            "due_date": bill.due_date,
            "status": bill.status.value,
            "paid_at": bill.paid_at,
            "invoice_url": bill.invoice_url,
            "created_at": bill.created_at,
            "owner_name": bill.owner.name,
            "property_info": property_info
        })
    
    return result


@router.put("/bills/{bill_id}", response_model=BillResponse)
async def update_bill(
    bill_id: int,
    amount: Decimal = None,
    billing_period: str = None,
    due_date: date = None,
    current_user: User = Depends(get_current_manager)
):
    """修改账单（仅允许修改未支付的账单）"""
    bill = await Bill.get_or_none(id=bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="账单不存在")
    
    if bill.status != BillStatus.UNPAID:
        raise HTTPException(status_code=400, detail="只能修改未支付的账单")
    
    if amount is not None:
        bill.amount = amount
    if billing_period is not None:
        bill.billing_period = billing_period
    if due_date is not None:
        bill.due_date = due_date
    
    await bill.save()
    
    return BillResponse(
        id=bill.id,
        owner_id=bill.owner_id,
        property_id=bill.property_id,
        fee_type=bill.fee_type.value,
        amount=bill.amount,
        billing_period=bill.billing_period,
        due_date=bill.due_date,
        status=bill.status.value,
        paid_at=bill.paid_at,
        invoice_url=bill.invoice_url,
        created_at=bill.created_at
    )


@router.delete("/bills/{bill_id}", response_model=MessageResponse)
async def delete_bill(
    bill_id: int,
    current_user: User = Depends(get_current_manager)
):
    """删除账单（仅允许删除未支付的账单）"""
    bill = await Bill.get_or_none(id=bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="账单不存在")
    
    if bill.status != BillStatus.UNPAID:
        raise HTTPException(status_code=400, detail="只能删除未支付的账单")
    
    await bill.delete()
    return MessageResponse(message="账单已删除")


# ============= 报修管理 =============
@router.get("/repairs", response_model=List[RepairOrderWithDetails])
async def get_all_repair_orders(
    status: str = None,
    urgency_level: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_manager)
):
    """查看所有报修工单"""
    query = RepairOrder.all()
    
    if status:
        query = query.filter(status=status)
    
    if urgency_level:
        query = query.filter(urgency_level=urgency_level)
    
    orders = await query.order_by("-created_at").offset(skip).limit(limit).prefetch_related(
        "owner", "property", "property__building", "maintenance_worker"
    )
    
    result = []
    for order in orders:
        property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
        
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "owner_id": order.owner_id,
            "property_id": order.property_id,
            "description": order.description,
            "images": order.images,
            "urgency_level": order.urgency_level.value,
            "status": order.status.value,
            "maintenance_worker_id": order.maintenance_worker_id,
            "assigned_at": order.assigned_at,
            "started_at": order.started_at,
            "completed_at": order.completed_at,
            "repair_images": order.repair_images,
            "rating": order.rating,
            "comment": order.comment,
            "created_at": order.created_at,
            "owner_name": order.owner.name,
            "owner_phone": order.owner.phone,
            "property_info": property_info,
            "maintenance_worker_name": order.maintenance_worker.name if order.maintenance_worker else None
        })
    
    return result


@router.post("/repairs/{order_id}/assign", response_model=MessageResponse)
async def assign_repair_order(
    order_id: int,
    maintenance_worker_id: int,
    current_user: User = Depends(get_current_manager)
):
    """分配维修工单"""
    order = await RepairOrder.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # 验证维修人员存在
    worker = await User.get_or_none(id=maintenance_worker_id, role=UserRole.MAINTENANCE)
    if not worker:
        raise HTTPException(status_code=404, detail="维修人员不存在")
    
    order.maintenance_worker_id = maintenance_worker_id
    order.status = RepairStatus.ASSIGNED
    order.assigned_at = datetime.now()
    await order.save()
    
    return MessageResponse(message="工单已分配")


@router.put("/repairs/{order_id}", response_model=MessageResponse)
async def update_repair_order_status(
    order_id: int,
    update_data: RepairOrderUpdate,
    current_user: User = Depends(get_current_manager)
):
    """更新工单状态"""
    order = await RepairOrder.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if update_data.status:
        order.status = update_data.status
    
    if update_data.maintenance_worker_id:
        worker = await User.get_or_none(id=update_data.maintenance_worker_id, role=UserRole.MAINTENANCE)
        if not worker:
            raise HTTPException(status_code=404, detail="维修人员不存在")
        order.maintenance_worker_id = update_data.maintenance_worker_id
        order.assigned_at = datetime.now()
    
    await order.save()
    return MessageResponse(message="工单已更新")


# ============= 维修人员管理 =============
@router.get("/maintenance-workers", response_model=List[UserResponse])
async def get_maintenance_workers(
    current_user: User = Depends(get_current_manager)
):
    """获取维修人员列表"""
    workers = await User.filter(role=UserRole.MAINTENANCE, is_active=True)
    return workers


@router.post("/maintenance-workers", response_model=UserResponse)
async def create_maintenance_worker(
    worker_data: MaintenanceCreate,
    current_user: User = Depends(get_current_manager)
):
    """创建维修人员"""
    # 检查用户名是否已存在
    existing_user = await User.get_or_none(username=worker_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    worker = await User.create(
        username=worker_data.username,
        password=get_password_hash(worker_data.password),
        name=worker_data.name,
        phone=worker_data.phone,
        email=worker_data.email,
        role=UserRole.MAINTENANCE
    )
    return worker


@router.put("/maintenance-workers/{worker_id}", response_model=UserResponse)
async def update_maintenance_worker(
    worker_id: int,
    worker_data: MaintenanceUpdate,
    current_user: User = Depends(get_current_manager)
):
    """更新维修人员信息"""
    worker = await User.get_or_none(id=worker_id, role=UserRole.MAINTENANCE)
    if not worker:
        raise HTTPException(status_code=404, detail="维修人员不存在")
    
    worker.name = worker_data.name
    worker.phone = worker_data.phone
    worker.email = worker_data.email
    if worker_data.password:
        worker.password = get_password_hash(worker_data.password)
    
    await worker.save()
    return worker


@router.delete("/maintenance-workers/{worker_id}", response_model=MessageResponse)
async def delete_maintenance_worker(
    worker_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_manager)
):
    """删除维修人员"""
    worker = await User.get_or_none(id=worker_id, role=UserRole.MAINTENANCE)
    if not worker:
        raise HTTPException(status_code=404, detail="维修人员不存在")
    
    # 检查是否有关联的维修工单
    repair_count = await RepairOrder.filter(maintenance_worker_id=worker_id).count()
    
    if repair_count > 0 and not force:
        raise HTTPException(
            status_code=400, 
            detail=f"该维修人员有 {repair_count} 个关联的维修工单"
        )
    
    # 如果强制删除，解绑所有关联工单
    if force and repair_count > 0:
        await RepairOrder.filter(maintenance_worker_id=worker_id).update(
            maintenance_worker_id=None,
            status=RepairStatus.PENDING  # 重置为待分配状态
        )
    
    # 真删除
    await worker.delete()
    return MessageResponse(message="维修人员已删除")


# ============= 公告管理 =============
@router.post("/announcements", response_model=AnnouncementWithPublisher)
async def create_announcement(
    announcement_data: AnnouncementCreate,
    current_user: User = Depends(get_current_manager)
):
    """发布公告"""
    announcement = await Announcement.create(
        title=announcement_data.title,
        content=announcement_data.content,
        publisher_id=current_user.id,
        published_at=datetime.now()
    )
    
    return {
        "id": announcement.id,
        "title": announcement.title,
        "content": announcement.content,
        "publisher_id": announcement.publisher_id,
        "is_published": announcement.is_published,
        "published_at": announcement.published_at,
        "created_at": announcement.created_at,
        "publisher_name": current_user.name
    }


@router.get("/announcements", response_model=List[AnnouncementWithPublisher])
async def get_all_announcements(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_manager)
):
    """获取所有公告"""
    announcements = await Announcement.all().order_by("-created_at").offset(skip).limit(limit).prefetch_related("publisher")
    
    result = []
    for ann in announcements:
        result.append({
            "id": ann.id,
            "title": ann.title,
            "content": ann.content,
            "publisher_id": ann.publisher_id,
            "is_published": ann.is_published,
            "published_at": ann.published_at,
            "created_at": ann.created_at,
            "publisher_name": ann.publisher.name
        })
    
    return result


@router.put("/announcements/{announcement_id}", response_model=MessageResponse)
async def update_announcement(
    announcement_id: int,
    announcement_data: AnnouncementUpdate,
    current_user: User = Depends(get_current_manager)
):
    """更新公告"""
    announcement = await Announcement.get_or_none(id=announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    update_data = announcement_data.model_dump(exclude_unset=True)
    await announcement.update_from_dict(update_data).save()
    
    return MessageResponse(message="公告已更新")


@router.delete("/announcements/{announcement_id}", response_model=MessageResponse)
async def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_manager)
):
    """删除公告"""
    announcement = await Announcement.get_or_none(id=announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    await announcement.delete()
    return MessageResponse(message="公告已删除")


# ============= 数据统计 =============
@router.get("/statistics/revenue", response_model=RevenueStatistics)
async def get_revenue_statistics(
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(get_current_manager)
):
    """获取收入统计"""
    query = Bill.all()
    
    if start_date:
        query = query.filter(created_at__gte=start_date)
    if end_date:
        query = query.filter(created_at__lte=end_date)
    
    bills = await query
    
    total_revenue = sum(bill.amount for bill in bills)
    paid_revenue = sum(bill.amount for bill in bills if bill.status == BillStatus.PAID)
    unpaid_revenue = sum(bill.amount for bill in bills if bill.status == BillStatus.UNPAID)
    overdue_revenue = sum(bill.amount for bill in bills if bill.status == BillStatus.OVERDUE)
    
    payment_rate = (paid_revenue / total_revenue * 100) if total_revenue > 0 else 0
    
    return RevenueStatistics(
        total_revenue=total_revenue,
        paid_revenue=paid_revenue,
        unpaid_revenue=unpaid_revenue,
        overdue_revenue=overdue_revenue,
        payment_rate=round(payment_rate, 2)
    )


@router.get("/statistics/repairs", response_model=RepairStatistics)
async def get_repair_statistics(
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(get_current_manager)
):
    """获取维修统计"""
    query = RepairOrder.all()
    
    if start_date:
        query = query.filter(created_at__gte=start_date)
    if end_date:
        query = query.filter(created_at__lte=end_date)
    
    orders = await query
    
    total_orders = len(orders)
    pending_orders = sum(1 for order in orders if order.status == RepairStatus.PENDING)
    in_progress_orders = sum(1 for order in orders if order.status in [RepairStatus.ASSIGNED, RepairStatus.IN_PROGRESS])
    completed_orders = sum(1 for order in orders if order.status == RepairStatus.COMPLETED)
    
    ratings = [order.rating for order in orders if order.rating is not None]
    average_rating = sum(ratings) / len(ratings) if ratings else None
    
    return RepairStatistics(
        total_orders=total_orders,
        pending_orders=pending_orders,
        in_progress_orders=in_progress_orders,
        completed_orders=completed_orders,
        average_rating=round(average_rating, 2) if average_rating else None
    )


@router.get("/statistics/owners", response_model=OwnerStatistics)
async def get_owner_statistics(
    current_user: User = Depends(get_current_manager)
):
    """获取业主统计"""
    total_owners = await User.filter(role=UserRole.OWNER).count()
    active_owners = await User.filter(role=UserRole.OWNER, is_active=True).count()
    total_properties = await Property.all().count()
    
    return OwnerStatistics(
        total_owners=total_owners,
        active_owners=active_owners,
        total_properties=total_properties
    )


@router.get("/alerts")
async def get_alerts(
    current_user: User = Depends(get_current_manager)
):
    """查看预警信息"""
    alerts = []
    
    # 逾期账单预警
    today = date.today()
    overdue_bills = await Bill.filter(status=BillStatus.UNPAID, due_date__lt=today).count()
    if overdue_bills > 0:
        alerts.append({
            "type": "overdue_bills",
            "level": "warning",
            "message": f"有 {overdue_bills} 条账单已逾期未支付",
            "count": overdue_bills
        })
    
    # 待处理报修预警
    pending_repairs = await RepairOrder.filter(status=RepairStatus.PENDING).count()
    if pending_repairs > 0:
        alerts.append({
            "type": "pending_repairs",
            "level": "info",
            "message": f"有 {pending_repairs} 条报修工单待处理",
            "count": pending_repairs
        })
    
    # 紧急报修预警
    urgent_repairs = await RepairOrder.filter(
        urgency_level="urgent",
        status__in=[RepairStatus.PENDING, RepairStatus.ASSIGNED]
    ).count()
    if urgent_repairs > 0:
        alerts.append({
            "type": "urgent_repairs",
            "level": "error",
            "message": f"有 {urgent_repairs} 条紧急报修工单需要处理",
            "count": urgent_repairs
        })
    
    return {"alerts": alerts}
