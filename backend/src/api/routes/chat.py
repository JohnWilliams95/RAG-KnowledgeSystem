from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from src.api.schemas.request import ChatRequest
from src.api.schemas.response import ChatResponse
from src.generation.rag_chain import RAGChain
from src.generation.prompt_templates import PromptStyle
from src.middleware.guardrails import Guardrails

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_rag_chain: Optional[RAGChain] = None
_guardrails: Optional[Guardrails] = None


def get_rag_chain() -> RAGChain:
    global _rag_chain
    if _rag_chain is None:
        from src.api.dependencies import get_llm, get_ensemble_retriever
        llm = get_llm()
        retriever = get_ensemble_retriever()
        _rag_chain = RAGChain(llm=llm, retriever=retriever)
    return _rag_chain


def get_guardrails() -> Guardrails:
    global _guardrails
    if _guardrails is None:
        _guardrails = Guardrails(
            check_prompt_injection=True,
            check_sensitive_info=True,
            check_pii=False,
        )
    return _guardrails


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chain: RAGChain = Depends(get_rag_chain),
    guardrails: Guardrails = Depends(get_guardrails),
):
    is_valid, reason = guardrails.validate_input(request.question)
    if not is_valid:
        return ChatResponse(
            question=request.question,
            answer=f"输入验证失败: {reason}",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
        )

    conversation_id = request.conversation_id or str(uuid.uuid4())

    prompt = None
    if request.prompt_style in ("concise", "detailed", "academic"):
        from src.generation.prompt_templates import get_prompt as _get_prompt, PromptStyle as _PS
        prompt = _get_prompt(_PS(request.prompt_style))

    chain_config = {
        "enable_query_rewriting": request.enable_query_rewriting,
        "enable_reranking": request.enable_reranking,
        "enable_hyde": request.enable_hyde,
        "enable_stepback": request.enable_stepback,
        "enable_decomposition": request.enable_decomposition,
        "prompt": prompt,
    }

    result = chain.invoke(
        request.question,
        conversation_id=conversation_id,
        chain_config=chain_config,
    )

    return ChatResponse(
        question=request.question,
        answer=result.get("answer", ""),
        conversation_id=conversation_id,
        rewritten_queries=result.get("rewritten_queries", []),
        num_documents=result.get("num_documents", 0),
        context_length=result.get("context_length", 0),
        metadata=result.get("metadata", {}),
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chain: RAGChain = Depends(get_rag_chain),
):
    from fastapi.responses import StreamingResponse
    import json

    conversation_id = request.conversation_id or str(uuid.uuid4())
    logger.info(f"[Stream] Question: {request.question[:50]}...")

    def format_sse(event_type: str, data: str) -> str:
        """格式化 SSE 事件"""
        payload = json.dumps(
            {"event_type": event_type, "data": data},
            ensure_ascii=False,
        )
        return f"data: {payload}\n\n"

    async def event_generator():
        try:
            for output in chain.stream(request.question, conversation_id=conversation_id):
                # 处理意图分类事件
                if "classify_intent" in output:
                    intent = output["classify_intent"].get("intent", "")
                    logger.info(f"[Stream] Intent: {intent}")
                    yield format_sse("intent", intent)

                # 处理查询重写事件
                elif "rewrite_query" in output:
                    queries = output["rewrite_query"].get("rewritten_queries", [])
                    yield format_sse("rewritten_queries", json.dumps(queries, ensure_ascii=False))

                # 处理检索事件
                elif "retrieve" in output:
                    docs = output["retrieve"].get("documents", [])
                    yield format_sse("documents", str(len(docs)))

                # 处理生成事件
                elif "generate" in output:
                    answer = output["generate"].get("answer", "")
                    logger.info(f"[Stream] Generated {len(answer)} chars")
                    # 逐字符流式输出，模拟打字效果
                    for char in answer:
                        yield format_sse("token", char)

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"[Stream] Error: {e}", exc_info=True)
            yield format_sse("error", str(e))
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Conversation-ID": conversation_id},
    )


@router.delete("/history/{conversation_id}")
async def clear_history(conversation_id: str):
    from src.api.dependencies import get_memory
    memory = get_memory()
    memory.clear(conversation_id)
    return {"status": "success", "message": f"History for {conversation_id} cleared"}