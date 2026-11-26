import os
import shutil
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PageObject, PdfReader


class ResumeExtractionError(ValueError):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def _extract_pdf_page_ocr_text(page: PageObject) -> str:
    import pytesseract
    from PIL import Image

    configured_command = os.getenv("TESSERACT_CMD", "").strip()
    tesseract_command = shutil.which(configured_command or "tesseract")
    if tesseract_command is None and not configured_command:
        candidate = (
            Path(os.getenv("ProgramFiles", r"C:\Program Files"))
            / "Tesseract-OCR"
            / "tesseract.exe"
        )
        if candidate.is_file():
            tesseract_command = str(candidate)
    if tesseract_command is None:
        raise ResumeExtractionError(
            "OCR is unavailable for this scanned PDF.",
            503,
        )
    pytesseract.pytesseract.tesseract_cmd = tesseract_command

    image_text = []
    for embedded_image in page.images:
        with Image.open(BytesIO(embedded_image.data)) as image:
            text = pytesseract.image_to_string(image.convert("RGB"), timeout=30)
        if text.strip():
            image_text.append(text)
    return "\n".join(image_text)


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
            page_text = []
            for page in reader.pages:
                extracted_text = page.extract_text() or ""
                if not any(character.isalnum() for character in extracted_text):
                    extracted_text = _extract_pdf_page_ocr_text(page)
                page_text.append(extracted_text)
            text = "\n".join(page_text)
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
    except ResumeExtractionError:
        raise
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