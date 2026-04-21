from __future__ import annotations

from io import BytesIO

from docx import Document

from app.schemas.content import ExtractionResult, TextBlock
from app.utils.text import collapse_whitespace


class DOCXExtractor:
    def extract(self, file_bytes: bytes) -> ExtractionResult:
        document = Document(BytesIO(file_bytes))
        blocks: list[TextBlock] = []
        order = 0

        for paragraph in document.paragraphs:
            text = collapse_whitespace(paragraph.text)
            if not text:
                continue
            blocks.append(TextBlock(text=text, order=order))
            order += 1

        for table in document.tables:
            for row in table.rows:
                text = collapse_whitespace(
                    " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                )
                if not text:
                    continue
                blocks.append(TextBlock(text=text, order=order))
                order += 1

        return ExtractionResult(
            blocks=blocks,
            extraction_method="python-docx",
            warnings=[],
            ocr_candidate=False,
        )
