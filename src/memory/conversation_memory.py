from __future__ import annotations

import logging
from collections import deque
from typing import Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

logger = logging.getLogger(__name__)


class ConversationMemory:
    def __init__(
        self,
        *,
        max_turns: int = 10,
        max_token_estimate: int = 4000,
    ):
        self._max_turns = max_turns
        self._max_token_estimate = max_token_estimate
        self._histories: dict[str, deque] = {}

    def add_message(
        self,
        conversation_id: str,
        message: BaseMessage,
    ) -> None:
        if conversation_id not in self._histories:
            self._histories[conversation_id] = deque(maxlen=self._max_turns * 2)

        self._histories[conversation_id].append(message)

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
        history = self._histories.get(conversation_id, deque())
        messages = list(history)

        if max_turns and max_turns * 2 < len(messages):
            messages = messages[-(max_turns * 2):]

        return messages

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

        from src.generation.prompt_templates import CONDENSE_QUESTION_PROMPT

        chain = CONDENSE_QUESTION_PROMPT | llm
        response = chain.invoke({
            "history": history_text,
            "question": new_question,
        })
        return response.content.strip()

    def clear(self, conversation_id: str) -> None:
        if conversation_id in self._histories:
            del self._histories[conversation_id]

    def clear_all(self) -> None:
        self._histories.clear()

    def list_conversations(self) -> list[str]:
        return list(self._histories.keys())

    def conversation_length(self, conversation_id: str) -> int:
        return len(self._histories.get(conversation_id, deque()))