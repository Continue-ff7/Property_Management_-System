"""
物业投诉相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from datetime import datetime
from app.models import User, Complaint, ComplaintType, ComplaintStatus
from app.core.dependencies import get_current_user, get_current_manager
from app.api.v1.websocket import notify_new_complaint, notify_complaint_update, notify_complaint_rated
from pydantic import BaseModel

router = APIRouter()


# ==================== Schemas ====================

class ComplaintCreate(BaseModel):
    type: str
    content: str
    images: Optional[List[str]] = None


class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    reply: Optional[str] = None
    handler_id: Optional[int] = None


class ComplaintRate(BaseModel):
    rating: int


class ComplaintResponse(BaseModel):
    id: int
    type: str
    content: str
    images: Optional[List[str]]
    contact_phone: str
    status: str
    reply: Optional[str]
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    owner_name: str
    owner_id: int
    handler_name: Optional[str] = None


class ComplaintListResponse(BaseModel):
    items: List[ComplaintResponse]
    total: int


# ==================== 业主端API ====================

@router.post("/complaints", response_model=ComplaintResponse)
async def create_complaint(
    complaint_data: ComplaintCreate,
    current_user: User = Depends(get_current_user)
):
    """提交投诉"""
    complaint = await Complaint.create(
        owner_id=current_user.id,
        type=complaint_data.type,
        content=complaint_data.content,
        images=complaint_data.images or [],
        contact_phone=current_user.phone,
        status=ComplaintStatus.PENDING
    )
    
    await complaint.fetch_related('owner', 'handler')
    
    result = {
        "id": complaint.id,
        "type": complaint.type.value,
        "content": complaint.content,
        "images": complaint.images,
        "contact_phone": complaint.contact_phone,
        "status": complaint.status.value,
        "reply": complaint.reply,
        "rating": complaint.rating,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
        "completed_at": complaint.completed_at.isoformat() if complaint.completed_at else None,
        "owner_name": complaint.owner.name,
        "owner_id": complaint.owner.id,
        "handler_name": complaint.handler.name if complaint.handler else None
    }
    
    # 发送 WebSocket 通知给管理员
    try:
        print(f"[DEBUG] 准备发送 WebSocket 通知，投诉ID: {complaint.id}")
        await notify_new_complaint(result)
        print(f"[DEBUG] WebSocket 通知发送完成")
    except Exception as e:
        print(f"[ERROR] WebSocket 通知失败: {e}")
        import traceback
        traceback.print_exc()
    
    return result


@router.get("/complaints", response_model=List[ComplaintResponse])
async def get_my_complaints(
    current_user: User = Depends(get_current_user)
):
    """获取我的投诉列表"""
    complaints = await Complaint.filter(owner_id=current_user.id).prefetch_related('owner', 'handler')
    
    result = []
    for complaint in complaints:
        result.append({
            "id": complaint.id,
            "type": complaint.type.value,
            "content": complaint.content,
            "images": complaint.images,
            "contact_phone": complaint.contact_phone,
            "status": complaint.status.value,
            "reply": complaint.reply,
            "rating": complaint.rating,
            "created_at": complaint.created_at,
            "updated_at": complaint.updated_at,
            "completed_at": complaint.completed_at,
            "owner_name": complaint.owner.name,
            "owner_id": complaint.owner.id,
            "handler_name": complaint.handler.name if complaint.handler else None
        })
    
    return result


@router.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint_detail(
    complaint_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取投诉详情"""
    complaint = await Complaint.filter(id=complaint_id).prefetch_related('owner', 'handler').first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="投诉不存在")
    
    if complaint.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问")
    
    return {
        "id": complaint.id,
        "type": complaint.type.value,
        "content": complaint.content,
        "images": complaint.images,
        "contact_phone": complaint.contact_phone,
        "status": complaint.status.value,
        "reply": complaint.reply,
        "rating": complaint.rating,
        "created_at": complaint.created_at,
        "updated_at": complaint.updated_at,
        "completed_at": complaint.completed_at,
        "owner_name": complaint.owner.name,
        "owner_id": complaint.owner.id,
        "handler_name": complaint.handler.name if complaint.handler else None
    }


@router.delete("/complaints/{complaint_id}")
async def cancel_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user)
):
    """撤销投诉（只能撤销待处理的）"""
    complaint = await Complaint.get_or_none(id=complaint_id)
    
    if not complaint:
        raise HTTPException(status_code=404, detail="投诉不存在")
    
    if complaint.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    if complaint.status != ComplaintStatus.PENDING:
        raise HTTPException(status_code=400, detail="只能撤销待处理的投诉")
    
    await complaint.delete()
    
    return {"message": "已撤销投诉"}


@router.post("/complaints/{complaint_id}/rate")
async def rate_complaint(
    complaint_id: int,
    rate_data: ComplaintRate,
    current_user: User = Depends(get_current_user)
):
    """评价投诉处理"""
    complaint = await Complaint.get_or_none(id=complaint_id)
    
    if not complaint:
        raise HTTPException(status_code=404, detail="投诉不存在")
    
    if complaint.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    if complaint.status != ComplaintStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="只能评价已完成的投诉")
    
    if not (1 <= rate_data.rating <= 5):
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")
    
    complaint.rating = rate_data.rating
    await complaint.save()
    await complaint.fetch_related('owner', 'handler')
    
    # 发送 WebSocket 通知给管理员
    try:
        result = {
            "id": complaint.id,
            "type": complaint.type.value,
            "content": complaint.content,
            "rating": complaint.rating,
            "status": complaint.status.value,
            "reply": complaint.reply,
            "owner_name": complaint.owner.name,
            "owner_id": complaint.owner.id,
            "handler_name": complaint.handler.name if complaint.handler else None,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
            "completed_at": complaint.completed_at.isoformat() if complaint.completed_at else None
        }
        await notify_complaint_rated(result)
    except Exception as e:
        print(f"[ERROR] 发送评价通知失败: {e}")
    
    return {"message": "评价成功"}


