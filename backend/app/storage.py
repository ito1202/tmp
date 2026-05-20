from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid


@dataclass
class StoredMessage:
    id: str
    role: str
    content: str
    file_ids: List[str]
    created_at: datetime


@dataclass
class StoredThread:
    id: str
    title: str
    messages: List[StoredMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


threads: Dict[str, StoredThread] = {}
files: Dict[str, dict] = {}


def get_or_create_thread(thread_id: Optional[str]) -> StoredThread:
    if thread_id and thread_id in threads:
        return threads[thread_id]
    t = StoredThread(id=thread_id or str(uuid.uuid4()), title="新しい会話")
    threads[t.id] = t
    return t


def save_message(
    thread_id: str, role: str, content: str, file_ids: List[str] = []
) -> StoredMessage:
    msg = StoredMessage(
        id=str(uuid.uuid4()),
        role=role,
        content=content,
        file_ids=file_ids,
        created_at=datetime.now(),
    )
    t = threads[thread_id]
    t.messages.append(msg)
    t.updated_at = datetime.now()
    if t.title == "新しい会話" and role == "user" and content:
        t.title = content[:30] + ("…" if len(content) > 30 else "")
    return msg
