import uuid

from fastapi import APIRouter, File, UploadFile

from app import storage
from app.schemas import UploadResponse

router = APIRouter(prefix="/api", tags=["files"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    content = await file.read()
    storage.files[file_id] = {
        "filename": file.filename,
        "content_type": file.content_type,
        "content": content,
    }
    return UploadResponse(
        file_id=file_id,
        filename=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
    )
