#!/usr/bin/env python
"""RAG系统检索效果评估脚本"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# 确保可以导入项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.retrieval_metrics import RetrievalMetrics
from src.api.dependencies import get_ensemble_retriever


def load_test_dataset(filepath: str) -> list[dict]:
    """加载测试数据集"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_evaluation(test_cases: list[dict], top_k: int = 20) -> dict:
    """执行评估"""
    retriever = get_ensemble_retriever()
    metrics = RetrievalMetrics()

    all_retrieved_ids = []
    all_relevant_ids = []
    queries = []
    retrieval_times = []

    print("=" * 60)
    print("开始评估...")
    print("=" * 60)

    for i, case in enumerate(test_cases, 1):
        question = case['question']
        relevant_files = case['relevant_source_files']
        category = case.get('category', '未分类')

        print(f"\n[{i}/{len(test_cases)}] 问题: {question}")
        print(f"  分类: {category}")
        print(f"  相关文档: {relevant_files}")

        # 执行检索并计时
        start_time = time.time()
        docs = retriever.retrieve(question, top_k=top_k, rerank_enabled=False)
        elapsed = time.time() - start_time

        retrieved_files = [doc.metadata.get('source_file', '') for doc in docs]

        print(f"  检索耗时: {elapsed:.2f}s")
        print(f"  检索结果前5: {retrieved_files[:5]}")

        # 检查是否命中
        hit = any(f in relevant_files for f in retrieved_files)
        print(f"  命中: {'YES' if hit else 'NO'}")

        all_retrieved_ids.append(retrieved_files)
        all_relevant_ids.append(relevant_files)
        queries.append(question)
        retrieval_times.append(elapsed)

    # 计算指标
    results = metrics.evaluate(
        queries=queries,
        all_retrieved_ids=all_retrieved_ids,
        all_relevant_ids=all_relevant_ids,
        k_values=[1, 3, 5, 10],
    )

    # 添加统计信息
    results['avg_retrieval_time'] = sum(retrieval_times) / len(retrieval_times)
    results['total_questions'] = len(test_cases)

    return results


def print_results(results: dict):
    """格式化输出评估结果"""
    print("\n" + "=" * 60)
    print("评估结果汇总")
    print("=" * 60)

    print(f"\n总问题数: {results['total_questions']}")
    print(f"平均检索耗时: {results['avg_retrieval_time']:.3f}s")

    print("\n--- 检索质量指标 ---")
    print(f"Hit Rate (命中率):    {results['hit_rate']:.4f}")
    print(f"MRR (平均倒数排名):   {results['mrr']:.4f}")

    print("\n--- 不同Top-K下的指标 ---")
    for k in [1, 3, 5, 10]:
        if f"precision@{k}" in results:
            print(f"\n  Top-{k}:")
            print(f"    Precision@{k}: {results[f'precision@{k}']:.4f}")
            print(f"    Recall@{k}:    {results[f'recall@{k}']:.4f}")
            print(f"    NDCG@{k}:      {results[f'ndcg@{k}']:.4f}")

    print("\n--- 指标解读 ---")
    print("Hit Rate > 0.9: 优秀 | 0.7-0.9: 良好 | < 0.7: 需改进")
    print("MRR > 0.8:      优秀 | 0.5-0.8: 良好 | < 0.5: 需改进")
    print("Recall@5 > 0.8: 优秀 | 0.6-0.8: 良好 | < 0.6: 需改进")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RAG检索效果评估")
    parser.add_argument(
        "--dataset",
        default=str(Path(__file__).parent / "test_dataset.json"),
        help="测试数据集路径"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="检索返回的文档数量"
    )
    parser.add_argument(
        "--output",
        help="结果输出文件路径（JSON格式）"
    )

    args = parser.parse_args()

    # 加载测试数据
    test_cases = load_test_dataset(args.dataset)
    print(f"加载了 {len(test_cases)} 个测试用例")

    # 执行评估
    results = run_evaluation(test_cases, top_k=args.top_k)

    # 输出结果
    print_results(results)

    # 保存结果
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
