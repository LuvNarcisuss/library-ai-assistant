# -*- coding: utf-8 -*-
"""对话日志 API 路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Conversation, User
from app.models.schemas import ConversationResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/logs", tags=["日志"])


@router.get("")
def list_logs(
    knowledge_base_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话日志列表，支持按知识库/关键词筛选。管理员可查看所有，普通用户只能查看自己的。"""
    q = db.query(Conversation)

    # 非管理员只能查看自己的对话
    if current_user.role != "admin":
        q = q.filter(Conversation.user_id == current_user.id)

    if knowledge_base_id is not None:
        q = q.filter(Conversation.knowledge_base_id == knowledge_base_id)
    if keyword:
        q = q.filter(
            Conversation.question.contains(keyword) |
            Conversation.answer.contains(keyword)
        )
    total = q.count()
    items = q.order_by(Conversation.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    # 构建返回数据，包含用户名
    result_items = []
    for item in items:
        user = db.query(User).filter(User.id == item.user_id).first() if item.user_id else None
        result_items.append({
            "id": item.id,
            "user_id": item.user_id,
            "username": user.username if user else "未知用户",
            "session_id": item.session_id,
            "knowledge_base_id": item.knowledge_base_id,
            "question": item.question,
            "answer": item.answer,
            "sources": item.sources,
            "created_at": item.created_at.isoformat() if item.created_at else "",
        })

    return {"total": total, "page": page, "page_size": page_size, "items": result_items}


@router.get("/{log_id}")
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取日志详情"""
    log = db.query(Conversation).filter(Conversation.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    # 非管理员只能查看自己的对话
    if current_user.role != "admin" and log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此日志")

    user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": user.username if user else "未知用户",
        "session_id": log.session_id,
        "knowledge_base_id": log.knowledge_base_id,
        "question": log.question,
        "answer": log.answer,
        "sources": log.sources,
        "created_at": log.created_at.isoformat() if log.created_at else "",
    }
