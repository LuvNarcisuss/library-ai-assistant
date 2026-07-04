# -*- coding: utf-8 -*-
"""文档解析服务

支持 txt / pdf / docx / md 格式的文本提取。
"""
from pathlib import Path
from typing import Optional

def parse_document(file_path: str) -> Optional[str]:
    """解析文档，提取纯文本内容。失败返回空字符串"""
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".txt":
            return _parse_txt(file_path)
        elif ext == ".pdf":
            return _parse_pdf(file_path)
        elif ext == ".docx":
            return _parse_docx(file_path)
        elif ext == ".md":
            return _parse_md(file_path)
    except Exception as e:
        print(f"[document_parser] 解析失败 {file_path}: {e}")
        return ""
    return ""

def _parse_txt(file_path: str) -> str:
    """解析纯文本文件"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()

def _parse_pdf(file_path: str) -> str:
    """使用 pypdf 解析 PDF 文件"""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    texts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    return "\n\n".join(texts)

def _parse_docx(file_path: str) -> str:
    """使用 python-docx 解析 Word 文档"""
    from docx import Document
    doc = Document(file_path)
    texts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(texts)

def _parse_md(file_path: str) -> str:
    """解析 Markdown 文件"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()
