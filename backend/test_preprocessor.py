# -*- coding: utf-8 -*-
"""智能预处理模块测试脚本

测试语义纠错、意图识别、问题重写三个功能。
"""
import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_spell_correction():
    """测试语义纠错"""
    print("\n" + "=" * 60)
    print("测试语义纠错")
    print("=" * 60)

    try:
        from app.services.preprocessor.spell_correction import spell_corrector

        test_cases = [
            ("图收馆开放时间", "图书馆开放时间"),
            ("葡淘的营养成分", "葡萄的营养成分"),
            ("借月规则说明", "借阅规则说明"),
            ("知识裤管理", "知识库管理"),
            ("数据裤查询", "数据库查询"),
            ("文挡上传", "文档上传"),
            ("检索功能介绍", "检索功能介绍"),  # 正确的不需要修改
        ]

        passed = 0
        failed = 0

        for original, expected in test_cases:
            corrected, details = spell_corrector.correct(original)
            # 检查是否包含预期的正确词汇
            if expected in corrected:
                print(f"✓ '{original}' -> '{corrected}'")
                passed += 1
            else:
                print(f"✗ '{original}' -> '{corrected}' (期望包含 '{expected}')")
                failed += 1

        print(f"\n语义纠错测试: {passed}/{passed + failed} 通过")
        return failed == 0

    except Exception as e:
        print(f"✗ 语义纠错测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intent_recognition():
    """测试意图识别"""
    print("\n" + "=" * 60)
    print("测试意图识别")
    print("=" * 60)

    try:
        from app.services.preprocessor.intent_recognition import intent_recognizer

        test_cases = [
            ("你好", "greeting"),
            ("早上好", "greeting"),
            ("你是谁", "greeting"),
            ("上传文档", "doc_manage"),
            ("删除文件", "doc_manage"),
            ("文档管理", "doc_manage"),
            ("创建知识库", "kb_manage"),
            ("知识库管理", "kb_manage"),
            ("怎么使用", "system_help"),
            ("帮助", "system_help"),
            ("功能介绍", "system_help"),
            ("图书馆开放时间", "query"),
            ("借阅规则", "query"),
            ("Python教程", "query"),
        ]

        passed = 0
        failed = 0

        for text, expected_intent in test_cases:
            intent, confidence = intent_recognizer.recognize(text)
            if intent == expected_intent:
                print(f"✓ '{text}' -> {intent} ({confidence:.2f})")
                passed += 1
            else:
                print(f"✗ '{text}' -> {intent} (期望: {expected_intent})")
                failed += 1

        print(f"\n意图识别测试: {passed}/{passed + failed} 通过")
        return failed == 0

    except Exception as e:
        print(f"✗ 意图识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_rewrite():
    """测试问题重写"""
    print("\n" + "=" * 60)
    print("测试问题重写")
    print("=" * 60)

    try:
        from app.services.preprocessor.query_rewrite import query_rewriter

        # 测试是否需要重写
        test_cases_need_rewrite = [
            ("葡萄", True),  # 过短
            ("咋借书", True),  # 口语化
            ("Python", True),  # 过短
            ("图书馆开放时间是什么", False),  # 已经清晰
            ("如何借阅图书", False),  # 已经清晰
        ]

        print("\n--- 重写判断测试 ---")
        passed = 0
        failed = 0

        for query, expected in test_cases_need_rewrite:
            result = query_rewriter.need_rewrite(query)
            if result == expected:
                print(f"✓ '{query}' -> need_rewrite={result}")
                passed += 1
            else:
                print(f"✗ '{query}' -> need_rewrite={result} (期望: {expected})")
                failed += 1

        print(f"\n重写判断测试: {passed}/{passed + failed} 通过")

        # 测试问题重写（需要 LLM）
        print("\n--- 问题重写测试（需要 LLM 配置）---")
        test_rewrite_cases = [
            "葡萄怎么样",
            "咋借书",
            "Python",
        ]

        for query in test_rewrite_cases:
            try:
                rewritten = query_rewriter.rewrite(query)
                print(f"✓ '{query}' -> '{rewritten}'")
            except Exception as e:
                print(f"⚠ '{query}' 重写失败: {e}")

        return failed == 0

    except Exception as e:
        print(f"✗ 问题重写测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preprocessor():
    """测试完整预处理流程"""
    print("\n" + "=" * 60)
    print("测试完整预处理流程")
    print("=" * 60)

    try:
        from app.services.preprocessor import preprocessor

        test_cases = [
            "图收馆开放时间",
            "你好",
            "上传文档",
            "咋借书",
            "知识裤怎么用",
        ]

        for query in test_cases:
            result = preprocessor.process(query)
            print(f"\n原始问题: '{query}'")
            print(f"  纠错后: '{result['corrected_query']}'")
            print(f"  意图: {result['intent']} ({result['intent_confidence']:.2f})")
            print(f"  最终问题: '{result['final_query']}'")
            if result['corrections']:
                print(f"  纠错详情: {result['corrections']}")

        return True

    except Exception as e:
        print(f"✗ 完整预处理流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("智能预处理模块测试")
    print("=" * 60)

    results = {}

    # 测试各个模块
    results['语义纠错'] = test_spell_correction()
    results['意图识别'] = test_intent_recognition()
    results['问题重写'] = test_query_rewrite()
    results['完整流程'] = test_preprocessor()

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name:12} {status}")

    total = len(results)
    passed_count = sum(1 for v in results.values() if v)
    print(f"\n总计: {passed_count}/{total} 通过")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
