from fastapi import UploadFile
from ..config import settings
from uuid import uuid4
from .pdf_converter import convert_txt_to_pdf, convert_docx_to_pdf


async def save_file(file: UploadFile, dir: str = "documents") -> dict:
    original_filename = file.filename or "file"
    ext = "." + original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    file_uuid = uuid4()

    # Save original file
    orig_upload_filename = f"{file_uuid}{ext}"
    orig_file_path = f"{dir}/{orig_upload_filename}"
    orig_file_abs_path = settings.storage_dir.joinpath(orig_file_path)
    orig_file_abs_path.parent.mkdir(parents=True, exist_ok=True)

    with orig_file_abs_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    # Prepare PDF target
    pdf_upload_filename = f"{file_uuid}.pdf"
    pdf_file_path = f"{dir}/{pdf_upload_filename}"
    pdf_file_abs_path = settings.storage_dir.joinpath(pdf_file_path)

    if ext == ".txt":
        convert_txt_to_pdf(orig_file_abs_path, pdf_file_abs_path)
    elif ext == ".docx":
        convert_docx_to_pdf(orig_file_abs_path, pdf_file_abs_path)
    elif ext == ".pdf":
        pdf_file_path = orig_file_path

    return {
        "original_file_path": orig_file_path,
        "pdf_file_path": pdf_file_path,
        "pdf_filename": pdf_upload_filename,
        "original_ext": ext,
        "original_title": original_filename,
    }




