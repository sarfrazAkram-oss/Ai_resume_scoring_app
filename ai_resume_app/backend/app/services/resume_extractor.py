from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


class ResumeExtractionError(ValueError):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def extract_resume_text(file_name: str, file_bytes: bytes) -> tuple[str, str]:
    extension = Path(file_name).suffix.lower()
    if extension == ".doc":
        raise ResumeExtractionError(
            "Legacy .doc files are not supported; upload a PDF or DOCX file.",
            415,
        )
    if extension not in {".pdf", ".docx"}:
        raise ResumeExtractionError(
            "Unsupported file type; upload a PDF or DOCX file.",
            415,
        )
    if not file_bytes:
        raise ResumeExtractionError("The uploaded file is empty.", 400)

    try:
        if extension == ".pdf":
            reader = PdfReader(BytesIO(file_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            file_type = "pdf"
        else:
            document = Document(BytesIO(file_bytes))
            text_parts = [paragraph.text for paragraph in document.paragraphs]
            text_parts.extend(
                cell.text
                for table in document.tables
                for row in table.rows
                for cell in row.cells
            )
            text = "\n".join(text_parts)
            file_type = "docx"
    except Exception as error:
        raise ResumeExtractionError(
            f"Could not read the {extension[1:].upper()} file.",
            400,
        ) from error

    if not any(character.isalnum() for character in text):
        raise ResumeExtractionError(
            "No readable text was found in the resume.",
            422,
        )

    return file_type, text.strip()