from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

STEPBACK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "你是一个专业的问题抽象助手。你的任务是将具体的用户问题"
        "回推到一个更广泛、更抽象的背景问题。\n\n"
        "回推规则：\n"
        "1. 从具体问题中识别核心概念\n"
        "2. 将概念提升到更一般的层次\n"
        "3. 生成一个或多个背景问题，这些问题的答案有助于回答原始问题\n"
        "4. 背景问题应该更宽泛，能覆盖原始问题的知识域\n"
        "5. 每行输出一个背景问题\n\n"
        "示例：\n"
        "原始问题：Python的列表推导式怎么用？\n"
        "背景问题：Python中可迭代对象的操作方式有哪些？"
    )),
    ("human", "原始问题：{query}\n\n请生成背景问题："),
])


class StepBackPrompting:
    def __init__(self, llm: BaseChatModel, *, max_steps: int = 3):
        self._llm = llm
        self._max_steps = max_steps

    def generate(self, query: str) -> list[str]:
        chain = STEPBACK_PROMPT | self._llm
        response = chain.invoke({"query": query})

        content = response.content.strip()
        stepback_queries = [line.strip() for line in content.split("\n") if line.strip()]

        return stepback_queries[: self._max_steps]