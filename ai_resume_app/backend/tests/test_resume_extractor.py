import unittest
from unittest.mock import Mock, patch

from app.services.resume_extractor import extract_resume_text


class ResumeExtractorTests(unittest.TestCase):
    @patch("app.services.resume_extractor.PdfReader")
    @patch("app.services.resume_extractor._extract_pdf_page_ocr_text")
    def test_scanned_pdf_uses_ocr_when_page_has_no_text(
        self,
        mock_ocr: Mock,
        mock_pdf_reader: Mock,
    ) -> None:
        page = Mock()
        page.extract_text.return_value = ""
        mock_pdf_reader.return_value.pages = [page]
        mock_ocr.return_value = "Flutter Developer experience"

        file_type, text = extract_resume_text("resume.pdf", b"pdf bytes")

        self.assertEqual(file_type, "pdf")
        self.assertEqual(text, "Flutter Developer experience")
        mock_ocr.assert_called_once_with(page)

    @patch("app.services.resume_extractor.PdfReader")
    @patch("app.services.resume_extractor._extract_pdf_page_ocr_text")
    def test_digital_pdf_does_not_run_ocr(
        self,
        mock_ocr: Mock,
        mock_pdf_reader: Mock,
    ) -> None:
        page = Mock()
        page.extract_text.return_value = "Selectable resume text"
        mock_pdf_reader.return_value.pages = [page]

        file_type, text = extract_resume_text("resume.pdf", b"pdf bytes")

        self.assertEqual(file_type, "pdf")
        self.assertEqual(text, "Selectable resume text")
        mock_ocr.assert_not_called()

    @patch("app.services.resume_extractor.PdfReader")
    @patch(
        "app.services.resume_extractor._extract_pdf_page_ocr_text",
        return_value="",
    )
    def test_scanned_pdf_without_ocr_text_is_rejected(
        self,
        _mock_ocr: Mock,
        mock_pdf_reader: Mock,
    ) -> None:
        page = Mock()
        page.extract_text.return_value = ""
        mock_pdf_reader.return_value.pages = [page]

        with self.assertRaisesRegex(
            ValueError,
            "No readable text was found in the resume.",
        ):
            extract_resume_text("resume.pdf", b"pdf bytes")


if __name__ == "__main__":
    unittest.main()
