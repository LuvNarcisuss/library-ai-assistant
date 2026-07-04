# -*- coding: utf-8 -*-
"""对话 API 路由

优化后的 RAG 流程：智能预处理 → 知识库检索 → LLM 增强 → 返回用户
"""
import uuid
import json
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import KnowledgeBase, Conversation, ChatSession, User
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.services.preprocessor import preprocessor
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["对话"])

MAX_HISTORY_ROUNDS = 10


class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    knowledge_base_id: Optional[int] = None


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    title: str
    knowledge_base_id: Optional[int] = None
    created_at: str
    updated_at: str


@router.post("", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """智能问答"""
    # 会话管理 - 使用数据库持久化
    session_id = req.session_id or uuid.uuid4().hex

    # 获取或创建会话
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(
            session_id=session_id,
            user_id=current_user.id,
            title=req.question[:50] if req.question else "新会话",
            knowledge_base_id=req.knowledge_base_id,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # 获取历史对话
    history_records = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.desc())
        .limit(MAX_HISTORY_ROUNDS)
        .all()
    )
    history = [{"question": r.question, "answer": r.answer} for r in reversed(history_records)]

    # 知识库选择
    kb_id = req.knowledge_base_id or session.knowledge_base_id
    if kb_id is not None:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

    # ========== 智能预处理 ==========
    history_context = ""
    if history:
        history_context = "\n".join([f"用户：{h['question']}\n助手：{h['answer']}" for h in history[-3:]])

    preprocess_result = preprocessor.process(
        query=req.question,
        context=history_context,
    )

    intent = preprocess_result.get("intent", "query")
    final_query = preprocess_result.get("final_query", req.question)

    # ========== 意图分发 ==========
    if intent == "greeting":
        # 问候语 - 直接返回问候回复
        answer = "您好！我是小江，您的图书馆智能助手。有什么可以帮助您的吗？"
        return ChatResponse(
            answer=answer,
            sources=[],
            session_id=session_id,
        )

    elif intent == "system_help":
        # 系统帮助 - 返回帮助信息
        answer = (
            "我是小江，您的图书馆智能助手。以下是我的主要功能：\n\n"
            "📚 **知识库查询**：可以问我图书馆相关的任何问题\n"
            "📄 **文档管理**：支持上传、查看、删除文档\n"
            "🗄️ **知识库管理**：创建、编辑、删除知识库\n"
            "🔍 **智能问答**：我会根据知识库为您提供准确答案\n\n"
            "您可以直接输入问题，我会为您检索知识库并生成答案。"
        )
        return ChatResponse(
            answer=answer,
            sources=[],
            session_id=session_id,
        )

    elif intent == "doc_manage":
        # 文档管理 - 引导到文档管理页面
        answer = (
            "📚 **文档管理**\n\n"
            "您可以在「文档管理」页面进行以下操作：\n"
            "- 上传文档（支持 txt/pdf/docx/md 格式）\n"
            "- 查看文档内容\n"
            "- 删除不需要的文档\n\n"
            "请点击左侧菜单的「文档管理」进入操作页面。"
        )
        return ChatResponse(
            answer=answer,
            sources=[],
            session_id=session_id,
        )

    elif intent == "kb_manage":
        # 知识库管理 - 引导到知识库管理页面
        answer = (
            "🗄️ **知识库管理**\n\n"
            "您可以在「知识库」页面进行以下操作：\n"
            "- 创建新的知识库\n"
            "- 编辑知识库信息\n"
            "- 删除知识库\n\n"
            "请点击左侧菜单的「知识库」进入操作页面。"
        )
        return ChatResponse(
            answer=answer,
            sources=[],
            session_id=session_id,
        )

    # ========== 知识库查询（query 意图）==========
    collection = str(kb_id) if kb_id else None
    retrieved_docs = []
    if collection:
        retrieved_docs = rag_service.retrieve(collection, final_query)

    # 生成答案
    result = rag_service.generate_answer(
        query=final_query,
        retrieved_docs=retrieved_docs,
        history=history if history else None,
    )

    # 添加预处理信息到响应
    if preprocess_result.get("corrections"):
        result["corrections"] = preprocess_result["corrections"]
    if preprocess_result.get("rewritten_query") != req.question:
        result["rewritten_query"] = preprocess_result["rewritten_query"]

    # 记录对话到数据库
    try:
        log = Conversation(
            user_id=current_user.id,
            session_id=session_id,
            knowledge_base_id=kb_id,
            question=req.question,
            answer=result["answer"],
            sources=json.dumps(result.get("sources", []), ensure_ascii=False),
        )
        db.add(log)

        # 更新会话标题（首次提问时使用问题作为标题）
        if session.title == "新会话" and req.question:
            session.title = req.question[:50]

        # 更新会话时间
        from datetime import datetime, timezone
        session.updated_at = datetime.now(timezone.utc)

        db.commit()
    except Exception as e:
        print(f"[chat] 日志记录失败: {e}")

    return ChatResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        session_id=session_id,
    )


