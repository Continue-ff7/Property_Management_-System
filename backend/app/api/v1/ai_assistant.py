from fastapi import APIRouter, Depends
from app.models import User, RepairOrder, Bill, Property
from app.core.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter()


@router.get("/ai/bills")
async def get_user_bills(current_user: User = Depends(get_current_user)):
    """获取用户的账单信息"""
    try:
        # 获取用户的房产
        properties = await Property.filter(owner_id=current_user.id).prefetch_related('building')
        
        if not properties:
            return {
                "success": True,
                "data": [],
                "message": "您还没有关联房产"
            }
        
        # 获取所有房产的账单
        bills_data = []
        for prop in properties:
            bills = await Bill.filter(property_id=prop.id).order_by('-created_at')
            
            for bill in bills:
                bills_data.append({
                    "id": bill.id,
                    "property_info": f"{prop.building.name}{prop.unit}单元{prop.room_number}",
                    "type": bill.fee_type.value,
                    "type_text": "水费" if bill.fee_type.value == "water" else 
                                 "电费" if bill.fee_type.value == "electricity" else
                                 "物业费" if bill.fee_type.value == "property" else 
                                 "停车费" if bill.fee_type.value == "parking" else "其他",
                    "amount": float(bill.amount),
                    "status": bill.status.value,
                    "status_text": "未缴费" if bill.status.value == "unpaid" else "已缴费",
                    "billing_period": bill.billing_period if hasattr(bill, 'billing_period') else None,
                    "due_date": bill.due_date.isoformat() if bill.due_date else None,
                    "paid_at": bill.paid_at.isoformat() if bill.paid_at else None
                })
        
        return {
            "success": True,
            "data": bills_data,
            "message": f"找到 {len(bills_data)} 条账单记录"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询账单失败: {str(e)}"
        }


@router.get("/ai/repairs")
async def get_user_repairs(current_user: User = Depends(get_current_user)):
    """获取用户的报修记录"""
    try:
        repairs = await RepairOrder.filter(owner_id=current_user.id).prefetch_related(
            'property', 'property__building', 'maintenance_worker'
        ).order_by('-created_at')
        
        repairs_data = []
        for repair in repairs:
            repairs_data.append({
                "id": repair.id,
                "order_number": repair.order_number,
                "property_info": f"{repair.property.building.name}{repair.property.unit}单元{repair.property.room_number}",
                "description": repair.description,
                "status": repair.status.value,
                "status_text": "待处理" if repair.status.value == "pending" else
                              "已分配" if repair.status.value == "assigned" else
                              "维修中" if repair.status.value == "in_progress" else
                              "已完成",
                "urgency_level": repair.urgency_level.value,
                "urgency_text": "低" if repair.urgency_level.value == "low" else
                               "中" if repair.urgency_level.value == "medium" else
                               "高" if repair.urgency_level.value == "high" else "紧急",
                "created_at": repair.created_at.isoformat(),
                "worker_name": repair.maintenance_worker.name if repair.maintenance_worker else None
            })
        
        return {
            "success": True,
            "data": repairs_data,
            "message": f"找到 {len(repairs_data)} 条报修记录"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询报修记录失败: {str(e)}"
        }


@router.get("/ai/properties")
async def get_user_properties(current_user: User = Depends(get_current_user)):
    """获取用户的房产信息"""
    try:
        properties = await Property.filter(owner_id=current_user.id).prefetch_related('building')
        
        properties_data = []
        for prop in properties:
            properties_data.append({
                "id": prop.id,
                "building_name": prop.building.name,
                "unit": prop.unit,
                "room_number": prop.room_number,
                "full_address": f"{prop.building.name}{prop.unit}单元{prop.room_number}",
                "area": float(prop.area) if prop.area else 0
            })
        
        return {
            "success": True,
            "data": properties_data,
            "message": f"找到 {len(properties_data)} 处房产"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询房产信息失败: {str(e)}"
        }


@router.post("/ai/create-repair")
async def create_repair_order(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """创建报修工单"""
    try:
        from app.models import RepairStatus, UrgencyLevel
        from datetime import datetime
        import secrets
        
        # 获取参数
        property_id = data.get('property_id')
        description = data.get('description')
        urgency_level = data.get('urgency_level', 'medium')
        
        if not property_id or not description:
            return {
                "code": 400,
                "success": False,
                "message": "缺少必要参数"
            }
        
        # 验证房产是否属于当前用户
        property = await Property.get_or_none(id=property_id, owner_id=current_user.id)
        if not property:
            return {
                "code": 404,
                "success": False,
                "message": "房产不存在或不属于您"
            }
        
        # 生成工单号
        order_number = f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}"
        
        # 创建报修工单
        repair = await RepairOrder.create(
            order_number=order_number,
            owner_id=current_user.id,
            property_id=property_id,
            description=description,
            urgency_level=UrgencyLevel(urgency_level),
            status=RepairStatus.PENDING,
            images=[]
        )
        
        await repair.fetch_related('property', 'property__building')
        
        # WebSocket通知管理员
        from app.api.v1.websocket import notify_new_repair
        await notify_new_repair({
            "id": repair.id,
            "order_number": repair.order_number,
            "owner_id": current_user.id,
            "owner_name": current_user.name,
            "owner_phone": current_user.phone,
            "property_id": property_id,
            "property_info": f"{repair.property.building.name}{repair.property.unit}单元{repair.property.room_number}",
            "description": description,
            "urgency_level": urgency_level,
            "status": "pending",
            "created_at": repair.created_at.isoformat()
        })
        
        return {
            "code": 200,
            "success": True,
            "data": {
                "id": repair.id,
                "order_number": repair.order_number,
                "created_at": repair.created_at.isoformat()
            },
            "message": "报修申请已提交成功"
        }
    except Exception as e:
        return {
            "code": 500,
            "success": False,
            "message": f"创建报修失败: {str(e)}"
        }
