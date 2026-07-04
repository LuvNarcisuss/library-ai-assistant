# -*- coding: utf-8 -*-
"""RAG 检索增强生成服务

完整的 RAG 流程：智能预处理 → 知识库检索 → LLM 增强 → 返回用户
基于 RAG 实操手册最佳实践优化：
- 智能预处理（语义纠错、意图识别、问题重写）
- 结构化 Prompt 模板
- 检索结果重排序
- 上下文管理优化
- 答案来源精确标注
"""
import re
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.services.preprocessor import preprocessor

# 配置常量
PAGE_SIZE = 3  # 单页分组显示的文本块数
MAX_HISTORY_TURNS = 3  # 保留的最大历史对话轮数
MAX_CONTEXT_LENGTH = 2000  # 最大上下文长度（字符）


# ==================== Prompt 模板 ====================

# 有知识库上下文时的 Prompt 模板
RAG_PROMPT_TEMPLATE = """你是"小江"，一个专业的高校图书馆智能咨询助手。

## 任务说明
请根据下方提供的【参考资料】来回答用户的问题。

## 回答规则
1. **严格基于参考资料**：仅使用参考资料中的信息回答，不要编造或推测
2. **准确引用**：在回答中标注信息来源，格式为 [来源：文档名]
3. **简洁友好**：回答要简洁、准确、友好，使用中文
4. **结构清晰**：使用适当的格式（如列表、分点）使回答更易读
5. **承认局限**：如果参考资料中没有完全匹配的信息，请明确说明

## 参考资料
{context}

## 用户问题
{question}

## 回答"""


# 无知识库上下文时的 Prompt 模板
NO_CONTEXT_PROMPT_TEMPLATE = """你是"小江"，一个专业的高校图书馆智能咨询助手。

## 任务说明
知识库中没有找到与用户问题直接相关的内容。请根据你的通用知识来回答。

## 回答规则
1. **说明情况**：在回答开头说明"知识库中暂无相关内容，以下是根据通用知识的回答"
2. **提供价值**：尽量提供有用的信息或建议
3. **引导用户**：如果是图书馆具体事务（如开放时间、借阅规则等），建议用户查看图书馆官方公告或咨询工作人员
4. **简洁友好**：回答要简洁、准确、友好，使用中文

## 用户问题
{question}

## 回答"""


# 带历史对话的 Prompt 模板
HISTORY_PROMPT_TEMPLATE = """## 历史对话
{history}

## 当前问题
{question}"""


