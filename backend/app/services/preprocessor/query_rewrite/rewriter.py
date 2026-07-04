# -*- coding: utf-8 -*-
"""问题重写服务

使用 LLM 自动优化用户的模糊问题，提升检索准确率。
支持补充上下文、扩展关键词、消除歧义、口语化转书面化等场景。
"""
import re
from typing import Optional


# 重写判断阈值
MIN_QUERY_LENGTH = 5  # 最小问题长度
ORAL_PATTERN = re.compile(r'[咋|咋样|咋整|咋办|咋回事|嘛呢|啥|啥意思|阔以|能不能|可不可以]')


class QueryRewriter:
    """问题重写服务

    功能：
    1. 判断是否需要重写
    2. 调用 LLM 进行问题重写
    3. 保持原意不变，提升检索准确性
    """

    def __init__(self):
        self._llm_service = None

    def _get_llm_service(self):
        """延迟加载 LLM 服务"""
        if self._llm_service is None:
            from app.services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    def rewrite(self, query: str, context: Optional[str] = None) -> str:
        """重写用户问题

        Args:
            query: 原始用户问题
            context: 可选的上下文信息（如历史对话）

        Returns:
            重写后的问题（如果不需要重写，返回原问题）
        """
        if not query or not query.strip():
            return query

        query = query.strip()

        # 判断是否需要重写
        if not self.need_rewrite(query):
            print(f"[QueryRewriter] 问题已足够清晰，无需重写: '{query}'")
            return query

        print(f"[QueryRewriter] 开始重写问题: '{query}'")

        try:
            rewritten = self._rewrite_with_llm(query, context)
            print(f"[QueryRewriter] 重写完成: '{query}' -> '{rewritten}'")
            return rewritten
        except Exception as e:
            print(f"[QueryRewriter] 重写失败，使用原问题: {e}")
            return query

    def need_rewrite(self, query: str) -> bool:
        """判断是否需要重写

        规则：
        1. 问题过短（< 5字）
        2. 包含口语化表达
        3. 缺少主语或宾语

        Args:
            query: 用户问题

        Returns:
            是否需要重写
        """
        if not query:
            return False

        # 1. 问题过短
        if len(query) < MIN_QUERY_LENGTH:
            print(f"[QueryRewriter] 问题过短 ({len(query)}字)，需要重写")
            return True

        # 2. 包含口语化表达
        if ORAL_PATTERN.search(query):
            print(f"[QueryRewriter] 包含口语化表达，需要重写")
            return True

        # 3. 检查是否缺少关键信息
        if self._lacks_key_info(query):
            print(f"[QueryRewriter] 缺少关键信息，需要重写")
            return True

        return False

    def _lacks_key_info(self, query: str) -> bool:
        """检查问题是否缺少关键信息

        Args:
            query: 用户问题

        Returns:
            是否缺少关键信息
        """
        # 简单规则：问题长度适中但缺少明确的动词或名词
        if len(query) < 8:
            return True

        # 检查是否包含疑问词
        question_words = ["什么", "怎么", "如何", "为什么", "哪里", "哪个", "多少", "几"]
        has_question_word = any(word in query for word in question_words)

        # 如果没有疑问词且问题较短，可能需要补充
        if not has_question_word and len(query) < 10:
            return True

        return False

    def _rewrite_with_llm(self, query: str, context: Optional[str] = None) -> str:
        """使用 LLM 进行问题重写

        Args:
            query: 原始问题
            context: 上下文信息

        Returns:
            重写后的问题
        """
        prompt = self._build_rewrite_prompt(query, context)

        llm_service = self._get_llm_service()
        response = llm_service.generate(prompt)

        # 提取重写后的问题
        rewritten = self._extract_query_from_response(response)

        return rewritten

    def _build_rewrite_prompt(self, query: str, context: Optional[str] = None) -> str:
        """构建重写 Prompt

        Args:
            query: 原始问题
            context: 上下文信息

        Returns:
            完整的 Prompt
        """
        prompt = """你是一个问题优化助手。请将用户的问题重写为更清晰、更适合检索的形式。

## 重写规则
1. 保持原意不变
2. 补充隐含的关键信息
3. 将口语化表达转换为书面语
4. 如果问题已经很清晰，直接返回原问题
5. 只返回重写后的问题，不要添加任何解释

## 重写示例
- "葡萄怎么样" → "葡萄的口感和营养成分怎么样"
- "咋借书" → "如何借阅图书"
- "Python" → "Python编程语言学习教程"
- "苹果" → "苹果公司的产品介绍" (如果是科技相关)
- "图书馆开门吗" → "图书馆的开放时间是什么"
"""

        if context:
            prompt += f"\n## 上下文信息\n{context}\n"

        prompt += f"\n## 用户问题\n{query}\n\n## 重写后的问题\n"

        return prompt

    def _extract_query_from_response(self, response: str) -> str:
        """从 LLM 响应中提取重写后的问题

        Args:
            response: LLM 响应文本

        Returns:
            提取的问题
        """
        if not response:
            return ""

        # 清理响应文本
        response = response.strip()

        # 移除可能的前缀
        prefixes = ["重写后的问题：", "重写后的问题:", "问题：", "问题:", "回答：", "回答:"]
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()

        # 移除引号
        if (response.startswith('"') and response.endswith('"')) or \
           (response.startswith("'") and response.endswith("'")):
            response = response[1:-1].strip()

        # 移除末尾的标点符号（如果有）
        response = response.rstrip("。.？?！!")

        return response


# 单例
query_rewriter = QueryRewriter()
