from pydantic import BaseModel, Field


class ParseResumeResponse(BaseModel):
    resume_id: str
    parse_status: str
    partial_parse: bool
    fallback_used: bool = False
    ocr_used: bool = False
    extraction_method: str | None = None
    layout_detected: str | None = None
    has_complex_layout: bool = False
    has_graphics: bool = False
    has_headers_footers: bool = False
    has_non_standard_fonts: bool = False
    event_published: bool = False
    warnings: list[str] = Field(default_factory=list)
    major_sections_found: list[str] = Field(default_factory=list)
