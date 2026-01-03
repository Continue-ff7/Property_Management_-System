from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from app.core.dependencies import get_current_maintenance, save_upload_file
from app.models import User, RepairOrder, RepairStatus
from app.schemas import RepairOrderWithDetails, MessageResponse
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_maintenance)):
    """获取个人信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "avatar": current_user.avatar,  # 添加头像字段
        "created_at": current_user.created_at
    }


class UpdateProfileRequest(BaseModel):
    """update profile request schema"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None  # 头像URL


@router.put("/profile")
async def update_profile(
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_maintenance)
):
    """更新个人信息"""
    # 更新字段
    if update_data.name is not None:
        current_user.name = update_data.name
    if update_data.phone is not None:
        current_user.phone = update_data.phone
    if update_data.email is not None:
        current_user.email = update_data.email
    if update_data.avatar is not None:
        current_user.avatar = update_data.avatar
    
    await current_user.save()
    
    return {
        "message": "更新成功",
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "avatar": current_user.avatar
    }


@router.get("/orders", response_model=List[RepairOrderWithDetails])
async def get_my_orders(
    status: str = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_maintenance)
):
    """查看分配给自己的维修工单"""
    query = RepairOrder.filter(maintenance_worker_id=current_user.id)
    
    if status and status != 'all':
        if status == 'assigned':
            query = query.filter(status=RepairStatus.ASSIGNED)
        elif status == 'in_progress':
            query = query.filter(status=RepairStatus.IN_PROGRESS)
        elif status == 'completed':
            query = query.filter(status=RepairStatus.COMPLETED)
    
    orders = await query.order_by("-created_at").offset(skip).limit(limit).prefetch_related(
        "owner", "property", "property__building"
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
            "images": order.images or [],
            "urgency_level": order.urgency_level.value,
            "status": order.status.value,
            "maintenance_worker_id": order.maintenance_worker_id,
            "assigned_at": order.assigned_at,
            "started_at": order.started_at,
            "completed_at": order.completed_at,
            "repair_images": order.repair_images or [],
            "rating": order.rating,
            "comment": order.comment,
            "created_at": order.created_at,
            "owner_name": order.owner.name,
            "owner_phone": order.owner.phone,
            "owner_avatar": order.owner.avatar,  # 添加业主头像
            "property_info": property_info,
            "maintenance_worker_name": current_user.name,
            "maintenance_worker_avatar": current_user.avatar,  # 添加维修人员头像
            "area": order.property.area
        })
    
    return result


@router.get("/orders/{order_id}", response_model=RepairOrderWithDetails)
async def get_order_detail(
    order_id: int,
    current_user: User = Depends(get_current_maintenance)
):
    """查看工单详情（包含业主联系方式）"""
    order = await RepairOrder.get_or_none(
        id=order_id, 
        maintenance_worker_id=current_user.id
    ).prefetch_related("owner", "property", "property__building")
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在或不属于您")
    
    property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
    
    return {
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
        "owner_avatar": order.owner.avatar,  # 添加业主头像
        "property_info": property_info,
        "maintenance_worker_name": current_user.name,
        "maintenance_worker_avatar": current_user.avatar  # 添加维修人员头像
    }


@router.post("/orders/{order_id}/start", response_model=MessageResponse)
async def start_repair(
    order_id: int,
    current_user: User = Depends(get_current_maintenance)
):
    """开始维修"""
    order = await RepairOrder.get_or_none(
        id=order_id, 
        maintenance_worker_id=current_user.id
    ).prefetch_related("owner", "property", "property__building")
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在或不属于您")
    
    if order.status not in [RepairStatus.ASSIGNED, RepairStatus.PENDING]:
        raise HTTPException(status_code=400, detail="工单状态不允许开始维修")
    
    order.status = RepairStatus.IN_PROGRESS
    order.started_at = datetime.now()
    await order.save()
    
    # 通过WebSocket通知业主
    from app.api.v1.websocket import notify_repair_status_update, notify_manager_repair_update
    property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
    
    # 通知业主
    await notify_repair_status_update(order.owner_id, {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "started_at": order.started_at.isoformat(),
        "property_info": property_info,
        "maintenance_worker_name": current_user.name,
        "message": "维修人员已开始维修"
    })
    
    # 通知管理员
    await notify_manager_repair_update({
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "started_at": order.started_at.isoformat(),
        "property_info": property_info,
        "maintenance_worker_name": current_user.name,
        "owner_name": order.owner.name,
        "message": f"维修人员{current_user.name}已开始处理工单"
    })
    
    return MessageResponse(message="已开始维修")


