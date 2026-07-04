# -*- coding: utf-8 -*-
"""智能预处理入口

集成语义纠错、意图识别、问题重写三个模块，
提供统一的预处理接口。
"""
from typing import Tuple, Optional, Dict, Any
from app.services.preprocessor.spell_correction import spell_corrector
from app.services.preprocessor.intent_recognition import intent_recognizer
from app.services.preprocessor.query_rewrite import query_rewriter


class Preprocessor:
    """智能预处理服务

    处理流程：
    1. 语义纠错 - 纠正用户输入的错别字
    2. 意图识别 - 判断用户意图类型
    3. 问题重写 - 优化模糊问题（仅查询意图）
    """

    def __init__(self):
        self._spell_corrector = spell_corrector
        self._intent_recognizer = intent_recognizer
        self._query_rewriter = query_rewriter

    def process(
        self,
        query: str,
        context: Optional[str] = None,
        skip_spell_correction: bool = False,
        skip_intent_recognition: bool = False,
        skip_query_rewrite: bool = False,
    ) -> Dict[str, Any]:
        """处理用户输入

        Args:
            query: 用户原始输入
            context: 可选的上下文信息
            skip_spell_correction: 是否跳过语义纠错
            skip_intent_recognition: 是否跳过意图识别
            skip_query_rewrite: 是否跳过问题重写

        Returns:
            处理结果字典，包含：
            - original_query: 原始问题
            - corrected_query: 纠错后的问题
            - intent: 识别的意图类型
            - intent_confidence: 意图置信度
            - rewritten_query: 重写后的问题
            - final_query: 最终用于检索的问题
            - corrections: 纠错详情
        """
        result = {
            "original_query": query,
            "corrected_query": query,
            "intent": "query",
            "intent_confidence": 0.5,
            "rewritten_query": query,
            "final_query": query,
            "corrections": [],
        }

        if not query or not query.strip():
            return result

        print(f"[Preprocessor] 开始处理: '{query}'")

        # 1. 语义纠错
        if not skip_spell_correction:
            corrected, corrections = self._spell_corrector.correct(query)
            result["corrected_query"] = corrected
            result["corrections"] = corrections
            if corrections:
                print(f"[Preprocessor] 纠错完成: '{query}' -> '{corrected}'")

        # 2. 意图识别
        working_query = result["corrected_query"]
        if not skip_intent_recognition:
            intent, confidence = self._intent_recognizer.recognize(working_query)
            result["intent"] = intent
            result["intent_confidence"] = confidence
            print(f"[Preprocessor] 意图识别: {intent} ({confidence:.2f})")

        # 3. 问题重写（仅对查询意图）
        if not skip_query_rewrite and result["intent"] == "query":
            rewritten = self._query_rewriter.rewrite(working_query, context)
            result["rewritten_query"] = rewritten
            result["final_query"] = rewritten
            if rewritten != working_query:
                print(f"[Preprocessor] 问题重写: '{working_query}' -> '{rewritten}'")
        else:
            result["rewritten_query"] = working_query
            result["final_query"] = working_query

        print(f"[Preprocessor] 处理完成: final_query='{result['final_query']}'")
        return result

    def correct_text(self, text: str) -> Tuple[str, list]:
        """仅执行语义纠错

        Args:
            text: 原始文本

        Returns:
            (纠正后的文本, 纠正详情)
        """
        return self._spell_corrector.correct(text)

    def recognize_intent(self, text: str) -> Tuple[str, float]:
        """仅执行意图识别

        Args:
            text: 用户输入

        Returns:
            (意图类型, 置信度)
        """
        return self._intent_recognizer.recognize(text)

    def rewrite_query(self, query: str, context: Optional[str] = None) -> str:
        """仅执行问题重写

        Args:
            query: 原始问题
            context: 上下文信息

        Returns:
            重写后的问题
        """
        return self._query_rewriter.rewrite(query, context)

    def get_intent_description(self, intent: str) -> str:
        """获取意图的中文描述

        Args:
            intent: 意图类型

        Returns:
            中文描述
        """
        return self._intent_recognizer.get_intent_description(intent)

    def get_stats(self) -> Dict[str, Any]:
        """获取预处理统计信息

        Returns:
            统计信息字典
        """
        return {
            "domain_dict_size": len(self._spell_corrector.get_domain_dict()),
            "intent_types": list(self._intent_recognizer._keyword_rules.keys()) if self._intent_recognizer._keyword_rules else [],
        }


# 单例
preprocessor = Preprocessor()