# ==================== 管理员端API ====================

@router.get("/manager/complaints", response_model=ComplaintListResponse)
async def get_all_complaints(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_manager)
):
    """获取所有投诉（管理员）"""
    query = Complaint.all()
    
    if status:
        query = query.filter(status=status)
    
    # 获取总数
    total = await query.count()
    
    # 分页查询
    complaints = await query.prefetch_related('owner', 'handler').offset(skip).limit(limit)
    
    result = []
    for complaint in complaints:
        result.append({
            "id": complaint.id,
            "type": complaint.type.value,
            "content": complaint.content,
            "images": complaint.images,
            "contact_phone": complaint.contact_phone,
            "status": complaint.status.value,
            "reply": complaint.reply,
            "rating": complaint.rating,
            "created_at": complaint.created_at,
            "updated_at": complaint.updated_at,
            "completed_at": complaint.completed_at,
            "owner_name": complaint.owner.name,
            "owner_id": complaint.owner.id,
            "handler_name": complaint.handler.name if complaint.handler else None
        })
    
    return {
        "items": result,
        "total": total
    }


@router.get("/manager/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint_detail_manager(
    complaint_id: int,
    current_user: User = Depends(get_current_manager)
):
    """获取投诉详情（管理员）"""
    complaint = await Complaint.filter(id=complaint_id).prefetch_related('owner', 'handler').first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="投诉不存在")
    
    return {
        "id": complaint.id,
        "type": complaint.type.value,
        "content": complaint.content,
        "images": complaint.images,
        "contact_phone": complaint.contact_phone,
        "status": complaint.status.value,
        "reply": complaint.reply,
        "rating": complaint.rating,
        "created_at": complaint.created_at,
        "updated_at": complaint.updated_at,
        "completed_at": complaint.completed_at,
        "owner_name": complaint.owner.name,
        "owner_id": complaint.owner.id,
        "handler_name": complaint.handler.name if complaint.handler else None
    }


@router.put("/manager/complaints/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: int,
    update_data: ComplaintUpdate,
    current_user: User = Depends(get_current_manager)
):
    """更新投诉状态/回复（管理员）"""
    complaint = await Complaint.get_or_none(id=complaint_id)
    
    if not complaint:
        raise HTTPException(status_code=404, detail="投诉不存在")
    
    # 更新状态
    if update_data.status:
        complaint.status = ComplaintStatus(update_data.status)
        
        if complaint.status == ComplaintStatus.COMPLETED:
            complaint.completed_at = datetime.now()
    
    # 更新回复
    if update_data.reply:
        complaint.reply = update_data.reply
    
    # 分配处理人
    if update_data.handler_id:
        complaint.handler_id = update_data.handler_id
    
    await complaint.save()
    await complaint.fetch_related('owner', 'handler')
    
    result = {
        "id": complaint.id,
        "type": complaint.type.value,
        "content": complaint.content,
        "images": complaint.images,
        "contact_phone": complaint.contact_phone,
        "status": complaint.status.value,
        "reply": complaint.reply,
        "rating": complaint.rating,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
        "completed_at": complaint.completed_at.isoformat() if complaint.completed_at else None,
        "owner_name": complaint.owner.name,
        "owner_id": complaint.owner.id,
        "handler_name": complaint.handler.name if complaint.handler else None
    }
    
    # 发送 WebSocket 通知给业主
    await notify_complaint_update(complaint.owner_id, result)
    
    return result


@router.get("/manager/complaints/stats/summary")
async def get_complaints_stats(
    current_user: User = Depends(get_current_manager)
):
    """获取投诉统计"""
    total = await Complaint.all().count()
    pending = await Complaint.filter(status=ComplaintStatus.PENDING).count()
    processing = await Complaint.filter(status=ComplaintStatus.PROCESSING).count()
    completed = await Complaint.filter(status=ComplaintStatus.COMPLETED).count()
    
    # 按类型统计
    type_stats = {}
    for complaint_type in ComplaintType:
        count = await Complaint.filter(type=complaint_type).count()
        type_stats[complaint_type.value] = count
    
    return {
        "total": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "by_type": type_stats
    }


@router.delete("/manager/complaints/{complaint_id}")
async def delete_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_manager)
):
    """删除投诉（管理员）"""
    complaint = await Complaint.get_or_none(id=complaint_id)
    
    if not complaint:
        raise HTTPException(status_code=404, detail="投诉不存在")
    
    # 获取业主 ID
    owner_id = complaint.owner_id
    await complaint.fetch_related('owner')
    
    # 发送 WebSocket 通知给业主
    try:
        notification_data = {
            "id": complaint.id,
            "type": complaint.type.value,
            "content": complaint.content,
            "status": "deleted",
            "owner_id": owner_id,
            "owner_name": complaint.owner.name,
            "message": "您的投诉已被管理员删除"
        }
        await notify_complaint_update(owner_id, notification_data)
    except Exception as e:
        print(f"[ERROR] 发送删除通知失败: {e}")
    
    # 删除投诉
    await complaint.delete()
    
    return {"message": "删除成功"}