class RAGService:
    """RAG 检索增强生成服务

    完整流程：
    1. 用户提问 → 2. 智能预处理 → 3. 语义检索知识库 → 4. 构建上下文 → 5. LLM 生成增强答案 → 6. 返回带来源的答案
    """

    def preprocess_query(
        self,
        query: str,
        context: Optional[str] = None,
        skip_spell_correction: bool = False,
        skip_query_rewrite: bool = False,
    ) -> Dict[str, Any]:
        """预处理用户问题

        Args:
            query: 用户原始问题
            context: 可选的上下文信息
            skip_spell_correction: 是否跳过语义纠错
            skip_query_rewrite: 是否跳过问题重写

        Returns:
            预处理结果字典
        """
        return preprocessor.process(
            query=query,
            context=context,
            skip_spell_correction=skip_spell_correction,
            skip_query_rewrite=skip_query_rewrite,
        )

    def retrieve(
        self,
        collection: str,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[dict]:
        """语义检索知识库

        Args:
            collection: 知识库名称
            query: 用户查询文本
            top_k: 返回结果数量
            score_threshold: 相似度阈值，低于此值的结果将被过滤

        Returns:
            检索结果列表，每个结果包含 id, text, metadata, similarity
        """
        k = top_k or settings.TOP_K
        threshold = score_threshold or settings.SIMILARITY_THRESHOLD

        # 1. 生成查询向量
        try:
            query_vector = embedding_service.embed_query(query)
        except Exception as e:
            print(f"[RAGService] 嵌入查询失败: {e}")
            return []

        # 2. 向量检索
        results = vector_service.search(collection, query_vector, top_k=k)

        # 3. 过滤和排序
        filtered = []
        for r in results:
            # ChromaDB 返回的 distance 越小表示越相似
            # 将 distance 转换为 similarity (0-1)
            distance = r.get("distance", 1)
            similarity = max(0, 1 - distance)  # 确保不小于0

            if similarity >= threshold:
                r["similarity"] = round(similarity, 4)
                filtered.append(r)

        # 4. 按相似度降序排序
        filtered.sort(key=lambda x: x["similarity"], reverse=True)

        print(f"[RAGService] 检索完成: 查询='{query[:30]}...', 结果数={len(filtered)}")
        return filtered

    def _deduplicate_sources(self, docs: List[dict]) -> List[dict]:
        """去重并格式化来源信息

        Args:
            docs: 检索结果列表

        Returns:
            去重后的来源信息列表
        """
        seen_files = set()
        sources = []

        for doc in docs:
            meta = doc.get("metadata", {})
            filename = meta.get("filename", "未知文档")
            doc_id = meta.get("doc_id", "")

            # 使用文件名去重
            if filename not in seen_files:
                seen_files.add(filename)
                text = doc.get("text", "")
                sources.append({
                    "filename": filename,
                    "doc_id": doc_id,
                    "similarity": doc.get("similarity", 0),
                    "snippet": text[:150] + "..." if len(text) > 150 else text,
                })

        return sources

    def _build_context(self, retrieved_docs: List[dict]) -> str:
        """构建 LLM 输入的上下文

        Args:
            retrieved_docs: 检索结果列表

        Returns:
            格式化的上下文字符串
        """
        if not retrieved_docs:
            return ""

        context_parts = []
        total_length = 0

        for i, doc in enumerate(retrieved_docs[:PAGE_SIZE]):
            text = doc.get("text", "")
            filename = doc.get("metadata", {}).get("filename", "未知文档")
            similarity = doc.get("similarity", 0)

            # 格式化每个文本块
            chunk = f"[来源{i+1}: {filename} (相关度: {similarity:.1%})]\n{text}"
            context_parts.append(chunk)
            total_length += len(chunk)

            # 防止上下文过长
            if total_length >= MAX_CONTEXT_LENGTH:
                print(f"[RAGService] 上下文已达到长度限制 ({MAX_CONTEXT_LENGTH} 字符)")
                break

        return "\n\n".join(context_parts)

    def _build_history_context(self, history: Optional[List[dict]]) -> str:
        """构建历史对话上下文

        Args:
            history: 历史对话列表 [{"question": ..., "answer": ...}, ...]

        Returns:
            格式化的历史对话字符串
        """
        if not history:
            return ""

        # 只保留最近 N 轮对话
        recent_history = history[-MAX_HISTORY_TURNS:]

        history_parts = []
        for h in recent_history:
            q = h.get("question", "")
            a = h.get("answer", "")
            if q and a:
                history_parts.append(f"用户：{q}\n助手：{a}")

        return "\n\n".join(history_parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        history: Optional[List[dict]] = None,
    ) -> str:
        """构建完整的 RAG Prompt

        Args:
            query: 用户问题
            context: 检索到的参考资料
            history: 历史对话记录

        Returns:
            完整的 prompt 字符串
        """
        # 1. 根据是否有上下文选择基础模板
        if context.strip():
            base_prompt = RAG_PROMPT_TEMPLATE.format(
                context=context,
                question=query
            )
        else:
            base_prompt = NO_CONTEXT_PROMPT_TEMPLATE.format(question=query)

        # 2. 如果有历史对话，添加到 prompt 中
        history_text = self._build_history_context(history)
        if history_text:
            history_prompt = HISTORY_PROMPT_TEMPLATE.format(
                history=history_text,
                question=query
            )
            # 将历史对话添加到 prompt 开头
            base_prompt = f"{history_prompt}\n\n{base_prompt}"

        return base_prompt

    def _clean_answer(self, text: str) -> str:
        """清理 LLM 回答中的特殊字符

        Args:
            text: LLM 原始回答

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除 emoji 字符和其他非 BMP 字符
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        # 移除多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def generate_answer(
        self,
        query: str,
        retrieved_docs: List[dict],
        history: Optional[List[dict]] = None,
    ) -> dict:
        """生成带来源引用的答案（核心方法）

        完整流程：
        1. 格式化来源信息
        2. 构建上下文
        3. 构建 Prompt
        4. 调用 LLM 生成答案
        5. 清理和格式化答案

        Args:
            query: 用户问题
            retrieved_docs: retrieve() 返回的检索结果
            history: 历史消息列表 [{"question": ..., "answer": ...}, ...]

        Returns:
            {"answer": str, "sources": list, "has_context": bool}
        """
        # 1. 格式化来源信息
        sources = self._deduplicate_sources(retrieved_docs) if retrieved_docs else []

        # 2. 构建上下文
        context = self._build_context(retrieved_docs)

        # 3. 构建 Prompt
        prompt = self._build_prompt(query, context, history)

        # 4. 调用 LLM 生成答案
        try:
            print(f"[RAGService] 开始调用LLM，问题: {query[:50]}...")
            print(f"[RAGService] 上下文长度: {len(context)} 字符")

            answer = llm_service.generate(prompt)

            print(f"[RAGService] LLM返回成功，长度: {len(answer)}")

            # 5. 清理答案
            answer = self._clean_answer(answer)

            print(f"[RAGService] 清理后长度: {len(answer)}")

            return {
                "answer": answer,
                "sources": sources,
                "has_context": bool(context),
            }

        except ValueError as e:
            # API Key 未配置
            print(f"[RAGService] LLM 未配置: {e}")
            return self._fallback_answer(query, context, sources, "未配置")

        except Exception as e:
            # LLM 调用失败
            print(f"[RAGService] LLM 调用失败: {type(e).__name__}: {e}")
            return self._fallback_answer(query, context, sources, "调用失败")

    def _fallback_answer(
        self,
        query: str,
        context: str,
        sources: list,
        error_type: str,
    ) -> dict:
        """生成降级答案（当 LLM 不可用时）

        Args:
            query: 用户问题
            context: 检索到的上下文
            sources: 来源信息
            error_type: 错误类型

        Returns:
            降级答案字典
        """
        if context:
            answer = (
                f"知识库中找到以下相关内容：\n\n{context}\n\n"
                f"（注意：AI服务{error_type}，以上为原始检索结果，仅供参考）"
            )
        else:
            answer = "抱歉，AI服务暂未配置，无法为您生成智能回复。请联系管理员配置AI服务。"

        return {
            "answer": answer,
            "sources": sources,
            "has_context": bool(context),
        }


# 单例
rag_service = RAGService()
