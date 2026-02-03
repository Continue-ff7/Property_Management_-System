from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.models import User
from typing import Dict, Set
import json

router = APIRouter()

# 存储维修人员的WebSocket连接
maintenance_connections: Dict[int, Set[WebSocket]] = {}

# 存储管理员的WebSocket连接（改用字典，支持多个管理员）
manager_connections: Dict[int, Set[WebSocket]] = {}

# 存储业主的WebSocket连接
owner_connections: Dict[int, Set[WebSocket]] = {}


@router.websocket("/ws/maintenance/{user_id}")
async def maintenance_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...)
):
    """维修人员WebSocket连接 - 接收新工单推送"""
    await websocket.accept()
    
    # 验证token (简化版，实际应该用JWT验证)
    try:
        # 这里应该验证token并获取用户信息
        # current_user = await get_current_user_from_token(token)
        
        # 添加连接到管理器
        if user_id not in maintenance_connections:
            maintenance_connections[user_id] = set()
        maintenance_connections[user_id].add(websocket)
        
        try:
            while True:
                # 保持连接，接收客户端心跳
                data = await websocket.receive_text()
                # 可以处理心跳或其他消息
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            # 移除连接
            maintenance_connections[user_id].remove(websocket)
            if not maintenance_connections[user_id]:
                del maintenance_connections[user_id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


async def notify_new_workorder(maintenance_worker_id: int, order_data: dict):
    """通知维修人员有新工单分配"""
    if maintenance_worker_id in maintenance_connections:
        # 向该维修人员的所有连接发送消息
        for websocket in maintenance_connections[maintenance_worker_id].copy():
            try:
                await websocket.send_json({
                    "type": "new_workorder",
                    "data": order_data
                })
            except:
                # 如果发送失败，移除这个连接
                maintenance_connections[maintenance_worker_id].discard(websocket)


async def notify_workorder_update(maintenance_worker_id: int, order_id: int, update_type: str, data: dict = None):
    """通知维修人员工单状态更新"""
    if maintenance_worker_id in maintenance_connections:
        for websocket in maintenance_connections[maintenance_worker_id].copy():
            try:
                await websocket.send_json({
                    "type": "workorder_update",
                    "update_type": update_type,
                    "order_id": order_id,
                    "data": data
                })
            except:
                maintenance_connections[maintenance_worker_id].discard(websocket)


@router.websocket("/ws/manager/{user_id}")
async def manager_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...)
):
    """管理员WebSocket连接 - 接收新报修通知"""
    await websocket.accept()
    
    try:
        # 添加连接到管理器（按用户ID管理）
        if user_id not in manager_connections:
            manager_connections[user_id] = set()
        manager_connections[user_id].add(websocket)
        print(f"[WebSocket] 管理员 {user_id} 连接成功, 当前连接数: {len(manager_connections[user_id])}")
        
        try:
            while True:
                # 保持连接，接收客户端心跳
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            # 移除连接
            manager_connections[user_id].discard(websocket)
            if not manager_connections[user_id]:
                del manager_connections[user_id]
            print(f"[WebSocket] 管理员 {user_id} 断开连接")
    except Exception as e:
        print(f"Manager WebSocket error: {e}")
        if user_id in manager_connections:
            manager_connections[user_id].discard(websocket)
            if not manager_connections[user_id]:
                del manager_connections[user_id]
        await websocket.close()


async def notify_new_repair(repair_data: dict):
    """通知所有管理员有新的报修"""
    total_connections = sum(len(connections) for connections in manager_connections.values())
    print(f"[WebSocket] 通知管理员新报修, 当前管理员数: {len(manager_connections)}, 总连接数: {total_connections}")
    print(f"[WebSocket] 消息: {repair_data}")
    
    # 遍历所有管理员的所有连接
    for user_id, connections in list(manager_connections.items()):
        for websocket in connections.copy():
            try:
                await websocket.send_json({
                    "type": "new_repair",
                    "data": repair_data
                })
                print(f"[WebSocket] 成功发送消息给管理员 {user_id}")
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                manager_connections[user_id].discard(websocket)
                if not manager_connections[user_id]:
                    del manager_connections[user_id]


@router.websocket("/ws/owner/{user_id}")
async def owner_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...)
):
    """业主 WebSocket连接 - 接收工单状态更新通知"""
    await websocket.accept()
    
    try:
        # 添加连接到管理器
        if user_id not in owner_connections:
            owner_connections[user_id] = set()
        owner_connections[user_id].add(websocket)
        
        try:
            while True:
                # 保持连接，接收客户端心跳
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            # 移除连接
            owner_connections[user_id].discard(websocket)
            if not owner_connections[user_id]:
                del owner_connections[user_id]
    except Exception as e:
        print(f"Owner WebSocket error: {e}")
        if user_id in owner_connections:
            owner_connections[user_id].discard(websocket)
        await websocket.close()


async def notify_repair_status_update(owner_id: int, repair_data: dict):
    """通知业主工单状态更新"""
    print(f"[WebSocket] 通知业主 {owner_id}, 当前连接数: {len(owner_connections.get(owner_id, []))}")
    print(f"[WebSocket] 消息: {repair_data}")
    if owner_id in owner_connections:
        for websocket in owner_connections[owner_id].copy():
            try:
                await websocket.send_json({
                    "type": "repair_status_update",
                    "data": repair_data
                })
                print(f"[WebSocket] 成功发送消息给业主 {owner_id}")
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                owner_connections[owner_id].discard(websocket)
    else:
        print(f"[WebSocket] 业主 {owner_id} 未连接")


