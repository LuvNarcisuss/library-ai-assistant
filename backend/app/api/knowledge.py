# -*- coding: utf-8 -*-
"""知识库管理 API 路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import KnowledgeBase, Document
from app.models.schemas import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from app.services.vector_service import vector_service

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("")
def list_knowledge_bases(
    name: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取知识库列表，支持按名称/部门筛选"""
    q = db.query(KnowledgeBase)
    if name:
        q = q.filter(KnowledgeBase.name.contains(name))
    if department:
        q = q.filter(KnowledgeBase.department.contains(department))
    total = q.count()
    items = q.order_by(KnowledgeBase.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    results = []
    for kb in items:
        doc_count = db.query(Document).filter(Document.knowledge_base_id == kb.id).count()
        results.append(KnowledgeBaseResponse(
            id=kb.id, name=kb.name, description=kb.description or "",
            department=kb.department or "", owner=kb.owner or "",
            embedding_model=kb.embedding_model, created_at=kb.created_at,
            doc_count=doc_count,
        ))
    return {"total": total, "page": page, "page_size": page_size, "items": results}


@router.post("", status_code=201)
def create_knowledge_base(req: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    """创建知识库"""
    kb = KnowledgeBase(
        name=req.name, description=req.description or "",
        department=req.department or "", owner=req.owner or "",
        embedding_model=req.embedding_model or "BAAI/bge-small-zh-v1.5",
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    try:
        vector_service.create_collection(str(kb.id))
    except Exception as e:
        print(f"[knowledge] 创建向量集合失败: {e}")
    return {"id": kb.id, "message": "知识库创建成功"}


@router.get("/{kb_id}")
def get_knowledge_base(kb_id: int, db: Session = Depends(get_db)):
    """获取知识库详情"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    doc_count = db.query(Document).filter(Document.knowledge_base_id == kb.id).count()
    return KnowledgeBaseResponse(
        id=kb.id, name=kb.name, description=kb.description or "",
        department=kb.department or "", owner=kb.owner or "",
        embedding_model=kb.embedding_model, created_at=kb.created_at,
        doc_count=doc_count,
    )


@router.put("/{kb_id}")
def update_knowledge_base(kb_id: int, req: KnowledgeBaseUpdate, db: Session = Depends(get_db)):
    """更新知识库信息"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if req.name is not None:
        kb.name = req.name
    if req.description is not None:
        kb.description = req.description
    if req.department is not None:
        kb.department = req.department
    if req.owner is not None:
        kb.owner = req.owner
    if req.embedding_model is not None:
        kb.embedding_model = req.embedding_model
    db.commit()
    return {"message": "知识库更新成功"}


@router.delete("/{kb_id}")
def delete_knowledge_base(kb_id: int, db: Session = Depends(get_db)):
    """删除知识库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    db.query(Document).filter(Document.knowledge_base_id == kb_id).delete()
    db.delete(kb)
    db.commit()
    vector_service.delete_collection(str(kb_id))
    return {"message": "知识库删除成功"}


@router.post("/{kb_id}/clone")
def clone_knowledge_base(kb_id: int, db: Session = Depends(get_db)):
    """克隆知识库"""
    source = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="知识库不存在")
    new_kb = KnowledgeBase(
        name=f"{source.name}(副本)", description=source.description,
        department=source.department, owner=source.owner,
        embedding_model=source.embedding_model,
    )
    db.add(new_kb)
    db.commit()
    db.refresh(new_kb)
    try:
        vector_service.create_collection(str(new_kb.id))
    except Exception as e:
        print(f"[knowledge] 克隆向量集合失败: {e}")
    return {"id": new_kb.id, "message": "知识库克隆成功"}
