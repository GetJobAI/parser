from __future__ import annotations

import fitz

from app.schemas.content import ExtractionResult, TextBlock
from app.utils.text import collapse_whitespace

COMMON_FONT_KEYWORDS = (
    "arial",
    "calibri",
    "cambria",
    "courier",
    "georgia",
    "helvetica",
    "times",
    "verdana",
    "tahoma",
    "trebuchet",
    "garamond",
    "palatino",
)


class PDFExtractor:
    def extract(self, file_bytes: bytes) -> ExtractionResult:
        blocks: list[TextBlock] = []
        order = 0
        has_graphics = False
        seen_fonts: set[str] = set()

        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            for page_index, page in enumerate(document, start=1):
                if page.get_images(full=True) or page.get_drawings():
                    has_graphics = True

                text_dict = page.get_text("dict")
                for block in text_dict.get("blocks", []):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            font_name = collapse_whitespace(str(span.get("font", ""))).lower()
                            if font_name:
                                seen_fonts.add(font_name)

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

        has_non_standard_fonts = any(
            not any(keyword in font_name for keyword in COMMON_FONT_KEYWORDS)
            for font_name in seen_fonts
        )

        return ExtractionResult(
            blocks=blocks,
            extraction_method="pymupdf",
            warnings=warnings,
            ocr_candidate=useful_chars < 80,
            has_graphics=has_graphics,
            has_headers_footers=False,
            has_non_standard_fonts=has_non_standard_fonts,
        )
