from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str
    content: str
    file_ids: List[str] = []


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    thread_id: Optional[str] = None


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    content_type: str


class ThreadSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    file_ids: List[str]
    created_at: datetime
