from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from src.config import settings

logger = logging.getLogger(__name__)


class ConversationMemory:
    def __init__(
        self,
        *,
        max_turns: int = 10,
        max_token_estimate: int = 4000,
        redis_url: Optional[str] = None,
    ):
        self._max_turns = max_turns
        self._max_token_estimate = max_token_estimate
        self._redis_url = redis_url
        self._redis = None
        self._local_histories: dict[str, list[dict]] = {}

    def _get_redis(self):
        if self._redis is not None:
            return self._redis
        if not self._redis_url:
            return None
        try:
            import redis
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
            self._redis.ping()
            logger.info(f"Connected to Redis: {self._redis_url}")
            return self._redis
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to in-memory.")
            return None

    def add_message(
        self,
        conversation_id: str,
        message: BaseMessage,
    ) -> None:
        r = self._get_redis()
        if r:
            self._add_to_redis(r, conversation_id, message)
        else:
            self._add_to_local(conversation_id, message)

    def _add_to_redis(self, r, conversation_id: str, message: BaseMessage) -> None:
        key = f"rag:history:{conversation_id}"
        entry = self._serialize_message(message)
        r.rpush(key, json.dumps(entry, ensure_ascii=False))
        r.ltrim(key, -(self._max_turns * 2), -1)

    def _add_to_local(self, conversation_id: str, message: BaseMessage) -> None:
        if conversation_id not in self._local_histories:
            self._local_histories[conversation_id] = []
        self._local_histories[conversation_id].append(self._serialize_message(message))
        if len(self._local_histories[conversation_id]) > self._max_turns * 2:
            self._local_histories[conversation_id] = self._local_histories[conversation_id][-(self._max_turns * 2):]

    def add_user_message(self, conversation_id: str, content: str) -> None:
        self.add_message(conversation_id, HumanMessage(content=content))

    def add_ai_message(self, conversation_id: str, content: str) -> None:
        self.add_message(conversation_id, AIMessage(content=content))

    def get_history(
        self,
        conversation_id: str,
        *,
        max_turns: Optional[int] = None,
    ) -> list[BaseMessage]:
        r = self._get_redis()
        if r:
            return self._get_from_redis(r, conversation_id, max_turns)
        return self._get_from_local(conversation_id, max_turns)

    def _get_from_redis(self, r, conversation_id: str, max_turns: Optional[int]) -> list[BaseMessage]:
        key = f"rag:history:{conversation_id}"
        limit = (max_turns or self._max_turns) * 2
        entries = r.lrange(key, -limit, -1)
        return [self._deserialize_message(json.loads(e)) for e in entries]

    def _get_from_local(self, conversation_id: str, max_turns: Optional[int]) -> list[BaseMessage]:
        entries = self._local_histories.get(conversation_id, [])
        limit = (max_turns or self._max_turns) * 2
        if len(entries) > limit:
            entries = entries[-limit:]
        return [self._deserialize_message(e) for e in entries]

    def get_history_text(
        self,
        conversation_id: str,
        *,
        max_turns: Optional[int] = None,
    ) -> str:
        messages = self.get_history(conversation_id, max_turns=max_turns)
        parts = []
        for msg in messages:
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            parts.append(f"{role}: {msg.content}")
        return "\n".join(parts)

    def condense_question(
        self,
        conversation_id: str,
        new_question: str,
        llm,
    ) -> str:
        history_text = self.get_history_text(conversation_id, max_turns=5)
        if not history_text.strip():
            return new_question

        from backend.src.generation.prompt_templates import CONDENSE_QUESTION_PROMPT

        chain = CONDENSE_QUESTION_PROMPT | llm
        response = chain.invoke({
            "history": history_text,
            "question": new_question,
        })
        return response.content.strip()

    def clear(self, conversation_id: str) -> None:
        r = self._get_redis()
        if r:
            r.delete(f"rag:history:{conversation_id}")
        else:
            self._local_histories.pop(conversation_id, None)

    def clear_all(self) -> None:
        r = self._get_redis()
        if r:
            for key in r.scan_iter("rag:history:*"):
                r.delete(key)
        self._local_histories.clear()

    def list_conversations(self) -> list[str]:
        r = self._get_redis()
        if r:
            return [k.replace("rag:history:", "") for k in r.scan_iter("rag:history:*")]
        return list(self._local_histories.keys())

    def conversation_length(self, conversation_id: str) -> int:
        r = self._get_redis()
        if r:
            return r.llen(f"rag:history:{conversation_id}")
        return len(self._local_histories.get(conversation_id, []))

    @staticmethod
    def _serialize_message(message: BaseMessage) -> dict:
        if isinstance(message, HumanMessage):
            return {"role": "human", "content": message.content}
        elif isinstance(message, AIMessage):
            return {"role": "ai", "content": message.content}
        return {"role": "unknown", "content": str(message.content)}

    @staticmethod
    def _deserialize_message(data: dict) -> BaseMessage:
        role = data.get("role", "unknown")
        content = data.get("content", "")
        if role == "human":
            return HumanMessage(content=content)
        elif role == "ai":
            return AIMessage(content=content)
        return HumanMessage(content=content)