async def notify_repair_deleted(maintenance_worker_id: int, repair_data: dict):
    """通知维修人员工单被删除/撤销"""
    print(f"[WebSocket] 通知维修人员 {maintenance_worker_id}, 当前连接数: {len(maintenance_connections.get(maintenance_worker_id, []))}")
    print(f"[WebSocket] 消息: {repair_data}")
    if maintenance_worker_id in maintenance_connections:
        for websocket in maintenance_connections[maintenance_worker_id].copy():
            try:
                await websocket.send_json({
                    "type": "workorder_deleted",
                    "data": repair_data
                })
                print(f"[WebSocket] 成功发送消息给维修人员 {maintenance_worker_id}")
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                maintenance_connections[maintenance_worker_id].discard(websocket)
    else:
        print(f"[WebSocket] 维修人员 {maintenance_worker_id} 未连接")


async def notify_manager_repair_update(repair_data: dict):
    """通知所有管理员工单状态更新（维修人员开始/完成维修）"""
    total_connections = sum(len(connections) for connections in manager_connections.values())
    print(f"[WebSocket] 通知管理员工单状态更新, 当前管理员数: {len(manager_connections)}, 总连接数: {total_connections}")
    print(f"[WebSocket] 消息: {repair_data}")
    
    # 遍历所有管理员的所有连接
    for user_id, connections in list(manager_connections.items()):
        for websocket in connections.copy():
            try:
                await websocket.send_json({
                    "type": "repair_status_update",  # 复用类型，前端统一处理
                    "data": repair_data
                })
                print(f"[WebSocket] 成功发送消息给管理员 {user_id}")
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                manager_connections[user_id].discard(websocket)
                if not manager_connections[user_id]:
                    del manager_connections[user_id]


async def notify_repair_evaluation(order_id: int, maintenance_worker_id: int, evaluation_data: dict):
    """通知维修人员和管理员：业主已评价"""
    print(f"[WebSocket] 发送评价通知, 工单ID: {order_id}, 维修人员ID: {maintenance_worker_id}")
    
    # 1. 通知维修人员
    if maintenance_worker_id and maintenance_worker_id in maintenance_connections:
        for websocket in maintenance_connections[maintenance_worker_id].copy():
            try:
                await websocket.send_json({
                    "type": "repair_evaluated",  # 新的消息类型
                    "data": evaluation_data
                })
                print(f"[WebSocket] 已通知维修人员 {maintenance_worker_id}")
            except Exception as e:
                print(f"[WebSocket] 通知维修人员失败: {e}")
                maintenance_connections[maintenance_worker_id].discard(websocket)
    
    # 2. 通知所有管理员
    total_managers = len(manager_connections)
    for user_id, connections in list(manager_connections.items()):
        for websocket in connections.copy():
            try:
                await websocket.send_json({
                    "type": "repair_evaluated",  # 同样的消息类型
                    "data": evaluation_data
                })
            except Exception as e:
                print(f"[WebSocket] 通知管理员失败: {e}")
                manager_connections[user_id].discard(websocket)
                if not manager_connections[user_id]:
                    del manager_connections[user_id]
    
    print(f"[WebSocket] 评价通知完成, 已通知 {total_managers} 个管理员")


async def notify_new_complaint(complaint_data: dict):
    """通知所有管理员有新的投诉"""
    total_connections = sum(len(connections) for connections in manager_connections.values())
    print(f"[WebSocket] 通知管理员新投诉, 当前管理员数: {len(manager_connections)}, 总连接数: {total_connections}")
    print(f"[WebSocket] 消息: {complaint_data}")
    
    # 遍历所有管理员的所有连接
    for user_id, connections in list(manager_connections.items()):
        for websocket in connections.copy():
            try:
                await websocket.send_json({
                    "type": "new_complaint",
                    "data": complaint_data
                })
                print(f"[WebSocket] 成功发送消息给管理员 {user_id}")
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                manager_connections[user_id].discard(websocket)
                if not manager_connections[user_id]:
                    del manager_connections[user_id]


async def notify_complaint_update(owner_id: int, complaint_data: dict):
    """通知业主投诉状态更新"""
    print(f"[WebSocket] 通知业主 {owner_id} 投诉更新, 当前连接数: {len(owner_connections.get(owner_id, []))}")
    print(f"[WebSocket] 消息: {complaint_data}")
    if owner_id in owner_connections:
        for websocket in owner_connections[owner_id].copy():
            try:
                await websocket.send_json({
                    "type": "complaint_update",
                    "data": complaint_data
                })
                print(f"[WebSocket] 成功发送消息给业主 {owner_id}")
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                owner_connections[owner_id].discard(websocket)
    else:
        print(f"[WebSocket] 业主 {owner_id} 未连接")


async def notify_complaint_rated(complaint_data: dict):
    """通知所有管理员有新的投诉评价"""
    total_connections = sum(len(connections) for connections in manager_connections.values())
    print(f"[WebSocket] 通知管理员投诉被评价, 当前管理员数: {len(manager_connections)}, 总连接数: {total_connections}")
    
    for user_id, connections in list(manager_connections.items()):
        for websocket in connections.copy():
            try:
                await websocket.send_json({
                    "type": "complaint_rated",
                    "data": complaint_data
                })
                print(f"[WebSocket] 成功发送评价通知给管理员 {user_id}")
            except Exception as e:
                print(f"[WebSocket] 发送失败: {e}")
                manager_connections[user_id].discard(websocket)
                if not manager_connections[user_id]:
                    del manager_connections[user_id]
