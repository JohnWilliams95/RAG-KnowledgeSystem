from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from src.api.schemas.response import (
    ChatRequest,
    ChatResponse,
)
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

    chain._enable_query_rewriting = request.enable_query_rewriting
    chain._enable_reranking = request.enable_reranking
    chain._enable_hyde = request.enable_hyde
    chain._enable_stepback = request.enable_stepback
    chain._enable_decomposition = request.enable_decomposition

    if request.prompt_style in ("concise", "detailed", "academic"):
        from src.generation.prompt_templates import get_prompt as _get_prompt, PromptStyle as _PS
        chain._prompt = _get_prompt(_PS(request.prompt_style))

    result = chain.invoke(request.question, conversation_id=conversation_id)

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

    async def event_generator():
        for output in chain.stream(request.question, conversation_id=conversation_id):
            yield f"data: {json.dumps(output, ensure_ascii=False, default=str)}\n\n"
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