from fastapi import APIRouter, HTTPException, Depends, status
from app.core.dependencies import get_current_owner, generate_order_number
from app.models import User, Property, Bill, RepairOrder, Building, BillStatus, RepairStatus
from app.schemas import (
    PropertyWithOwner, BillWithDetails, BillResponse,
    RepairOrderCreate, RepairOrderWithDetails, RepairEvaluation,
    ChatRequest, ChatResponse, MessageResponse
)
from typing import List
from datetime import datetime
import io
#from reportlab.lib.pagesizes import letter
#from reportlab.pdfgen import canvas
#from reportlab.pdfbase import pdfmetrics
#from reportlab.pdfbase.ttfonts import TTFont
#from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_owner)):
    """获取个人信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


@router.get("/properties", response_model=List[PropertyWithOwner])
async def get_my_properties(current_user: User = Depends(get_current_owner)):
    """获取个人房产信息"""
    properties = await Property.filter(owner_id=current_user.id).prefetch_related("building")
    
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
            "owner_name": current_user.name,
            "building_name": prop.building.name
        })
    
    return result


@router.get("/bills", response_model=List[BillWithDetails])
async def get_my_bills(
    status: str = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_owner)
):
    """获取个人缴费记录和账单"""
    query = Bill.filter(owner_id=current_user.id)
    
    if status:
        query = query.filter(status=status)
    
    bills = await query.order_by("-created_at").offset(skip).limit(limit).prefetch_related("property", "property__building")
    
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
            "owner_name": current_user.name,
            "property_info": property_info
        })
    
    return result


@router.post("/bills/{bill_id}/pay", response_model=BillResponse)
async def pay_bill(
    bill_id: int,
    current_user: User = Depends(get_current_owner)
):
    """在线支付物业费用"""
    bill = await Bill.get_or_none(id=bill_id, owner_id=current_user.id)
    
    if not bill:
        raise HTTPException(status_code=404, detail="账单不存在")
    
    if bill.status == BillStatus.PAID:
        raise HTTPException(status_code=400, detail="账单已支付")
    
    # 这里应该集成第三方支付，简化处理直接标记为已支付
    bill.status = BillStatus.PAID
    bill.paid_at = datetime.now()
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


@router.get("/bills/{bill_id}/invoice")
async def download_invoice(
    bill_id: int,
    current_user: User = Depends(get_current_owner)
):
    """下载个人缴费发票"""
    bill = await Bill.get_or_none(id=bill_id, owner_id=current_user.id).prefetch_related("property", "property__building")
    
    if not bill:
        raise HTTPException(status_code=404, detail="账单不存在")
    
    if bill.status != BillStatus.PAID:
        raise HTTPException(status_code=400, detail="账单未支付，无法下载发票")
    ''' 
    # 生成PDF发票
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # 添加发票内容
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Payment Invoice")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"Invoice ID: {bill.id}")
    p.drawString(100, 680, f"Owner: {current_user.name}")
    p.drawString(100, 660, f"Property: {bill.property.building.name} {bill.property.unit}-{bill.property.room_number}")
    p.drawString(100, 640, f"Fee Type: {bill.fee_type.value}")
    p.drawString(100, 620, f"Amount: {bill.amount} CNY")
    p.drawString(100, 600, f"Billing Period: {bill.billing_period}")
    p.drawString(100, 580, f"Paid At: {bill.paid_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{bill.id}.pdf"}
    )
'''

@router.post("/repairs", response_model=RepairOrderWithDetails)
async def create_repair_order(
    order_data: RepairOrderCreate,
    current_user: User = Depends(get_current_owner)
):
    """提交报修申请"""
    # 验证房产属于当前用户
    property_obj = await Property.get_or_none(id=order_data.property_id, owner_id=current_user.id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="房产不存在或不属于您")
    
    # 创建报修工单
    order = await RepairOrder.create(
        order_number=generate_order_number(),
        owner_id=current_user.id,
        property_id=order_data.property_id,
        description=order_data.description,
        images=order_data.images,
        urgency_level=order_data.urgency_level,
        status=RepairStatus.PENDING
    )
    
    await order.fetch_related("property", "property__building")
    
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
        "owner_name": current_user.name,
        "owner_phone": current_user.phone,
        "property_info": property_info,
        "maintenance_worker_name": None
    }


@router.get("/repairs", response_model=List[RepairOrderWithDetails])
async def get_my_repair_orders(
    status: str = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_owner)
):
    """查看报修进度和维修人员信息"""
    query = RepairOrder.filter(owner_id=current_user.id)
    
    if status:
        query = query.filter(status=status)
    
    orders = await query.order_by("-created_at").offset(skip).limit(limit).prefetch_related(
        "property", "property__building", "maintenance_worker"
    )
    
    result = []
    for order in orders:
        property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
        maintenance_worker_name = order.maintenance_worker.name if order.maintenance_worker else None
        
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
            "owner_name": current_user.name,
            "owner_phone": current_user.phone,
            "property_info": property_info,
            "maintenance_worker_name": maintenance_worker_name
        })
    
    return result


@router.post("/repairs/{order_id}/evaluate", response_model=MessageResponse)
async def evaluate_repair_order(
    order_id: int,
    evaluation: RepairEvaluation,
    current_user: User = Depends(get_current_owner)
):
    """对完成的维修进行评价与确认"""
    order = await RepairOrder.get_or_none(id=order_id, owner_id=current_user.id)
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if order.status != RepairStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="只能对已完成的工单进行评价")
    
    if order.rating is not None:
        raise HTTPException(status_code=400, detail="该工单已评价")
    
    if evaluation.rating < 1 or evaluation.rating > 5:
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")
    
    order.rating = evaluation.rating
    order.comment = evaluation.comment
    await order.save()
    
    return MessageResponse(message="评价成功")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_owner)
):
    """与AI客服进行对话咨询"""
    # 这里应该集成AI服务，简化处理返回模拟回复
    from app.models import ChatMessage
    
    # 简单的规则回复
    reply = "您好，我是AI客服助手。您的问题已收到，物业工作人员会尽快为您处理。如需紧急服务，请拨打24小时服务热线：400-123-4567"
    
    if "报修" in chat_data.message or "维修" in chat_data.message:
        reply = "如需报修，请在报修管理中提交工单，我们会在2小时内安排维修人员处理。紧急情况请选择'紧急'级别。"
    elif "缴费" in chat_data.message or "账单" in chat_data.message:
        reply = "您可以在'账单管理'中查看所有账单，支持在线支付。如有疑问，请联系物业管理处。"
    elif "公告" in chat_data.message:
        reply = "小区公告已在首页发布，请及时查看。重要通知我们也会通过短信方式通知您。"
    
    message = await ChatMessage.create(
        user_id=current_user.id,
        message=chat_data.message,
        reply=reply
    )
    
    return ChatResponse(
        message=message.message,
        reply=message.reply,
        created_at=message.created_at
    )
