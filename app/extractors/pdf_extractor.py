from __future__ import annotations

import fitz

from app.schemas.content import ExtractionResult, TextBlock
from app.utils.text import collapse_whitespace


class PDFExtractor:
    def extract(self, file_bytes: bytes) -> ExtractionResult:
        blocks: list[TextBlock] = []
        order = 0

        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            for page_index, page in enumerate(document, start=1):
                raw_blocks = page.get_text("blocks")
                raw_blocks.sort(key=lambda block: (round(block[1], 1), round(block[0], 1)))
                for raw_block in raw_blocks:
                    text = collapse_whitespace(raw_block[4])
                    if not text:
                        continue
                    blocks.append(
                        TextBlock(
                            text=text,
                            page=page_index,
                            order=order,
                            x0=float(raw_block[0]),
                            y0=float(raw_block[1]),
                            x1=float(raw_block[2]),
                            y1=float(raw_block[3]),
                        )
                    )
                    order += 1

        useful_chars = sum(len(block.text) for block in blocks)
        warnings: list[str] = []
        if useful_chars < 80:
            warnings.append("PDF text layer is very small; OCR fallback may be needed.")

        return ExtractionResult(
            blocks=blocks,
            extraction_method="pymupdf",
            warnings=warnings,
            ocr_candidate=useful_chars < 80,
        )
