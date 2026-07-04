# -*- coding: utf-8 -*-
"""向量数据库服务

封装 ChromaDB 的增删改查操作。
"""
from typing import List, Optional
import os
import chromadb
from chromadb.errors import NotFoundError
from app.core.config import settings

class VectorService:
    """ChromaDB 操作封装"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self.init_client()
        return self._client

    def init_client(self):
        persist_dir = settings.CHROMA_PERSIST_DIR
        os.makedirs(persist_dir, exist_ok=True)
        print(f"[VectorService] 初始化 ChromaDB: {persist_dir}")
        self._client = chromadb.PersistentClient(path=persist_dir)

    def _format_collection_name(self, name: str) -> str:
        """格式化 collection 名称，确保符合 ChromaDB 命名规则（3-512字符）"""
        # 添加前缀确保最小长度
        formatted = f"kb_{name}" if len(name) < 3 else name
        return formatted

    def _get_collection(self, name: str):
        formatted_name = self._format_collection_name(name)
        try:
            return self.client.get_collection(formatted_name)
        except (ValueError, NotFoundError):
            return self.client.create_collection(formatted_name)

    def create_collection(self, name: str):
        formatted_name = self._format_collection_name(name)
        try:
            self.client.delete_collection(formatted_name)
        except (ValueError, NotFoundError):
            pass
        return self.client.create_collection(formatted_name)

    def list_collections(self) -> List[str]:
        return [c.name for c in self.client.list_collections()]

    def add_documents(self, collection: str, texts: List[str],
                    embeddings: List[List[float]], metadatas: List[dict],
                    ids: List[str]):
        col = self._get_collection(collection)
        col.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

    def search(self, collection: str, query_embedding: List[float],
              top_k: Optional[int] = None) -> List[dict]:
        k = top_k or settings.TOP_K
        formatted_name = self._format_collection_name(collection)
        try:
            col = self.client.get_collection(formatted_name)
        except (ValueError, NotFoundError):
            return []
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        items = []
        if results["ids"][0]:
            for i in range(len(results["ids"][0])):
                items.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                })
        return items

    def delete_collection(self, name: str):
        formatted_name = self._format_collection_name(name)
        try:
            self.client.delete_collection(formatted_name)
        except (ValueError, NotFoundError):
            pass

    def delete_documents(self, collection: str, ids: List[str]):
        formatted_name = self._format_collection_name(collection)
        try:
            col = self.client.get_collection(formatted_name)
            col.delete(ids=ids)
        except (ValueError, NotFoundError):
            pass

    def get_document_chunks(self, collection: str, doc_id: str) -> List[dict]:
        formatted_name = self._format_collection_name(collection)
        try:
            col = self.client.get_collection(formatted_name)
        except (ValueError, NotFoundError):
            return []
        results = col.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas"],
        )
        items = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                items.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                })
        return items

vector_service = VectorService()
