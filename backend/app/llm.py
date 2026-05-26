import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator, List

from app.schemas import ChatMessage


class BaseLLMService(ABC):
    @abstractmethod
    async def stream(
        self, messages: List[ChatMessage], file_ids: List[str] = []
    ) -> AsyncIterator[str]:
        pass


class DummyLLMService(BaseLLMService):
    """Foundry接続待ちのダミー実装。最後のユーザー発言をオウム返しする。"""

    async def stream(
        self, messages: List[ChatMessage], file_ids: List[str] = []
    ) -> AsyncIterator[str]:
        last_user = next(
            (m for m in reversed(messages) if m.role == "user"), None
        )
        if not last_user:
            return

        file_note = f"（添付 {len(file_ids)} 件）" if file_ids else ""
        response = f"[Echo{file_note}] {last_user.content}"

        for char in response:
            yield char
            await asyncio.sleep(0.02)


# TODO: Foundry接続時はここを差し替える
# class FoundryLLMService(BaseLLMService):
#     def __init__(self, endpoint: str, agent_id: str): ...
#     async def stream(self, messages, file_ids=[]) -> AsyncIterator[str]: ...

llm_service: BaseLLMService = DummyLLMService()
