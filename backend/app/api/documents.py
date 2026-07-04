# -*- coding: utf-8 -*-
"""文档管理 API 路由"""
import os
import uuid
import hashlib
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.database import get_db
from app.models.models import KnowledgeBase, Document
from app.models.schemas import DocumentResponse
from app.services.document_parser import parse_document
from app.services.text_splitter import split_text
from app.services.embedding_service import embedding_service
from app.services.vector_service import vector_service
import chardet

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "data", "uploads")
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md"}


def fix_filename_encoding(filename: str) -> str:
    """修复中文文件名编码问题

    curl 上传文件时，中文文件名可能被错误编码（如 GB18030），需要检测并转换回 UTF-8
    """
    if not filename:
        return filename

    # 检查是否包含中文字符（已经是 UTF-8）
    try:
        filename.encode('utf-8')
        # 如果能直接编码为 UTF-8，检查是否包含中文
        if any('一' <= c <= '鿿' for c in filename):
            return filename
    except UnicodeEncodeError:
        pass

    # 尝试使用 chardet 检测编码
    try:
        # 将字符串编码为 latin-1（兼容所有字节）
        raw_bytes = filename.encode('latin-1')
        detected = chardet.detect(raw_bytes)

        if detected and detected['encoding']:
            encoding = detected['encoding']
            # 尝试使用检测到的编码解码
            try:
                fixed = raw_bytes.decode(encoding)
                # 验证修复后的文件名是否包含中文
                if any('一' <= c <= '鿿' for c in fixed):
                    return fixed
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    # 如果都失败，返回原始文件名
    return filename

router = APIRouter(prefix="/api/documents", tags=["文档"])


@router.get("")
def list_documents(
    knowledge_base_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取文档列表"""
    q = db.query(Document)
    if knowledge_base_id is not None:
        q = q.filter(Document.knowledge_base_id == knowledge_base_id)
    if status:
        q = q.filter(Document.status == status)
    total = q.count()
    items = q.order_by(Document.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/upload", status_code=201)
async def upload_document(
    knowledge_base_id: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传文档并自动解析、切分、向量化、入库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，仅支持 txt/pdf/docx/md")

    # 保存文件
    kb_dir = os.path.join(UPLOAD_DIR, str(knowledge_base_id))
    os.makedirs(kb_dir, exist_ok=True)

    # 读取文件内容并计算哈希
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    # 检查文件是否已存在（去重）
    existing_doc = db.query(Document).filter(
        Document.knowledge_base_id == knowledge_base_id,
        Document.file_hash == file_hash
    ).first()

    if existing_doc:
        # 文件已存在，返回已有文档信息
        return {
            "id": existing_doc.id,
            "filename": existing_doc.filename,
            "status": existing_doc.status,
            "chunk_count": existing_doc.chunk_count,
            "message": f"文件已存在（与文档 {existing_doc.id} 重复）",
        }

    # 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(kb_dir, unique_name)
    with open(file_path, "wb") as fh:
        fh.write(content)

    # 修复文件名编码
    fixed_filename = fix_filename_encoding(file.filename) or "unknown"

    # DB 记录
    doc = Document(
        knowledge_base_id=knowledge_base_id,
        filename=fixed_filename,
        file_size=len(content),
        file_type=ext.lstrip("."),
        file_hash=file_hash,
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        doc.status = "processing"
        db.commit()

        # 1. 解析文档
        text = parse_document(file_path)
        if not text:
            raise ValueError("文档内容为空")

        # 2. 文本切分
        chunks = split_text(text)
        if not chunks:
            raise ValueError("切分后文本块为空")

        # 3. 生成向量
        embeddings = embedding_service.embed_texts(chunks)

        # 4. 入库 Chroma
        metadatas = [
            {
                "doc_id": str(doc.id),
                "kb_id": str(knowledge_base_id),
                "filename": doc.filename,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]
        ids = [f"{doc.id}_{i}" for i in range(len(chunks))]
        vector_service.add_documents(
            collection=str(knowledge_base_id),
            texts=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        # 5. 更新状态
        doc.status = "completed"
        doc.chunk_count = len(chunks)
        db.commit()

    except Exception as e:
        doc.status = "failed"
        db.commit()
        print(f"[documents] 处理失败 {file.filename}: {e}")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "message": "文档上传成功" if doc.status == "completed" else "文档处理失败",
    }


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """删除文档及其向量数据"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删除向量
    collection = str(doc.knowledge_base_id)
    chunk_ids = [f"{doc.id}_{i}" for i in range(doc.chunk_count)]
    if chunk_ids:
        vector_service.delete_documents(collection, chunk_ids)

    # 删除文件
    db.delete(doc)
    db.commit()
    return {"message": "文档删除成功"}


@router.get("/{doc_id}/preview")
def preview_document(doc_id: int, db: Session = Depends(get_db)):
    """预览文档的文本块内容"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    chunks = vector_service.get_document_chunks(
        collection=str(doc.knowledge_base_id),
        doc_id=str(doc.id),
    )
    return {"filename": doc.filename, "chunk_count": len(chunks), "chunks": chunks}
