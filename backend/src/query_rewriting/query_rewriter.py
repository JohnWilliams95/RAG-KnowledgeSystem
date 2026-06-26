from __future__ import annotations

import logging
import re
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

INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一个意图分类器。判断用户的问题是否需要从知识库检索信息。\n\n"
        "【需要检索】的情况：\n"
        "- 询问具体事实、定义、流程、数据\n"
        "- 涉及文档、资料、报告的内容\n"
        "- 需要引用来源的专业问题\n"
        "- 技术问题、产品问题、业务问题\n\n"
        "【不需要检索】的情况：\n"
        "- 简单问候、闲聊、寒暄\n"
        "- 情感表达（开心、难过、感谢）\n"
        "- 通用常识问题（LLM自身知识足够）\n"
        "- 创作任务（写诗、写代码）\n"
        "- 系统指令（清空对话、帮助）\n\n"
        "请只回答 \"retrieve\" 或 \"chat\"，不要输出其他内容。"
    )),
    ("human", "用户问题：{question}"),
])

CHAT_PATTERNS = [
    r"^(你好|hello|hi|hey|嗨|哈喽|早上好|下午好|晚上好|早安|晚安)",
    r"^(谢谢|感谢|thanks|thank you|多谢|辛苦了)",
    r"^(再见|bye|拜拜|回头见|下次见)",
    r"^(你是谁|who are you|你叫什么|你的名字)",
    r"^(哈哈|呵呵|嘿嘿|233|666|6|嗯嗯|好的|ok|okay)",
    r"^(在吗|在不在|能听到吗)",
    r"^(天气|今天天气)",
    r"^(帮我写(一首|个)(诗|歌|故事))",
    r"^(讲个笑话|说个笑话)",
]


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

    def classify_intent(self, query: str) -> str:
        """两层意图分类：规则快速过滤 + LLM准确判断"""
        # 第一层：规则快速过滤
        for pattern in CHAT_PATTERNS:
            if re.match(pattern, query.strip(), re.IGNORECASE):
                logger.debug(f"Intent classified as 'chat' by rule: {query}")
                return "chat"

        # 第二层：LLM 分类
        try:
            chain = INTENT_PROMPT | self._llm
            response = chain.invoke({"question": query})
            result = response.content.strip().lower()

            if "chat" in result:
                logger.debug(f"Intent classified as 'chat' by LLM: {query}")
                return "chat"

            logger.debug(f"Intent classified as 'retrieve' by LLM: {query}")
            return "retrieve"
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}, defaulting to retrieve")
            return "retrieve"