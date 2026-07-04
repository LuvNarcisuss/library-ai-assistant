# -*- coding: utf-8 -*-
"""文本切分服务

基于 LangChain 的 RecursiveCharacterTextSplitter 实现。
"""
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

def split_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[str]:
    """将文本切分为指定大小的块

    Args:
        text: 原始文本
        chunk_size: 每块字符数，默认从 settings 读取
        chunk_overlap: 块间重叠字符数，默认从 settings 读取

    Returns:
        切分后的文本块列表
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=[
            "\n\n", "\n", "。", "！", "？", "；", "，", " ", "",
        ],
    )

    return splitter.split_text(text)
