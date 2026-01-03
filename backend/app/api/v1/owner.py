from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse, HTMLResponse
from app.core.dependencies import get_current_owner, get_current_owner_optional_token, generate_order_number
from pydantic import BaseModel
from app.models import User, Property, Bill, RepairOrder, Building, BillStatus, RepairStatus
from app.schemas import (
    PropertyWithOwner, BillWithDetails, BillResponse,
    RepairOrderCreate, RepairOrderWithDetails, RepairEvaluation,
    ChatRequest, ChatResponse, MessageResponse
)
from typing import List
from datetime import datetime
import hashlib
import uuid
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from app.core.config import settings
#from reportlab.lib.pagesizes import letter
#from reportlab.pdfgen import canvas
#from reportlab.pdfbase import pdfmetrics
#from reportlab.pdfbase.ttfonts import TTFont
#from fastapi.responses import StreamingResponse

router = APIRouter()


# 用户信息更新请求模型
class UpdateProfileRequest(BaseModel):
    name: str = None
    email: str = None
    avatar: str = None  # 头像URL


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_owner)):
    """获取个人信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "avatar": current_user.avatar,
        "created_at": current_user.created_at
    }


@router.put("/profile")
async def update_profile(
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_owner)
):
    """更新个人信息"""
    # 更新字段
    if update_data.name is not None:
        current_user.name = update_data.name
    
    if update_data.email is not None:
        current_user.email = update_data.email
    
    if update_data.avatar is not None:
        current_user.avatar = update_data.avatar
    
    await current_user.save()
    
    return {
        "message": "个人信息更新成功",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "name": current_user.name,
            "phone": current_user.phone,
            "email": current_user.email,
            "avatar": current_user.avatar,
            "role": current_user.role,  # 必须返回 role 字段，否则前端路由守卫会判断角色不匹配
            "created_at": current_user.created_at
        }
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
    
    # ✅ 添加调试日志
    print(f"\n账单查询 - 用户ID: {current_user.id}, status参数: {status}")
    
    # 如果有status参数，过滤状态
    if status:
        # 将字符串转换为BillStatus枚举
        try:
            bill_status = BillStatus(status)
            query = query.filter(status=bill_status)
            print(f"✅ 已过滤状态: {bill_status}")
        except ValueError:
            # 如果传入的status不合法，忽略过滤条件
            print(f"❌ status不合法: {status}")
            pass
    else:
        print("ℹ️ 未传status参数，返回全部账单")
    
    bills = await query.order_by("-created_at").offset(skip).limit(limit).prefetch_related("property", "property__building")
    
    # ✅ 日志：显示查询结果
    print(f"✅ 查询到 {len(bills)} 条账单")
    if bills:
        for bill in bills[:3]:  # 只显示前3条
            print(f"  - 账单ID: {bill.id}, 状态: {bill.status.value}, 金额: {bill.amount}")
    
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
    current_user: User = Depends(get_current_owner_optional_token)
):
    """下载个人缴费发票（PDF + 二维码）"""
    bill = await Bill.get_or_none(id=bill_id, owner_id=current_user.id)
    if not bill:
        raise HTTPException(status_code=404, detail="账单不存在")
    
    await bill.fetch_related("property", "property__building")
    
    if bill.status != BillStatus.PAID:
        raise HTTPException(status_code=400, detail="账单未支付，无法下载发票")
    
    # 生成或获取验证码
    if not bill.invoice_url:
        verification_data = f"{bill.id}-{bill.paid_at.isoformat()}-{uuid.uuid4().hex[:8]}"
        verification_code = hashlib.md5(verification_data.encode()).hexdigest()[:16]
        bill.invoice_url = verification_code
        await bill.save()
    else:
        verification_code = bill.invoice_url
    
    # 生成验证URL（使用配置的后端地址，支持局域网访问）
    # 修改 .env 中的 BACKEND_HOST 可切换局域网IP（如：192.168.64.24:8088）
    verify_url = f"http://{settings.BACKEND_HOST}/api/v1/owner/bills/verify/{verification_code}"
    
    # 生成PDF发票
    pdf_path = generate_invoice_pdf(bill, current_user, verification_code, verify_url)
    
    # 返回PDF文件
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"invoice_{bill.id}_{bill.billing_period.replace(' ', '_')}.pdf"
    )


def generate_invoice_pdf(bill, owner, verification_code, verify_url):
    """生成PDF发票（带二维码）"""
    # 延迟导入qrcode，避免模块初始化时报错
    try:
        import qrcode
    except ImportError:
        raise HTTPException(status_code=500, detail="qrcode库未安装，请运行: pip install qrcode[pil]")
    
    # 确保发票目录存在
    invoice_dir = os.path.join(settings.UPLOAD_DIR, "invoices")
    os.makedirs(invoice_dir, exist_ok=True)
    
    pdf_filename = f"invoice_{bill.id}.pdf"
    pdf_path = os.path.join(invoice_dir, pdf_filename)
    
    # 生成二维码图片
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # 保存二维码图片
    qr_path = os.path.join(invoice_dir, f"qr_{bill.id}.png")
    qr_img.save(qr_path)
    
    # 创建PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # 设置颜色
    primary_color = (0.4, 0.49, 0.92)  # #667eea
    
    # 标题区域（渐变背景）
    c.setFillColorRGB(*primary_color)
    c.rect(0, height - 120*mm, width, 120*mm, fill=True, stroke=False)
    
    # 标题
    c.setFillColorRGB(1, 1, 1)  # 白色
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width/2, height - 40*mm, "PAYMENT INVOICE")
    
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, height - 55*mm, "Payment Receipt")  # 使用英文替代
    
    # 发票编号
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 75*mm, f"Invoice No: INV-{bill.id:06d}")
    
    # 信息区域
    y = height - 140*mm
    x_left = 40*mm
    x_right = width - 40*mm
    
    c.setFillColorRGB(0, 0, 0)
    
    # 左侧：业主信息
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_left, y, "Bill To:")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(x_left, y, f"Name: {owner.name}")
    y -= 12
    c.drawString(x_left, y, f"Phone: {owner.phone}")
    y -= 12
    property_info = f"{bill.property.building.name} {bill.property.unit}-{bill.property.room_number}"
    c.drawString(x_left, y, f"Property: {property_info}")
    
    # 右侧：物业信息
    y = height - 140*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(x_right, y, "Property Management:")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawRightString(x_right, y, "XX Property Management Co.")
    y -= 12
    c.drawRightString(x_right, y, "Tel: 400-123-4567")
    y -= 12
    c.drawRightString(x_right, y, f"Date: {bill.paid_at.strftime('%Y-%m-%d')}")
    
    # 分隔线
    y -= 20
    c.setStrokeColorRGB(0.9, 0.9, 0.9)
    c.line(x_left, y, x_right, y)
    
    # 账单详情表格
    y -= 30
    table_y = y
    
    # 表头
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(x_left, table_y - 20, x_right - x_left, 20, fill=True, stroke=False)
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_left + 5, table_y - 13, "Fee Type")
    c.drawString(x_left + 80, table_y - 13, "Billing Period")
    c.drawString(x_left + 160, table_y - 13, "Due Date")
    c.drawString(x_left + 240, table_y - 13, "Amount (CNY)")
    
    # 表格数据
    table_y -= 20
    c.setFont("Helvetica", 10)
    
    fee_type_map = {
        "property": "Property Fee",
        "parking": "Parking Fee",
        "water": "Water",
        "electricity": "Electricity"
    }
    fee_type_text = fee_type_map.get(bill.fee_type.value, bill.fee_type.value)
    
    c.drawString(x_left + 5, table_y - 13, fee_type_text)
    c.drawString(x_left + 80, table_y - 13, bill.billing_period)
    c.drawString(x_left + 160, table_y - 13, str(bill.due_date))
    c.drawString(x_left + 240, table_y - 13, f"CNY {float(bill.amount):.2f}")
    
    # 底部分隔线
    table_y -= 20
    c.setStrokeColorRGB(0.9, 0.9, 0.9)
    c.line(x_left, table_y, x_right, table_y)
    
    # 总计
    table_y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(x_right - 120, table_y, "Total Amount:")
    c.setFillColorRGB(*primary_color)
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(x_right, table_y, f"CNY {float(bill.amount):.2f}")
    
    # 二维码区域
    qr_y = table_y - 100
    
    # 二维码标题
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, qr_y + 20, "Scan QR Code to Verify Invoice")
    
    # 插入二维码图片
    qr_size = 80
    c.drawImage(qr_path, width/2 - qr_size/2, qr_y - qr_size - 20, qr_size, qr_size)
    
    # 验证码
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width/2, qr_y - qr_size - 35, f"Verification Code: {verification_code}")
    
    # 页脚
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 30, "Thank you for your payment!")
    c.drawCentredString(width/2, 20, f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 保存PDF
    c.save()
    
    # 删除临时二维码图片
    try:
        os.remove(qr_path)
    except:
        pass
    
    return pdf_path


@router.get("/bills/verify/{verification_code}", response_class=HTMLResponse)
async def verify_invoice(verification_code: str):
    """验证发票真伪（扫码后跳转的页面）"""
    # 查找对应的账单
    bill = await Bill.get_or_none(invoice_url=verification_code)
    
    if not bill:
        # 发票不存在
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>发票验证</title>
            <style>
                body {{
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .result-card {{
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    text-align: center;
                    max-width: 500px;
                }}
                .icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #f56c6c;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #666;
                    line-height: 1.8;
                }}
                .code {{
                    background: #f5f5f5;
                    padding: 10px;
                    border-radius: 4px;
                    margin-top: 20px;
                    color: #999;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="result-card">
                <div class="icon">❌</div>
                <h1>发票不存在</h1>
                <p>抱歉，未找到对应的发票记录。</p>
                <p>请检查验证码是否正确，或联系物业客服。</p>
                <div class="code">验证码：{verification_code}</div>
            </div>
        </body>
        </html>
        """
    else:
        # 发票存在，显示验证结果
        await bill.fetch_related("owner", "property", "property__building")
        
        fee_type_map = {
            "property": "物业费",
            "parking": "停车费",
            "water": "水费",
            "electricity": "电费"
        }
        fee_type_text = fee_type_map.get(bill.fee_type.value, bill.fee_type.value)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>发票验证结果</title>
            <style>
                body {{
                    font-family: "Microsoft YaHei", Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .result-card {{
                    background: white;
                    max-width: 600px;
                    margin: 0 auto;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .icon {{
                    font-size: 64px;
                    margin-bottom: 10px;
                }}
                h1 {{
                    font-size: 28px;
                    margin: 0;
                }}
                .body {{
                    padding: 30px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 12px 0;
                    border-bottom: 1px solid #f0f0f0;
                }}
                .info-row:last-child {{
                    border-bottom: none;
                }}
                .label {{
                    color: #999;
                    font-size: 14px;
                }}
                .value {{
                    color: #333;
                    font-weight: 500;
                    font-size: 14px;
                }}
                .amount-row {{
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .amount {{
                    font-size: 32px;
                    color: #52c41a;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    background: #f9f9f9;
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="result-card">
                <div class="header">
                    <div class="icon">✅</div>
                    <h1>发票验证成功</h1>
                    <p style="margin-top: 10px; opacity: 0.9;">该发票真实有效</p>
                </div>
                <div class="body">
                    <div class="info-row">
                        <span class="label">发票编号</span>
                        <span class="value">INV-{bill.id:06d}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">业主姓名</span>
                        <span class="value">{bill.owner.name}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">房产地址</span>
                        <span class="value">{bill.property.building.name} {bill.property.unit}单元{bill.property.room_number}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">费用类型</span>
                        <span class="value">{fee_type_text}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">账期</span>
                        <span class="value">{bill.billing_period}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">支付时间</span>
                        <span class="value">{bill.paid_at.strftime('%Y年%m月%d日 %H:%M')}</span>
                    </div>
                    
                    <div class="amount-row">
                        <div class="label">支付金额</div>
                        <div class="amount">￥{float(bill.amount):.2f}</div>
                    </div>
                    
                    <div class="info-row">
                        <span class="label">验证码</span>
                        <span class="value">{verification_code}</span>
                    </div>
                </div>
                <div class="footer">
                    <p>此发票由XX物业管理有限公司开具</p>
                    <p style="margin-top: 5px;">验证时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    return HTMLResponse(content=html_content)

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
    
    # 通过WebSocket通知管理员
    from app.api.v1.websocket import notify_new_repair
    await notify_new_repair({
        "id": order.id,
        "order_number": order.order_number,
        "owner_id": order.owner_id,
        "owner_name": current_user.name,
        "owner_phone": current_user.phone,
        "property_id": order.property_id,
        "property_info": property_info,
        "description": order.description,
        "images": order.images or [],
        "urgency_level": order.urgency_level.value,
        "status": order.status.value,
        "created_at": order.created_at.isoformat()
    })
    
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
        maintenance_worker_avatar = order.maintenance_worker.avatar if order.maintenance_worker else None
        
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
            # ✅ 新增：维修费用相关字段（转换为float避免序列化问题）
            "repair_cost": float(order.repair_cost) if order.repair_cost else None,
            "cost_paid": order.cost_paid,
            "paid_at": order.paid_at,
            "created_at": order.created_at,
            "owner_name": current_user.name,
            "owner_phone": current_user.phone,
            "owner_avatar": current_user.avatar,
            "property_info": property_info,
            "maintenance_worker_name": maintenance_worker_name,
            "maintenance_worker_avatar": maintenance_worker_avatar
        })
    
    return result


@router.get("/repairs/{order_id}", response_model=RepairOrderWithDetails)
async def get_repair_detail(
    order_id: int,
    current_user: User = Depends(get_current_owner)
):
    """获取单个工单详情"""
    order = await RepairOrder.get_or_none(id=order_id, owner_id=current_user.id).prefetch_related(
        "property", "property__building", "maintenance_worker"
    )
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
    maintenance_worker_name = order.maintenance_worker.name if order.maintenance_worker else None
    maintenance_worker_avatar = order.maintenance_worker.avatar if order.maintenance_worker else None
    
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
        # ✅ 新增：维修费用相关字段
        "repair_cost": float(order.repair_cost) if order.repair_cost else None,
        "cost_paid": order.cost_paid,
        "paid_at": order.paid_at,
        "created_at": order.created_at,
        "owner_name": current_user.name,
        "owner_phone": current_user.phone,
        "owner_avatar": current_user.avatar,
        "property_info": property_info,
        "maintenance_worker_name": maintenance_worker_name,
        "maintenance_worker_avatar": maintenance_worker_avatar
    }


@router.post("/repairs/{order_id}/evaluate", response_model=MessageResponse)
async def evaluate_repair_order(
    order_id: int,
    evaluation: RepairEvaluation,
    current_user: User = Depends(get_current_owner)
):
    """对完成的维修进行评价与确认"""
    order = await RepairOrder.get_or_none(id=order_id, owner_id=current_user.id).prefetch_related(
        "property", "property__building", "maintenance_worker"
    )
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # ✅ 修改：状态应该是 pending_evaluation
    if order.status != RepairStatus.PENDING_EVALUATION:
        raise HTTPException(status_code=400, detail="工单不是待评价状态")
    
    if order.rating is not None:
        raise HTTPException(status_code=400, detail="该工单已评价")
    
    if evaluation.rating < 1 or evaluation.rating > 5:
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")
    
    order.rating = evaluation.rating
    order.comment = evaluation.comment
    order.status = RepairStatus.FINISHED  # ✅ 评价后自动改为已完结
    await order.save()
    
    print(f"✅ 业主 {current_user.name} 评价工单: {evaluation.rating}分，状态改为已完结")
    
    # ✅ 新增：通过WebSocket通知维修人员和管理员
    from app.api.v1.websocket import notify_repair_evaluation
    property_info = f"{order.property.building.name}{order.property.unit}单元{order.property.room_number}"
    
    # 获取评分星级文字
    rating_text = "⭐" * evaluation.rating
    
    evaluation_data = {
        "id": order.id,
        "order_number": order.order_number,
        "property_info": property_info,
        "owner_name": current_user.name,
        "maintenance_worker_name": order.maintenance_worker.name if order.maintenance_worker else None,
        "rating": evaluation.rating,
        "rating_text": rating_text,
        "comment": evaluation.comment,
        "message": f"业主已评价: {rating_text} {evaluation.rating}分"
    }
    
    await notify_repair_evaluation(
        order_id=order.id,
        maintenance_worker_id=order.maintenance_worker_id,
        evaluation_data=evaluation_data
    )
    
    return MessageResponse(message="评价成功")


@router.post("/repairs/{order_id}/pay", response_model=MessageResponse)
async def pay_repair_cost(
    order_id: int,
    current_user: User = Depends(get_current_owner)
):
    """支付维修费用（复用账单支付逻辑）"""
    order = await RepairOrder.get_or_none(id=order_id, owner_id=current_user.id)
    
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # ✅ 修改：状态应该是 pending_payment
    if order.status != RepairStatus.PENDING_PAYMENT:
        raise HTTPException(status_code=400, detail="工单不是待支付状态")
    
    if not order.repair_cost or order.repair_cost <= 0:
        raise HTTPException(status_code=400, detail="该工单无需支付费用")
    
    if order.cost_paid:
        raise HTTPException(status_code=400, detail="费用已支付")
    
    # ✅ 模拟支付成功（实际应该集成支付宝/微信支付）
    order.cost_paid = True
    order.paid_at = datetime.now()
    order.status = RepairStatus.PENDING_EVALUATION  # ✅ 支付后自动改为待评价
    await order.save()
    
    print(f"✅ 业主 {current_user.name} 支付维修费用: ￥{order.repair_cost}，状态改为待评价")
    
    return MessageResponse(message="支付成功")


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