@router.post("/orders/{order_id}/complete", response_model=MessageResponse)
async def complete_repair(
    order_id: int,
    current_user: User = Depends(get_current_maintenance)
):
    """完成维修"""
    order = await RepairOrder.get_or_none(
        id=order_id, 
        maintenance_worker_id=current_user.id
    ).prefetch_related("owner", "property", "property__building")
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在或不属于您")
    
    if order.status != RepairStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="工单未在维修中")
    
    order.status = RepairStatus.COMPLETED
    order.completed_at = datetime.now()
    await order.save()
    
    # 通过WebSocket通知业主
    from app.api.v1.websocket import notify_repair_status_update, notify_manager_repair_update
    property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
    
    # 通知业主
    await notify_repair_status_update(order.owner_id, {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "completed_at": order.completed_at.isoformat(),
        "property_info": property_info,
        "maintenance_worker_name": current_user.name,
        "message": "维修已完成，请进行评价"
    })
    
    # 通知管理员
    await notify_manager_repair_update({
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "completed_at": order.completed_at.isoformat(),
        "property_info": property_info,
        "maintenance_worker_name": current_user.name,
        "owner_name": order.owner.name,
        "message": f"维修人员{current_user.name}已完成工单"
    })
    
    return MessageResponse(message="维修已完成")


@router.post("/orders/{order_id}/upload-image")
async def upload_repair_image(
    order_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_maintenance)
):
    """上传维修现场照片"""
    order = await RepairOrder.get_or_none(
        id=order_id, 
        maintenance_worker_id=current_user.id
    )
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在或不属于您")
    
    # 保存图片
    image_url = await save_upload_file(file, folder="repair_images")
    
    # 添加到工单的维修图片列表
    if order.repair_images is None:
        order.repair_images = []
    
    order.repair_images.append(image_url)
    await order.save()
    
    return {"url": image_url, "message": "图片上传成功"}


@router.get("/statistics")
async def get_my_statistics(
    current_user: User = Depends(get_current_maintenance)
):
    """获取个人工作统计"""
    # 总工单数
    total_orders = await RepairOrder.filter(maintenance_worker_id=current_user.id).count()
    
    # 待处理
    pending_orders = await RepairOrder.filter(
        maintenance_worker_id=current_user.id,
        status=RepairStatus.ASSIGNED
    ).count()
    
    # 进行中
    in_progress_orders = await RepairOrder.filter(
        maintenance_worker_id=current_user.id,
        status=RepairStatus.IN_PROGRESS
    ).count()
    
    # 已完成
    completed_orders = await RepairOrder.filter(
        maintenance_worker_id=current_user.id,
        status=RepairStatus.COMPLETED
    ).count()
    
    # 平均评分
    completed = await RepairOrder.filter(
        maintenance_worker_id=current_user.id,
        status=RepairStatus.COMPLETED,
        rating__not_isnull=True
    )
    
    ratings = [order.rating for order in completed if order.rating]
    average_rating = sum(ratings) / len(ratings) if ratings else None
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "in_progress_orders": in_progress_orders,
        "completed_orders": completed_orders,
        "average_rating": round(average_rating, 2) if average_rating else None,
        "total_ratings": len(ratings)
    }
