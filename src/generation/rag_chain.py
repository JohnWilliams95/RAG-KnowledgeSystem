from __future__ import annotations

import logging
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from typing import TypedDict

from src.config import settings
from src.generation.context_builder import ContextBuilder
from src.generation.prompt_templates import PromptStyle, get_prompt
from src.generation.response_synthesizer import ResponseSynthesizer
from src.query_rewriting.hyde_generator import HyDEGenerator
from src.query_rewriting.query_decomposer import QueryDecomposer
from src.query_rewriting.query_rewriter import QueryRewriter
from src.query_rewriting.stepback_prompt import StepBackPrompting
from src.retrieval.ensemble_retriever import EnsembleRetriever
from src.memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class RAGState(TypedDict, total=False):
    query: str
    rewritten_queries: list[str]
    documents: list
    context: str
    answer: str
    history: list
    metadata: dict


class RAGChain:
    def __init__(
        self,
        llm: BaseChatModel,
        retriever: EnsembleRetriever,
        *,
        memory: Optional[ConversationMemory] = None,
        query_rewriter: Optional[QueryRewriter] = None,
        query_decomposer: Optional[QueryDecomposer] = None,
        hyde_generator: Optional[HyDEGenerator] = None,
        stepback: Optional[StepBackPrompting] = None,
        prompt_style: PromptStyle = PromptStyle.DETAILED,
        synthesis_mode: str = "compact",
        enable_query_rewriting: bool = True,
        enable_hyde: bool = True,
        enable_stepback: bool = True,
        enable_decomposition: bool = True,
        enable_reranking: bool = True,
        max_context_length: int = 8000,
    ):
        self._llm = llm
        self._retriever = retriever
        self._memory = memory or ConversationMemory()
        self._context_builder = ContextBuilder(max_context_length=max_context_length)
        self._synthesizer = ResponseSynthesizer(llm, mode=synthesis_mode)
        self._prompt = get_prompt(prompt_style)

        self._query_rewriter = query_rewriter or QueryRewriter(llm)
        self._query_decomposer = query_decomposer or QueryDecomposer(llm)
        self._hyde_generator = hyde_generator or HyDEGenerator(llm)
        self._stepback = stepback or StepBackPrompting(llm)

        self._enable_query_rewriting = enable_query_rewriting
        self._enable_hyde = enable_hyde
        self._enable_stepback = enable_stepback
        self._enable_decomposition = enable_decomposition
        self._enable_reranking = enable_reranking

        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(RAGState)

        graph.add_node("rewrite_query", self._rewrite_query_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("build_context", self._build_context_node)
        graph.add_node("generate", self._generate_node)

        graph.set_entry_point("rewrite_query")
        graph.add_edge("rewrite_query", "retrieve")
        graph.add_edge("retrieve", "build_context")
        graph.add_edge("build_context", "generate")
        graph.add_edge("generate", END)

        return graph.compile()

    def invoke(
        self,
        query: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> dict:
        history = self._memory.get_history(conversation_id or "default")
        state = RAGState(
            query=query,
            history=[m for m in history] if history else [],
            metadata={},
        )

        result = self._graph.invoke(state)

        if conversation_id:
            self._memory.add_message(conversation_id, HumanMessage(content=query))
            self._memory.add_message(conversation_id, AIMessage(content=result.get("answer", "")))

        return {
            "query": query,
            "answer": result.get("answer", ""),
            "rewritten_queries": result.get("rewritten_queries", []),
            "num_documents": len(result.get("documents", [])),
            "context_length": len(result.get("context", "")),
            "metadata": result.get("metadata", {}),
        }

    def stream(self, query: str, *, conversation_id: Optional[str] = None):
        conv_id = conversation_id or "default"
        history = self._memory.get_history(conv_id)
        state = RAGState(
            query=query,
            history=[m for m in history] if history else [],
            metadata={},
        )

        full_answer = ""
        for output in self._graph.stream(state):
            if "generate" in output:
                full_answer = output["generate"].get("answer", "")
            yield output

        if full_answer:
            self._memory.add_message(conv_id, HumanMessage(content=query))
            self._memory.add_message(conv_id, AIMessage(content=full_answer))

    def _rewrite_query_node(self, state: RAGState) -> dict:
        query = state["query"]
        all_queries: list[str] = [query]
        meta: dict = {"original_query": query}

        if self._enable_query_rewriting:
            rewrites = self._query_rewriter.rewrite(query)
            all_queries.extend(rewrites[1:])
            meta["rewrites"] = rewrites[1:]

        if self._enable_decomposition and len(query) > 50:
            sub_queries = self._query_decomposer.decompose(query)
            if sub_queries != [query]:
                all_queries.extend(sub_queries)
                meta["sub_queries"] = sub_queries

        if self._enable_hyde:
            hyde_doc = self._hyde_generator.generate(query)
            all_queries.append(hyde_doc)
            meta["hyde_document"] = hyde_doc

        if self._enable_stepback:
            stepback_queries = self._stepback.generate(query)
            all_queries.extend(stepback_queries)
            meta["stepback_queries"] = stepback_queries

        return {"rewritten_queries": all_queries, "metadata": meta}

    def _retrieve_node(self, state: RAGState) -> dict:
        queries = state.get("rewritten_queries", [state["query"]])
        all_documents = []

        seen_ids: set[str] = set()
        for q in queries:
            docs = self._retriever.retrieve(
                q,
                rerank_enabled=self._enable_reranking,
            )
            for doc in docs:
                doc_id = doc.metadata.get("_id", doc.page_content[:100])
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_documents.append(doc)

        return {"documents": all_documents}

    def _build_context_node(self, state: RAGState) -> dict:
        documents = state.get("documents", [])
        context = self._context_builder.build(documents, query=state["query"])
        return {"context": context}

    def _generate_node(self, state: RAGState) -> dict:
        context = state.get("context", "")
        query = state["query"]
        history = state.get("history", [])

        answer = self._synthesizer.synthesize(
            query=query,
            context=context,
            prompt=self._prompt,
            history=history if history else None,
        )

        return {"answer": answer}