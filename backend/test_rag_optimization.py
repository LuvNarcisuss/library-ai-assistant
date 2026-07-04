# -*- coding: utf-8 -*-
"""RAG 优化测试脚本

用于验证优化后的 RAG 服务功能。
"""
import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_embedding_service():
    """测试 Embedding 服务优化"""
    print("\n" + "="*60)
    print("测试 Embedding 服务")
    print("="*60)

    try:
        from app.services.embedding_service import embedding_service

        # 测试查询向量生成
        query = "图书馆开放时间"
        print(f"\n测试查询: {query}")

        # 生成查询向量
        query_vector = embedding_service.embed_query(query)
        print(f"✓ 查询向量生成成功，维度: {len(query_vector)}")

        # 检查向量是否归一化
        import numpy as np
        norm = np.linalg.norm(query_vector)
        print(f"✓ 向量范数: {norm:.6f} (归一化后应接近1.0)")

        # 测试批量编码
        texts = ["图书馆借阅规则", "数据库使用指南", "论文写作指导"]
        text_vectors = embedding_service.embed_texts(texts)
        print(f"✓ 批量编码成功，生成 {len(text_vectors)} 个向量")

        # 获取向量维度
        dim = embedding_service.get_embedding_dim()
        print(f"✓ 向量维度: {dim}")

        return True

    except Exception as e:
        print(f"✗ Embedding 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_service():
    """测试 LLM 服务优化"""
    print("\n" + "="*60)
    print("测试 LLM 服务")
    print("="*60)

    try:
        from app.services.llm_service import llm_service

        # 测试简单生成
        prompt = "请用一句话介绍图书馆的作用。"
        print(f"\n测试 Prompt: {prompt}")

        answer = llm_service.generate(prompt)
        print(f"✓ LLM 生成成功")
        print(f"  回答: {answer[:100]}...")

        # 获取统计信息
        stats = llm_service.get_stats()
        print(f"✓ 统计信息: 调用次数={stats['call_count']}, 总Token={stats['total_tokens']}")

        return True

    except ValueError as e:
        print(f"⚠ LLM 未配置: {e}")
        print("  请在 .env 文件中配置 LLM_API_KEY")
        return False

    except Exception as e:
        print(f"✗ LLM 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_service():
    """测试 RAG 服务优化"""
    print("\n" + "="*60)
    print("测试 RAG 服务")
    print("="*60)

    try:
        from app.services.rag_service import rag_service

        # 测试检索（假设有一个测试知识库）
        test_collection = "test_kb"
        test_query = "图书馆开放时间"

        print(f"\n测试检索: 集合={test_collection}, 查询={test_query}")

        # 尝试检索
        results = rag_service.retrieve(test_collection, test_query)
        print(f"✓ 检索完成，返回 {len(results)} 条结果")

        # 测试答案生成
        if results:
            print("\n测试答案生成...")
            answer_result = rag_service.generate_answer(
                query=test_query,
                retrieved_docs=results,
                history=[
                    {"question": "你好", "answer": "你好！我是小江，图书馆智能助手。"}
                ]
            )

            print(f"✓ 答案生成成功")
            print(f"  回答: {answer_result['answer'][:150]}...")
            print(f"  来源数: {len(answer_result['sources'])}")
            print(f"  有上下文: {answer_result['has_context']}")
        else:
            print("⚠ 未找到检索结果，跳过答案生成测试")

        return True

    except Exception as e:
        print(f"✗ RAG 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("RAG 优化功能测试")
    print("="*60)

    results = {}

    # 测试各个服务
    results['embedding'] = test_embedding_service()
    results['llm'] = test_llm_service()
    results['rag'] = test_rag_service()

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for service, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {service:12} {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n总计: {passed}/{total} 通过")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
