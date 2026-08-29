from fastapi import UploadFile
from ..config import settings
from uuid import uuid4

async def save_file(file: UploadFile, dir: str = "tmp"):

    filename = file.filename or "file"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    upload_filename = f"{uuid4()}{ext}"
    upload_file_path = f"{dir}/{upload_filename}"
    upload_file_abs_path = settings.storage_dir.joinpath(upload_file_path)
    upload_file_abs_path.parent.mkdir(parents=True, exist_ok=True)

    with upload_file_abs_path.open("wb") as buffer:
           while chunk := await file.read(1024 * 1024):
                 buffer.write( chunk )
    return upload_file_path




