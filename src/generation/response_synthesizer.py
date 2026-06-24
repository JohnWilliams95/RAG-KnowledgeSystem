from __future__ import annotations

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from src.generation.prompt_templates import SUMMARIZE_CONTEXT_PROMPT

logger = logging.getLogger(__name__)


class ResponseSynthesizer:
    def __init__(
        self,
        llm: BaseChatModel,
        *,
        mode: str = "compact",
        max_refine_iterations: int = 3,
    ):
        self._llm = llm
        self._mode = mode
        self._max_refine_iterations = max_refine_iterations

    def synthesize(
        self,
        query: str,
        context: str,
        *,
        prompt: Optional[ChatPromptTemplate] = None,
        history: Optional[list] = None,
    ) -> str:
        if self._mode == "refine":
            return self._refine_mode(query, context, prompt, history)
        elif self._mode == "tree_summarize":
            return self._tree_summarize_mode(query, context, prompt, history)
        else:
            return self._compact_mode(query, context, prompt, history)

    def _compact_mode(
        self,
        query: str,
        context: str,
        prompt: Optional[ChatPromptTemplate],
        history: Optional[list],
    ) -> str:
        if len(context) > 6000:
            context = self._summarize_context(query, context)

        chain_kwargs = {"context": context, "question": query}
        if history:
            chain_kwargs["history"] = history

        p = prompt or self._get_default_prompt()
        chain = p | self._llm
        response = chain.invoke(chain_kwargs)
        return response.content

    def _refine_mode(
        self,
        query: str,
        context: str,
        prompt: Optional[ChatPromptTemplate],
        history: Optional[list],
    ) -> str:
        chunks = self._split_context(context, chunk_size=3000)
        if not chunks:
            return ""

        current_answer = self._generate_initial(query, chunks[0], prompt, history)

        refine_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "你是一个专业的答案优化助手。以下是一个已有的答案和一些新的参考资料。\n"
                "请基于新资料优化现有答案，使其更准确、更完整。\n\n"
                "现有答案：\n{existing_answer}\n\n"
                "新参考资料：\n{new_context}\n\n"
                "问题：{question}\n\n"
                "优化后的答案："
            )),
            ("human", ""),
        ])

        for i, chunk in enumerate(chunks[1:], start=1):
            if i >= self._max_refine_iterations:
                break
            chain = refine_prompt | self._llm
            response = chain.invoke({
                "existing_answer": current_answer,
                "new_context": chunk,
                "question": query,
            })
            current_answer = response.content

        return current_answer

    def _tree_summarize_mode(
        self,
        query: str,
        context: str,
        prompt: Optional[ChatPromptTemplate],
        history: Optional[list],
    ) -> str:
        chunks = self._split_context(context, chunk_size=3000)

        if len(chunks) <= 1:
            return self._compact_mode(query, context, prompt, history)

        summaries: list[str] = []
        for chunk in chunks:
            p = prompt or self._get_default_prompt()
            chain = p | self._llm
            response = chain.invoke({"context": chunk, "question": query})
            summaries.append(response.content)

        merged = "\n\n".join(summaries)
        p = prompt or self._get_default_prompt()
        chain = p | self._llm
        response = chain.invoke({"context": merged, "question": query})
        return response.content

    def _generate_initial(
        self,
        query: str,
        context: str,
        prompt: Optional[ChatPromptTemplate],
        history: Optional[list],
    ) -> str:
        p = prompt or self._get_default_prompt()
        chain = p | self._llm
        response = chain.invoke({"context": context, "question": query})
        return response.content

    def _summarize_context(self, query: str, context: str) -> str:
        chain = SUMMARIZE_CONTEXT_PROMPT | self._llm
        response = chain.invoke({"question": query, "context": context})
        return response.content

    def _split_context(self, context: str, chunk_size: int = 3000) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(context):
            end = start + chunk_size
            if end < len(context):
                last_newline = context.rfind("\n", start, end)
                if last_newline > start:
                    end = last_newline
            chunks.append(context[start:end])
            start = end
        return chunks

    def _get_default_prompt(self):
        from src.generation.prompt_templates import RAG_QA_PROMPT
        return RAG_QA_PROMPT