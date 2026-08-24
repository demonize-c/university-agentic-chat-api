
from pypdf import PdfReader
from docx import Document
from fastapi import UploadFile
from io import BytesIO

async def extract_file(file: UploadFile ) -> str:

    content = await file.read()
    text = ""

    if not content:
        raise ValueError("Uploaded file is empty")
    
    if file.content_type == "text/plain":
        text = content.decode("utf-8")

    elif file.content_type == "application/pdf":
        reader = PdfReader(BytesIO(content))

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    elif file.content_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        doc = Document(BytesIO(content))

        text = "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
        )
    else:
        raise ValueError(f"Unsupported file type: {file.filename}. Use .txt, .pdf, or .docx")
    
    return text