import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app import storage
from app.llm import llm_service
from app.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(req: ChatRequest):
    thread = storage.get_or_create_thread(req.thread_id)
    thread_id = thread.id

    if req.messages:
        last = req.messages[-1]
        storage.save_message(thread_id, "user", last.content, last.file_ids)

    file_ids = req.messages[-1].file_ids if req.messages else []
    collected: list[str] = []

    async def generate():
        yield f"data: {json.dumps({'type': 'thread_id', 'thread_id': thread_id})}\n\n"

        async for chunk in llm_service.stream(req.messages, file_ids):
            collected.append(chunk)
            yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

        storage.save_message(thread_id, "assistant", "".join(collected))
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
