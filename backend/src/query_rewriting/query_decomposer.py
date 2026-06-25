from __future__ import annotations

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

QUERY_DECOMPOSITION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一个专业的问题分解助手。用户可能会提出复杂的问题，"
        "你的任务是将复杂问题分解为多个简单的子问题。"
        "每个子问题应该独立可回答，且解决所有子问题后能够回答原始问题。\n\n"
        "规则：\n"
        "1. 如果问题本身足够简单，不需要分解，直接返回原问题\n"
        "2. 每行输出一个子问题\n"
        "3. 不要添加编号或额外标记\n"
        "4. 保持子问题的准确性，不要偏离原意"
    )),
    ("human", "原始问题：{query}"),
])


class QueryDecomposer:
    def __init__(
        self,
        llm: BaseChatModel,
        *,
        max_sub_queries: int = 4,
    ):
        self._llm = llm
        self._max_sub_queries = max_sub_queries

    def decompose(self, query: str) -> list[str]:
        chain = QUERY_DECOMPOSITION_PROMPT | self._llm
        response = chain.invoke({"query": query})

        content = response.content.strip()
        sub_queries = [line.strip() for line in content.split("\n") if line.strip()]

        if not sub_queries:
            return [query]

        sub_queries = sub_queries[: self._max_sub_queries]

        if len(sub_queries) == 1 and self._is_similar(sub_queries[0], query):
            return [query]

        return sub_queries

    def _is_similar(self, a: str, b: str) -> bool:
        return a.strip().rstrip("。.？?！!") == b.strip().rstrip("。.？?！!")