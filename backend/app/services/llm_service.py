# -*- coding: utf-8 -*-
"""LLM 服务

使用 langchain 调用 OpenAI 兼容 API（支持 DeepSeek、智谱 GLM、通义千问等）。
基于 RAG 实操手册最佳实践优化：
- 结构化消息格式
- 更好的错误处理
- 重试机制
- Token 使用统计
- 编码兼容性处理（Windows GBK）
"""
import re
import sys
from typing import Optional, Dict, Any
from app.core.config import settings


class LLMService:
    """LLM 调用封装，延迟加载

    优化点：
    1. 使用 ChatPromptTemplate 结构化消息
    2. 添加重试机制
    3. 记录 Token 使用统计
    4. 更好的错误处理
    5. Windows 编码兼容性处理
    """

    def __init__(self):
        self._llm = None
        self._call_count = 0
        self._total_tokens = 0

    @property
    def llm(self):
        """延迟加载 LLM 实例"""
        if self._llm is None:
            self._init_llm()
        return self._llm

    def _init_llm(self):
        """初始化 langchain ChatOpenAI"""
        from langchain_openai import ChatOpenAI

        if not settings.LLM_API_KEY:
            raise ValueError(
                "未配置 LLM_API_KEY，请在 .env 文件中设置。"
                "支持 DeepSeek、智谱 GLM、通义千问等 OpenAI 兼容 API。"
            )

        print(f"[LLMService] 初始化 LLM: {settings.LLM_MODEL_NAME} @ {settings.LLM_BASE_URL}")

        self._llm = ChatOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            # 添加请求超时
            request_timeout=60,
        )

        print("[LLMService] LLM 初始化完成")

    def _clean_response(self, text: str) -> str:
        """清理 LLM 响应中的特殊字符

        处理 Windows GBK 编码问题，移除或替换无法编码的字符。

        Args:
            text: LLM 原始响应

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除 emoji 字符（Unicode 范围）
        # emoji 通常在 U+1F000 到 U+1FFFF 之间
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)

        # 移除其他可能导致编码问题的特殊字符
        # 保留常见的中文、英文、数字和标点
        text = re.sub(r'[^\w\s一-鿿　-〿＀-￯ -⁯.,!?;:()（）【】《》""''、。，！？；：]', '', text)

        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

        return text.strip()

    def generate(self, prompt: str, max_retries: int = 2) -> str:
        """调用 LLM 生成回答

        Args:
            prompt: 完整的 prompt 内容
            max_retries: 最大重试次数

        Returns:
            LLM 生成的文本回答

        Raises:
            ValueError: 未配置 API Key
            RuntimeError: API 调用失败（重试后仍失败）
        """
        from langchain_core.messages import HumanMessage

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # 记录调用次数
                self._call_count += 1

                # 调用 LLM
                response = self.llm.invoke([HumanMessage(content=prompt)])

                # 记录 Token 使用（如果可用）
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    tokens = response.usage_metadata.get('total_tokens', 0)
                    self._total_tokens += tokens
                    print(f"[LLMService] Token 使用: {tokens}, 累计: {self._total_tokens}")

                # 清理响应中的特殊字符
                cleaned_content = self._clean_response(response.content)
                return cleaned_content

            except ValueError as e:
                # API Key 未配置，不重试
                raise e

            except UnicodeEncodeError as e:
                # 编码错误，清理后返回
                print(f"[LLMService] 编码错误，尝试清理: {e}")
                if hasattr(response, 'content'):
                    return self._clean_response(response.content)
                raise

            except Exception as e:
                last_error = e
                print(f"[LLMService] LLM 调用失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")

                # 如果还有重试机会，等待后重试
                if attempt < max_retries:
                    import time
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    print(f"[LLMService] 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

        # 所有重试都失败
        raise RuntimeError(f"LLM 调用失败（已重试 {max_retries} 次）: {last_error}") from last_error

    def get_stats(self) -> Dict[str, Any]:
        """获取 LLM 调用统计

        Returns:
            统计信息字典
        """
        return {
            "model": settings.LLM_MODEL_NAME,
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "avg_tokens_per_call": (
                self._total_tokens // self._call_count
                if self._call_count > 0
                else 0
            ),
        }

    def reset_stats(self):
        """重置统计信息"""
        self._call_count = 0
        self._total_tokens = 0


# 单例
llm_service = LLMService()
