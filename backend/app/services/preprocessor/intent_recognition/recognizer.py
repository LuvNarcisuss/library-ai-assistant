# -*- coding: utf-8 -*-
"""意图识别服务

使用关键词规则 + sklearn 分类模型实现意图识别。
支持多种意图类型：查询、文档管理、知识库管理、帮助、问候等。
"""
import os
import json
import re
from typing import Tuple, Optional, List
from pathlib import Path


# 意图类型定义
INTENT_TYPES = {
    "query": "知识库查询",
    "doc_manage": "文档管理",
    "kb_manage": "知识库管理",
    "system_help": "系统帮助",
    "greeting": "问候语",
    "other": "其他",
}

# 意图置信度阈值
CONFIDENCE_THRESHOLD = 0.6


class IntentRecognizer:
    """意图识别服务

    功能：
    1. 基于关键词规则快速识别高频意图
    2. 基于 sklearn 分类模型处理模糊意图
    3. 返回意图类型和置信度
    """

    def __init__(self):
        self._keyword_rules = {}
        self._model = None
        self._vectorizer = None
        self._initialized = False

    def _init_recognizer(self):
        """初始化意图识别器"""
        if self._initialized:
            return

        # 加载关键词规则
        self._load_keyword_rules()

        # 加载 sklearn 模型（如果存在）
        self._load_model()

        self._initialized = True
        print("[IntentRecognizer] 意图识别器初始化完成")

    def _load_keyword_rules(self):
        """加载关键词规则"""
        rules_path = Path(__file__).parent / "keywords.json"

        if rules_path.exists():
            with open(rules_path, "r", encoding="utf-8") as f:
                self._keyword_rules = json.load(f)
            print(f"[IntentRecognizer] 关键词规则加载完成，包含 {len(self._keyword_rules)} 个意图")
        else:
            # 使用默认规则
            self._keyword_rules = self._get_default_rules()
            # 保存默认规则
            with open(rules_path, "w", encoding="utf-8") as f:
                json.dump(self._keyword_rules, f, ensure_ascii=False, indent=2)
            print("[IntentRecognizer] 使用默认关键词规则")

    def _get_default_rules(self) -> dict:
        """获取默认关键词规则"""
        return {
            "doc_manage": {
                "keywords": [
                    "上传文档", "删除文档", "文档管理", "管理文档", "上传文件",
                    "文档列表", "查看文档", "文档预览", "文档解析", "文本切分",
                    "上传", "文档", "文件管理"
                ],
                "patterns": [
                    r"上传.{0,5}(文档|文件|资料)",
                    r"(删除|移除|去掉).{0,5}(文档|文件)",
                    r"(查看|预览|浏览).{0,5}(文档|文件|内容)",
                ]
            },
            "kb_manage": {
                "keywords": [
                    "创建知识库", "删除知识库", "知识库管理", "编辑知识库", "新建知识库",
                    "知识库列表", "知识库设置", "知识库配置", "向量库", "向量管理",
                    "知识库"
                ],
                "patterns": [
                    r"(创建|新建|建立).{0,5}知识库",
                    r"(删除|移除|去掉).{0,5}知识库",
                    r"(编辑|修改|更新).{0,5}知识库",
                    r"知识库.{0,5}(管理|设置|配置|列表)",
                ]
            },
            "system_help": {
                "keywords": [
                    "怎么使用", "使用帮助", "帮助", "功能介绍", "使用说明",
                    "操作指南", "使用方法", "功能说明", "教程", "指南",
                    "怎么用", "如何使用", "使用流程", "操作说明", "帮助文档",
                    "使用手册", "功能列表", "系统功能"
                ],
                "patterns": [
                    r"(怎么|如何|怎样).{0,5}(使用|用|操作)",
                    r"(帮助|指南|教程|手册)",
                    r"功能.{0,5}(介绍|说明|列表)",
                ]
            },
            "greeting": {
                "keywords": [
                    "你好", "您好", "嗨", "在吗", "你是谁", "你是",
                    "早上好", "下午好", "晚上好", "hello", "hi",
                    "你好呀", "您好呀", "嗨嗨", "在不在"
                ],
                "patterns": [
                    r"^(你好|您好|嗨|hi|hello)",
                    r"(早上|下午|晚上)(好|安康)",
                    r"^在(吗|么|不在)$",
                    r"你是(谁|什么|哪位)",
                ]
            },
        }

    def recognize(self, text: str) -> Tuple[str, float]:
        """识别用户意图

        Args:
            text: 用户输入文本

        Returns:
            (意图类型, 置信度)
        """
        if not text or not text.strip():
            return "query", 0.5  # 默认为查询意图

        self._init_recognizer()

        text = text.strip()

        # 1. 基于关键词规则识别
        intent, confidence = self._recognize_by_keywords(text)

        # 2. 如果置信度不够，尝试使用模型识别
        if confidence < CONFIDENCE_THRESHOLD and self._model:
            model_intent, model_confidence = self._recognize_by_model(text)
            if model_confidence > confidence:
                intent, confidence = model_intent, model_confidence

        # 3. 如果仍然置信度低，默认为查询意图
        if confidence < CONFIDENCE_THRESHOLD:
            intent = "query"
            confidence = 0.5

        print(f"[IntentRecognizer] 识别结果: '{text[:30]}...' -> {intent} ({confidence:.2f})")
        return intent, confidence

    def _recognize_by_keywords(self, text: str) -> Tuple[str, float]:
        """基于关键词规则识别意图

        Args:
            text: 用户输入文本

        Returns:
            (意图类型, 置信度)
        """
        text_lower = text.lower()
        best_intent = "other"
        best_confidence = 0.0

        for intent, rules in self._keyword_rules.items():
            keywords = rules.get("keywords", [])
            patterns = rules.get("patterns", [])

            # 检查关键词匹配
            keyword_score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    keyword_score += 1

            # 检查正则模式匹配
            pattern_score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    pattern_score += 1

            # 计算总分
            total_score = keyword_score * 1.0 + pattern_score * 1.5

            # 计算置信度
            if total_score > 0:
                confidence = min(0.5 + total_score * 0.15, 1.0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent

        return best_intent, best_confidence

    def _recognize_by_model(self, text: str) -> Tuple[str, float]:
        """基于 sklearn 模型识别意图

        Args:
            text: 用户输入文本

        Returns:
            (意图类型, 置信度)
        """
        try:
            if not self._model or not self._vectorizer:
                return "other", 0.0

            # 文本向量化
            text_vector = self._vectorizer.transform([text])

            # 预测
            intent = self._model.predict(text_vector)[0]
            confidence = max(self._model.predict_proba(text_vector)[0])

            return intent, confidence

        except Exception as e:
            print(f"[IntentRecognizer] 模型预测失败: {e}")
            return "other", 0.0

    def _load_model(self):
        """加载 sklearn 模型"""
        model_path = Path(__file__).parent / "model"
        model_file = model_path / "intent_model.pkl"
        vectorizer_file = model_path / "vectorizer.pkl"

        if model_file.exists() and vectorizer_file.exists():
            try:
                import joblib
                self._model = joblib.load(model_file)
                self._vectorizer = joblib.load(vectorizer_file)
                print("[IntentRecognizer] sklearn 模型加载成功")
            except Exception as e:
                print(f"[IntentRecognizer] 模型加载失败: {e}")
                self._model = None
                self._vectorizer = None
        else:
            print("[IntentRecognizer] sklearn 模型不存在，仅使用关键词规则")

    def train_model(self, training_data: List[Tuple[str, str]]):
        """训练意图识别模型

        Args:
            training_data: 训练数据列表，格式为 [(文本, 意图), ...]
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.model_selection import train_test_split
            import joblib
            import jieba

            print(f"[IntentRecognizer] 开始训练模型，样本数: {len(training_data)}")

            # 分词处理
            texts = [" ".join(jieba.cut(text)) for text, _ in training_data]
            labels = [label for _, label in training_data]

            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42
            )

            # 特征提取
            self._vectorizer = TfidfVectorizer(max_features=5000)
            X_train_vec = self._vectorizer.fit_transform(X_train)
            X_test_vec = self._vectorizer.transform(X_test)

            # 训练模型
            self._model = MultinomialNB()
            self._model.fit(X_train_vec, y_train)

            # 评估
            accuracy = self._model.score(X_test_vec, y_test)
            print(f"[IntentRecognizer] 模型训练完成，准确率: {accuracy:.2%}")

            # 保存模型
            model_path = Path(__file__).parent / "model"
            model_path.mkdir(exist_ok=True)

            joblib.dump(self._model, model_path / "intent_model.pkl")
            joblib.dump(self._vectorizer, model_path / "vectorizer.pkl")

            print("[IntentRecognizer] 模型保存成功")

        except ImportError as e:
            print(f"[IntentRecognizer] 缺少依赖: {e}")
            print("请安装: pip install scikit-learn jieba joblib")
        except Exception as e:
            print(f"[IntentRecognizer] 模型训练失败: {e}")

    def get_intent_description(self, intent: str) -> str:
        """获取意图的中文描述

        Args:
            intent: 意图类型

        Returns:
            中文描述
        """
        return INTENT_TYPES.get(intent, "未知意图")

    def add_keyword_rule(self, intent: str, keywords: List[str], patterns: List[str] = None):
        """添加关键词规则

        Args:
            intent: 意图类型
            keywords: 关键词列表
            patterns: 正则模式列表
        """
        self._init_recognizer()

        if intent not in self._keyword_rules:
            self._keyword_rules[intent] = {"keywords": [], "patterns": []}

        self._keyword_rules[intent]["keywords"].extend(keywords)
        if patterns:
            self._keyword_rules[intent]["patterns"].extend(patterns)

        # 保存到文件
        rules_path = Path(__file__).parent / "keywords.json"
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(self._keyword_rules, f, ensure_ascii=False, indent=2)

        print(f"[IntentRecognizer] 添加关键词规则: {intent}")


# 单例
intent_recognizer = IntentRecognizer()
