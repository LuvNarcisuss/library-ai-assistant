# -*- coding: utf-8 -*-
"""向量生成服务

加载 Sentence-Transformer 模型并生成文本向量。
基于 RAG 实操手册最佳实践优化：
- 添加 BGE 查询前缀，提升检索效果
- 向量归一化，便于计算余弦相似度
- 支持批量处理，提升效率
"""
import os
from typing import List, Optional
from app.core.config import settings

# 设置离线模式，优先使用本地缓存（在导入sentence_transformers之前）
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

# BGE 模型查询前缀（用于检索时提升效果）
# 参考：https://huggingface.co/BAAI/bge-small-zh-v1.5
BGE_QUERY_PREFIX = "为这个句子生成表示以用于检索相关文档："


class EmbeddingService:
    """Embedding 模型封装，延迟加载

    优化点：
    1. 查询时添加 BGE 前缀，提升检索准确性
    2. 向量归一化，便于计算余弦相似度
    3. 支持批量处理和进度显示
    """

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.device = device or settings.EMBEDDING_DEVICE
        self._model = None
        # 检查是否使用 BGE 模型
        self._is_bge_model = "bge" in self.model_name.lower()

    @property
    def model(self):
        """延迟加载模型"""
        if self._model is None:
            self.load_model()
        return self._model

    def load_model(self):
        """加载 Sentence-Transformer 模型"""
        from sentence_transformers import SentenceTransformer
        print(f"[EmbeddingService] 加载模型 {self.model_name} 到 {self.device}...")

        try:
            # 尝试从本地缓存加载
            from huggingface_hub import snapshot_download
            local_dir = snapshot_download(
                repo_id=f"BAAI/{self.model_name.replace('BAAI/', '')}",
                local_files_only=True,
                ignore_patterns=["*.md", "*.txt"],
            )
            self._model = SentenceTransformer(local_dir, device=self.device)
            print("[EmbeddingService] 模型加载完成（本地缓存）")
        except Exception as e:
            print(f"[EmbeddingService] 本地加载失败: {e}")
            try:
                # 尝试直接加载
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
                print("[EmbeddingService] 模型加载完成")
            except Exception as e2:
                print(f"[EmbeddingService] 离线加载失败，尝试在线加载: {e2}")
                # 如果离线加载失败，尝试在线加载
                os.environ.pop('HF_HUB_OFFLINE', None)
                os.environ.pop('TRANSFORMERS_OFFLINE', None)
                self._model = SentenceTransformer(self.model_name, device=self.device)
                print("[EmbeddingService] 模型加载完成（在线模式）")

    def embed_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """批量生成文本向量

        Args:
            texts: 待向量化的文本列表
            batch_size: 批处理大小，None 时使用默认值

        Returns:
            向量列表，每个向量为 float 列表
        """
        if not texts:
            return []

        # 过滤空文本
        valid_texts = [t.strip() for t in texts if t.strip()]
        if not valid_texts:
            return []

        # 根据设备设置合适的 batch_size
        if batch_size is None:
            batch_size = 64 if "cuda" in self.device.lower() else 32

        print(f"[EmbeddingService] 开始批量编码 {len(valid_texts)} 条文本...")

        # BGE 模型在编码文档时不需要添加前缀（前缀仅用于查询）
        embeddings = self.model.encode(
            valid_texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,  # 归一化向量，便于计算余弦相似度
            convert_to_numpy=True,
        )

        print(f"[EmbeddingService] 编码完成，向量维度: {embeddings.shape[1]}")
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """生成单条查询向量

        对于 BGE 模型，会在查询文本前添加特定前缀以提升检索效果。
        参考文档：https://huggingface.co/BAAI/bge-small-zh-v1.5

        Args:
            text: 查询文本

        Returns:
            查询向量，float 列表
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # BGE 模型在查询时需要添加前缀
        if self._is_bge_model:
            query_text = f"{BGE_QUERY_PREFIX}{text}"
        else:
            query_text = text

        embedding = self.model.encode(
            [query_text],
            show_progress_bar=False,
            normalize_embeddings=True,  # 归一化向量
            convert_to_numpy=True,
        )

        return embedding[0].tolist()

    def get_embedding_dim(self) -> int:
        """获取向量维度

        Returns:
            向量维度
        """
        # 触发模型加载
        _ = self.model
        return self.model.get_sentence_embedding_dimension()


# 单例
embedding_service = EmbeddingService()
