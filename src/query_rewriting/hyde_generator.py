from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

HYDE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一个专业的文档生成助手。用户会提出一个问题，"
        "你需要生成一段假设性文档来回答这个问题。\n\n"
        "规则：\n"
        "1. 生成的文档应该看起来像真实的、权威的参考资料\n"
        "2. 包含具体的技术细节和事实\n"
        "3. 长度在200-500字左右\n"
        "4. 使用专业、正式的语气\n"
        "5. 即使不确定，也要以确定性的方式编写"
    )),
    ("human", "问题：{query}\n\n请生成一段假设性文档来回答此问题："),
])


class HyDEGenerator:
    def __init__(self, llm: BaseChatModel):
        self._llm = llm

    def generate(self, query: str) -> str:
        chain = HYDE_PROMPT | self._llm
        response = chain.invoke({"query": query})
        return response.content.strip()

    def generate_batch(self, queries: list[str]) -> list[str]:
        return [self.generate(q) for q in queries]