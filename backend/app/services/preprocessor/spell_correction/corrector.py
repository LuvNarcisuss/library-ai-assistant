# -*- coding: utf-8 -*-
"""语义纠错服务

使用 pycorrector + 领域词库实现中文错别字纠正。
支持同音字、形近字、拼音输入等错误类型。
"""
import os
import json
from typing import Tuple, List, Optional
from pathlib import Path


class SpellCorrector:
    """语义纠错服务

    功能：
    1. 自动纠正用户输入的错别字
    2. 支持图书馆领域专业词汇
    3. 透明处理，不显示中间结果
    """

    def __init__(self):
        self._corrector = None
        self._domain_dict = {}
        self._initialized = False

    def _init_corrector(self):
        """初始化 pycorrector 和领域词库"""
        if self._initialized:
            return

        try:
            import pycorrector
            self._corrector = pycorrector
            print("[SpellCorrector] pycorrector 加载成功")
        except ImportError:
            print("[SpellCorrector] pycorrector 未安装，使用基础纠错")
            self._corrector = None

        # 加载领域词库
        self._load_domain_dict()
        self._initialized = True

    def _load_domain_dict(self):
        """加载图书馆领域词库"""
        dict_path = Path(__file__).parent / "library_dict.json"

        if dict_path.exists():
            with open(dict_path, "r", encoding="utf-8") as f:
                self._domain_dict = json.load(f)
            print(f"[SpellCorrector] 领域词库加载完成，包含 {len(self._domain_dict)} 个词条")
        else:
            # 使用默认词库
            self._domain_dict = self._get_default_dict()
            # 保存默认词库
            with open(dict_path, "w", encoding="utf-8") as f:
                json.dump(self._domain_dict, f, ensure_ascii=False, indent=2)
            print("[SpellCorrector] 使用默认领域词库")

    def _get_default_dict(self) -> dict:
        """获取默认领域词库"""
        return {
            "图书馆": ["图收馆", "图书管", "图书官", "图苏馆", "图数馆", "图书倌"],
            "借阅": ["借月", "借约", "借越", "借乐", "借钥"],
            "归还": ["归幻", "归环", "鬼还", "规还"],
            "知识库": ["知识裤", "知是库", "智识库", "知试库", "只是库"],
            "文档": ["文挡", "文当", "稳档", "问档", "蚊档"],
            "检索": ["简索", "捡索", "监索", "见索", "剑索"],
            "向量": ["像量", "相量", "响量", "象量", "箱量"],
            "嵌入": ["欠入", "潜入", "浅入", "前入"],
            "模型": ["莫行", "磨型", "模形", "末型"],
            "智能": ["只嫩", "知能", "制能", "质能"],
            "问答": ["稳答", "问达", "文答", "温答"],
            "系统": ["系同", "戏统", "细统", "系通"],
            "用户": ["用胡", "有户", "用护", "友户"],
            "登录": ["陆登", "录登", "路登", "鹿登"],
            "注册": ["注策", "住册", "祝册", "注拆"],
            "搜索": ["所搜", "缩搜", "素搜", "锁搜"],
            "查询": ["查寻", "差询", "察询", "插询"],
            "帮助": ["帮主", "邦助", "棒助", "帮住"],
            "设置": ["设只", "社置", "设制", "射置"],
            "导出": ["倒出", "到出", "道出", "盗出"],
            "导入": ["倒人", "到人", "道人", "盗人"],
            "分析": ["分西", "份析", "分细", "纷析"],
            "统计": ["统记", "通计", "同记", "桶计"],
            "报告": ["抱告", "报高", "暴告", "爆告"],
            "数据": ["数剧", "书据", "数具", "属据"],
            "信息": ["新息", "信西", "心息", "欣息"],
            "通知": ["通只", "同知", "通制", "统知"],
            "历史": ["力史", "丽史", "利史", "立史"],
            "记录": ["记路", "纪绿", "记鹿", "继录"],
            "权限": ["全限", "权现", "全现", "权县"],
            "角色": ["角四", "绝色", "脚色", "觉色"],
            "管理员": ["管理圆", "官理员", "管里员", "管丽员"],
            "借书": ["借梳", "借叔", "借熟", "接书"],
            "还书": ["换书", "环书", "缓书", "幻书"],
            "续借": ["序借", "续接", "续解", "虚借"],
            "预约": ["预曰", "予约", "预越", "遇约"],
            "座位": ["做位", "座为", "作位", "座喂"],
            "图书": ["图苏", "图书", "涂书", "图梳"],
            "期刊": ["七刊", "其刊", "气刊", "期看"],
            "论文": ["论稳", "伦文", "轮文", "论闻"],
            "数据库": ["数据裤", "数剧库", "书据库", "数据哭"],
            "电子书": ["电紫书", "电子梳", "电资书", "电子叔"],
            "借阅证": ["借阅正", "借月证", "借约证", "接阅证"],
            "开放时间": ["开放使间", "开访时间", "开房时间", "开放是间"],
        }

    def correct(self, text: str) -> Tuple[str, List[dict]]:
        """纠正文本中的错别字

        Args:
            text: 原始文本

        Returns:
            (纠正后的文本, 纠正详情列表)
        """
        if not text or not text.strip():
            return text, []

        self._init_corrector()

        corrections = []
        corrected_text = text

        # 1. 先用领域词库纠正
        corrected_text, domain_corrections = self._correct_with_domain_dict(text)
        corrections.extend(domain_corrections)

        # 2. 再用 pycorrector 纠正剩余错误
        if self._corrector:
            try:
                pyc_corrected, details = self._corrector.correct(corrected_text)
                if pyc_corrected != corrected_text:
                    corrected_text = pyc_corrected
                    for detail in details:
                        if len(detail) >= 3:
                            corrections.append({
                                "original": detail[0],
                                "corrected": detail[1],
                                "start": detail[1] if len(detail) > 3 else -1,
                                "end": detail[2] if len(detail) > 3 else -1,
                                "source": "pycorrector"
                            })
            except Exception as e:
                print(f"[SpellCorrector] pycorrector 纠错失败: {e}")

        return corrected_text, corrections

    def _correct_with_domain_dict(self, text: str) -> Tuple[str, List[dict]]:
        """使用领域词库进行纠正

        Args:
            text: 原始文本

        Returns:
            (纠正后的文本, 纠正详情列表)
        """
        corrected = text
        corrections = []

        # 遍历领域词库
        for correct_word, wrong_words in self._domain_dict.items():
            for wrong_word in wrong_words:
                if wrong_word in corrected:
                    corrected = corrected.replace(wrong_word, correct_word)
                    corrections.append({
                        "original": wrong_word,
                        "corrected": correct_word,
                        "start": -1,
                        "end": -1,
                        "source": "domain_dict"
                    })

        return corrected, corrections

    def add_domain_word(self, correct_word: str, wrong_words: List[str]):
        """添加领域词汇到词库

        Args:
            correct_word: 正确的词汇
            wrong_words: 常见的错误写法列表
        """
        self._init_corrector()
        self._domain_dict[correct_word] = wrong_words

        # 保存到文件
        dict_path = Path(__file__).parent / "library_dict.json"
        with open(dict_path, "w", encoding="utf-8") as f:
            json.dump(self._domain_dict, f, ensure_ascii=False, indent=2)

        print(f"[SpellCorrector] 添加领域词汇: {correct_word}")

    def get_domain_dict(self) -> dict:
        """获取领域词库

        Returns:
            领域词库字典
        """
        self._init_corrector()
        return self._domain_dict.copy()


# 单例
spell_corrector = SpellCorrector()
