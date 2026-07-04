"""Pydantic 请求/响应模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# 认证
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    class Config:
        from_attributes = True


# 知识库
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    department: Optional[str] = ""
    owner: Optional[str] = ""
    embedding_model: Optional[str] = "BAAI/bge-small-zh-v1.5"


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    embedding_model: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: str
    department: str
    owner: str
    embedding_model: str
    created_at: datetime
    doc_count: Optional[int] = 0
    class Config:
        from_attributes = True


# 文档
class DocumentResponse(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    file_size: int
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime
    class Config:
        from_attributes = True


# 对话
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    knowledge_base_id: Optional[int] = None
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list = []
    session_id: str


class ConversationResponse(BaseModel):
    id: int
    session_id: str
    question: str
    answer: str
    sources: str
    created_at: datetime
    class Config:
        from_attributes = True


# 通用
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list