@router.get("/sessions")
def list_sessions(
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的会话列表"""
    query = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.user_id.isnot(None)  # 排除user_id为NULL的旧数据
    )
    if knowledge_base_id is not None:
        query = query.filter(ChatSession.knowledge_base_id == knowledge_base_id)

    sessions = query.order_by(ChatSession.updated_at.desc()).all()

    return [
        SessionResponse(
            session_id=s.session_id,
            title=s.title,
            knowledge_base_id=s.knowledge_base_id,
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else "",
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话详情及历史对话"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id,  # 只能访问自己的会话
        ChatSession.user_id.isnot(None),  # 排除user_id为NULL的旧数据
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取历史对话
    history = (
        db.query(Conversation)
        .filter(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.asc())
        .all()
    )

    return {
        "session": SessionResponse(
            session_id=session.session_id,
            title=session.title,
            knowledge_base_id=session.knowledge_base_id,
            created_at=session.created_at.isoformat() if session.created_at else "",
            updated_at=session.updated_at.isoformat() if session.updated_at else "",
        ),
        "history": [
            {
                "question": h.question,
                "answer": h.answer,
                "sources": json.loads(h.sources) if h.sources else [],
                "created_at": h.created_at.isoformat() if h.created_at else "",
            }
            for h in history
        ],
    }


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除会话及其所有对话记录"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id,  # 只能删除自己的会话
        ChatSession.user_id.isnot(None),  # 排除user_id为NULL的旧数据
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 删除对话记录
    db.query(Conversation).filter(Conversation.session_id == session_id).delete()

    # 删除会话
    db.delete(session)
    db.commit()

    return {"message": "会话删除成功"}


@router.post("/sessions/{session_id}/title")
def update_session_title(
    session_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """更新会话标题"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    title = body.get("title", "")
    if title:
        session.title = title[:255]
        db.commit()

    return {"message": "标题更新成功"}


@router.post("/clear")
def clear_context(req: dict = {}):
    """清空对话上下文（保留会话记录）"""
    session_id = req.get("session_id")
    if session_id:
        # 只清空历史，不删除会话
        pass
    return {"message": "上下文已清空"}


@router.get("/stats")
def get_stats(current_user: User = Depends(get_current_user)):
    """获取 RAG 服务统计信息

    返回 LLM 调用次数、Token 使用量等统计信息。
    仅管理员可访问。
    """
    # 检查管理员权限
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    stats = llm_service.get_stats()
    return {
        "llm": stats,
        "config": {
            "model": stats.get("model", ""),
            "chunk_size": 500,  # 从 settings 读取
            "top_k": 3,
            "similarity_threshold": 0.5,
        }
    }


@router.post("/stats/reset")
def reset_stats(current_user: User = Depends(get_current_user)):
    """重置统计信息（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    llm_service.reset_stats()
    return {"message": "统计信息已重置"}


# ========== 智能预处理 API ==========

class PreprocessRequest(BaseModel):
    """预处理请求"""
    query: str
    context: Optional[str] = None
    skip_spell_correction: bool = False
    skip_intent_recognition: bool = False
    skip_query_rewrite: bool = False


@router.post("/preprocess")
def preprocess_text(
    req: PreprocessRequest,
    current_user: User = Depends(get_current_user),
):
    """预处理用户输入

    执行语义纠错、意图识别、问题重写，返回处理结果。
    """
    result = preprocessor.process(
        query=req.query,
        context=req.context,
        skip_spell_correction=req.skip_spell_correction,
        skip_intent_recognition=req.skip_intent_recognition,
        skip_query_rewrite=req.skip_query_rewrite,
    )

    # 添加意图中文描述
    result["intent_description"] = preprocessor.get_intent_description(result["intent"])

    return result


@router.post("/correct")
def correct_text(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """语义纠错

    纠正用户输入中的错别字。
    """
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text 参数不能为空")

    corrected, corrections = preprocessor.correct_text(text)
    return {
        "original": text,
        "corrected": corrected,
        "corrections": corrections,
    }


@router.post("/intent")
def recognize_intent(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """意图识别

    识别用户输入的意图类型。
    """
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text 参数不能为空")

    intent, confidence = preprocessor.recognize_intent(text)
    return {
        "text": text,
        "intent": intent,
        "intent_description": preprocessor.get_intent_description(intent),
        "confidence": confidence,
    }


@router.post("/rewrite")
def rewrite_query(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """问题重写

    优化用户的模糊问题。
    """
    query = body.get("query", "")
    context = body.get("context", None)

    if not query:
        raise HTTPException(status_code=400, detail="query 参数不能为空")

    rewritten = preprocessor.rewrite_query(query, context)
    return {
        "original": query,
        "rewritten": rewritten,
        "changed": query != rewritten,
    }
