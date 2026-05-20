from fastapi import APIRouter, HTTPException

from app import storage
from app.schemas import MessageResponse, ThreadSummary

router = APIRouter(prefix="/api", tags=["threads"])


@router.get("/threads", response_model=list[ThreadSummary])
async def list_threads():
    return [
        ThreadSummary(
            id=t.id,
            title=t.title,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in sorted(
            storage.threads.values(), key=lambda x: x.updated_at, reverse=True
        )
    ]


@router.get("/threads/{thread_id}/messages", response_model=list[MessageResponse])
async def get_messages(thread_id: str):
    t = storage.threads.get(thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            file_ids=m.file_ids,
            created_at=m.created_at,
        )
        for m in t.messages
    ]


@router.delete("/threads/{thread_id}", status_code=204)
async def delete_thread(thread_id: str):
    if thread_id not in storage.threads:
        raise HTTPException(404, "Thread not found")
    del storage.threads[thread_id]
