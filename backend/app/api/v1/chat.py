from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.models import User, RepairOrder, RepairChatMessage
from typing import Dict, Set, List
import json
from datetime import datetime

router = APIRouter()

# 存储聊天WebSocket连接：{repair_order_id: {user_id: websocket}}
chat_connections: Dict[int, Dict[int, WebSocket]] = {}


@router.websocket("/ws/chat/{repair_order_id}")
async def chat_websocket(
    websocket: WebSocket,
    repair_order_id: int,
    token: str = Query(...)
):
    """聊天WebSocket连接"""
    await websocket.accept()
    
    user_id = None
    
    try:
        # 简单的token验证（实际应该用JWT）
        # 这里为了演示，直接从query中获取user_id
        # 实际应该从token解析出user_id
        
        # 验证工单存在
        repair_order = await RepairOrder.get_or_none(id=repair_order_id).prefetch_related(
            "owner", "maintenance_worker"
        )
        if not repair_order:
            await websocket.send_json({
                "type": "error",
                "message": "工单不存在"
            })
            await websocket.close()
            return
        
        # 接收第一条消息来确认用户身份
        first_msg = await websocket.receive_text()
        init_data = json.loads(first_msg)
        user_id = init_data.get("user_id")
        
        if not user_id:
            await websocket.send_json({
                "type": "error",
                "message": "用户身份验证失败"
            })
            await websocket.close()
            return
        
        # 验证用户是否有权访问这个工单的聊天
        if user_id not in [repair_order.owner_id, repair_order.maintenance_worker_id]:
            await websocket.send_json({
                "type": "error",
                "message": "您没有权限访问此聊天"
            })
            await websocket.close()
            return
        
        # 添加连接到管理器
        if repair_order_id not in chat_connections:
            chat_connections[repair_order_id] = {}
        chat_connections[repair_order_id][user_id] = websocket
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "message": "聊天连接成功"
        })
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_text("pong")
                    continue
                
                try:
                    message_data = json.loads(data)
                    message_text = message_data.get("message")
                    
                    if not message_text:
                        continue
                    
                    # 获取发送者信息
                    sender = await User.get_or_none(id=user_id)
                    if not sender:
                        continue
                    
                    # 保存消息到数据库
                    chat_msg = await RepairChatMessage.create(
                        repair_order_id=repair_order_id,
                        sender_id=user_id,
                        message=message_text,
                        is_owner=(user_id == repair_order.owner_id)
                    )
                    
                    # 构造消息
                    chat_message = {
                        "type": "message",
                        "id": chat_msg.id,
                        "sender_id": user_id,
                        "sender_name": sender.name,
                        "message": message_text,
                        "timestamp": chat_msg.created_at.isoformat(),
                        "is_owner": user_id == repair_order.owner_id
                    }
                    
                    # 广播消息给该工单的所有在线用户
                    if repair_order_id in chat_connections:
                        for uid, ws in chat_connections[repair_order_id].items():
                            try:
                                await ws.send_json(chat_message)
                            except:
                                # 如果发送失败，移除这个连接
                                pass
                    
                except json.JSONDecodeError:
                    continue
                    
        except WebSocketDisconnect:
            # 移除连接
            if repair_order_id in chat_connections and user_id in chat_connections[repair_order_id]:
                del chat_connections[repair_order_id][user_id]
                if not chat_connections[repair_order_id]:
                    del chat_connections[repair_order_id]
                    
    except Exception as e:
        print(f"Chat WebSocket error: {e}")
        if repair_order_id in chat_connections and user_id and user_id in chat_connections[repair_order_id]:
            del chat_connections[repair_order_id][user_id]
        await websocket.close()


@router.get("/chat/history/{repair_order_id}")
async def get_chat_history(
    repair_order_id: int,
    limit: int = 100
):
    """获取聊天历史记录"""
    # 验证工单存在
    repair_order = await RepairOrder.get_or_none(id=repair_order_id)
    if not repair_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # 获取聊天记录
    messages = await RepairChatMessage.filter(
        repair_order_id=repair_order_id
    ).order_by("created_at").limit(limit).prefetch_related("sender")
    
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.name,
            "message": msg.message,
            "timestamp": msg.created_at.isoformat(),
            "is_owner": msg.is_owner
        })
    
    return result
