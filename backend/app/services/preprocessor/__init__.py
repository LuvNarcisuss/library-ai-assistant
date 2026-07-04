# -*- coding: utf-8 -*-
"""智能预处理模块

包含三个子模块：
1. spell_correction - 语义纠错
2. intent_recognition - 意图识别
3. query_rewrite - 问题重写
"""
from app.services.preprocessor.preprocessor import preprocessor

__all__ = ["preprocessor"]
