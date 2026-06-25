from __future__ import annotations

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一个专业的查询改写助手。你的任务是将用户的查询改写为"
        "更适合信息检索的形式。\n\n"
        "改写规则：\n"
        "1. 展开缩写和代词，使指代明确\n"
        "2. 补充必要的上下文信息\n"
        "3. 将口语化表达转为更正式的检索用语\n"
        "4. 保留原始查询的核心意图\n"
        "5. 输出多个不同角度的改写版本，每行一个\n"
        "6. 至少生成3个改写版本，最多5个"
    )),
    ("human", "原始查询：{query}\n\n请输出改写后的查询版本："),
])


class QueryRewriter:
    def __init__(
        self,
        llm: BaseChatModel,
        *,
        max_rewrites: int = 5,
    ):
        self._llm = llm
        self._max_rewrites = max_rewrites

    def rewrite(self, query: str) -> list[str]:
        chain = REWRITE_PROMPT | self._llm
        response = chain.invoke({"query": query})

        content = response.content.strip()
        rewrites = [line.strip() for line in content.split("\n") if line.strip()]

        if not rewrites:
            return [query]

        all_queries = [query] + rewrites[: self._max_rewrites]
        seen = set()
        unique = []
        for q in all_queries:
            if q not in seen:
                seen.add(q)
                unique.append(q)

        return unique